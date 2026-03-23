"""Deterministic robustness sweeps and adversarial diagnostics for T15."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from fractions import Fraction
import csv
import json
from pathlib import Path
from typing import Any, Callable

from sixbirds_nogo.affinity import is_exact_oneform, max_cycle_affinity
from sixbirds_nogo.arrow import (
    PathKLDivergence,
    honest_observed_path_reversal_kl,
    micro_path_reversal_kl,
    path_reversal_kl_from_law,
)
from sixbirds_nogo.coarse import DeterministicLens, load_lens_from_witness
from sixbirds_nogo.definability import definable_predicate_count
from sixbirds_nogo.graph_cycle import cycle_rank
from sixbirds_nogo.markov import (
    FiniteMarkovChain,
    parse_probability_matrix,
    pushforward_distribution,
    solve_stationary_distribution,
)
from sixbirds_nogo.objecthood import (
    epsilon_stable_distributions,
    total_variation_distance,
)
from sixbirds_nogo.packaging import load_packaging_from_witness
from sixbirds_nogo.proxy_macro_fit import fit_proxy_macro_chain, proxy_path_law
from sixbirds_nogo.witnesses import load_witness


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def serialize_fraction(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def serialize_decimal(value: Decimal) -> str:
    return str(value)


def scalarize_kl_like(value: Any) -> tuple[str, str]:
    obj: Any = value
    if isinstance(value, dict):
        obj = value
    if isinstance(obj, dict) and "kind" in obj:
        kind = str(obj["kind"])
        if kind == "zero":
            return "0", "zero"
        if kind == "infinite":
            return "Infinity", "infinite"
        if kind == "finite_positive":
            return str(obj.get("decimal_value")), "finite_positive"
        return "", kind

    if not isinstance(obj, PathKLDivergence):
        raise ValueError("unsupported KL-like object")
    if obj.kind == "zero":
        return "0", "zero"
    if obj.kind == "infinite":
        return "Infinity", "infinite"
    return serialize_decimal(obj.decimal_value if obj.decimal_value is not None else Decimal(0)), "finite_positive"


def _parse_scalar(value: Any, kind: str | None = None) -> Any:
    if kind == "zero":
        return Decimal(0)
    if kind == "infinite":
        return Decimal("Infinity")
    if value is None or value == "":
        return None
    if isinstance(value, (int, bool, Fraction, Decimal)):
        return value
    if isinstance(value, str):
        t = value.strip()
        if t == "Infinity":
            return Decimal("Infinity")
        if "/" in t:
            a, b = t.split("/", 1)
            return Fraction(int(a), int(b))
        if t.lstrip("-").isdigit():
            return Decimal(int(t))
        return Decimal(t)
    return value


def _material_proxy_divergence(h_scalar: str, h_kind: str, p_scalar: str, p_kind: str) -> bool:
    if h_kind != p_kind:
        return True
    if h_kind == "zero" and p_kind == "finite_positive":
        return True
    if h_kind == "finite_positive" and p_kind == "finite_positive":
        h = _parse_scalar(h_scalar)
        p = _parse_scalar(p_scalar)
        return abs(h - p) > Decimal("0.1")
    return False


def convex_mix_chains(chain_a: FiniteMarkovChain, chain_b: FiniteMarkovChain, alpha: Fraction) -> FiniteMarkovChain:
    if chain_a.states != chain_b.states:
        raise ValueError("chain states must match for convex mix")
    if alpha < 0 or alpha > 1:
        raise ValueError("alpha must be in [0,1]")

    one_minus = Fraction(1, 1) - alpha
    n = chain_a.size
    mixed_rows: list[tuple[Fraction, ...]] = []
    for i in range(n):
        row: list[Fraction] = []
        for j in range(n):
            row.append(one_minus * chain_a.matrix[i][j] + alpha * chain_b.matrix[i][j])
        mixed_rows.append(tuple(row))
    matrix = tuple(mixed_rows)
    mixed = FiniteMarkovChain(states=chain_a.states, matrix=matrix)
    pi = solve_stationary_distribution(mixed)
    return FiniteMarkovChain(states=chain_a.states, matrix=matrix, stationary_distribution=pi)


def threshold_support_proxy(chain: FiniteMarkovChain, floor: Fraction, include_self_loops: bool = False) -> dict:
    if floor < 0:
        raise ValueError("floor must be nonnegative")
    states = chain.states
    idx = {s: i for i, s in enumerate(states)}

    directed: list[tuple[str, str]] = []
    for i, u in enumerate(states):
        for j, v in enumerate(states):
            if not include_self_loops and i == j:
                continue
            if chain.matrix[i][j] >= floor and chain.matrix[i][j] > 0:
                directed.append((u, v))

    directed_set = set(directed)
    bidirected_pairs: set[tuple[str, str]] = set()
    one_way_directed: list[tuple[str, str]] = []
    one_way_pairs: set[tuple[str, str]] = set()

    for u, v in directed:
        if (v, u) in directed_set:
            a, b = (u, v) if idx[u] < idx[v] else (v, u)
            bidirected_pairs.add((a, b))
        else:
            one_way_directed.append((u, v))
            a, b = (u, v) if idx[u] < idx[v] else (v, u)
            one_way_pairs.add((a, b))

    undirected_pairs: set[tuple[str, str]] = set()
    for u, v in directed:
        if u == v:
            continue
        a, b = (u, v) if idx[u] < idx[v] else (v, u)
        undirected_pairs.add((a, b))

    n = len(states)
    m = len(undirected_pairs)

    parent = {s: s for s in states}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra = find(a)
        rb = find(b)
        if ra != rb:
            parent[rb] = ra

    for a, b in undirected_pairs:
        union(a, b)
    c = len({find(s) for s in states})
    cycle_rank_val = m - n + c

    return {
        "floor": floor,
        "retained_directed_edges": tuple(sorted(directed, key=lambda e: (idx[e[0]], idx[e[1]]))),
        "retained_directed_edge_count": len(directed),
        "retained_bidirected_edge_count": len(bidirected_pairs),
        "one_way_directed_edges": tuple(sorted(one_way_directed, key=lambda e: (idx[e[0]], idx[e[1]]))),
        "one_way_directed_edge_count": len(one_way_directed),
        "one_way_pair_count": len(one_way_pairs),
        "thresholded_support_cycle_rank": cycle_rank_val,
    }


def support_signature_distance(dist_a: tuple[Fraction, ...], dist_b: tuple[Fraction, ...]) -> Fraction:
    supp_a = tuple(i for i, x in enumerate(dist_a) if x > 0)
    supp_b = tuple(i for i, x in enumerate(dist_b) if x > 0)
    return Fraction(0, 1) if supp_a == supp_b else Fraction(1, 1)


def connected_cluster_count(
    points: tuple[tuple[Fraction, ...], ...],
    distance_fn: Callable[[tuple[Fraction, ...], tuple[Fraction, ...]], Fraction],
    threshold: Fraction,
) -> int:
    n = len(points)
    if n == 0:
        return 0

    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri = find(i)
        rj = find(j)
        if ri != rj:
            parent[rj] = ri

    for i in range(n):
        for j in range(i + 1, n):
            if distance_fn(points[i], points[j]) <= threshold:
                union(i, j)

    return len({find(i) for i in range(n)})


def _load_chain(witness_id: str) -> FiniteMarkovChain:
    from sixbirds_nogo.markov import load_chain_from_witness

    return load_chain_from_witness(witness_id)


def _proxy_macro_kl(chain: FiniteMarkovChain, lens: DeterministicLens, horizon: int, initial_dist: Any) -> PathKLDivergence:
    fit = fit_proxy_macro_chain(chain, lens, initial_dist=initial_dist)
    law = proxy_path_law(fit, horizon=horizon)
    return path_reversal_kl_from_law(law, precision=80)


def run_horizon_lens_sweep(precision: int = 80, max_horizon: int = 5) -> list[dict]:
    rows: list[dict] = []
    cases = [
        ("hidden_clock_reversible", ("identity", "observe_x_binary", "observe_clock_3")),
        ("hidden_clock_driven", ("identity", "observe_x_binary", "observe_clock_3")),
    ]
    for witness_id, lens_ids in cases:
        chain = _load_chain(witness_id)
        init = chain.stationary_distribution
        if init is None:
            raise ValueError(f"{witness_id} requires stationary distribution")
        for lens_id in lens_ids:
            lens = load_lens_from_witness(witness_id, lens_id)
            for horizon in range(0, max_horizon + 1):
                micro = micro_path_reversal_kl(chain, horizon, initial_dist=init, precision=precision)
                honest = honest_observed_path_reversal_kl(chain, lens, horizon, initial_dist=init, precision=precision)
                micro_scalar, micro_kind = scalarize_kl_like(micro)
                honest_scalar, honest_kind = scalarize_kl_like(honest)

                proxy_scalar = ""
                proxy_kind = ""
                proxy_diverges = False
                proxy_note = "not_applicable:identity_lens" if lens_id == "identity" else ""
                if lens_id != "identity":
                    proxy = _proxy_macro_kl(chain, lens, horizon, init)
                    proxy_scalar, proxy_kind = scalarize_kl_like(proxy)
                    proxy_diverges = _material_proxy_divergence(honest_scalar, honest_kind, proxy_scalar, proxy_kind)

                rows.append(
                    {
                        "witness_id": witness_id,
                        "lens_id": lens_id,
                        "horizon": horizon,
                        "initial_mode": "stationary",
                        "micro_arrow_kl": micro_scalar,
                        "micro_arrow_kind": micro_kind,
                        "macro_arrow_kl_honest": honest_scalar,
                        "macro_arrow_kind_honest": honest_kind,
                        "macro_arrow_kl_proxy": proxy_scalar,
                        "macro_arrow_kind_proxy": proxy_kind,
                        "proxy_diverges_materially": proxy_diverges,
                        "proxy_explanation": proxy_note,
                        "interface_size": len(lens.image_states),
                        "definable_predicate_count": definable_predicate_count(lens),
                    }
                )
    rows.sort(key=lambda r: (r["witness_id"], r["lens_id"], r["horizon"]))
    return rows


def _delta(chain: FiniteMarkovChain, state: str) -> tuple[Fraction, ...]:
    idx = chain.index_of(state)
    return tuple(Fraction(1, 1) if i == idx else Fraction(0, 1) for i in range(chain.size))


def run_initial_distribution_sweep(precision: int = 80) -> list[dict]:
    rows: list[dict] = []

    # Family 1
    chain = _load_chain("hidden_clock_reversible")
    lens = load_lens_from_witness("hidden_clock_reversible", "identity")
    initials: list[tuple[str, tuple[Fraction, ...] | None]] = [("stationary", chain.stationary_distribution)]
    initials.extend((f"delta_{s}", _delta(chain, s)) for s in chain.states)

    for init_id, init in initials:
        if init is None:
            raise ValueError("hidden_clock_reversible missing stationary distribution")
        micro = micro_path_reversal_kl(chain, 3, initial_dist=init, precision=precision)
        honest = honest_observed_path_reversal_kl(chain, lens, 3, initial_dist=init, precision=precision)
        m_scalar, m_kind = scalarize_kl_like(micro)
        h_scalar, h_kind = scalarize_kl_like(honest)
        rows.append(
            {
                "witness_id": "hidden_clock_reversible",
                "lens_id": "identity",
                "horizon": 3,
                "initial_id": init_id,
                "micro_arrow_kl": m_scalar,
                "micro_arrow_kind": m_kind,
                "macro_arrow_kl_honest": h_scalar,
                "macro_arrow_kind_honest": h_kind,
                "macro_arrow_kl_proxy": "",
                "macro_arrow_kind_proxy": "",
                "proxy_diverges_materially": False,
            }
        )

    # Family 2
    chain = _load_chain("hidden_clock_driven")
    lens = load_lens_from_witness("hidden_clock_driven", "observe_x_binary")
    init_stationary = chain.stationary_distribution
    if init_stationary is None:
        raise ValueError("hidden_clock_driven missing stationary distribution")

    init_family = [
        ("stationary", init_stationary),
        ("phase0_balanced", (Fraction(1, 2), Fraction(1, 2), Fraction(0, 1), Fraction(0, 1))),
        ("phase1_balanced", (Fraction(0, 1), Fraction(0, 1), Fraction(1, 2), Fraction(1, 2))),
    ]

    for horizon in (2, 3):
        for init_id, init in init_family:
            micro = micro_path_reversal_kl(chain, horizon, initial_dist=init, precision=precision)
            honest = honest_observed_path_reversal_kl(chain, lens, horizon, initial_dist=init, precision=precision)
            proxy = _proxy_macro_kl(chain, lens, horizon, init)
            m_scalar, m_kind = scalarize_kl_like(micro)
            h_scalar, h_kind = scalarize_kl_like(honest)
            p_scalar, p_kind = scalarize_kl_like(proxy)

            rows.append(
                {
                    "witness_id": "hidden_clock_driven",
                    "lens_id": "observe_x_binary",
                    "horizon": horizon,
                    "initial_id": init_id,
                    "micro_arrow_kl": m_scalar,
                    "micro_arrow_kind": m_kind,
                    "macro_arrow_kl_honest": h_scalar,
                    "macro_arrow_kind_honest": h_kind,
                    "macro_arrow_kl_proxy": p_scalar,
                    "macro_arrow_kind_proxy": p_kind,
                    "proxy_diverges_materially": _material_proxy_divergence(h_scalar, h_kind, p_scalar, p_kind),
                }
            )

    rows.sort(key=lambda r: (r["witness_id"], r["lens_id"], r["horizon"], r["initial_id"]))
    return rows


def _tiny_reversible_triangle() -> FiniteMarkovChain:
    states = ("0", "1", "2")
    matrix = parse_probability_matrix(
        [
            ["389/500", "111/1000", "111/1000"],
            ["111/10000", "4889/5000", "111/10000"],
            ["111/100000", "111/100000", "49889/50000"],
        ]
    )
    pi = (Fraction(1, 111), Fraction(10, 111), Fraction(100, 111))
    return FiniteMarkovChain(states=states, matrix=matrix, stationary_distribution=pi)


def run_threshold_sweep() -> list[dict]:
    chain = _tiny_reversible_triangle()
    floors = [Fraction(0, 1), Fraction(1, 1000), Fraction(1, 100), Fraction(1, 50)]
    original_cycle = cycle_rank(chain)
    original_exactness = is_exact_oneform(chain)

    rows: list[dict] = []
    for floor in floors:
        proxy = threshold_support_proxy(chain, floor)
        rows.append(
            {
                "case_id": "tiny_reversible_triangle",
                "floor": serialize_fraction(floor),
                "retained_directed_edge_count": proxy["retained_directed_edge_count"],
                "retained_bidirected_edge_count": proxy["retained_bidirected_edge_count"],
                "one_way_directed_edge_count": proxy["one_way_directed_edge_count"],
                "one_way_pair_count": proxy["one_way_pair_count"],
                "one_way_edges": ";".join(f"{u}->{v}" for u, v in proxy["one_way_directed_edges"]),
                "thresholded_support_cycle_rank": proxy["thresholded_support_cycle_rank"],
                "original_cycle_rank": original_cycle,
                "original_exactness_flag": original_exactness,
                "note": "threshold proxy diagnostics over tiny reversible triangle",
            }
        )
    return rows


def run_perturbation_sweep(precision: int = 80) -> list[dict]:
    rows: list[dict] = []
    alphas = [Fraction(0, 1), Fraction(1, 20), Fraction(1, 10), Fraction(1, 5), Fraction(1, 2), Fraction(1, 1)]

    # Family 1 hidden_clock_mix
    h_rev = _load_chain("hidden_clock_reversible")
    h_drv = _load_chain("hidden_clock_driven")
    lens_x = load_lens_from_witness("hidden_clock_driven", "observe_x_binary")
    lens_c = load_lens_from_witness("hidden_clock_driven", "observe_clock_3")

    for alpha in alphas:
        mix = convex_mix_chains(h_rev, h_drv, alpha)
        init = mix.stationary_distribution
        if init is None:
            raise ValueError("mixed hidden-clock chain missing stationary distribution")

        micro = micro_path_reversal_kl(mix, 3, initial_dist=init, precision=precision)
        macro_x = honest_observed_path_reversal_kl(mix, lens_x, 3, initial_dist=init, precision=precision)
        macro_c = honest_observed_path_reversal_kl(mix, lens_c, 3, initial_dist=init, precision=precision)

        micro_s, micro_k = scalarize_kl_like(micro)
        x_s, x_k = scalarize_kl_like(macro_x)
        c_s, c_k = scalarize_kl_like(macro_c)

        rows.append(
            {
                "family_id": "hidden_clock_mix",
                "alpha": alpha,
                "micro_arrow_kl": micro_s,
                "micro_arrow_kind": micro_k,
                "macro_arrow_observe_x_binary": x_s,
                "macro_arrow_observe_x_binary_kind": x_k,
                "macro_arrow_observe_clock_3": c_s,
                "macro_arrow_observe_clock_3_kind": c_k,
                "max_cycle_affinity": "",
                "exactness_flag": "",
            }
        )

    # Family 2 cycle_drive_mix
    c_rev = _load_chain("rev_cycle_3")
    c_drv = _load_chain("biased_cycle_3")
    for alpha in alphas:
        mix = convex_mix_chains(c_rev, c_drv, alpha)
        rows.append(
            {
                "family_id": "cycle_drive_mix",
                "alpha": alpha,
                "micro_arrow_kl": "",
                "micro_arrow_kind": "",
                "macro_arrow_observe_x_binary": "",
                "macro_arrow_observe_x_binary_kind": "",
                "macro_arrow_observe_clock_3": "",
                "macro_arrow_observe_clock_3_kind": "",
                "max_cycle_affinity": max_cycle_affinity(mix),
                "exactness_flag": is_exact_oneform(mix),
            }
        )

    rows.sort(key=lambda r: (r["family_id"], r["alpha"]))
    return rows


def run_objecthood_metric_sweep() -> list[dict]:
    pkg = load_packaging_from_witness("contractive_unique_object")
    eps = Fraction(1, 4)
    den = 4
    points = epsilon_stable_distributions(pkg, denominator=den, epsilon=eps)
    threshold = Fraction(1, 2)

    tv_count = connected_cluster_count(points, total_variation_distance, threshold)
    sig_count = connected_cluster_count(points, support_signature_distance, threshold)

    point_str = ";".join(
        ",".join(serialize_fraction(x) for x in p)
        for p in points
    )

    return [
        {
            "witness_id": "contractive_unique_object",
            "metric_id": "tv",
            "cluster_threshold": serialize_fraction(threshold),
            "stable_point_count": len(points),
            "cluster_count": tv_count,
            "points": point_str,
        },
        {
            "witness_id": "contractive_unique_object",
            "metric_id": "support_signature",
            "cluster_threshold": serialize_fraction(threshold),
            "stable_point_count": len(points),
            "cluster_count": sig_count,
            "points": point_str,
        },
    ]


def build_adversarial_cases(precision: int = 80) -> dict:
    initial_rows = run_initial_distribution_sweep(precision=precision)
    horizon_rows = run_horizon_lens_sweep(precision=precision, max_horizon=5)
    threshold_rows = run_threshold_sweep()
    objecthood_rows = run_objecthood_metric_sweep()

    def find_initial(initial_id: str, horizon: int) -> dict:
        for row in initial_rows:
            if (
                row["witness_id"] == "hidden_clock_driven"
                and row["lens_id"] == "observe_x_binary"
                and row["initial_id"] == initial_id
                and row["horizon"] == horizon
            ):
                return row
        raise ValueError("required initial-sweep row not found")

    def find_horizon(lens_id: str, horizon: int) -> dict:
        for row in horizon_rows:
            if (
                row["witness_id"] == "hidden_clock_driven"
                and row["lens_id"] == lens_id
                and row["horizon"] == horizon
            ):
                return row
        raise ValueError("required horizon-sweep row not found")

    thr_100 = next(r for r in threshold_rows if r["floor"] == "1/100")
    tv_row = next(r for r in objecthood_rows if r["metric_id"] == "tv")
    sig_row = next(r for r in objecthood_rows if r["metric_id"] == "support_signature")

    row_spurious = find_initial("phase1_balanced", 2)
    row_under = find_horizon("observe_clock_3", 3)

    cases = [
        {
            "case_id": "proxy_spurious_macro_arrow_nonstationary",
            "proxy_id": "PROXY_MACRO_MARKOV_ARROW",
            "category": "proxy_arrow",
            "description": "Nonstationary phase-balanced init creates proxy macro arrow under observe_x_binary at horizon 2.",
            "honest_reference": {
                "witness_id": "hidden_clock_driven",
                "lens_id": "observe_x_binary",
                "horizon": 2,
                "initial_id": "phase1_balanced",
                "macro_arrow_kl_honest": row_spurious["macro_arrow_kl_honest"],
                "macro_arrow_kind_honest": row_spurious["macro_arrow_kind_honest"],
            },
            "proxy_reference": {
                "proxy_id": "PROXY_MACRO_MARKOV_ARROW",
                "macro_arrow_kl_proxy": row_spurious["macro_arrow_kl_proxy"],
                "macro_arrow_kind_proxy": row_spurious["macro_arrow_kind_proxy"],
            },
            "divergence_status": "honest_zero_proxy_positive",
            "material_divergence": row_spurious["proxy_diverges_materially"],
            "key_values": {
                "honest": row_spurious["macro_arrow_kl_honest"],
                "proxy": row_spurious["macro_arrow_kl_proxy"],
            },
            "fragile_setting": "hidden_clock_driven/observe_x_binary/h2/phase1_balanced",
            "note": "Proxy introduces spurious macro arrow where honest observed arrow is exactly zero.",
        },
        {
            "case_id": "proxy_underestimates_nonmarkov_macro_arrow",
            "proxy_id": "PROXY_MACRO_MARKOV_ARROW",
            "category": "proxy_arrow",
            "description": "Proxy underestimates non-Markov observed arrow for observe_clock_3 at horizon 3.",
            "honest_reference": {
                "witness_id": "hidden_clock_driven",
                "lens_id": "observe_clock_3",
                "horizon": 3,
                "initial_id": "stationary",
                "macro_arrow_kl_honest": row_under["macro_arrow_kl_honest"],
                "macro_arrow_kind_honest": row_under["macro_arrow_kind_honest"],
            },
            "proxy_reference": {
                "proxy_id": "PROXY_MACRO_MARKOV_ARROW",
                "macro_arrow_kl_proxy": row_under["macro_arrow_kl_proxy"],
                "macro_arrow_kind_proxy": row_under["macro_arrow_kind_proxy"],
            },
            "divergence_status": "proxy_materially_smaller",
            "material_divergence": row_under["proxy_diverges_materially"],
            "key_values": {
                "honest": row_under["macro_arrow_kl_honest"],
                "proxy": row_under["macro_arrow_kl_proxy"],
            },
            "fragile_setting": "hidden_clock_driven/observe_clock_3/h3/stationary",
            "note": "Proxy remains finite positive but materially smaller than honest macro arrow.",
        },
        {
            "case_id": "threshold_creates_spurious_one_way_support",
            "proxy_id": "PROXY_THRESHOLD_SUPPORT_GRAPH",
            "category": "threshold_support",
            "description": "Threshold floor removes tiny reverse edges and creates one-way support artifacts.",
            "honest_reference": {
                "case_id": "tiny_reversible_triangle",
                "original_exactness_flag": thr_100["original_exactness_flag"],
                "original_cycle_rank": thr_100["original_cycle_rank"],
            },
            "proxy_reference": {
                "floor": "1/100",
                "one_way_directed_edge_count": thr_100["one_way_directed_edge_count"],
                "one_way_edges": thr_100["one_way_edges"],
            },
            "divergence_status": "spurious_one_way_edges",
            "material_divergence": True,
            "key_values": {
                "one_way_directed_edge_count": thr_100["one_way_directed_edge_count"],
                "one_way_edges": thr_100["one_way_edges"],
            },
            "fragile_setting": "tiny_reversible_triangle/floor=1/100",
            "note": "Original chain is exact/reversible class, thresholded proxy creates apparent directionality.",
        },
        {
            "case_id": "poor_metric_splits_unique_object",
            "proxy_id": "PROXY_CLUSTERED_OBJECT_COUNT",
            "category": "objecthood_metric",
            "description": "Support-signature proxy metric splits a unique-object contractive witness into two clusters.",
            "honest_reference": {
                "metric_id": "tv",
                "cluster_count": tv_row["cluster_count"],
            },
            "proxy_reference": {
                "metric_id": "support_signature",
                "cluster_count": sig_row["cluster_count"],
            },
            "divergence_status": "metric_artifact_split",
            "material_divergence": sig_row["cluster_count"] != tv_row["cluster_count"],
            "key_values": {
                "tv_cluster_count": tv_row["cluster_count"],
                "support_signature_cluster_count": sig_row["cluster_count"],
            },
            "fragile_setting": "contractive_unique_object/den=4/eps=1/4/threshold=1/2",
            "note": "Object multiplicity changes purely by metric choice.",
        },
    ]

    return {
        "generation_timestamp_utc": _now_utc(),
        "case_count": len(cases),
        "cases": cases,
    }


def build_fragility_summary(
    adversarial_cases: dict,
    horizon_rows: list[dict],
    initial_rows: list[dict],
    perturb_rows: list[dict],
    threshold_rows: list[dict],
    objecthood_rows: list[dict],
) -> dict:
    del perturb_rows
    entries = []

    entries.append(
        {
            "fragility_id": "stationary_zero_arrow_is_fragile_to_initial_distribution",
            "category": "initial_distribution",
            "severity": "high",
            "evidence_refs": ["initial_distribution_sweep:hidden_clock_reversible:identity:h3"],
            "note": "Stationary initialization gives zero arrow while basis-state initializations yield infinite arrow at the same horizon.",
        }
    )
    entries.append(
        {
            "fragility_id": "macro_arrow_depends_strongly_on_lens_choice",
            "category": "lens_choice",
            "severity": "high",
            "evidence_refs": ["horizon_lens_sweep:hidden_clock_driven:h3:identity|observe_x_binary|observe_clock_3"],
            "note": "At fixed witness and horizon, macro arrow is positive for identity/observe_clock_3 but zero for observe_x_binary.",
        }
    )
    entries.append(
        {
            "fragility_id": "fitted_markov_proxy_can_create_or_distort_macro_arrow",
            "category": "proxy_fit",
            "severity": "high",
            "evidence_refs": [
                "adversarial_cases:proxy_spurious_macro_arrow_nonstationary",
                "adversarial_cases:proxy_underestimates_nonmarkov_macro_arrow",
            ],
            "note": "Fitted first-order macro proxy can create spurious macro arrow or materially underestimate honest macro arrow.",
        }
    )
    entries.append(
        {
            "fragility_id": "threshold_floors_can_introduce_spurious_one_way_support",
            "category": "thresholding",
            "severity": "medium",
            "evidence_refs": ["threshold_sweep:tiny_reversible_triangle:floor=1/100"],
            "note": "Applying floor threshold introduces one-way edges in a chain with originally exact reversible support.",
        }
    )
    entries.append(
        {
            "fragility_id": "object_multiplicity_can_be_metric_artifact",
            "category": "metric_choice",
            "severity": "medium",
            "evidence_refs": ["objecthood_metric_sweep:contractive_unique_object:tv_vs_support_signature"],
            "note": "Cluster count changes from 1 to 2 when switching from TV metric to support-signature metric.",
        }
    )

    return {
        "generation_timestamp_utc": _now_utc(),
        "fragility_count": len(entries),
        "entries": entries,
    }


def run_t15_suite(precision: int = 80, max_horizon: int = 5) -> dict:
    horizon_rows = run_horizon_lens_sweep(precision=precision, max_horizon=max_horizon)
    initial_rows = run_initial_distribution_sweep(precision=precision)
    perturb_rows = run_perturbation_sweep(precision=precision)
    threshold_rows = run_threshold_sweep()
    objecthood_rows = run_objecthood_metric_sweep()
    adversarial_cases = build_adversarial_cases(precision=precision)
    fragility_summary = build_fragility_summary(
        adversarial_cases,
        horizon_rows,
        initial_rows,
        perturb_rows,
        threshold_rows,
        objecthood_rows,
    )

    notes_lines = ["# T15 Fragility Notes", ""]
    for ent in fragility_summary["entries"]:
        notes_lines.append(f"- `{ent['fragility_id']}`: {ent['note']}")
    fragility_notes = "\n".join(notes_lines) + "\n"

    return {
        "generation_timestamp_utc": _now_utc(),
        "precision": precision,
        "max_horizon": max_horizon,
        "horizon_rows": horizon_rows,
        "initial_rows": initial_rows,
        "perturb_rows": perturb_rows,
        "threshold_rows": threshold_rows,
        "objecthood_rows": objecthood_rows,
        "adversarial_cases": adversarial_cases,
        "fragility_summary": fragility_summary,
        "fragility_notes": fragility_notes,
        "case_manifest": {
            "generation_timestamp_utc": _now_utc(),
            "precision": precision,
            "max_horizon": max_horizon,
            "horizon_row_count": len(horizon_rows),
            "initial_row_count": len(initial_rows),
            "perturbation_row_count": len(perturb_rows),
            "threshold_row_count": len(threshold_rows),
            "objecthood_row_count": len(objecthood_rows),
            "adversarial_case_count": adversarial_cases["case_count"],
            "fragility_count": fragility_summary["fragility_count"],
        },
    }


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            rec = {}
            for k in fields:
                v = row.get(k)
                if isinstance(v, Fraction):
                    rec[k] = serialize_fraction(v)
                elif isinstance(v, Decimal):
                    rec[k] = serialize_decimal(v)
                elif isinstance(v, bool):
                    rec[k] = "true" if v else "false"
                elif isinstance(v, (list, tuple, dict)):
                    rec[k] = json.dumps(v, sort_keys=True)
                elif v is None:
                    rec[k] = ""
                else:
                    rec[k] = str(v)
            w.writerow(rec)


def _assert_required_anchors(manifest: dict) -> None:
    horizon_rows = manifest["horizon_rows"]
    initial_rows = manifest["initial_rows"]
    perturb_rows = manifest["perturb_rows"]
    threshold_rows = manifest["threshold_rows"]
    objecthood_rows = manifest["objecthood_rows"]

    # Horizon anchors
    for r in horizon_rows:
        if r["witness_id"] == "hidden_clock_reversible":
            if r["micro_arrow_kl"] != "0" or r["macro_arrow_kl_honest"] != "0":
                raise ValueError("hidden_clock_reversible horizon anchor failed")

    for h in (1, 2, 3, 4, 5):
        identity = next(x for x in horizon_rows if x["witness_id"] == "hidden_clock_driven" and x["lens_id"] == "identity" and x["horizon"] == h)
        if identity["macro_arrow_kind_honest"] != "finite_positive":
            raise ValueError("hidden_clock_driven identity macro arrow should be positive for h>=1")

        xbin = next(x for x in horizon_rows if x["witness_id"] == "hidden_clock_driven" and x["lens_id"] == "observe_x_binary" and x["horizon"] == h)
        if xbin["macro_arrow_kl_honest"] != "0":
            raise ValueError("hidden_clock_driven observe_x_binary honest macro arrow should be zero")

        clock = next(x for x in horizon_rows if x["witness_id"] == "hidden_clock_driven" and x["lens_id"] == "observe_clock_3" and x["horizon"] == h)
        if clock["macro_arrow_kind_honest"] != "finite_positive":
            raise ValueError("hidden_clock_driven observe_clock_3 honest macro arrow should be positive for h>=1")

    for h in (2, 3):
        clock = next(x for x in horizon_rows if x["witness_id"] == "hidden_clock_driven" and x["lens_id"] == "observe_clock_3" and x["horizon"] == h)
        if not clock["proxy_diverges_materially"]:
            raise ValueError("hidden_clock_driven observe_clock_3 proxy should materially diverge at h=2,3")

    # Initial anchors
    stationary = next(r for r in initial_rows if r["witness_id"] == "hidden_clock_reversible" and r["initial_id"] == "stationary" and r["horizon"] == 3)
    if stationary["micro_arrow_kl"] != "0" or stationary["macro_arrow_kl_honest"] != "0":
        raise ValueError("hidden_clock_reversible stationary anchor failed")

    for s in ("delta_L0", "delta_R0", "delta_R1", "delta_L1"):
        row = next(r for r in initial_rows if r["witness_id"] == "hidden_clock_reversible" and r["initial_id"] == s)
        if row["micro_arrow_kind"] != "infinite" or row["macro_arrow_kind_honest"] != "infinite":
            raise ValueError("hidden_clock_reversible basis init should be infinite")

    row = next(r for r in initial_rows if r["witness_id"] == "hidden_clock_driven" and r["lens_id"] == "observe_x_binary" and r["initial_id"] == "phase1_balanced" and r["horizon"] == 2)
    if not (row["macro_arrow_kl_honest"] == "0" and row["macro_arrow_kind_proxy"] == "finite_positive" and row["proxy_diverges_materially"]):
        raise ValueError("phase1_balanced spurious proxy anchor failed")

    # Threshold anchors
    f0 = next(r for r in threshold_rows if r["floor"] == "0")
    if f0["one_way_directed_edge_count"] != 0:
        raise ValueError("threshold floor 0 one-way count anchor failed")
    f100 = next(r for r in threshold_rows if r["floor"] == "1/100")
    if f100["one_way_directed_edge_count"] != 2 or f100["original_exactness_flag"] is not True or f100["original_cycle_rank"] != 1:
        raise ValueError("threshold floor 1/100 anchor failed")

    # Perturb anchors
    h0 = next(r for r in perturb_rows if r["family_id"] == "hidden_clock_mix" and r["alpha"] == Fraction(0, 1))
    if not (h0["micro_arrow_kl"] == "0" and h0["macro_arrow_observe_x_binary"] == "0" and h0["macro_arrow_observe_clock_3"] == "0"):
        raise ValueError("hidden_clock_mix alpha0 anchor failed")

    hsmall = next(r for r in perturb_rows if r["family_id"] == "hidden_clock_mix" and r["alpha"] == Fraction(1, 20))
    if not (hsmall["micro_arrow_kind"] == "finite_positive" and hsmall["macro_arrow_observe_x_binary"] == "0" and hsmall["macro_arrow_observe_clock_3_kind"] == "finite_positive"):
        raise ValueError("hidden_clock_mix alpha1/20 anchor failed")

    c0 = next(r for r in perturb_rows if r["family_id"] == "cycle_drive_mix" and r["alpha"] == Fraction(0, 1))
    if not (c0["max_cycle_affinity"] == Fraction(0, 1) and c0["exactness_flag"] is True):
        raise ValueError("cycle_drive_mix alpha0 anchor failed")

    csmall = next(r for r in perturb_rows if r["family_id"] == "cycle_drive_mix" and r["alpha"] == Fraction(1, 20))
    if not (csmall["max_cycle_affinity"] > Fraction(0, 1) and csmall["exactness_flag"] is False):
        raise ValueError("cycle_drive_mix alpha1/20 anchor failed")

    # Objecthood anchors
    tv = next(r for r in objecthood_rows if r["metric_id"] == "tv")
    ss = next(r for r in objecthood_rows if r["metric_id"] == "support_signature")
    if not (tv["stable_point_count"] == 3 and tv["cluster_count"] == 1 and ss["cluster_count"] == 2):
        raise ValueError("objecthood metric anchors failed")


def write_t15_outputs(manifest: dict, output_dir: str = "results/T15") -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    _assert_required_anchors(manifest)

    _write_csv(out / "horizon_lens_sweep.csv", manifest["horizon_rows"])
    _write_csv(out / "initial_distribution_sweep.csv", manifest["initial_rows"])
    _write_csv(out / "perturbation_sweep.csv", manifest["perturb_rows"])
    _write_csv(out / "threshold_sweep.csv", manifest["threshold_rows"])
    _write_csv(out / "objecthood_metric_sweep.csv", manifest["objecthood_rows"])

    (out / "adversarial_cases.json").write_text(json.dumps(manifest["adversarial_cases"], indent=2), encoding="utf-8")
    (out / "fragility_summary.json").write_text(json.dumps(manifest["fragility_summary"], indent=2), encoding="utf-8")
    (out / "fragility_notes.md").write_text(manifest["fragility_notes"], encoding="utf-8")
    (out / "case_manifest.json").write_text(json.dumps(manifest["case_manifest"], indent=2), encoding="utf-8")
