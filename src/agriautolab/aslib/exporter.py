"""把三目标语料拆成三个 ASlib 风格单目标 scenario；绝不偷偷加权。"""

from __future__ import annotations

import hashlib
from pathlib import Path


_OBJECTIVES = ("path_length", "headland_turns", "row_crossings")


def _quote(value: object) -> str:
    text = str(value)
    if any(ch in text for ch in " ,{}'\t"):
        return "'" + text.replace("'", "\\'") + "'"
    return text


def _write_arff(path: Path, relation: str, attributes: tuple[tuple[str, str], ...], rows: list[tuple[object, ...]]) -> None:
    lines = [f"@RELATION {_quote(relation)}", ""]
    lines.extend(f"@ATTRIBUTE {_quote(name)} {kind}" for name, kind in attributes)
    lines.extend(["", "@DATA"])
    lines.extend(",".join("?" if value is None else _quote(value) for value in row) for row in rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _fold(group_key: str, folds: int) -> int:
    """折按地块分组。

    同一地块派生出的全部实例（行方向 x 行距 x 机具）必须落在同一折。
    理由：实例特征里绝大多数只由地块多边形决定（单机具语料下 10 个里 9 个恒定，
    多机具变幅宽时也有 7 个恒定），按实例分折等于把同一块地同时放进训练与测试，
    推荐器可以靠记住地块拿分。ASlib 的 cv 固定假设实例独立；我们的实例不独立，
    所以必须扩展它——description.txt 里已声明这一偏离。
    Python hash() 每进程有随机盐，不能用；SHA-256 分折两次导出逐字节相同。
    """
    digest = hashlib.sha256(group_key.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % folds + 1


def export_aslib_scenarios(
    runs_parquet: str | Path,
    output_dir: str | Path,
    *,
    cv_folds: int,
    row_crossable: bool,
) -> tuple[Path, ...]:
    """按目标拆成三个 ASlib 风格目录，并按 crossable 分层标注。

    ASlib 原格式假设单目标；AgriAutoLab 是三目标。这里的兼容策略是“每个目标一个
    scenario”，并在 description.txt 明说三者来自同一运行语料。绝不把三目标加权成
    一个伪单目标，否则下游会误以为权重是 benchmark 的标准定义。

    row_crossable 无默认值（任务 6）：crossable 不做特征、做分层。它一变，
    crossing_penalty 从有限变 inf，可行性整体改变——可穿越与不可穿越是两个问题族，
    混在一个推荐器里训练是错的。分层的载体是 CorpusProtocol.row_crossable（进协议哈希），
    但导出目录必须自己也带上，否则两层导出的目录长得一模一样、下游无从分辨。
    """
    try:
        import pyarrow.parquet as pq
    except ImportError as error:
        raise RuntimeError("ASlib 导出需要项目声明的 pyarrow>=16") from error
    table = pq.read_table(runs_parquet)
    rows = table.to_pylist()
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    feature_names = sorted(name for name in table.column_names if name.startswith("feature__"))
    feature_cost_names = sorted(name for name in table.column_names if name.startswith("feature_cost__"))
    instances = sorted({str(row["instance_id"]) for row in rows})
    # 折的分组键是地块，不是实例：field_id 必须逐实例可查（run_corpus 的产物自带该列）。
    field_of_instance: dict[str, str] = {}
    for row in rows:
        field_of_instance.setdefault(str(row["instance_id"]), str(row["field_id"]))

    stratum = "crossable" if row_crossable else "uncrossable"
    outputs = []
    for objective in _OBJECTIVES:
        scenario = root / stratum / objective
        scenario.mkdir(parents=True, exist_ok=True)
        description = (
            f"scenario_id: agriautolab-{objective}-{stratum}\n"
            f"row_crossable: {str(row_crossable).lower()}\n"
            "stratification note: crossable is a stratum, not a feature. Flipping it turns "
            "crossing_penalty from finite to infinite, i.e. it changes feasibility itself. "
            "Crossable and uncrossable are two problem families; training one recommender over "
            "their union is a modelling error, so they are exported as separate scenario trees.\n"
            "metric: solution_quality\n"
            "maximize: false\n"
            "ASlib compatibility note: ASlib assumes a single objective. AgriAutoLab uses three objectives; "
            "therefore this export is an extension-by-splitting, not a weighted scalarization.\n"
            "Sibling scenarios: path_length, headland_turns, row_crossings. They share identical instances, "
            "algorithm runs, features, feature costs and cv folds; only solution_quality changes.\n"
            "cv note: folds are grouped by field_id, an extension of the fixed ASlib cv assumption. "
            "AgriAutoLab derives 10N instances per field (row offsets x spacings x vehicles) whose features "
            "are mostly field-determined; instances are not independent, so all instances of one field go to "
            "the same fold to prevent group leakage.\n"
            f"cv_folds: {cv_folds}\n"
        )
        (scenario / "description.txt").write_text(description, encoding="utf-8")

        run_rows = []
        for row in sorted(rows, key=lambda item: (str(item["instance_id"]), str(item["config_id"]))):
            run_rows.append((
                row["instance_id"], 1, row["config_id"],
                row.get("planning_s"), row["runstatus"], row.get(objective),
            ))
        _write_arff(
            scenario / "algorithm_runs.arff",
            f"agriautolab_{objective}_runs",
            (("instance_id", "STRING"), ("repetition", "NUMERIC"), ("algorithm", "STRING"),
             ("runtime", "NUMERIC"), ("runstatus", "{ok,timeout,memout,not_applicable,crash,other}"),
             ("quality", "NUMERIC")),
            run_rows,
        )

        first_by_instance = {}
        for row in rows:
            first_by_instance.setdefault(str(row["instance_id"]), row)
        feature_rows = [
            tuple([instance] + [first_by_instance[instance].get(name) for name in feature_names]) for instance in instances
        ]
        _write_arff(
            scenario / "feature_values.arff",
            f"agriautolab_{objective}_features",
            tuple([("instance_id", "STRING")] + [(name.removeprefix("feature__"), "NUMERIC") for name in feature_names]),
            feature_rows,
        )
        feature_cost_rows = [
            tuple([instance] + [first_by_instance[instance].get(name) for name in feature_cost_names]) for instance in instances
        ]
        _write_arff(
            scenario / "feature_costs.arff",
            f"agriautolab_{objective}_feature_costs",
            tuple([("instance_id", "STRING")] + [(name.removeprefix("feature_cost__"), "NUMERIC") for name in feature_cost_names]),
            feature_cost_rows,
        )
        cv_rows = [(instance, 1, _fold(field_of_instance[instance], cv_folds)) for instance in instances]
        _write_arff(
            scenario / "cv.arff",
            f"agriautolab_{objective}_cv",
            (("instance_id", "STRING"), ("repetition", "NUMERIC"), ("fold", "NUMERIC")),
            cv_rows,
        )
        outputs.append(scenario)
    return tuple(outputs)
