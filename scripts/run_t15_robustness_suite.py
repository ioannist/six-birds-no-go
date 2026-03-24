#!/usr/bin/env python3
"""Run T15 robustness sweeps and adversarial diagnostics."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sixbirds_nogo.robustness import run_t15_suite, write_t15_outputs  # noqa: E402


REQUIRED_FILES = [
    "horizon_lens_sweep.csv",
    "initial_distribution_sweep.csv",
    "perturbation_sweep.csv",
    "threshold_sweep.csv",
    "objecthood_metric_sweep.csv",
    "adversarial_cases.json",
    "fragility_summary.json",
    "fragility_notes.md",
    "case_manifest.json",
]


def _validate_outputs(output_dir: Path) -> bool:
    try:
        for name in REQUIRED_FILES:
            p = output_dir / name
            if not p.exists() or p.stat().st_size == 0:
                return False

        # parse CSV / JSON shape smoke
        for name in [
            "horizon_lens_sweep.csv",
            "initial_distribution_sweep.csv",
            "perturbation_sweep.csv",
            "threshold_sweep.csv",
            "objecthood_metric_sweep.csv",
        ]:
            with (output_dir / name).open(encoding="utf-8") as f:
                list(csv.DictReader(f))

        json.loads((output_dir / "adversarial_cases.json").read_text(encoding="utf-8"))
        json.loads((output_dir / "fragility_summary.json").read_text(encoding="utf-8"))
        json.loads((output_dir / "case_manifest.json").read_text(encoding="utf-8"))
        return True
    except Exception:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Run T15 robustness suite")
    parser.add_argument("--output-dir", default="results/T15")
    parser.add_argument("--precision", type=int, default=80)
    parser.add_argument("--max-horizon", type=int, default=5)
    args = parser.parse_args()

    manifest = run_t15_suite(precision=args.precision, max_horizon=args.max_horizon)
    write_t15_outputs(manifest, output_dir=args.output_dir)

    out = Path(args.output_dir)

    if manifest["adversarial_cases"]["case_count"] < 3:
        return 1

    if not any(bool(c.get("material_divergence")) for c in manifest["adversarial_cases"]["cases"]):
        return 1

    if manifest["fragility_summary"]["fragility_count"] == 0:
        return 1

    if not _validate_outputs(out):
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
