namespace SixBirdsNoGo

/-- Minimal rooted tree with signed labels on parent→child edges.
Reverse orientation is interpreted implicitly as label negation `-w`. -/
inductive RootedTree where
  | node : List (Int × RootedTree) → RootedTree
  deriving Repr

namespace RootedTree

def children : RootedTree → List (Int × RootedTree)
  | .node cs => cs

end RootedTree

/-- `Path root current` is a descent path from `root` to `current`. -/
inductive Path : RootedTree → RootedTree → Type where
  | here (root : RootedTree) : Path root root
  | down {root parent child : RootedTree}
      (p : Path root parent)
      (w : Int)
      (h : (w, child) ∈ RootedTree.children parent) :
      Path root child

/-- Root-path sum of edge labels. -/
def pathSum {root current : RootedTree} : Path root current → Int
  | .here _ => 0
  | .down p w _ => pathSum p + w

/-- Potential induced by choosing a root value and summing edge labels along the path. -/
def potential {root current : RootedTree}
    (rootValue : Int) (p : Path root current) : Int :=
  rootValue + pathSum p

@[simp] theorem pathSum_here (root : RootedTree) :
    pathSum (Path.here root) = 0 := rfl

@[simp] theorem pathSum_down {root parent child : RootedTree}
    (p : Path root parent) (w : Int)
    (h : (w, child) ∈ RootedTree.children parent) :
    pathSum (Path.down p w h) = pathSum p + w := rfl

@[simp] theorem potential_here (root : RootedTree) (rootValue : Int) :
    potential rootValue (Path.here root) = rootValue := by
  simp [potential]

/-- Exactness under one-step extension along a tree edge. -/
theorem potential_down_eq_parent_plus_label
    {root parent child : RootedTree}
    (rootValue : Int)
    (p : Path root parent)
    (w : Int)
    (h : (w, child) ∈ RootedTree.children parent) :
    potential rootValue (Path.down p w h) = potential rootValue p + w := by
  simp [potential, Int.add_assoc]

end SixBirdsNoGo
