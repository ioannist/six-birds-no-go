import SixBirdsNoGo.ClosureVariationalCore
import SixBirdsNoGo.FiniteProbabilityCoreExample
import SixBirdsNoGo.FiniteKLDPIExample

namespace SixBirdsNoGo

private def third : Rat := (1 : Rat) / 3
private def twoThirds : Rat := (2 : Rat) / 3

private def rowHalfHalf : FinLaw (Fin 2) where
  entries := [((0 : Fin 2), half), ((1 : Fin 2), half)]
  nonneg := by
    intro e h
    have hhalf : (0 : Rat) ≤ half := by native_decide
    have hEq : e = ((0 : Fin 2), half) ∨ e = ((1 : Fin 2), half) := by simpa using h
    rcases hEq with hEq | hEq <;> cases hEq <;> simpa [half] using hhalf
  sum_eq_one := by
    native_decide

private def rowThirdTwoThirds : FinLaw (Fin 2) where
  entries := [((0 : Fin 2), third), ((1 : Fin 2), twoThirds)]
  nonneg := by
    intro e h
    have hthird : (0 : Rat) ≤ third := by native_decide
    have htwo : (0 : Rat) ≤ twoThirds := by native_decide
    have hEq : e = ((0 : Fin 2), third) ∨ e = ((1 : Fin 2), twoThirds) := by simpa using h
    rcases hEq with hEq | hEq
    · cases hEq
      simpa [third] using hthird
    · cases hEq
      simpa [twoThirds] using htwo
  sum_eq_one := by
    native_decide

private def toyKernel : FiniteKernel (Fin 2) (Fin 2)
  | 0 => rowHalfHalf
  | 1 => rowThirdTwoThirds

private def idLens2 : Fin 2 → Fin 2 := fun x => x

private def toyClosureLayer : ClosureVariationalLayer where
  toScalarLogLayer := zeroLogLayer
  bestKernel_minimizer := by
    intro n m μ f K tau candidate
    have hzeroRow :
        ∀ {α : Type} (row : List (α × Rat)),
          massSum (row.map ((fun a => (a, 0)) ∘ Prod.fst)) = 0 := by
      intro α row
      induction row with
      | nil =>
          simp
      | cons e es ih =>
          simpa [ih] using (show (0 : Rat) + 0 = 0 by native_decide)
    have hfutureZero :
        ∀ x : Fin n,
          massSum (List.map ((fun a => (a, 0)) ∘ Prod.fst) (packagedFutureLaw f K tau x).entries) = 0 := by
      intro x
      exact hzeroRow (packagedFutureLaw f K tau x).entries
    simp [variationalObjective, rowwiseObjective, zeroLogLayer, supportList, Rat.mul_zero, hfutureZero]
    exact Rat.le_refl

example : packagedFutureLaw idLens2 toyKernel 1 (0 : Fin 2) = rowHalfHalf := by
  apply FinLaw.ext_entries
  native_decide

example : packagedFutureLaw idLens2 toyKernel 1 (1 : Fin 2) = rowThirdTwoThirds := by
  apply FinLaw.ext_entries
  native_decide

example : packagedFutureLawFamily idLens2 toyKernel 1 (0 : Fin 2) = rowHalfHalf := by
  simpa [packagedFutureLawFamily] using (show packagedFutureLaw idLens2 toyKernel 1 (0 : Fin 2) = rowHalfHalf from by
    apply FinLaw.ext_entries
    native_decide)

example : macroCurrentLaw idLens2 uniformTwo = uniformTwo := by
  apply FinLaw.ext_entries
  native_decide

example : macroPairLaw uniformTwo idLens2 toyKernel 1 = [
    (((0 : Fin 2), (0 : Fin 2)), (1 : Rat) / 4),
    (((0 : Fin 2), (1 : Fin 2)), (1 : Rat) / 4),
    (((1 : Fin 2), (0 : Fin 2)), (1 : Rat) / 6),
    (((1 : Fin 2), (1 : Fin 2)), (1 : Rat) / 3)
  ] := by
  native_decide

example : bestMacroKernel uniformTwo idLens2 toyKernel 1 (0 : Fin 2) =
    [((0 : Fin 2), half), ((1 : Fin 2), half)] := by
  native_decide

example : bestMacroKernel uniformTwo idLens2 toyKernel 1 (1 : Fin 2) =
    [((0 : Fin 2), third), ((1 : Fin 2), twoThirds)] := by
  native_decide

example : bestMacroKernel uniformTwo idLens2 toyKernel 1 (1 : Fin 2) =
    conditionalMacroFutureRow uniformTwo idLens2 toyKernel 1 (1 : Fin 2) := by
  exact bestMacroKernel_row_formula uniformTwo idLens2 toyKernel 1 (1 : Fin 2)

example :
    variationalObjective toyClosureLayer.toScalarLogLayer uniformTwo idLens2 toyKernel 1
      (bestMacroKernel uniformTwo idLens2 toyKernel 1) ≤
    variationalObjective toyClosureLayer.toScalarLogLayer uniformTwo idLens2 toyKernel 1
      (bestMacroKernel uniformTwo idLens2 toyKernel 1) := by
  exact bestMacroKernel_minimizesObjective toyClosureLayer uniformTwo idLens2 toyKernel 1
    (bestMacroKernel uniformTwo idLens2 toyKernel 1)

end SixBirdsNoGo
