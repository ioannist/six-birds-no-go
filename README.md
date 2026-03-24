# Six Birds: No-Go Theorems for Audited Emergence

This repository contains the **math-only no-go theorem paper**:

> **Six Birds: No-Go Theorems for Audited Emergence**
>
> DOI: [10.5281/zenodo.19187777](https://doi.org/10.5281/zenodo.19187777)
>
> Zenodo: https://zenodo.org/records/19187777

The paper studies finite systems observed through deterministic coarse-grainings and proves eight no-go theorems constraining when common emergence narratives can be certified honestly in a finite, auditable setting. The theorem fronts cover arrow-of-time under observation, protocol traps, graph-theoretic force obstructions, closure deficit, contractive objecthood, and bounded-interface anti-ladder results.

## What this repository provides

The repository provides:

- **Canonical theorem paper**: the main manuscript under `paper/` and the separate supplement under `paper/supplement/`
- **Machine-readable theorem spine**: authoritative theorem statements and notation registries under `docs/project/`
- **Theorem/evidence packs**: deterministic result bundles under `results/T**` covering witness suites, atlas generation, closure/objecthood packs, and Lean-facing bridge artifacts
- **Validation and audit tooling**: citation checks, theorem-paper structural validation, and red-team review runners under `scripts/`
- **Submission bundle outputs**: the built paper, supplement, flattened TeX sources, and bundle manifest generated from the canonical TeX line

## Scope and limitations

The paper is explicit about what it does and does not establish:

- The setting is finite-state and audit-oriented; the paper does not claim a general treatment of emergence in arbitrary continuous or infinite systems
- The main results are no-go theorems and obstruction statements; they delimit what can be certified under the stated hypotheses rather than providing a positive general construction theory
- The objecthood front is restricted to the strict-contraction regime and its associated total-variation consequences
- The supplement contains provenance, audit maps, fragility summaries, and formalization-status material; the main paper is intended to stand on its own mathematically

## Install

```bash
pip install -e .[dev]
```

Optional Lean-related steps depend on the local theorem-pack toolchain already present in the repository.

## Test

```bash
make test
pytest -q
```

## Reproduce

```bash
make reproduce
```

This regenerates the theorem/evidence artifacts, validation summaries, and the outward-facing submission bundle.

## Build paper

```bash
cd paper && latexmk -pdf -bibtex -interaction=nonstopmode -halt-on-error main.tex
cd paper/supplement && latexmk -pdf -bibtex -interaction=nonstopmode -halt-on-error main.tex
```

Canonical build outputs are written to:

- `paper/build/main.pdf`
- `paper/build/main_flat.tex`
- `paper/supplement/build/supplement.pdf`
- `paper/supplement/build/supplement_flat.tex`

## Submission bundle

To refresh the outward-facing bundle from the canonical TeX line:

```bash
python3 scripts/run_r15_finalize_and_bundle.py
```

This writes:

- `results/submission_bundle/main.pdf`
- `results/submission_bundle/supplement.pdf`
- `results/submission_bundle/main_flat.tex`
- `results/submission_bundle/supplement_flat.tex`
- `results/submission_bundle/source.zip`
- `results/submission_bundle/manifest.json`
