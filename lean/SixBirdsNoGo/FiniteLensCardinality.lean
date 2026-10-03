import SixBirdsNoGo.FiniteLensDefinability
import Mathlib.Data.Fintype.Card
import Mathlib.Data.Fintype.Pi
import Mathlib.Tactic

/-! The original enumeration-length theorem alone did not prove a cardinality
or rule out an infinite sequence. These declarations establish both. -/

namespace SixBirdsNoGo

noncomputable def definablePredMathlibEquiv (L : FinLens) :
    _root_.Equiv (DefinablePred L) (BoolVec L.imgSize) where
  toFun := (definablePredEquivAssignments L).toFun
  invFun := (definablePredEquivAssignments L).invFun
  left_inv := (definablePredEquivAssignments L).left_inv
  right_inv := (definablePredEquivAssignments L).right_inv

noncomputable instance (L : FinLens) : Fintype (DefinablePred L) :=
  Fintype.ofEquiv (BoolVec L.imgSize) (definablePredMathlibEquiv L).symm

theorem finiteLens_definableCardinality (L : FinLens) :
    Fintype.card (DefinablePred L) = 2 ^ L.imgSize := by
  rw [Fintype.card_congr (definablePredMathlibEquiv L)]
  simp [BoolVec]

theorem finiteLens_noInfiniteDistinctSequence (L : FinLens)
    (p : Nat → DefinablePred L) : ¬ _root_.Function.Injective p := by
  intro hp
  have hcard : Fintype.card (DefinablePred L) + 1 ≤ Fintype.card (DefinablePred L) :=
    by
      simpa using Fintype.card_le_of_injective
        (fun i : Fin (Fintype.card (DefinablePred L) + 1) => p i.val)
        (fun i j h => Fin.ext (hp h))
  omega

end SixBirdsNoGo
