import SixBirdsNoGo.ClosureVariationalCore

namespace SixBirdsNoGo

def closureDeficitValue {n m : Nat}
    (V : ClosureVariationalLayer) (μ : FinLaw (Fin n)) (f : Fin n → Fin m)
    (K : FiniteKernel (Fin n) (Fin n)) (tau : Nat) : Rat :=
  bestMacroGap V μ f K tau

def ExactClosedMacroLaw {n m : Nat}
    (V : ClosureVariationalLayer) (μ : FinLaw (Fin n)) (f : Fin n → Fin m)
    (K : FiniteKernel (Fin n) (Fin n)) (tau : Nat) : Prop :=
  ∃ candidate : MacroKernel m,
    variationalObjective V.toScalarLogLayer μ f K tau candidate = 0

theorem closureDeficit_attainedBy_bestMacroKernel {n m : Nat}
    (V : ClosureVariationalLayer) (μ : FinLaw (Fin n)) (f : Fin n → Fin m)
    (K : FiniteKernel (Fin n) (Fin n)) (tau : Nat) :
    closureDeficitValue V μ f K tau =
      variationalObjective V.toScalarLogLayer μ f K tau (bestMacroKernel μ f K tau) := by
  rfl

theorem closureDeficit_le_allKernels {n m : Nat}
    (V : ClosureVariationalLayer) (μ : FinLaw (Fin n)) (f : Fin n → Fin m)
    (K : FiniteKernel (Fin n) (Fin n)) (tau : Nat) (candidate : MacroKernel m) :
    closureDeficitValue V μ f K tau ≤
      variationalObjective V.toScalarLogLayer μ f K tau candidate := by
  simpa [closureDeficitValue] using bestMacroKernel_minimizesObjective V μ f K tau candidate

theorem closureDeficit_is_variationalMinimum {n m : Nat}
    (V : ClosureVariationalLayer) (μ : FinLaw (Fin n)) (f : Fin n → Fin m)
    (K : FiniteKernel (Fin n) (Fin n)) (tau : Nat) :
    (closureDeficitValue V μ f K tau =
        variationalObjective V.toScalarLogLayer μ f K tau (bestMacroKernel μ f K tau)) ∧
      (∀ candidate : MacroKernel m,
        closureDeficitValue V μ f K tau ≤
          variationalObjective V.toScalarLogLayer μ f K tau candidate) := by
  constructor
  · exact closureDeficit_attainedBy_bestMacroKernel V μ f K tau
  · intro candidate
    exact closureDeficit_le_allKernels V μ f K tau candidate

theorem positiveClosureDeficit_forbidsExactClosure {n m : Nat}
    (V : ClosureVariationalLayer) (μ : FinLaw (Fin n)) (f : Fin n → Fin m)
    (K : FiniteKernel (Fin n) (Fin n)) (tau : Nat)
    (hpos : 0 < closureDeficitValue V μ f K tau) :
    ¬ ExactClosedMacroLaw V μ f K tau := by
  intro hclosed
  rcases hclosed with ⟨candidate, hzero⟩
  have hle : closureDeficitValue V μ f K tau ≤ 0 := by
    simpa [hzero] using closureDeficit_le_allKernels V μ f K tau candidate
  change Rat.blt 0 (closureDeficitValue V μ f K tau) = true at hpos
  change Rat.blt 0 (closureDeficitValue V μ f K tau) = false at hle
  rw [hle] at hpos
  exact Bool.false_ne_true hpos

theorem closureTheorem_directPack {n m : Nat}
    (V : ClosureVariationalLayer) (μ : FinLaw (Fin n)) (f : Fin n → Fin m)
    (K : FiniteKernel (Fin n) (Fin n)) (tau : Nat) :
    (closureDeficitValue V μ f K tau =
        variationalObjective V.toScalarLogLayer μ f K tau (bestMacroKernel μ f K tau)) ∧
      (∀ candidate : MacroKernel m,
        closureDeficitValue V μ f K tau ≤
          variationalObjective V.toScalarLogLayer μ f K tau candidate) := by
  exact closureDeficit_is_variationalMinimum V μ f K tau

end SixBirdsNoGo
