#!/usr/bin/env python3
"""Check current theorem targets, full root build, and transitive proof axioms.

The target mapping is a reviewed semantic claim, tested by CheckTargets.lean.
Compilation alone does not assess the meaning of a definition. The separate
review record documents that assessment; older schema validators are not used.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}


def theorem_targets() -> list[dict]:
    rp = "SixBirdsNoGo.RealProbability."
    rg = "SixBirdsNoGo.RealGraph."
    fi = "SixBirdsNoGo.FiniteImage."
    rows = [
        ("NG_ARROW_DPI", [rp + "markovArrowDPI", rp + "KL_pushforward_le"],
         ["RealFiniteKL", "RealArrowDPI", "RealMarkovPaths"],
         "Any current finite real probability law, stochastic rows, deterministic lens, any finite horizon; extended KL includes infinity."),
        ("NG_PROTOCOL_TRAP", [rp + "protocolTrap", rp + "detailedBalance_pathLaw_reversible"],
         ["RealMarkovPaths"],
         "Detailed balance of the initial real law with the stochastic kernel. Null states allowed. Path reversal symmetry is derived."),
        ("NG_FORCE_FOREST", [rg + "forest_exact"], ["RealGraphExactness"],
         "An actual acyclic simple graph and a real antisymmetric label on its edges. Potential identity only on edges. Finiteness is unnecessary."),
        ("NG_FORCE_NULL", [rg + "exact_closedWalk_zero"], ["RealGraphExactness"],
         "A real edge-local potential difference and a legal closed graph walk. Finiteness is unnecessary."),
        ("NG_MACRO_CLOSURE_DEFICIT", [rp + "closureTheorem", rp + "closure_variational_minimum",
                                     rp + "conditionalInfo_positive_of_distinct_fiber_rows"],
         ["RealKLMixture", "RealClosure"],
         "Arbitrary current law (time zero, or the law at time t), stochastic micro and candidate macro kernels, deterministic lens, any finite lag. CMI is independently defined. Only positive-weight rows enter support checks; null fibers permit arbitrary stochastic rows."),
        ("NG_OBJECT_CONTRACTIVE", [rp + "dobrushin_contraction", rp + "contractive_separation",
                                  rp + "contractive_stationary_unique"], ["RealTVContraction"],
         "Nonempty finite state space, genuine real stochastic rows, actual maximum row TV coefficient below one, two epsilon-stable probability laws. Full 2 epsilon/(1-coefficient) bound and uniqueness. Supplementary Banach existence/convergence argument is reviewed analytically, not exported here."),
        ("NG_LADDER_IDEM", ["SixBirdsNoGo.iterate_stabilizes_ext"], ["Idempotence"],
         "Any endomap on any carrier, with pointwise idempotence; all positive iterates equal one step."),
        ("NG_LADDER_BOUNDED_INTERFACE", [fi + "definable_cardinality", fi + "no_infinite_distinct_sequence"],
         ["FiniteImageDefinability"],
         "Arbitrary domain and codomain with finite lens image. All Boolean predicates factoring through the lens; exact cardinality and no injective sequence from Nat."),
    ]
    return [dict(theorem_id=tid, status="direct", declarations=decls,
                 modules=["SixBirdsNoGo." + m for m in modules], scope=scope)
            for tid, decls, modules, scope in rows]


def run_checked(args: list[str], cwd: Path, log: Path) -> str:
    proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    output = proc.stdout + proc.stderr
    log.write_text(output, encoding="utf-8")
    if proc.returncode:
        raise RuntimeError(f"{' '.join(args)} failed; see {log}\n{output}")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "review")
    args = parser.parse_args()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    # Remove an old success receipt before starting, so failure cannot leave a
    # stale successful certificate at the requested destination.
    receipt = out / "current-theorem-coverage.json"
    receipt.unlink(missing_ok=True)
    rows = theorem_targets()
    run_checked(["git", "diff", "--exit-code", "4cb53fa", "--", "paper"],
                ROOT, out / "paper-preservation.log")
    run_checked(["lake", "build"], ROOT / "lean", out / "lean-build.log")
    run_checked(["lake", "env", "lean", str(ROOT / "review/CheckTargets.lean")],
                ROOT / "lean", out / "target-check.log")
    axioms_text = run_checked(["lake", "env", "lean", str(ROOT / "review/CheckAxioms.lean")],
                              ROOT / "lean", out / "axioms.txt")
    matches = re.findall(r"'([^']+)' depends on axioms: \[(.*?)\]", axioms_text, re.S)
    audited = {}
    for name, body in matches:
        axioms = {x.strip() for x in body.split(",") if x.strip()}
        if not axioms <= ALLOWED_AXIOMS:
            raise RuntimeError(f"Unexpected proof axioms in {name}: {sorted(axioms - ALLOWED_AXIOMS)}")
        audited[name] = sorted(axioms)
    required = {name for row in rows for name in row["declarations"]}
    if required - audited.keys():
        raise RuntimeError(f"Missing axiom checks: {sorted(required - audited.keys())}")
    sources = [ROOT / "lean/SixBirdsNoGo.lean", ROOT / "lean/lakefile.lean",
               ROOT / "lean/lake-manifest.json", ROOT / "lean/lean-toolchain",
               ROOT / "review/CheckTargets.lean", ROOT / "review/CheckAxioms.lean",
               ROOT / "docs/project/theorem_statement_sheet.yaml",
               ROOT / "review/mathematical-review.txt", Path(__file__).resolve()]
    sources.extend(sorted((ROOT / "lean/SixBirdsNoGo").glob("*.lean")))
    sources.extend(sorted((ROOT / "src/sixbirds_nogo").glob("*.py")))
    for source in sources:
        if source.suffix == ".lean" and re.search(r"\b(sorry|admit|native_decide|axiom)\b", source.read_text()):
            raise RuntimeError(f"Forbidden hole, local axiom, or native proof shortcut in {source}")
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    data = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "evidence_role": "current_explicit_targets_and_kernel_checked_proofs",
        "review_type": "solo_review_and_adversarial_self_review",
        "semantic_review": "review/mathematical-review.txt",
        "paper_edited": False,
        "theorem_count": len(rows),
        "direct_front_count": len(rows),
        "auxiliary_front_count": 0,
        "toolchain": (ROOT / "lean/lean-toolchain").read_text().strip(),
        "verification": {"full_root_build": "passed", "explicit_target_types": "passed",
                         "transitive_axiom_audit": "passed", "source_hole_scan": "passed"},
        "axioms": audited,
        "theorems": rows,
        "source_sha256": hashes,
        "limits": ["This receipt checks the listed source content; rerun after source changes.",
                   "Finite experiment log values use uncertified Decimal evaluation; probability laws and regime classifications use exact rational arithmetic.",
                   "Older T20–T44 labels are historical schema/provenance claims, not proof certificates.",
                   "The paper and its historical formalization summaries await the separately requested editing phase."],
    }
    receipt.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Checked {len(rows)} theorem targets; full Lean build and axiom audit passed.\n{receipt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
