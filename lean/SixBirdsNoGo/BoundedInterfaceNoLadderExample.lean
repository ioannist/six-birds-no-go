import SixBirdsNoGo.BoundedInterfaceNoLadder

namespace SixBirdsNoGo

def exampleLens : FinLens where
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

def examplePack : Fin 3 → Fin 3
  | ⟨0, _⟩ => ⟨0, by decide⟩
  | _ => ⟨1, by decide⟩

theorem examplePack_idempotent : Idempotent examplePack := by
  intro x
  have hx : examplePack x = ⟨0, by decide⟩ ∨ examplePack x = ⟨1, by decide⟩ := by
    cases x using Fin.cases with
    | zero =>
        left
        rfl
    | succ x =>
        right
        rfl
  cases hx with
  | inl h0 =>
      rw [h0]
      rfl
  | inr h1 =>
      rw [h1]
      rfl

def exampleAssignFalse : BoolVec exampleLens.imgSize := fun _ => false

example : (allAssignments 2).length = 4 := by
  simpa using allAssignments_length_eq_two_pow 2

example : observedImageProfile exampleLens examplePack 4 = observedImageProfile exampleLens examplePack 1 := by
  simpa using observedImageProfile_stabilizes_after_one exampleLens examplePack examplePack_idempotent 3

example :
    observedDefinablePredicate exampleLens examplePack exampleAssignFalse 4 =
      observedDefinablePredicate exampleLens examplePack exampleAssignFalse 1 := by
  simpa using observedDefinablePredicate_stabilizes_after_one
    exampleLens examplePack examplePack_idempotent exampleAssignFalse 3

example :
    NoLadderUnderFixedInterface exampleLens examplePack ∧
      (Nonempty (DefinablePred exampleLens ≃ BoolVec exampleLens.imgSize) ∧
        (allAssignments exampleLens.imgSize).length = 2 ^ exampleLens.imgSize) := by
  exact boundedInterface_noLadderCorollary exampleLens examplePack examplePack_idempotent

end SixBirdsNoGo
