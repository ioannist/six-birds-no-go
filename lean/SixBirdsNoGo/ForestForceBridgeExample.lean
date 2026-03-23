import SixBirdsNoGo.ForestForceBridge

namespace SixBirdsNoGo

open RootedTree

def ffLeaf : RootedTree := .node []
def ffChild : RootedTree := .node [(5, ffLeaf)]
def ffRoot : RootedTree := .node [(3, ffChild)]

def ffPathRoot : Path ffRoot ffRoot := Path.here ffRoot

def ffPathChild : Path ffRoot ffChild :=
  Path.down ffPathRoot 3 (by
    exact List.Mem.head _)

def ffPathLeaf : Path ffRoot ffLeaf :=
  Path.down ffPathChild 5 (by
    exact List.Mem.head _)

def ffVRoot : ForestVertex ffRoot := ⟨ffRoot, ffPathRoot⟩
def ffVChild : ForestVertex ffRoot := ⟨ffChild, ffPathChild⟩
def ffVLeaf : ForestVertex ffRoot := ⟨ffLeaf, ffPathLeaf⟩

example :
    forestInducedLabel 0 ffVRoot ffVChild = 3 := by
  simpa [ffVRoot, ffVChild, ffPathRoot, ffPathChild] using
    (forest_child_step_label_agrees
      (root := ffRoot)
      (parent := ffRoot)
      (child := ffChild)
      (rootValue := 0)
      ffPathRoot
      3
      (by exact List.Mem.head _))

example :
    forestInducedLabel 0 ffVChild ffVLeaf = 5 := by
  simpa [ffVChild, ffVLeaf, ffPathChild, ffPathLeaf] using
    (forest_child_step_label_agrees
      (root := ffRoot)
      (parent := ffChild)
      (child := ffLeaf)
      (rootValue := 0)
      ffPathChild
      5
      (by exact List.Mem.head _))

def ffClosed : Walk (ForestVertex ffRoot) :=
  Walk.snoc (Walk.snoc (Walk.single ffVRoot) ffVChild) ffVRoot

example : edgeSum (forestInducedLabel 0) ffClosed = 0 := by
  apply forest_closedWalkSum_eq_zero (root := ffRoot) (rootValue := 0) ffClosed
  simp [ffClosed, ffVRoot, ffVChild]

end SixBirdsNoGo
