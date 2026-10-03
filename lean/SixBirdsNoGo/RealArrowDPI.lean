import SixBirdsNoGo.RealFiniteKL
import SixBirdsNoGo.ArrowDPI

/-! Concrete extended-real arrow DPI on finite path laws. The map/reversal
commutation lemma from the original development is reused; the analytic DPI
is proved in RealFiniteKL, not supplied by ScalarLogLayer. -/

namespace SixBirdsNoGo.RealProbability

instance fintypePathState (n horizon : Nat) : Fintype (PathState n horizon) := by
  induction horizon with
  | zero => dsimp [PathState]; infer_instance
  | succ h ih => dsimp [PathState]; infer_instance

noncomputable def observedLaw {n m h : Nat} (f : Fin n → Fin m)
    (p : Law (PathState n h)) : Law (PathState m h) :=
  pushforward (mapPathState f) p

noncomputable def reversedLaw {n h : Nat} (p : Law (PathState n h)) : Law (PathState n h) :=
  pushforward reversePathState p

theorem observation_reversal {n m h : Nat} (f : Fin n → Fin m)
    (p : Law (PathState n h)) :
    reversedLaw (observedLaw f p) = observedLaw f (reversedLaw p) := by
  unfold observedLaw reversedLaw
  rw [pushforward_comp, pushforward_comp]
  congr 1
  funext s
  exact (mapPathState_reversePathState f s).symm

theorem arrowDPI {n m h : Nat} (f : Fin n → Fin m)
    (p : Law (PathState n h)) :
    KL (observedLaw f p) (reversedLaw (observedLaw f p)) ≤ KL p (reversedLaw p) := by
  rw [observation_reversal]
  exact KL_pushforward_le (mapPathState f) p (reversedLaw p)

theorem reversible_observation_zeroArrow {n m h : Nat} (f : Fin n → Fin m)
    (p : Law (PathState n h)) (hrev : reversedLaw p = p) :
    KL (observedLaw f p) (reversedLaw (observedLaw f p)) = 0 := by
  rw [observation_reversal, hrev, KL_self]

end SixBirdsNoGo.RealProbability
