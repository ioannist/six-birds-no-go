namespace SixBirdsNoGo

/-- Minimal nonempty walk built by snoc-extension. -/
inductive Walk (α : Type u) where
  | single : α → Walk α
  | snoc : Walk α → α → Walk α

namespace Walk

@[simp] def start {α : Type u} : Walk α → α
  | .single a => a
  | .snoc w _ => start w

@[simp] def finish {α : Type u} : Walk α → α
  | .single a => a
  | .snoc _ b => b

end Walk

/-- Edge-sum along consecutive walk steps. -/
@[simp] def edgeSum {α : Type u} (ℓ : α → α → Int) : Walk α → Int
  | .single _ => 0
  | .snoc w b => edgeSum ℓ w + ℓ (Walk.finish w) b

/-- Additive exact-potential-difference encoding (`ℓ u v = φ v - φ u` informally). -/
def ExactPotentialDiff {α : Type u} (φ : α → Int) (ℓ : α → α → Int) : Prop :=
  ∀ u v, φ u + ℓ u v = φ v

@[simp] theorem start_single {α : Type u} (a : α) :
    Walk.start (Walk.single a) = a := rfl

@[simp] theorem start_snoc {α : Type u} (w : Walk α) (b : α) :
    Walk.start (Walk.snoc w b) = Walk.start w := rfl

@[simp] theorem finish_single {α : Type u} (a : α) :
    Walk.finish (Walk.single a) = a := rfl

@[simp] theorem finish_snoc {α : Type u} (w : Walk α) (b : α) :
    Walk.finish (Walk.snoc w b) = b := rfl

@[simp] theorem edgeSum_single {α : Type u} (ℓ : α → α → Int) (a : α) :
    edgeSum ℓ (Walk.single a) = 0 := rfl

@[simp] theorem edgeSum_snoc {α : Type u} (ℓ : α → α → Int) (w : Walk α) (b : α) :
    edgeSum ℓ (Walk.snoc w b) = edgeSum ℓ w + ℓ (Walk.finish w) b := rfl

/-- Telescoping lemma for exact potential differences on a walk. -/
theorem potential_start_add_edgeSum_eq_potential_finish
    {α : Type u}
    (φ : α → Int)
    (ℓ : α → α → Int)
    (hExact : ExactPotentialDiff φ ℓ) :
    ∀ w : Walk α, φ (Walk.start w) + edgeSum ℓ w = φ (Walk.finish w)
  | .single a => by
      simp [edgeSum]
  | .snoc w b => by
      have ih := potential_start_add_edgeSum_eq_potential_finish φ ℓ hExact w
      have hstep := hExact (Walk.finish w) b
      calc
        φ (Walk.start (Walk.snoc w b)) + edgeSum ℓ (Walk.snoc w b)
            = (φ (Walk.start w) + edgeSum ℓ w) + ℓ (Walk.finish w) b := by
                simp [Int.add_assoc]
        _ = φ (Walk.finish w) + ℓ (Walk.finish w) b := by
              simpa [ih]
        _ = φ b := by
              exact hstep
        _ = φ (Walk.finish (Walk.snoc w b)) := by
              simp

/-- Closed-walk corollary: exact potentials force zero total sum. -/
theorem closedWalkSum_eq_zero
    {α : Type u}
    (φ : α → Int)
    (ℓ : α → α → Int)
    (hExact : ExactPotentialDiff φ ℓ)
    (w : Walk α)
    (hclosed : Walk.finish w = Walk.start w) :
    edgeSum ℓ w = 0 := by
  have htel := potential_start_add_edgeSum_eq_potential_finish φ ℓ hExact w
  have hsame : φ (Walk.start w) + edgeSum ℓ w = φ (Walk.start w) + 0 := by
    have hfinish : φ (Walk.finish w) = φ (Walk.start w) := by
      exact congrArg φ hclosed
    calc
      φ (Walk.start w) + edgeSum ℓ w = φ (Walk.finish w) := by
        exact htel
      _ = φ (Walk.start w) := by
        exact hfinish
      _ = φ (Walk.start w) + 0 := by
        simp
  exact Int.add_left_cancel hsame

end SixBirdsNoGo
