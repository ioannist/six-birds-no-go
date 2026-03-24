import SixBirdsNoGo.ProtocolTrap
import SixBirdsNoGo.ArrowDPIExample

namespace SixBirdsNoGo

def identityKernelTwo : FiniteKernel (Fin 2) (Fin 2)
  | 0 => dirac (0 : Fin 2)
  | 1 => dirac (1 : Fin 2)

def toyLiftedSystem : AutonomousLiftedSystem 2 where
  initial := uniformTwo
  kernel := identityKernelTwo

def mergedObservation : Fin 2 → Fin 1
  | _ => 0

def toyLiftedPathLaw : FinLaw (PathState 2 1) :=
  liftedPathLaw toyLiftedSystem 1

theorem toyLiftedPathLaw_reversible :
    stationaryInitializedMicroReversible toyLiftedSystem 1 := by
  unfold stationaryInitializedMicroReversible liftedPathLaw toyLiftedSystem
  apply FinLaw.ext_entries
  native_decide

example : (honestObservedLiftedPathLaw mergedObservation toyLiftedSystem 1).entries =
    [(((0 : Fin 1), (0 : Fin 1)), half), (((0 : Fin 1), (0 : Fin 1)), half)] := by
  native_decide

example :
    honestObservedLiftedPathLaw mergedObservation toyLiftedSystem 1 =
      reversePathLaw (honestObservedLiftedPathLaw mergedObservation toyLiftedSystem 1) := by
  exact protocolTrap_noHonestArrow mergedObservation toyLiftedSystem 1 toyLiftedPathLaw_reversible

example :
    macroArrowKL zeroLogLayer mergedObservation toyLiftedPathLaw ≤ microArrowKL zeroLogLayer toyLiftedPathLaw := by
  have hAC : AbsolutelyContinuous toyLiftedPathLaw (reversePathLaw toyLiftedPathLaw) := by
    intro a hzero
    rw [show toyLiftedPathLaw = reversePathLaw toyLiftedPathLaw from toyLiftedPathLaw_reversible] at hzero
    exact hzero
  simpa [toyLiftedPathLaw] using
    stationaryLiftedArrowDPI (n := 2) (m := 1) zeroLogLayer mergedObservation toyLiftedSystem 1 hAC
