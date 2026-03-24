import SixBirdsNoGo.Idempotence
import SixBirdsNoGo.FiniteLensDefinability

namespace SixBirdsNoGo

/-- Observed finite interface profile under repeated packaging. -/
def observedImageProfile (L : FinLens)
    (e : Fin L.domSize → Fin L.domSize) (n : Nat) : Fin L.domSize → Fin L.imgSize :=
  fun x => L.toImage ((Function.iterate e n) x)

/-- Observed definable predicate under repeated packaging. -/
def observedDefinablePredicate (L : FinLens)
    (e : Fin L.domSize → Fin L.domSize) (a : BoolVec L.imgSize) (n : Nat) :
    Fin L.domSize → Bool :=
  fun x => a (observedImageProfile L e n x)

/-- No laddering under a fixed interface means the observed profile stabilizes after one step. -/
def NoLadderUnderFixedInterface (L : FinLens) (e : Fin L.domSize → Fin L.domSize) : Prop :=
  ∀ n, observedImageProfile L e (n + 1) = observedImageProfile L e 1

theorem observedImageProfile_stabilizes_after_one
    (L : FinLens)
    (e : Fin L.domSize → Fin L.domSize)
    (h : Idempotent e) :
    ∀ n, observedImageProfile L e (n + 1) = observedImageProfile L e 1 := by
  intro n
  have hiter : Function.iterate e (n + 1) = e := iterate_stabilizes_ext e h n
  have hone : Function.iterate e 1 = e := by
    funext x
    simp [Function.iterate]
  funext x
  simp [observedImageProfile, hiter, hone]

theorem observedDefinablePredicate_stabilizes_after_one
    (L : FinLens)
    (e : Fin L.domSize → Fin L.domSize)
    (h : Idempotent e)
    (a : BoolVec L.imgSize) :
    ∀ n, observedDefinablePredicate L e a (n + 1) =
      observedDefinablePredicate L e a 1 := by
  intro n
  funext x
  have hprof := observedImageProfile_stabilizes_after_one L e h n
  have hx := congrArg (fun p => a (p x)) hprof
  simpa [observedDefinablePredicate] using hx

/-- Direct bounded-interface no-ladder corollary packaging count core and stabilization. -/
theorem boundedInterface_noLadderCorollary
    (L : FinLens)
    (e : Fin L.domSize → Fin L.domSize)
    (h : Idempotent e) :
    NoLadderUnderFixedInterface L e ∧
      (Nonempty (DefinablePred L ≃ BoolVec L.imgSize) ∧
        (allAssignments L.imgSize).length = 2 ^ L.imgSize) := by
  constructor
  · intro n
    exact observedImageProfile_stabilizes_after_one L e h n
  · exact finiteLens_definableCountCore L

end SixBirdsNoGo
