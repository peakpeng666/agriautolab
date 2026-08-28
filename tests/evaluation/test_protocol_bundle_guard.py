"""The --protocol-bundle-hash override must match the archived preregistration identity.

The first sealing script is the sole entry point for the protocol identity into the
experiment log, and the later scripts inherit it from the log; every override is
therefore validated against the bundle identity recorded at the study-001-frozen
tag before it can seal or replay.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_SCRIPT_NAMES = (
    "evaluate_pareto_optimality.py",
    "evaluate_feature_effects.py",
    "evaluate_recommender.py",
)


def _load_script(name: str):
    path = Path(__file__).resolve().parents[2] / "scripts" / name
    spec = importlib.util.spec_from_file_location(f"agriautolab_test_{path.stem}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("script_name", _SCRIPT_NAMES)
def test_override_must_match_known_bundle_identity(script_name):
    module = _load_script(script_name)
    known = module.KNOWN_PROTOCOL_BUNDLE_HASH
    assert len(known) == 64 and all(char in "0123456789abcdef" for char in known)

    entries = ({"payload": {"protocol_bundle_hash": "a" * 64}},)
    assert module._protocol_bundle_hash_from_log(entries, None) == "a" * 64
    assert module._protocol_bundle_hash_from_log((), known) == known

    with pytest.raises(ValueError, match="study-001-frozen"):
        module._protocol_bundle_hash_from_log((), "b" * 64)
    with pytest.raises(ValueError, match="study-001-frozen"):
        module._protocol_bundle_hash_from_log(entries, "b" * 64)
