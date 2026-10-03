import Mathlib.Combinatorics.SimpleGraph.Acyclic
import Mathlib.Tactic

/-! Edge-local real exactness and forest potential construction on actual
graphs. The vertex is not a root-path record, and labels are not defined from
a potential. -/

namespace SixBirdsNoGo.RealGraph

noncomputable def integral {V : Type*} {G : SimpleGraph V}
    (a : V → V → ℝ) : {u v : V} → G.Walk u v → ℝ
  | _, _, .nil => 0
  | u, _, .cons (v := v) _ p => a u v + integral a p

theorem integral_append {V : Type*} {G : SimpleGraph V} (a : V → V → ℝ)
    {u v w : V} (p : G.Walk u v) (q : G.Walk v w) :
    integral a (p.append q) = integral a p + integral a q := by
  induction p with
  | nil => simp [integral]
  | cons h p ih => simp [integral, ih, add_assoc]

theorem integral_concat {V : Type*} {G : SimpleGraph V} (a : V → V → ℝ)
    {u v w : V} (p : G.Walk u v) (h : G.Adj v w) :
    integral a (p.concat h) = integral a p + a v w := by
  simp [SimpleGraph.Walk.concat, integral_append, integral]

theorem integral_of_exact {V : Type*} {G : SimpleGraph V} (a : V → V → ℝ)
    (φ : V → ℝ) (hexact : ∀ u v, G.Adj u v → a u v = φ v - φ u)
    {u v : V} (p : G.Walk u v) : integral a p = φ v - φ u := by
  induction p with
  | nil => simp [integral]
  | cons h p ih => simp only [integral, hexact _ _ h, ih]; ring

theorem exact_closedWalk_zero {V : Type*} {G : SimpleGraph V} (a : V → V → ℝ)
    (φ : V → ℝ) (hexact : ∀ u v, G.Adj u v → a u v = φ v - φ u)
    {u : V} (p : G.Walk u u) : integral a p = 0 := by
  simpa using integral_of_exact a φ hexact p

noncomputable def rootedPotential {V : Type*} (G : SimpleGraph V)
    (a : V → V → ℝ) (r v : V) : ℝ := by
  classical
  exact if hv : G.Reachable r v then integral a hv.some.toPath.val else 0

theorem rootedPotential_edge {V : Type*} {G : SimpleGraph V}
    (hG : G.IsAcyclic) (a : V → V → ℝ)
    (hanti : ∀ u v, G.Adj u v → a u v = -a v u)
    {r u v : V} (hru : G.Reachable r u) (hadj : G.Adj u v) :
    a u v = rootedPotential G a r v - rootedPotential G a r u := by
  classical
  have hrv := hru.trans hadj.reachable
  let p := hru.some.toPath
  let q := hrv.some.toPath
  change a u v = (if _ : G.Reachable r v then _ else _) -
    (if _ : G.Reachable r u then _ else _)
  rw [dif_pos hrv, dif_pos hru]
  change a u v = integral a q.val - integral a p.val
  by_cases hu : u ∈ q.val.support
  · have heq := hG.path_concat p.property q.property hadj hu
    rw [heq, integral_concat]
    ring
  · have hv := hG.mem_support_of_ne_mem_support_of_adj_of_isPath p.property q.property hadj hu
    have heq := hG.path_concat q.property p.property hadj.symm hv
    rw [heq, integral_concat, hanti u v hadj]
    ring

theorem forest_exact {V : Type*} {G : SimpleGraph V} (hG : G.IsAcyclic)
    (a : V → V → ℝ) (hanti : ∀ u v, G.Adj u v → a u v = -a v u) :
    ∃ φ : V → ℝ, ∀ u v, G.Adj u v → a u v = φ v - φ u := by
  classical
  let root (v : V) := (G.connectedComponentMk v).out
  refine ⟨fun v => rootedPotential G a (root v) v, ?_⟩
  intro u v hadj
  have hcc := SimpleGraph.ConnectedComponent.sound hadj.reachable
  have hroot : root u = root v := congrArg (fun C : G.ConnectedComponent => C.out) hcc
  have hru : G.Reachable (root u) u :=
    SimpleGraph.ConnectedComponent.exact (G.connectedComponentMk u).out_eq
  change a u v = rootedPotential G a (root v) v - rootedPotential G a (root u) u
  rw [← hroot]
  exact rootedPotential_edge hG a hanti hru hadj

end SixBirdsNoGo.RealGraph
