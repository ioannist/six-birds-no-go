import SixBirdsNoGo.FiniteKLDPI
import SixBirdsNoGo.FiniteProbabilityCoreExample

namespace SixBirdsNoGo

open SixBirdsNoGo

theorem zeroMassOnEntries {α β : Type} : ∀ xs : List (α × β), massSum (xs.map ((fun a => (a, (0 : Rat))) ∘ Prod.fst)) = 0
  | [] => by simp
  | _ :: xs => by
      simp [zeroMassOnEntries xs, Rat.zero_add]

def zeroLogLayer : ScalarLogLayer where
  logTerm _ _ := 0
  deterministic_dpi := by
    intro α β _ _ f μ ν hAC
    simp [supportList, Rat.mul_zero]
    rw [zeroMassOnEntries, zeroMassOnEntries]
    native_decide

example : reversePathState (horizon := 2) ((((0 : Fin 2), (1 : Fin 2)), (0 : Fin 2)) : PathState 2 2) =
    ((((0 : Fin 2), (1 : Fin 2)), (0 : Fin 2)) : PathState 2 2) := by
  native_decide

example : reversePathLaw twoStepPathLaw = pushforward reversePathState twoStepPathLaw := rfl

example : fiberMass flipState uniformTwo (1 : Fin 2) = pointWeight (pushforward flipState uniformTwo) (1 : Fin 2) := by
  rfl

example : KL zeroLogLayer (pushforward flipState uniformTwo) (pushforward flipState uniformTwo)
    ≤ KL zeroLogLayer uniformTwo uniformTwo := by
  have hAC : AbsolutelyContinuous uniformTwo uniformTwo := by
    intro a h
    exact h
  simpa using KL_pushforward_dpi (α := Fin 2) (β := Fin 2) zeroLogLayer flipState uniformTwo uniformTwo hAC

example : KL zeroLogLayer (pushforwardPathLaw flipState oneStepPathLaw) (pushforwardPathLaw flipState oneStepPathLaw)
    ≤ KL zeroLogLayer oneStepPathLaw oneStepPathLaw := by
  have hAC : AbsolutelyContinuous oneStepPathLaw oneStepPathLaw := by
    intro a h
    exact h
  simpa using pathLawPushforwardDPI (n := 2) (m := 2) (horizon := 1) zeroLogLayer flipState oneStepPathLaw oneStepPathLaw hAC

end SixBirdsNoGo
