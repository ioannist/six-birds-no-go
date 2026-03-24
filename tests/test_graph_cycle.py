from sixbirds_nogo.graph_cycle import (
    cycle_rank,
    cycle_rank_from_edges,
    fundamental_cycle_basis,
    fundamental_cycle_basis_from_edges,
    is_forest,
    support_digraph,
    support_undirected_edges,
)
from sixbirds_nogo.markov import list_chain_witness_ids, load_chain_from_witness


def test_support_graph_extraction_and_self_loop_handling() -> None:
    for witness_id in list_chain_witness_ids():
        chain = load_chain_from_witness(witness_id)
        dg = support_digraph(chain)
        assert tuple(dg.keys()) == chain.states

    chain = load_chain_from_witness("positive_closure_deficit")
    dg_default = support_digraph(chain, include_self_loops=False)
    assert "A0" not in dg_default["A0"]

    dg_with_loops = support_digraph(chain, include_self_loops=True)
    assert "A0" in dg_with_loops["A0"]

    und_edges = support_undirected_edges(chain)
    assert all(u != v for (u, v) in und_edges)
    assert cycle_rank(chain) == cycle_rank(chain, include_self_loops=True)


def test_cycle_rank_forest_and_basis_named_fixtures() -> None:
    tree = load_chain_from_witness("rev_tree_4")
    assert cycle_rank(tree) == 0
    assert is_forest(tree) is True
    assert fundamental_cycle_basis(tree) == ()

    rev_cycle = load_chain_from_witness("rev_cycle_3")
    assert cycle_rank(rev_cycle) == 1
    assert is_forest(rev_cycle) is False
    basis = fundamental_cycle_basis(rev_cycle)
    assert len(basis) == 1
    assert basis == (("0", "1", "2", "0"),)

    biased = load_chain_from_witness("biased_cycle_3")
    assert cycle_rank(biased) == 1
    assert is_forest(biased) is False
    assert len(fundamental_cycle_basis(biased)) == 1


def test_structural_consistency_all_chain_witnesses() -> None:
    for witness_id in list_chain_witness_ids():
        chain = load_chain_from_witness(witness_id)
        r = cycle_rank(chain)
        basis1 = fundamental_cycle_basis(chain)
        basis2 = fundamental_cycle_basis(chain)
        assert r >= 0
        assert len(basis1) == r
        assert basis1 == basis2


def test_direct_edge_level_api() -> None:
    states = ("a", "b", "c", "d")
    edges = (("a", "b"), ("b", "c"), ("a", "c"))
    assert cycle_rank_from_edges(states, edges) == 1
    basis = fundamental_cycle_basis_from_edges(states, edges)
    assert len(basis) == 1
    assert basis == (("a", "b", "c", "a"),)
