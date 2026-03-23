#!/usr/bin/env python3
"""Run the T19 end-to-end reproducibility pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sixbirds_nogo.repro import run_repro_pipeline  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run T19 reproducibility pipeline")
    parser.add_argument("--manifest-dir", default="results/manifest")
    parser.add_argument("--precision", type=int, default=80)
    parser.add_argument("--skip-pytest", action="store_true")
    parser.add_argument("--skip-lean", action="store_true")
    args = parser.parse_args()

    manifest = run_repro_pipeline(
        manifest_dir=args.manifest_dir,
        precision=args.precision,
        skip_pytest=args.skip_pytest,
        skip_lean=args.skip_lean,
    )
    return 0 if manifest.get("status") == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
