import SixBirdsNoGo.TreeExactness

namespace SixBirdsNoGo

open RootedTree

/-- Example tree:
root has children `(3, childA)` and `(-2, childB)`;
`childA` has one child `(5, leaf)`. -/
def leaf : RootedTree := .node []
def childA : RootedTree := .node [(5, leaf)]
def childB : RootedTree := .node []
def exampleTree : RootedTree := .node [(3, childA), (-2, childB)]

def pToChildA : Path exampleTree childA :=
  Path.down (Path.here exampleTree) 3 (by
    exact List.Mem.head _)

def pToLeaf : Path exampleTree leaf :=
  Path.down pToChildA 5 (by
    exact List.Mem.head _)

example : potential 0 pToChildA = 3 := by
  decide

example : potential 0 pToLeaf = 8 := by
  decide

example : potential 7 pToLeaf = 15 := by
  decide

end SixBirdsNoGo
