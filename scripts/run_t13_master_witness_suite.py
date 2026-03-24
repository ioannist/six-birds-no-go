#!/usr/bin/env python3
"""Run deterministic master witness suite and emit results/master artifacts."""

from __future__ import annotations

import argparse
from fractions import Fraction
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sixbirds_nogo.master_suite import REQUIRED_METRICS, run_master_suite, write_master_suite_outputs  # noqa: E402


def _parse_fraction(text: str) -> Fraction:
    if "/" in text:
        a, b = text.split("/", 1)
        return Fraction(int(a), int(b))
    return Fraction(int(text), 1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run T13 master witness suite")
    parser.add_argument("--output-dir", default="results/master")
    parser.add_argument("--precision", type=int, default=80)
    parser.add_argument("--eps-denominator", type=int, default=4)
    parser.add_argument("--eps-epsilon", default="1/4")
    args = parser.parse_args()

    eps = _parse_fraction(args.eps_epsilon)
    manifest = run_master_suite(
        precision=args.precision,
        eps_denominator=args.eps_denominator,
        eps_epsilon=eps,
    )
    write_master_suite_outputs(manifest, output_dir=args.output_dir)

    bad_status = any(r["execution_status"] != "success" for r in manifest["rows"])
    bad_metric_error = any(any(m["status"] == "error" for m in r["metrics"].values()) for r in manifest["rows"])

    unexplained = manifest["unexplained_missing_count"] > 0

    missing_without_explanation = False
    for r in manifest["rows"]:
        for key in REQUIRED_METRICS:
            m = r["metrics"][key]
            blank = m.get("value") in (None, "")
            if blank and not m.get("explanation"):
                missing_without_explanation = True
                break

    return 1 if (bad_status or bad_metric_error or unexplained or missing_without_explanation) else 0


if __name__ == "__main__":
    raise SystemExit(main())
