import SixBirdsNoGo.ArrowDPI
import SixBirdsNoGo.FiniteKLDPIExample
import SixBirdsNoGo.FiniteProbabilityCoreExample

namespace SixBirdsNoGo

def collapseObs : Fin 2 → Fin 1
  | _ => 0

theorem twoStepPathLaw_reversible :
    twoStepPathLaw = reversePathLaw twoStepPathLaw := by
  apply FinLaw.ext_entries
  native_decide

example : (honestObservedPathLaw collapseObs twoStepPathLaw).entries =
    [((((0 : Fin 1), (0 : Fin 1)), (0 : Fin 1)), half), ((((0 : Fin 1), (0 : Fin 1)), (0 : Fin 1)), half)] := by
  native_decide

example : honestObservedPathLaw collapseObs twoStepPathLaw =
    reversePathLaw (honestObservedPathLaw collapseObs twoStepPathLaw) := by
  exact microReversible_implies_macroReversible collapseObs twoStepPathLaw twoStepPathLaw_reversible

example : macroArrowKL zeroLogLayer collapseObs twoStepPathLaw ≤ microArrowKL zeroLogLayer twoStepPathLaw := by
  have hAC : AbsolutelyContinuous twoStepPathLaw (reversePathLaw twoStepPathLaw) := by
    intro a hzero
    rw [← twoStepPathLaw_reversible] at hzero
    exact hzero
  exact arrowDPI zeroLogLayer collapseObs twoStepPathLaw hAC

end SixBirdsNoGo
