import SixBirdsNoGo.ContractionUniqueness

namespace SixBirdsNoGo

def Three : Type :=
  Fin 3

def toyDist : Three → Three → Nat :=
  fun x y => if x.val = y.val then 0 else 1

def collapseToZero : Three → Three :=
  fun _ => ⟨0, by decide⟩

theorem collapseToZero_strictContractive :
    StrictlyContractiveOnNe toyDist collapseToZero := by
  intro x y hxy
  have hvals : x.val ≠ y.val := by
    intro hEq
    apply hxy
    exact Fin.ext hEq
  simp [toyDist, collapseToZero, hvals]

def zero : Three := ⟨0, by decide⟩

example : FixedPoint collapseToZero zero := by
  simp [FixedPoint, collapseToZero, zero]

example (x : Three) : FixedPoint collapseToZero x → x = zero := by
  intro hx
  exact atMostOneFixedPoint_of_strictContraction toyDist collapseToZero
    collapseToZero_strictContractive x zero hx (by simp [FixedPoint, collapseToZero, zero])

example (x : Three) (hx : FixedPoint collapseToZero x) : x = zero := by
  exact atMostOneFixedPoint_of_strictContraction toyDist collapseToZero
    collapseToZero_strictContractive x zero hx (by simp [FixedPoint, collapseToZero, zero])

end SixBirdsNoGo
