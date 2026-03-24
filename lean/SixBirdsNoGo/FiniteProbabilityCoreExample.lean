import SixBirdsNoGo.FiniteProbabilityCore

namespace SixBirdsNoGo

def half : Rat := (1 : Rat) / 2

def dirac {α : Type} (a : α) : FinLaw α where
  entries := [(a, 1)]
  nonneg := by
    intro e h
    have hEq : e = (a, 1) := by simpa using h
    cases hEq
    simpa using (show (0 : Rat) ≤ (1 : Rat) by native_decide)
  sum_eq_one := by
    exact Rat.add_zero 1

def uniformTwo : FinLaw (Fin 2) where
  entries := [((0 : Fin 2), half), ((1 : Fin 2), half)]
  nonneg := by
    have hhalf : (0 : Rat) ≤ half := by
      native_decide
    intro e h
    have hEq : e = ((0 : Fin 2), half) ∨ e = ((1 : Fin 2), half) := by
      simpa using h
    rcases hEq with hEq | hEq
    · cases hEq
      simpa [half] using hhalf
    · cases hEq
      simpa [half] using hhalf
  sum_eq_one := by
    native_decide

def flipState : Fin 2 → Fin 2
  | 0 => 1
  | 1 => 0

def flipKernel : FiniteKernel (Fin 2) (Fin 2)
  | 0 => dirac (1 : Fin 2)
  | 1 => dirac (0 : Fin 2)

example : (pushforward flipState uniformTwo).entries = [((1 : Fin 2), half), ((0 : Fin 2), half)] := rfl

def oneStepPathLaw : FinLaw (PathState 2 1) :=
  pathLaw uniformTwo flipKernel 1

example : oneStepPathLaw.entries = [(((0 : Fin 2), (1 : Fin 2)), half), (((1 : Fin 2), (0 : Fin 2)), half)] := by
  native_decide

example : (firstMarginal oneStepPathLaw).entries = uniformTwo.entries := by
  native_decide

example : (twoTimeMarginal oneStepPathLaw ⟨0, by decide⟩ ⟨1, by decide⟩).entries =
    [(((0 : Fin 2), (1 : Fin 2)), half), (((1 : Fin 2), (0 : Fin 2)), half)] := by
  native_decide

def twoStepPathLaw : FinLaw (PathState 2 2) :=
  pathLaw uniformTwo flipKernel 2

example : (timeMarginal twoStepPathLaw ⟨2, by decide⟩).entries = uniformTwo.entries := by
  native_decide

end SixBirdsNoGo
