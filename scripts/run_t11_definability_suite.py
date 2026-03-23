#!/usr/bin/env python3
"""Deterministic runner for T11 definability/no-ladder suite."""

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

from sixbirds_nogo.coarse import load_lens_from_witness  # noqa: E402
from sixbirds_nogo.definability import (  # noqa: E402
    empirical_definability_rate,
    fixed_interface_no_ladder_report,
    formula_definability_probability,
    formula_definable_predicate_count,
    definable_predicate_count,
    lens_extension_escape_report,
)
from sixbirds_nogo.packaging import (  # noqa: E402
    is_idempotent,
    load_packaging_from_witness,
    max_state_saturation_step,
)


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _f(fr: Fraction) -> str:
    return f"{fr.numerator}/{fr.denominator}"


def _serialize_predicate(pred: tuple[bool, ...], states: tuple[str, ...]) -> list[str]:
    return [s for s, v in zip(states, pred) if v]


def _ser_report(report: dict) -> dict:
    out = dict(report)
    out["idempotence_defect"] = _f(out["idempotence_defect"])
    out["signature_sequence"] = [list(x) for x in out["signature_sequence"]]
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Run T11 definability suite")
    parser.add_argument("--output-dir", default="results/T11")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--max-steps", type=int, default=3)
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    witness_lens_cases = [
        ("fixed_idempotent_no_ladder", "base_binary"),
        ("lens_extension_escape", "base_binary"),
        ("lens_extension_escape", "extended_ternary"),
        ("hidden_clock_reversible", "observe_x_binary"),
        ("hidden_clock_reversible", "observe_clock_3"),
        ("zero_closure_deficit_lumpable", "macro_AB"),
    ]

    random_check_cases = [
        ("fixed_idempotent_no_ladder", "base_binary", 8, False),
        ("lens_extension_escape", "extended_ternary", 8, False),
        ("hidden_clock_reversible", "observe_x_binary", 16, False),
    ]

    rows = []
    detail_rows = []
    for wid, lid in witness_lens_cases:
        lens = load_lens_from_witness(wid, lid)
        n = len(lens.domain_states)
        exact_count = definable_predicate_count(lens)
        formula_count = formula_definable_predicate_count(lens)
        exact_prob = formula_definability_probability(lens)
        fullspace = 2**n
        empirical_full = empirical_definability_rate(lens, fullspace, seed=args.seed, replace=False)

        pkg_id = ""
        idemp = ""
        sat_max = ""
        sig_stab = ""
        no_ladder = ""

        try:
            pkg = load_packaging_from_witness(wid)
            pkg_id = pkg.id
            idemp = str(bool(is_idempotent(pkg))).lower()
            if pkg.family == "state_map":
                sat_max = str(max_state_saturation_step(pkg))
                rep = fixed_interface_no_ladder_report(pkg, lens, max_steps=args.max_steps)
                sig_stab = "" if rep["stabilization_step"] is None else str(rep["stabilization_step"])
                no_ladder = str(bool(rep["no_ladder_holds"])).lower()
        except Exception:
            pass

        row = {
            "witness_id": wid,
            "lens_id": lid,
            "state_count": n,
            "interface_size": len(lens.image_states),
            "exact_definable_count": exact_count,
            "formula_definable_count": formula_count,
            "exact_probability": _f(exact_prob),
            "fullspace_sample_count": fullspace,
            "fullspace_empirical_rate": _f(empirical_full),
            "packaging_id": pkg_id,
            "is_idempotent": idemp,
            "saturation_max_step": sat_max,
            "signature_stabilization_step": sig_stab,
            "no_ladder_holds": no_ladder,
        }
        rows.append(row)
        detail_rows.append(dict(row))

    random_checks = []
    for wid, lid, sample_count, replace in random_check_cases:
        lens = load_lens_from_witness(wid, lid)
        empirical = empirical_definability_rate(lens, sample_count, seed=args.seed, replace=replace)
        exact = formula_definability_probability(lens)
        random_checks.append(
            {
                "witness_id": wid,
                "lens_id": lid,
                "seed": args.seed,
                "replace": replace,
                "sample_count": sample_count,
                "empirical_rate": _f(empirical),
                "exact_probability": _f(exact),
                "matches_exact_formula": empirical == exact,
            }
        )

    fixed_reports = []
    for wid, lid in [
        ("fixed_idempotent_no_ladder", "base_binary"),
        ("lens_extension_escape", "extended_ternary"),
    ]:
        lens = load_lens_from_witness(wid, lid)
        pkg = load_packaging_from_witness(wid)
        fixed_reports.append(_ser_report(fixed_interface_no_ladder_report(pkg, lens, max_steps=args.max_steps)))

    base_lens = load_lens_from_witness("lens_extension_escape", "base_binary")
    ext_lens = load_lens_from_witness("lens_extension_escape", "extended_ternary")
    ext_report_raw = lens_extension_escape_report(base_lens, ext_lens)
    ext_report = dict(ext_report_raw)
    ext_report["gained_predicates"] = [
        _serialize_predicate(p, base_lens.domain_states) for p in ext_report_raw["gained_predicates"]
    ]

    no_ladder_demos = {
        "fixed_interface_reports": fixed_reports,
        "extension_escape_report": ext_report,
    }

    csv_path = out_dir / "definability_metrics.csv"
    json_path = out_dir / "definability_metrics.json"
    random_path = out_dir / "random_checks.json"
    demo_path = out_dir / "no_ladder_demos.json"
    manifest_path = out_dir / "case_manifest.json"

    fields = [
        "witness_id",
        "lens_id",
        "state_count",
        "interface_size",
        "exact_definable_count",
        "formula_definable_count",
        "exact_probability",
        "fullspace_sample_count",
        "fullspace_empirical_rate",
        "packaging_id",
        "is_idempotent",
        "saturation_max_step",
        "signature_stabilization_step",
        "no_ladder_holds",
    ]

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    json_path.write_text(json.dumps({"generated_at_utc": _now_utc(), "rows": detail_rows}, indent=2) + "\n", encoding="utf-8")
    random_path.write_text(json.dumps({"generated_at_utc": _now_utc(), "rows": random_checks}, indent=2) + "\n", encoding="utf-8")
    demo_path.write_text(json.dumps({"generated_at_utc": _now_utc(), **no_ladder_demos}, indent=2) + "\n", encoding="utf-8")

    manifest = {
        "witness_lens_cases": [{"witness_id": w, "lens_id": l} for w, l in witness_lens_cases],
        "random_check_cases": [
            {"witness_id": w, "lens_id": l, "sample_count": s, "replace": r}
            for (w, l, s, r) in random_check_cases
        ],
        "no_ladder_demo_count": 3,
        "seed": args.seed,
        "max_steps": args.max_steps,
        "generation_timestamp_utc": _now_utc(),
        "row_count": len(rows),
        "random_check_count": len(random_checks),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {csv_path}")
    print(f"wrote {json_path}")
    print(f"wrote {random_path}")
    print(f"wrote {demo_path}")
    print(f"wrote {manifest_path}")
    print(f"rows={len(rows)} random_checks={len(random_checks)} demos=3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
