import SixBirdsNoGo.TreeExactness
import SixBirdsNoGo.ClosedWalkExactness

namespace SixBirdsNoGo

open RootedTree

structure ForestVertex (root : RootedTree) where
  current : RootedTree
  path : Path root current

def forestPotential {root : RootedTree} (rootValue : Int) (v : ForestVertex root) : Int :=
  potential rootValue v.path

def forestInducedLabel {root : RootedTree} (rootValue : Int)
    (u v : ForestVertex root) : Int :=
  forestPotential rootValue v - forestPotential rootValue u

private theorem add_sub_cancel_left_int (a b : Int) : a + (b - a) = b := by
  calc
    a + (b - a) = a + (b + -a) := by rfl
    _ = (a + b) + -a := by rw [Int.add_assoc]
    _ = (b + a) + -a := by rw [Int.add_comm a b]
    _ = b + (a + -a) := by rw [← Int.add_assoc]
    _ = b + 0 := by rw [Int.add_right_neg]
    _ = b := by simp

private theorem add_right_sub_self_int (a b : Int) : (a + b) - a = b := by
  calc
    (a + b) - a = (a + b) + -a := by rfl
    _ = (b + a) + -a := by rw [Int.add_comm a b]
    _ = b + (a + -a) := by rw [← Int.add_assoc]
    _ = b + 0 := by rw [Int.add_right_neg]
    _ = b := by simp

theorem forestInducedLabel_exact {root : RootedTree} (rootValue : Int) :
    ExactPotentialDiff
      (forestPotential (root := root) rootValue)
      (forestInducedLabel (root := root) rootValue) := by
  intro u v
  exact add_sub_cancel_left_int (forestPotential rootValue u) (forestPotential rootValue v)

theorem forest_child_step_label_agrees
    {root parent child : RootedTree}
    (rootValue : Int)
    (p : Path root parent)
    (w : Int)
    (h : (w, child) ∈ RootedTree.children parent) :
    let u : ForestVertex root := ⟨parent, p⟩
    let v : ForestVertex root := ⟨child, Path.down p w h⟩
    forestInducedLabel rootValue u v = w := by
  dsimp [forestInducedLabel, forestPotential]
  rw [potential_down_eq_parent_plus_label]
  exact add_right_sub_self_int (potential rootValue p) w

theorem forest_closedWalkSum_eq_zero
    {root : RootedTree}
    (rootValue : Int)
    (w : Walk (ForestVertex root))
    (hclosed : Walk.finish w = Walk.start w) :
    edgeSum (forestInducedLabel (root := root) rootValue) w = 0 := by
  exact closedWalkSum_eq_zero
    (φ := forestPotential rootValue)
    (ℓ := forestInducedLabel rootValue)
    (hExact := forestInducedLabel_exact rootValue)
    (w := w)
    (hclosed := hclosed)

end SixBirdsNoGo
