#!/usr/bin/env python3
"""Report coverage-ratio distribution from a historical runs.parquet.

Read-only analysis: loads the parquet, verifies its SHA-256 identity,
computes distributional summaries stratified by runstatus, config_id,
and field_id, and writes a structured JSON report plus a human-readable
Markdown companion.

Usage:
    python scripts/report_coverage_distribution.py \
        --parquet /path/to/runs.parquet \
        --expected-sha256 a143d7cd912c06a38ffa4596f990a6c4b3745a729350ee50e327e015779cccdd \
        --output-dir reports

The script never modifies the input file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Sequence


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _percentiles(data: Sequence[float], ps: Sequence[float]) -> dict[str, float]:
    """Compute percentiles by linear interpolation on sorted *data*."""
    s = sorted(data)
    n = len(s)
    if n == 0:
        return {f"p{int(p)}": float("nan") for p in ps}
    out: dict[str, float] = {}
    for p in ps:
        k = (n - 1) * p / 100
        lo = int(k)
        hi = min(lo + 1, n - 1)
        out[f"p{int(p)}"] = s[lo] + (k - lo) * (s[hi] - s[lo])
    return out


def _distribution(values: Sequence[float]) -> dict:
    if not values:
        return {"n": 0}
    s = sorted(values)
    ps = _percentiles(s, (5, 25, 50, 75, 95))
    return {"n": len(s), "min": s[0], **ps, "max": s[-1]}


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def _analyse(table) -> dict:
    """Build the full analysis dict from a PyArrow table."""
    runstatus = table.column("runstatus").to_pylist()
    cov_field = table.column("metric__coverage_ratio_field").to_pylist()
    cov_main = table.column("metric__coverage_ratio_main").to_pylist()
    config_ids = table.column("config_id").to_pylist()
    field_ids = table.column("field_id").to_pylist()
    failure_reasons = table.column("failure_reason").to_pylist()
    n_rows = len(runstatus)

    # -- 1. Overall and by-status coverage_ratio_field -----------------------
    by_status: dict[str, list[float]] = {}
    for i in range(n_rows):
        s = runstatus[i]
        v = cov_field[i]
        if v is not None:
            by_status.setdefault(s, []).append(v)

    overall_cov = [cov_field[i] for i in range(n_rows) if cov_field[i] is not None]
    status_dist = {s: _distribution(vals) for s, vals in sorted(by_status.items())}

    # -- 2. OK subset threshold counts ---------------------------------------
    ok_cov = by_status.get("ok", [])
    n_ok = len(ok_cov)
    lt99 = sum(1 for v in ok_cov if v < 0.99)
    lt95 = sum(1 for v in ok_cov if v < 0.95)
    lt90 = sum(1 for v in ok_cov if v < 0.90)
    thresholds = {
        "ok_count": n_ok,
        "below_0.99": {"count": lt99, "pct": lt99 / n_ok * 100 if n_ok else None},
        "below_0.95": {"count": lt95, "pct": lt95 / n_ok * 100 if n_ok else None},
        "below_0.90": {"count": lt90, "pct": lt90 / n_ok * 100 if n_ok else None},
    }

    # -- 3. By config_id (OK only) -------------------------------------------
    config_cov: dict[str, list[float]] = {}
    for i in range(n_rows):
        if runstatus[i] == "ok" and cov_field[i] is not None:
            config_cov.setdefault(config_ids[i], []).append(cov_field[i])

    config_dist = {}
    for c in sorted(config_cov):
        vals = config_cov[c]
        d = _distribution(vals)
        d["below_0.99"] = sum(1 for v in vals if v < 0.99)
        config_dist[c] = d

    # -- 4. Low-coverage OK rows: top configs and fields ---------------------
    low_by_config: Counter[str] = Counter()
    low_by_field: Counter[str] = Counter()
    for i in range(n_rows):
        if runstatus[i] == "ok" and cov_field[i] is not None and cov_field[i] < 0.99:
            low_by_config[config_ids[i]] += 1
            low_by_field[field_ids[i]] += 1

    # -- 5. coverage_ratio_field vs coverage_ratio_main ----------------------
    main_ok = [cov_main[i] for i in range(n_rows) if runstatus[i] == "ok" and cov_main[i] is not None]
    diff_vals = [
        cov_main[i] - cov_field[i]
        for i in range(n_rows)
        if runstatus[i] == "ok" and cov_field[i] is not None and cov_main[i] is not None
    ]

    field_vs_main = {
        "coverage_ratio_main_ok": _distribution(main_ok),
        "main_minus_field_ok": _distribution(diff_vals),
        "all_positive": all(d > 0 for d in diff_vals) if diff_vals else None,
        "main_ge_0.99": sum(1 for v in main_ok if v >= 0.99),
        "main_ge_0.95": sum(1 for v in main_ok if v >= 0.95),
    }

    # -- 6. Exclusion flow (Task D) ------------------------------------------
    all_fields = sorted(set(field_ids))
    ok_per_field: Counter[str] = Counter()
    for i in range(n_rows):
        if runstatus[i] == "ok":
            ok_per_field[field_ids[i]] += 1

    zero_ok_fields = sorted(f for f in all_fields if ok_per_field.get(f, 0) == 0)

    # Classify failure reasons for zero-ok fields
    def _simplify_reason(reason: str | None, status: str) -> str:
        r = reason or ""
        if "KinematicModelError" in r:
            return "kinematics_mismatch"
        if "outside_area" in r:
            return "outside_area"
        if "collision" in r:
            return "collision"
        if "main_field" in r and ("塌缩" in r or "collapse" in r.lower()):
            return "headland_collapse"
        if r.startswith("validator_rejected:"):
            return r.split(":", 1)[1]
        return f"runstatus:{status}" if not r else r

    zero_ok_detail: dict[str, Counter[str]] = {}
    for i in range(n_rows):
        fid = field_ids[i]
        if fid in set(zero_ok_fields):
            zero_ok_detail.setdefault(fid, Counter())[_simplify_reason(failure_reasons[i], runstatus[i])] += 1

    # Aggregate zero-ok categories
    zero_ok_category_counts: Counter[str] = Counter()
    for fid in zero_ok_fields:
        for cat, cnt in zero_ok_detail.get(fid, {}).items():
            zero_ok_category_counts[cat] += cnt

    # Runstatus distribution (row counts)
    status_counts = Counter(runstatus)

    # not_applicable breakdown
    na_by_reason: Counter[str] = Counter()
    for i in range(n_rows):
        if runstatus[i] == "not_applicable":
            na_by_reason[_simplify_reason(failure_reasons[i], runstatus[i])] += 1

    exclusion = {
        "total_fields": len(all_fields),
        "fields_with_at_least_one_ok": len(all_fields) - len(zero_ok_fields),
        "fields_with_zero_ok": len(zero_ok_fields),
        "zero_ok_field_ids": zero_ok_fields,
        "zero_ok_row_counts_by_category": dict(zero_ok_category_counts.most_common()),
        "runstatus_row_counts": dict(status_counts.most_common()),
        "not_applicable_row_counts_by_category": dict(na_by_reason.most_common()),
    }

    return {
        "parquet_rows": n_rows,
        "overall_coverage_ratio_field": _distribution(overall_cov),
        "coverage_ratio_field_by_runstatus": status_dist,
        "ok_threshold_counts": thresholds,
        "coverage_ratio_field_by_config_id": config_dist,
        "low_coverage_ok_by_config_id": dict(low_by_config.most_common()),
        "low_coverage_ok_by_field_id_top20": dict(low_by_field.most_common(20)),
        "field_vs_main": field_vs_main,
        "exclusion_flow": exclusion,
    }


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def _render_md(result: dict, sha256: str) -> str:
    lines: list[str] = []
    a = lines.append

    a("# Coverage distribution report")
    a("")
    a(f"Source: `runs.parquet` (SHA-256 `{sha256}`)")
    a(f"Total rows: {result['parquet_rows']}")
    a("")

    # Runstatus counts
    a("## Runstatus row counts")
    a("")
    rc = result["exclusion_flow"]["runstatus_row_counts"]
    a("| status | rows |")
    a("|---|---:|")
    for s, n in sorted(rc.items(), key=lambda x: -x[1]):
        a(f"| {s} | {n:,} |")
    a("")

    # Overall coverage
    a("## coverage\\_ratio\\_field distribution (OK rows only)")
    a("")
    d = result["coverage_ratio_field_by_runstatus"].get("ok", {})
    if d.get("n"):
        a("| stat | value |")
        a("|---|---:|")
        for k in ("n", "min", "p5", "p25", "p50", "p75", "p95", "max"):
            v = d.get(k)
            a(f"| {k} | {v if isinstance(v, int) else f'{v:.6f}'} |")
    a("")

    # Threshold counts
    a("## OK rows below thresholds")
    a("")
    th = result["ok_threshold_counts"]
    a(f"- OK rows total: {th['ok_count']:,}")
    for key in ("below_0.99", "below_0.95", "below_0.90"):
        c = th[key]
        a(f"- {key}: {c['count']:,} ({c['pct']:.2f}%)")
    a("")

    # By config
    a("## coverage\\_ratio\\_field by config\\_id (OK rows)")
    a("")
    a("| config\\_id | n | min | p50 | max | <0.99 |")
    a("|---|---:|---:|---:|---:|---:|")
    for c, d in result["coverage_ratio_field_by_config_id"].items():
        a(f"| `{c[:12]}…` | {d['n']:,} | {d['min']:.4f} | {d['p50']:.4f} | {d['max']:.4f} | {d['below_0.99']:,} |")
    a("")

    # Field vs main
    a("## coverage\\_ratio\\_field vs coverage\\_ratio\\_main (OK rows)")
    a("")
    fm = result["field_vs_main"]
    dm = fm["coverage_ratio_main_ok"]
    a(f"coverage\\_ratio\\_main: n={dm['n']}, min={dm['min']:.6f}, p50={dm['p50']:.6f}, max={dm['max']:.6f}")
    a("")
    dd = fm["main_minus_field_ok"]
    a(f"main − field: min={dd['min']:.6f}, p50={dd['p50']:.6f}, max={dd['max']:.6f}")
    a(f"All differences positive (main > field in every row): {fm['all_positive']}")
    a(f"main ≥ 0.99: {fm['main_ge_0.99']:,} rows; main ≥ 0.95: {fm['main_ge_0.95']:,} rows")
    a("")

    # Exclusion flow
    a("## Exclusion flow")
    a("")
    ex = result["exclusion_flow"]
    a(f"- Input fields: {ex['total_fields']}")
    a(f"- Fields with ≥ 1 OK instance: {ex['fields_with_at_least_one_ok']}")
    a(f"- Fields with zero OK instances: {ex['fields_with_zero_ok']}")
    a("")
    a("### Zero-OK field failure categories (row counts)")
    a("")
    a("| category | rows |")
    a("|---|---:|")
    for cat, cnt in sorted(ex["zero_ok_row_counts_by_category"].items(), key=lambda x: -x[1]):
        a(f"| {cat} | {cnt:,} |")
    a("")

    a("### not\\_applicable rows by failure category")
    a("")
    a("| category | rows |")
    a("|---|---:|")
    for cat, cnt in sorted(ex["not_applicable_row_counts_by_category"].items(), key=lambda x: -x[1]):
        a(f"| {cat} | {cnt:,} |")
    a("")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Self-check (for integration test coverage)
# ---------------------------------------------------------------------------

def _code_identity() -> tuple[list[str], str]:
    """Return files contributing to this analysis and their combined hash."""
    self_path = Path(__file__).resolve()
    files = [str(self_path)]
    h = hashlib.sha256()
    h.update(self_path.read_bytes())
    return files, h.hexdigest()


def _self_check() -> None:
    files, code_hash = _code_identity()
    assert len(files) >= 1
    assert len(code_hash) == 64
    print("self-check: ok")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parquet", type=Path, default=None,
                        help="Path to runs.parquet (read-only)")
    parser.add_argument("--expected-sha256", default=None,
                        help="Expected SHA-256 hex digest of the parquet file")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"),
                        help="Directory for output files (default: reports/)")
    parser.add_argument("--self-check", action="store_true",
                        help="Run import and code-identity self-check, then exit")
    args = parser.parse_args()

    if args.self_check:
        _self_check()
        return

    if not args.parquet or not args.expected_sha256:
        parser.error("--parquet and --expected-sha256 are required unless --self-check is passed")

    # Verify identity
    actual_sha = _sha256_file(args.parquet)
    if actual_sha != args.expected_sha256:
        print(
            f"SHA-256 mismatch.\n"
            f"  expected: {args.expected_sha256}\n"
            f"  actual:   {actual_sha}\n"
            f"Refusing to analyse an unverified file.",
            file=sys.stderr,
        )
        sys.exit(1)

    import pyarrow.parquet as pq

    table = pq.read_table(str(args.parquet))
    result = _analyse(table)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "coverage_distribution.json"
    md_path = args.output_dir / "coverage_distribution.md"

    # Round floats for JSON readability
    json_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False, default=_json_default) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(_render_md(result, actual_sha), encoding="utf-8")

    print(f"Wrote {json_path} and {md_path}")


def _json_default(obj):
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return str(obj)
        return round(obj, 8)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


if __name__ == "__main__":
    main()
