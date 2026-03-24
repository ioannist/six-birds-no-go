import json
from pathlib import Path
import subprocess
import sys


REQUIRED_THEOREMS = {
    "NG_ARROW_DPI",
    "NG_PROTOCOL_TRAP",
    "NG_FORCE_FOREST",
    "NG_FORCE_NULL",
    "NG_MACRO_CLOSURE_DEFICIT",
    "NG_OBJECT_CONTRACTIVE",
    "NG_LADDER_IDEM",
    "NG_LADDER_BOUNDED_INTERFACE",
}


def test_validator_passes_on_committed_configs() -> None:
    proc = subprocess.run(
        [sys.executable, "scripts/validate_configs.py", "--summary"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "PASS" in proc.stdout


def test_required_theorem_ids_present() -> None:
    data = json.loads(Path("configs/theorems.yaml").read_text(encoding="utf-8"))
    ids = {item["id"] for item in data["theorems"]}
    assert ids == REQUIRED_THEOREMS


def test_validator_rejects_proxy_audit_in_theorem_required_audits(tmp_path: Path) -> None:
    cfg_dir = tmp_path / "configs"
    cfg_dir.mkdir()
    for name in ("assumptions.yaml", "theorems.yaml", "proxies.yaml"):
        cfg_dir.joinpath(name).write_text(Path("configs", name).read_text(encoding="utf-8"), encoding="utf-8")

    theorems = json.loads(cfg_dir.joinpath("theorems.yaml").read_text(encoding="utf-8"))
    theorems["theorems"][0]["required_audits"] = ["PROXY_MACRO_MARKOV_ARROW"]
    cfg_dir.joinpath("theorems.yaml").write_text(json.dumps(theorems, indent=2) + "\n", encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, "scripts/validate_configs.py", "--config-dir", str(cfg_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
    assert "unknown theorem audit" in proc.stdout
