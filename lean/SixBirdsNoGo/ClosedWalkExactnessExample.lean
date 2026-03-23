import SixBirdsNoGo.ClosedWalkExactness

namespace SixBirdsNoGo

inductive V where
  | a
  | b
  | c
  deriving Repr, DecidableEq

def φ : V → Int
  | .a => 1
  | .b => 4
  | .c => -2

def ℓ (u v : V) : Int :=
  φ v - φ u

theorem exactDiff : ExactPotentialDiff φ ℓ := by
  intro u v
  cases u <;> cases v <;> decide

def wA : Walk V := Walk.single V.a
def wAB : Walk V := Walk.snoc wA V.b
def wABC : Walk V := Walk.snoc wAB V.c
def wABCA : Walk V := Walk.snoc wABC V.a

example : Walk.finish wABCA = Walk.start wABCA := by
  simp [wABCA, wABC, wAB, wA]

example : edgeSum ℓ wABCA = 0 := by
  apply closedWalkSum_eq_zero φ ℓ exactDiff wABCA
  simp [wABCA, wABC, wAB, wA]

example : φ (Walk.start wABC) + edgeSum ℓ wABC = φ (Walk.finish wABC) := by
  exact potential_start_add_edgeSum_eq_potential_finish φ ℓ exactDiff wABC

end SixBirdsNoGo
