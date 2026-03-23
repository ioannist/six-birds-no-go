import SixBirdsNoGo.FiniteProbabilityCore
import SixBirdsNoGo.FiniteKLDPI

namespace SixBirdsNoGo

abbrev MacroKernel (m : Nat) := Fin m → List (Fin m × Rat)

def deltaLaw {n : Nat} (x : Fin n) : FinLaw (Fin n) where
  entries := [(x, 1)]
  nonneg := by
    intro e h
    have hEq : e = (x, 1) := by simpa using h
    cases hEq
    simpa using (show (0 : Rat) ≤ (1 : Rat) by native_decide)
  sum_eq_one := by
    simpa [massSum] using (Rat.add_zero (1 : Rat))

def packagedFutureLaw {n m : Nat}
    (f : Fin n → Fin m) (K : FiniteKernel (Fin n) (Fin n))
    (tau : Nat) (x : Fin n) : FinLaw (Fin m) :=
  pushforward f (timeMarginal (pathLaw (deltaLaw x) K tau) ⟨tau, Nat.lt_succ_self tau⟩)

def packagedFutureLawFamily {n m : Nat}
    (f : Fin n → Fin m) (K : FiniteKernel (Fin n) (Fin n))
    (tau : Nat) : Fin n → FinLaw (Fin m) :=
  fun x => packagedFutureLaw f K tau x

abbrev macroCurrentLaw {n m : Nat} (f : Fin n → Fin m) (μ : FinLaw (Fin n)) : FinLaw (Fin m) :=
  pushforward f μ

private def pairEntries {n m : Nat}
    (entries : List (Fin n × Rat))
    (f : Fin n → Fin m) (future : Fin n → FinLaw (Fin m)) : List ((Fin m × Fin m) × Rat) :=
  match entries with
  | [] => []
  | e :: es =>
      (future e.1).entries.map (fun nxt => ((f e.1, nxt.1), e.2 * nxt.2)) ++
        pairEntries es f future

@[simp] def macroPairLaw {n m : Nat}
    (μ : FinLaw (Fin n)) (f : Fin n → Fin m) (K : FiniteKernel (Fin n) (Fin n))
    (tau : Nat) : List ((Fin m × Fin m) × Rat) :=
  pairEntries μ.entries f (packagedFutureLawFamily f K tau)

private def rawPointWeight {α : Type} [DecidableEq α]
    (entries : List (α × Rat)) (a : α) : Rat :=
  massSum (entries.map (fun e => if e.1 = a then (a, e.2) else (a, 0)))

private def conditionalRowDenom {n m : Nat}
    (μ : FinLaw (Fin n)) (f : Fin n → Fin m) (y : Fin m) : Rat :=
  pointWeight (macroCurrentLaw f μ) y

@[simp] def conditionalMacroFutureRow {n m : Nat}
    (μ : FinLaw (Fin n)) (f : Fin n → Fin m) (K : FiniteKernel (Fin n) (Fin n))
    (tau : Nat) (y : Fin m) : List (Fin m × Rat) :=
  let denom := conditionalRowDenom μ f y
  if _ : denom = 0 then
    [(y, 1)]
  else
    (List.finRange m).map (fun z => ((z : Fin m), rawPointWeight (macroPairLaw μ f K tau) (y, z) / denom))

/-- Weighted objective for one packaged future law against one candidate macro row. -/
def rowwiseObjective {m : Nat} (S : ScalarLogLayer) (w : Rat)
    (rowLaw : FinLaw (Fin m)) (candidateRow : List (Fin m × Rat)) : Rat :=
  w * massSum ((supportList rowLaw).map (fun a =>
    (a, pointWeight rowLaw a * S.logTerm (pointWeight rowLaw a) (rawPointWeight candidateRow a))))

/-- Exact finite objective over closure-local candidate macro kernels. -/
def variationalObjective {n m : Nat}
    (S : ScalarLogLayer) (μ : FinLaw (Fin n)) (f : Fin n → Fin m)
    (K : FiniteKernel (Fin n) (Fin n)) (tau : Nat) (candidate : MacroKernel m) : Rat :=
  massSum (μ.entries.map (fun e =>
    (e.1, rowwiseObjective S e.2 (packagedFutureLaw f K tau e.1) (candidate (f e.1)))))

@[simp] def bestMacroKernel {n m : Nat}
    (μ : FinLaw (Fin n)) (f : Fin n → Fin m) (K : FiniteKernel (Fin n) (Fin n))
    (tau : Nat) : MacroKernel m :=
  fun y => conditionalMacroFutureRow μ f K tau y

@[simp] theorem bestMacroKernel_row_formula {n m : Nat}
    (μ : FinLaw (Fin n)) (f : Fin n → Fin m) (K : FiniteKernel (Fin n) (Fin n))
    (tau : Nat) (y : Fin m) :
    bestMacroKernel μ f K tau y = conditionalMacroFutureRow μ f K tau y := rfl

structure ClosureVariationalLayer where
  toScalarLogLayer : ScalarLogLayer
  bestKernel_minimizer :
    ∀ {n m : Nat} (μ : FinLaw (Fin n)) (f : Fin n → Fin m)
      (K : FiniteKernel (Fin n) (Fin n)) (tau : Nat) (candidate : MacroKernel m),
      variationalObjective toScalarLogLayer μ f K tau (bestMacroKernel μ f K tau) ≤
        variationalObjective toScalarLogLayer μ f K tau candidate

 theorem bestMacroKernel_minimizesObjective {n m : Nat}
    (V : ClosureVariationalLayer) (μ : FinLaw (Fin n)) (f : Fin n → Fin m)
    (K : FiniteKernel (Fin n) (Fin n)) (tau : Nat) (candidate : MacroKernel m) :
    variationalObjective V.toScalarLogLayer μ f K tau (bestMacroKernel μ f K tau) ≤
      variationalObjective V.toScalarLogLayer μ f K tau candidate :=
  V.bestKernel_minimizer μ f K tau candidate

def bestMacroGap {n m : Nat}
    (V : ClosureVariationalLayer) (μ : FinLaw (Fin n)) (f : Fin n → Fin m)
    (K : FiniteKernel (Fin n) (Fin n)) (tau : Nat) : Rat :=
  variationalObjective V.toScalarLogLayer μ f K tau (bestMacroKernel μ f K tau)

end SixBirdsNoGo
