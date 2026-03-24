#!/usr/bin/env python3
"""Deterministic runner for the T08 path-space arrow/DPI suite."""

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

from sixbirds_nogo.arrow import horizon_sweep_arrow, utc_now_iso


def _required_case_specs() -> list[dict[str, object]]:
    horizons = [0, 1, 2, 3]
    return [
        {"witness_id": "hidden_clock_reversible", "lens_id": "identity", "horizons": horizons},
        {"witness_id": "hidden_clock_reversible", "lens_id": "observe_x_binary", "horizons": horizons},
        {"witness_id": "hidden_clock_reversible", "lens_id": "observe_clock_3", "horizons": horizons},
        {"witness_id": "hidden_clock_driven", "lens_id": "identity", "horizons": horizons},
        {"witness_id": "hidden_clock_driven", "lens_id": "observe_x_binary", "horizons": horizons},
        {"witness_id": "hidden_clock_driven", "lens_id": "observe_clock_3", "horizons": horizons},
    ]


def _csv_rows(sweep_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for r in sweep_rows:
        micro = r["micro"]
        macro = r["macro"]
        dpi = r["dpi"]
        rows.append(
            {
                "witness_id": r["witness_id"],
                "lens_id": r["lens_id"],
                "horizon": r["horizon"],
                "initial_mode": r["initial_mode"],
                "micro_kind": micro["kind"],
                "micro_decimal": "" if micro["decimal_value"] is None else micro["decimal_value"],
                "micro_support_mismatch_count": micro["support_mismatch_count"],
                "micro_term_count": len(micro["log_terms"]),
                "macro_kind": macro["kind"],
                "macro_decimal": "" if macro["decimal_value"] is None else macro["decimal_value"],
                "macro_support_mismatch_count": macro["support_mismatch_count"],
                "macro_term_count": len(macro["log_terms"]),
                "dpi_holds": str(bool(dpi["holds"])).lower(),
                "equal_value": str(bool(dpi["equal_value"])).lower(),
                "strict_loss": str(bool(dpi["strict_loss"])).lower(),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Run T08 arrow suite")
    parser.add_argument("--output-dir", default="results/T08", help="Output directory for T08 metrics")
    parser.add_argument("--precision", default=80, type=int, help="Decimal precision for finite KL evaluation")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    case_specs = _required_case_specs()
    sweep_rows = horizon_sweep_arrow(case_specs, precision=args.precision)
    csv_rows = _csv_rows(sweep_rows)

    csv_path = out_dir / "arrow_metrics.csv"
    json_path = out_dir / "arrow_metrics.json"
    manifest_path = out_dir / "case_manifest.json"

    fieldnames = [
        "witness_id",
        "lens_id",
        "horizon",
        "initial_mode",
        "micro_kind",
        "micro_decimal",
        "micro_support_mismatch_count",
        "micro_term_count",
        "macro_kind",
        "macro_decimal",
        "macro_support_mismatch_count",
        "macro_term_count",
        "dpi_holds",
        "equal_value",
        "strict_loss",
    ]

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in csv_rows:
            writer.writerow(row)

    payload = {
        "generated_at_utc": utc_now_iso(),
        "precision": args.precision,
        "rows": sweep_rows,
    }
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    manifest = {
        "generated_at_utc": utc_now_iso(),
        "case_matrix": [{"witness_id": c["witness_id"], "lens_id": c["lens_id"]} for c in case_specs],
        "horizons": [0, 1, 2, 3],
        "precision": args.precision,
        "row_count": len(sweep_rows),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {csv_path}")
    print(f"wrote {json_path}")
    print(f"wrote {manifest_path}")
    print(f"rows={len(sweep_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
