#!/usr/bin/env python3
"""Run executable witness audits and emit deterministic manifest artifacts."""

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

from sixbirds_nogo.executable_witnesses import run_all_witnesses, serialize_execution_manifest  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run T12 executable witness manifest")
    parser.add_argument("--output-dir", default="results/T12")
    parser.add_argument("--precision", type=int, default=80)
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = run_all_witnesses(precision=args.precision)
    manifest_ser = serialize_execution_manifest(manifest)

    json_path = out_dir / "witness_manifest.json"
    csv_path = out_dir / "witness_summary.csv"

    json_path.write_text(json.dumps(manifest_ser, indent=2) + "\n", encoding="utf-8")

    fields = [
        "witness_id",
        "kind",
        "lens_count",
        "has_chain",
        "has_packaging",
        "required_audit_count",
        "executed_audit_count",
        "expectation_pass_count",
        "expectation_fail_count",
        "error_count",
        "execution_status",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in manifest_ser["witnesses"]:
            w.writerow(
                {
                    "witness_id": row["witness_id"],
                    "kind": row["kind"],
                    "lens_count": len(row["lens_ids"]),
                    "has_chain": str(row["kind"] in {"markov_chain", "phase_lift_markov"}).lower(),
                    "has_packaging": str(row["package_id"] is not None).lower(),
                    "required_audit_count": row["required_audit_count"],
                    "executed_audit_count": row["executed_audit_count"],
                    "expectation_pass_count": row["expectation_pass_count"],
                    "expectation_fail_count": row["expectation_fail_count"],
                    "error_count": row["error_count"],
                    "execution_status": row["execution_status"],
                }
            )

    print(f"wrote {json_path}")
    print(f"wrote {csv_path}")

    bad = manifest_ser["failed_count"] > 0 or manifest_ser["partial_count"] > 0 or manifest_ser["expectation_fail_count"] > 0
    if bad:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
