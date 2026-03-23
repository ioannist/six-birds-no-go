#!/usr/bin/env python3
"""Deterministic runner for T10 packaging/objecthood suite."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from fractions import Fraction

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sixbirds_nogo.objecthood import (  # noqa: E402
    check_approximate_object_separation,
    distribution_residual,
    dobrushin_contraction_lambda,
    epsilon_stable_distributions,
    fixed_point_count,
    solve_unique_fixed_distribution,
)
from sixbirds_nogo.packaging import (  # noqa: E402
    idempotence_defect,
    is_idempotent,
    load_packaging_from_witness,
    max_state_saturation_step,
    state_fixed_points,
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _fstr(x: Fraction | None) -> str:
    if x is None:
        return ""
    return f"{x.numerator}/{x.denominator}"


def _parse_fraction(text: str) -> Fraction:
    if "/" in text:
        a, b = text.split("/", 1)
        return Fraction(int(a), int(b))
    return Fraction(int(text), 1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run T10 objecthood suite")
    parser.add_argument("--output-dir", default="results/T10")
    parser.add_argument("--grid-denominator", type=int, default=4)
    parser.add_argument("--epsilon", default="1/4")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    epsilon = _parse_fraction(args.epsilon)
    witness_ids = [
        "contractive_unique_object",
        "noncontractive_multiobject",
        "fixed_idempotent_no_ladder",
        "lens_extension_escape",
    ]

    rows = []
    detail_rows = []

    stability_grid_payload = {}

    for wid in witness_ids:
        pkg = load_packaging_from_witness(wid)
        defect = idempotence_defect(pkg)
        idemp = is_idempotent(pkg)
        fpc = fixed_point_count(pkg)
        lam = dobrushin_contraction_lambda(pkg)

        fixed_states = ""
        sat_max = ""
        if pkg.family == "state_map":
            fixed_states = "|".join(state_fixed_points(pkg))
            sat_max = str(max_state_saturation_step(pkg))

        unique_fixed = ""
        try:
            ufd = solve_unique_fixed_distribution(pkg)
            unique_fixed = json.dumps([_fstr(x) for x in ufd], separators=(",", ":"))
        except Exception:
            ufd = None

        eps_count = ""
        bound_holds = ""
        bound_lhs = ""
        bound_rhs = ""
        grid_detail = None

        if wid == "contractive_unique_object":
            stable = epsilon_stable_distributions(pkg, args.grid_denominator, epsilon)
            eps_count = str(len(stable))

            dist_a = (Fraction(1, 2), Fraction(1, 2))
            dist_b = (Fraction(1, 1), Fraction(0, 1))
            bound = check_approximate_object_separation(pkg, dist_a, dist_b, epsilon)
            bound_holds = "" if bound["holds"] is None else str(bool(bound["holds"])).lower()
            bound_lhs = _fstr(bound["lhs_tv"])
            bound_rhs = _fstr(bound["rhs_bound"])

            grid_points = []
            all_points = []
            from sixbirds_nogo.objecthood import enumerate_simplex_grid

            for mu in enumerate_simplex_grid(pkg.states, args.grid_denominator):
                r = distribution_residual(pkg, mu)
                stable_flag = r <= epsilon
                all_points.append(
                    {
                        "point": [_fstr(x) for x in mu],
                        "residual": _fstr(r),
                        "stable": stable_flag,
                    }
                )
                if stable_flag:
                    grid_points.append([_fstr(x) for x in mu])

            grid_detail = {
                "witness_id": wid,
                "denominator": args.grid_denominator,
                "epsilon": _fstr(epsilon),
                "grid_points": all_points,
                "stable_points": grid_points,
                "bound_check": {
                    "lambda_coeff": _fstr(bound["lambda_coeff"]),
                    "epsilon": _fstr(bound["epsilon"]),
                    "residual_a": _fstr(bound["residual_a"]),
                    "residual_b": _fstr(bound["residual_b"]),
                    "premises_hold": bool(bound["premises_hold"]),
                    "lhs_tv": _fstr(bound["lhs_tv"]),
                    "rhs_bound": _fstr(bound["rhs_bound"]),
                    "holds": bound["holds"],
                },
            }
            stability_grid_payload = grid_detail

        row = {
            "witness_id": wid,
            "package_id": pkg.id,
            "family": pkg.family,
            "state_count": len(pkg.states),
            "idempotence_defect": _fstr(defect),
            "is_idempotent": str(bool(idemp)).lower(),
            "fixed_point_count": fpc,
            "contraction_lambda": _fstr(lam),
            "fixed_states": fixed_states,
            "unique_fixed_distribution": unique_fixed,
            "saturation_max_step": sat_max,
            "grid_denominator": args.grid_denominator,
            "epsilon": _fstr(epsilon),
            "eps_stable_count": eps_count,
            "bound_holds": bound_holds,
            "bound_lhs_tv": bound_lhs,
            "bound_rhs": bound_rhs,
        }
        rows.append(row)

        detail_rows.append(row)

    csv_path = out_dir / "objecthood_metrics.csv"
    json_path = out_dir / "objecthood_metrics.json"
    grid_path = out_dir / "stability_grid.json"
    manifest_path = out_dir / "case_manifest.json"

    fields = [
        "witness_id",
        "package_id",
        "family",
        "state_count",
        "idempotence_defect",
        "is_idempotent",
        "fixed_point_count",
        "contraction_lambda",
        "fixed_states",
        "unique_fixed_distribution",
        "saturation_max_step",
        "grid_denominator",
        "epsilon",
        "eps_stable_count",
        "bound_holds",
        "bound_lhs_tv",
        "bound_rhs",
    ]

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    json_path.write_text(
        json.dumps(
            {
                "generated_at_utc": _now_utc(),
                "rows": detail_rows,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    grid_path.write_text(json.dumps(stability_grid_payload, indent=2) + "\n", encoding="utf-8")

    manifest = {
        "witness_ids": witness_ids,
        "grid_denominator": args.grid_denominator,
        "epsilon": _fstr(epsilon),
        "generation_timestamp_utc": _now_utc(),
        "row_count": len(rows),
        "grid_case_count": 1,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {csv_path}")
    print(f"wrote {json_path}")
    print(f"wrote {grid_path}")
    print(f"wrote {manifest_path}")
    print(f"rows={len(rows)} grid_case_count=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
