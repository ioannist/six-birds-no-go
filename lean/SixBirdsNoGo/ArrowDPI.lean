import SixBirdsNoGo.FiniteKLDPI

namespace SixBirdsNoGo

section PathObservation

variable {n m : Nat}

@[simp] theorem mapPathState_prependState
    (f : Fin n → Fin m) :
    ∀ {horizon : Nat} (x : Fin n) (s : PathState n horizon),
      mapPathState f (prependState x s) = prependState (f x) (mapPathState f s)
  | 0, x, s => rfl
  | Nat.succ h, x, s => by
      cases s with
      | mk s y =>
          exact congrArg (fun t => (t, f y))
            (mapPathState_prependState (f := f) (horizon := h) (x := x) (s := s))

@[simp] theorem mapPathState_reversePathState
    (f : Fin n → Fin m) :
    ∀ {horizon : Nat} (s : PathState n horizon),
      mapPathState f (reversePathState s) = reversePathState (mapPathState f s)
  | 0, s => rfl
  | Nat.succ h, s => by
      cases s with
      | mk s y =>
          have hprepend := mapPathState_prependState (f := f) (horizon := h) (x := y) (s := reversePathStateAux h s)
          have hrev := mapPathState_reversePathState (f := f) (horizon := h) (s := s)
          calc
            mapPathState (horizon := Nat.succ h) f
                (reversePathState (horizon := Nat.succ h) (((s, y) : PathState n (Nat.succ h))))
                = prependState (f y) (mapPathState f (reversePathStateAux h s)) := by
                    simpa [reversePathState, reversePathStateAux] using hprepend
            _ = prependState (f y) (reversePathState (mapPathState f s)) := by
                  exact congrArg (prependState (f y)) hrev
            _ = reversePathState (horizon := Nat.succ h)
                  (mapPathState (horizon := Nat.succ h) f (((s, y) : PathState n (Nat.succ h)))) := by
                  rfl

end PathObservation

section ArrowBridge

variable {n m horizon : Nat}

abbrev honestObservedPathLaw (f : Fin n → Fin m) (μ : FinLaw (PathState n horizon)) :
    FinLaw (PathState m horizon) :=
  pushforwardPathLaw f μ

def microArrowKL (S : ScalarLogLayer) (μ : FinLaw (PathState n horizon)) : Rat :=
  KL S μ (reversePathLaw μ)

def macroArrowKL (S : ScalarLogLayer) (f : Fin n → Fin m) (μ : FinLaw (PathState n horizon)) : Rat :=
  KL S (honestObservedPathLaw f μ) (reversePathLaw (honestObservedPathLaw f μ))

theorem reversePushforwardPathLaw
    (f : Fin n → Fin m) (μ : FinLaw (PathState n horizon)) :
    reversePathLaw (honestObservedPathLaw f μ) = honestObservedPathLaw f (reversePathLaw μ) := by
  apply FinLaw.ext_entries
  simp [reversePathLaw, honestObservedPathLaw, pushforwardPathLaw, pushforward, List.map_map]

 theorem arrowDPI (S : ScalarLogLayer) (f : Fin n → Fin m)
    (μ : FinLaw (PathState n horizon))
    (hAC : AbsolutelyContinuous μ (reversePathLaw μ)) :
    macroArrowKL S f μ ≤ microArrowKL S μ := by
  simpa [macroArrowKL, microArrowKL, honestObservedPathLaw, reversePushforwardPathLaw] using
    pathLawPushforwardDPI (n := n) (m := m) (horizon := horizon) S f μ (reversePathLaw μ) hAC

theorem microReversible_implies_macroReversible
    (f : Fin n → Fin m) (μ : FinLaw (PathState n horizon))
    (hμ : μ = reversePathLaw μ) :
    honestObservedPathLaw f μ = reversePathLaw (honestObservedPathLaw f μ) := by
  have hobs : honestObservedPathLaw f μ = honestObservedPathLaw f (reversePathLaw μ) := by
    exact congrArg (honestObservedPathLaw f) hμ
  calc
    honestObservedPathLaw f μ = honestObservedPathLaw f (reversePathLaw μ) := by
      exact hobs
    _ = reversePathLaw (honestObservedPathLaw f μ) := by
      symm
      exact reversePushforwardPathLaw f μ

end ArrowBridge

end SixBirdsNoGo
