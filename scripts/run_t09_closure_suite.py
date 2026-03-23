#!/usr/bin/env python3
"""Deterministic runner for T09 closure-deficit suite."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sixbirds_nogo.closure_deficit import (  # noqa: E402
    best_macro_gap,
    best_macro_kernel,
    closure_deficit,
    grid_search_two_state_macro_kernels,
    grouped_kl_equal,
    packaged_future_laws,
)
from sixbirds_nogo.coarse import is_strongly_lumpable, load_lens_from_witness
from sixbirds_nogo.markov import load_chain_from_witness


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _grouped_to_json(v) -> dict:
    return {
        "kind": v.kind,
        "support_mismatch_count": v.support_mismatch_count,
        "log_terms": [
            {
                "ratio": f"{r.numerator}/{r.denominator}",
                "coeff": f"{c.numerator}/{c.denominator}",
            }
            for r, c in v.log_terms
        ],
        "decimal_value": None if v.decimal_value is None else str(v.decimal_value),
        "precision": v.precision,
    }


def _kernel_rows_to_str(kernel) -> list[list[str]]:
    return [[f"{x.numerator}/{x.denominator}" for x in row] for row in kernel.matrix]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run T09 closure-deficit suite")
    parser.add_argument("--output-dir", default="results/T09")
    parser.add_argument("--precision", type=int, default=80)
    parser.add_argument("--grid-denominator", type=int, default=12)
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cases = [
        {"witness_id": "zero_closure_deficit_lumpable", "lens_id": "macro_AB", "tau": 0},
        {"witness_id": "zero_closure_deficit_lumpable", "lens_id": "macro_AB", "tau": 1},
        {"witness_id": "positive_closure_deficit", "lens_id": "macro_AB", "tau": 0},
        {"witness_id": "positive_closure_deficit", "lens_id": "macro_AB", "tau": 1},
    ]

    rows = []
    detailed_rows = []
    for case in cases:
        wid = case["witness_id"]
        lid = case["lens_id"]
        tau = case["tau"]

        chain = load_chain_from_witness(wid)
        lens = load_lens_from_witness(wid, lid)
        initial_mode = "stationary"

        cdef = closure_deficit(chain, lens, tau, initial_dist=chain.stationary_distribution, precision=args.precision)
        bgap = best_macro_gap(chain, lens, tau, initial_dist=chain.stationary_distribution, precision=args.precision)
        kstar = best_macro_kernel(chain, lens, tau, initial_dist=chain.stationary_distribution)
        p_laws = packaged_future_laws(chain, lens, tau)

        distinct_packaged = len(set(p_laws.values()))

        row = {
            "witness_id": wid,
            "lens_id": lid,
            "tau": tau,
            "initial_mode": initial_mode,
            "strong_lumpable": str(bool(is_strongly_lumpable(chain, lens))).lower(),
            "closure_kind": cdef.kind,
            "closure_decimal": "" if cdef.decimal_value is None else str(cdef.decimal_value),
            "closure_term_count": len(cdef.log_terms),
            "best_gap_kind": bgap.kind,
            "best_gap_decimal": "" if bgap.decimal_value is None else str(bgap.decimal_value),
            "best_gap_term_count": len(bgap.log_terms),
            "variational_match": str(bool(grouped_kl_equal(cdef, bgap))).lower(),
            "best_kernel_rows": json.dumps(_kernel_rows_to_str(kstar), separators=(",", ":")),
            "packaged_future_distinct_count": distinct_packaged,
        }
        rows.append(row)

        detailed_rows.append(
            {
                "witness_id": wid,
                "lens_id": lid,
                "tau": tau,
                "initial_mode": initial_mode,
                "strong_lumpable": row["strong_lumpable"] == "true",
                "closure": _grouped_to_json(cdef),
                "best_gap": _grouped_to_json(bgap),
                "variational_match": row["variational_match"] == "true",
                "best_kernel_rows": _kernel_rows_to_str(kstar),
                "packaged_future_laws": {
                    x: [f"{v.numerator}/{v.denominator}" for v in p_laws[x]] for x in chain.states
                },
                "packaged_future_distinct_count": distinct_packaged,
                "precision": args.precision,
            }
        )

    grid_cases = [
        {"witness_id": "zero_closure_deficit_lumpable", "lens_id": "macro_AB", "tau": 1},
        {"witness_id": "positive_closure_deficit", "lens_id": "macro_AB", "tau": 1},
    ]

    grid_entries = []
    for gc in grid_cases:
        chain = load_chain_from_witness(gc["witness_id"])
        lens = load_lens_from_witness(gc["witness_id"], gc["lens_id"])
        res = grid_search_two_state_macro_kernels(
            chain,
            lens,
            gc["tau"],
            denominator=args.grid_denominator,
            initial_dist=chain.stationary_distribution,
            precision=args.precision,
        )
        res.update(
            {
                "witness_id": gc["witness_id"],
                "lens_id": gc["lens_id"],
                "tau": gc["tau"],
            }
        )
        grid_entries.append(res)

    csv_path = out_dir / "closure_metrics.csv"
    json_path = out_dir / "closure_metrics.json"
    grid_path = out_dir / "grid_check.json"
    manifest_path = out_dir / "case_manifest.json"

    fieldnames = [
        "witness_id",
        "lens_id",
        "tau",
        "initial_mode",
        "strong_lumpable",
        "closure_kind",
        "closure_decimal",
        "closure_term_count",
        "best_gap_kind",
        "best_gap_decimal",
        "best_gap_term_count",
        "variational_match",
        "best_kernel_rows",
        "packaged_future_distinct_count",
    ]

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)

    json_path.write_text(
        json.dumps(
            {
                "generated_at_utc": _now_utc(),
                "precision": args.precision,
                "rows": detailed_rows,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    grid_path.write_text(
        json.dumps(
            {
                "generated_at_utc": _now_utc(),
                "precision": args.precision,
                "grid_denominator": args.grid_denominator,
                "entries": grid_entries,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = {
        "generated_at_utc": _now_utc(),
        "case_matrix": cases,
        "taus": sorted({c["tau"] for c in cases}),
        "grid_denominator": args.grid_denominator,
        "precision": args.precision,
        "row_count": len(rows),
        "grid_check_count": len(grid_entries),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {csv_path}")
    print(f"wrote {json_path}")
    print(f"wrote {grid_path}")
    print(f"wrote {manifest_path}")
    print(f"rows={len(rows)} grid_checks={len(grid_entries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
