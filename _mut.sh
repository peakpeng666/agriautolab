#!/usr/bin/env bash
set -u
cd ~/wt/route-order-slot
PY=~/agriautolab/.venv/bin/python
export PYTHONPATH=~/wt/route-order-slot/src
S=src/agriautolab/agent/slots.py

echo "########## 变异 A：质心改回顶点算术平均 ##########"
$PY - <<'PYEOF'
import pathlib
p = pathlib.Path("src/agriautolab/agent/slots.py"); s = p.read_text(encoding="utf-8")
old = "        centroid_point = free.centroid\n        cx, cy = float(centroid_point.x), float(centroid_point.y)"
new = ("        ext = problem.field.exterior\n"
       "        cx = sum(pt.x for pt in ext) / len(ext)\n"
       "        cy = sum(pt.y for pt in ext) / len(ext)")
assert old in s, "变异 A 未匹配"
p.write_text(s.replace(old, new), encoding="utf-8")
PYEOF
$PY -m pytest tests/agent/test_route_order.py::test_field_centroid_is_encoding_independent -q 2>&1 | tail -2
git checkout -- $S

echo "########## 变异 B：基线改回取第一次变换的结果 ##########"
$PY - <<'PYEOF'
import pathlib
p = pathlib.Path("src/agriautolab/agent/slots.py"); s = p.read_text(encoding="utf-8")
old = """            base_scores = self._scores_along(function, endpoints, base_order,
                                             vehicle=vehicle, centroid=centroid, normal=normal)"""
new = """            base_scores = None"""
assert old in s, "变异 B 未匹配"
s = s.replace(old, new)
old2 = """            for step, (base_step, moved_step) in enumerate(zip(base_scores, moved_scores)):"""
new2 = """            if base_scores is None:
                base_scores = moved_scores
            for step, (base_step, moved_step) in enumerate(zip(base_scores, moved_scores)):"""
assert old2 in s, "变异 B2 未匹配"
p.write_text(s.replace(old2, new2), encoding="utf-8")
PYEOF
$PY -m pytest tests/agent/test_route_order.py::test_invariance_gate_baseline_is_the_untransformed_geometry -q 2>&1 | tail -2
git checkout -- $S

echo "########## 变异 C：闸门改回旋转地块（不隔离生成器） ##########"
$PY - <<'PYEOF'
import pathlib
p = pathlib.Path("src/agriautolab/agent/slots.py"); s = p.read_text(encoding="utf-8")
old = """            moved_endpoints = {
                swath_id: (move(start), move(end)) for swath_id, (start, end) in endpoints.items()
            }"""
new = """            from shapely.affinity import rotate as _rot, translate as _tr
            from agriautolab.geometry.validate import polygon_from_spec as _pfs, polygon_to_spec as _pts
            _rotated = problem.model_copy(update={
                "field": _pts(_tr(_rot(_pfs(problem.field), theta, origin=(0.0, 0.0), use_radians=True), tx, ty), problem.field.geometry_id),
                "obstacles": (),
            })
            moved_endpoints, _mc, _mn = self._geometry_for(_rotated, vehicle)"""
assert old in s, "变异 C 未匹配"
p.write_text(s.replace(old, new), encoding="utf-8")
PYEOF
$PY -m pytest tests/agent/test_route_order.py::test_invariance_gate_accepts_geometry_equivariant_candidate_on_asymmetric_field -q 2>&1 | tail -2
git checkout -- $S

echo "########## 还原确认 ##########"
$PY -m pytest -q 2>&1 | tail -1
git status --porcelain | head -3
