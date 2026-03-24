import SixBirdsNoGo.FiniteLensDefinability

namespace SixBirdsNoGo

def lens3to2 : FinLens where
  domSize := 3
  imgSize := 2
  toImage := fun x =>
    match x with
    | ⟨0, _⟩ => ⟨0, by decide⟩
    | _ => ⟨1, by decide⟩
  surj := by
    intro y
    cases y using Fin.cases with
    | zero =>
        refine ⟨⟨0, by decide⟩, ?_⟩
        rfl
    | succ y =>
        refine ⟨⟨1, by decide⟩, ?_⟩
        cases y using Fin.cases with
        | zero =>
            rfl
        | succ y =>
            cases y with
            | mk val isLt =>
                cases Nat.not_lt_zero _ isLt

example : (allAssignments 2).length = 4 := by
  simpa using allAssignments_length_eq_two_pow 2

example : Nonempty (Equiv (DefinablePred lens3to2) (BoolVec lens3to2.imgSize)) := by
  exact ⟨definablePredEquivAssignments lens3to2⟩

def assignFalse : BoolVec 2 := fun _ => false

def assignHeadTrue : BoolVec 2 := fun
  | ⟨0, _⟩ => true
  | ⟨1, _⟩ => false

example : inducedPredicate lens3to2 assignFalse ≠ inducedPredicate lens3to2 assignHeadTrue := by
  intro h
  have h' : assignFalse = assignHeadTrue :=
    inducedPredicate_injective lens3to2 assignFalse assignHeadTrue h
  have h0 := congrArg (fun f => f ⟨0, by decide⟩) h'
  simp [assignFalse, assignHeadTrue] at h0

end SixBirdsNoGo
