import SixBirdsNoGo.ClosedWalkExactness

namespace SixBirdsNoGo

theorem nullForce_closedWalkSum_eq_zero
    {α : Type u}
    (φ : α → Int)
    (ℓ : α → α → Int)
    (hExact : ExactPotentialDiff φ ℓ)
    (w : Walk α)
    (hclosed : Walk.finish w = Walk.start w) :
    edgeSum ℓ w = 0 := by
  exact closedWalkSum_eq_zero φ ℓ hExact w hclosed

theorem nullForce_allClosedWalksZero
    {α : Type u}
    (φ : α → Int)
    (ℓ : α → α → Int)
    (hExact : ExactPotentialDiff φ ℓ) :
    ∀ w : Walk α, Walk.finish w = Walk.start w → edgeSum ℓ w = 0 := by
  intro w hclosed
  exact nullForce_closedWalkSum_eq_zero φ ℓ hExact w hclosed

end SixBirdsNoGo
