import SixBirdsNoGo.ArrowDPI
import SixBirdsNoGo.FiniteProbabilityCore

namespace SixBirdsNoGo

structure AutonomousLiftedSystem (n : Nat) where
  initial : FinLaw (Fin n)
  kernel : FiniteKernel (Fin n) (Fin n)

def liftedPathLaw (A : AutonomousLiftedSystem n) (horizon : Nat) : FinLaw (PathState n horizon) :=
  pathLaw A.initial A.kernel horizon

def stationaryInitializedMicroReversible (A : AutonomousLiftedSystem n) (horizon : Nat) : Prop :=
  liftedPathLaw A horizon = reversePathLaw (liftedPathLaw A horizon)

def honestObservedLiftedPathLaw (f : Fin n → Fin m) (A : AutonomousLiftedSystem n) (horizon : Nat) :
    FinLaw (PathState m horizon) :=
  honestObservedPathLaw f (liftedPathLaw A horizon)

theorem stationaryLiftedArrowDPI
    (S : ScalarLogLayer) (f : Fin n → Fin m)
    (A : AutonomousLiftedSystem n) (horizon : Nat)
    (hAC : AbsolutelyContinuous (liftedPathLaw A horizon) (reversePathLaw (liftedPathLaw A horizon))) :
    macroArrowKL S f (liftedPathLaw A horizon) ≤ microArrowKL S (liftedPathLaw A horizon) := by
  simpa [liftedPathLaw] using arrowDPI (n := n) (m := m) (horizon := horizon) S f (liftedPathLaw A horizon) hAC

theorem stationaryLiftedMicroReversible_implies_macroReversible
    (f : Fin n → Fin m) (A : AutonomousLiftedSystem n) (horizon : Nat)
    (hrev : stationaryInitializedMicroReversible A horizon) :
    honestObservedLiftedPathLaw f A horizon = reversePathLaw (honestObservedLiftedPathLaw f A horizon) := by
  simpa [stationaryInitializedMicroReversible, honestObservedLiftedPathLaw, liftedPathLaw] using
    microReversible_implies_macroReversible (n := n) (m := m) (horizon := horizon) f (liftedPathLaw A horizon) hrev

theorem protocolTrap_noHonestArrow
    (f : Fin n → Fin m) (A : AutonomousLiftedSystem n) (horizon : Nat)
    (hrev : stationaryInitializedMicroReversible A horizon) :
    honestObservedLiftedPathLaw f A horizon = reversePathLaw (honestObservedLiftedPathLaw f A horizon) := by
  exact stationaryLiftedMicroReversible_implies_macroReversible (n := n) (m := m) f A horizon hrev

end SixBirdsNoGo
