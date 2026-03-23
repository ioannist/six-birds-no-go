#!/usr/bin/env python3
"""Run T14 primitive-toggle matrix and theorem-coverage pre-check."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sixbirds_nogo.primitives import PRIMITIVE_IDS, run_primitive_matrix, write_primitive_outputs  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run T14 primitive matrix suite")
    parser.add_argument("--output-dir", default="results/T14")
    parser.add_argument("--precision", type=int, default=80)
    args = parser.parse_args()

    manifest = run_primitive_matrix(precision=args.precision)
    write_primitive_outputs(manifest, output_dir=args.output_dir)

    rows = manifest["rows"]

    # Failure rule 1: every registered witness has primitive toggles
    for row in rows:
        if row["row_kind"] != "registered":
            continue
        for pid in PRIMITIVE_IDS:
            if row.get(pid) not in {"on", "off", "ambiguous"}:
                return 1

    # Failure rule 2: theorem target has supporting pair or nonempty gap note
    for t in manifest["coverage"]["theorem_targets"]:
        has_pair = t.get("satisfied_pair_count", 0) > 0
        has_gap = bool(str(t.get("gap_note", "")).strip())
        if not (has_pair or has_gap):
            return 1

    # Failure rule 3: ambiguous toggle must have ambiguity note
    for row in rows:
        if row.get("ambiguous_assignment"):
            if not str(row.get("ambiguity_note", "")).strip():
                return 1

    # Failure rule 4: unresolved pair references emerge as exceptions before here.

    # Failure rule 5: outputs exist
    out = Path(args.output_dir)
    if not (out / "primitive_matrix.csv").exists():
        return 1
    if not (out / "primitive_coverage.json").exists():
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
