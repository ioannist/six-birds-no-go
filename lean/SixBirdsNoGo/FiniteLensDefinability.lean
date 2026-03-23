namespace SixBirdsNoGo

structure Equiv (α : Sort u) (β : Sort v) where
  toFun : α → β
  invFun : β → α
  left_inv : ∀ x, invFun (toFun x) = x
  right_inv : ∀ y, toFun (invFun y) = y

infix:25 " ≃ " => Equiv

/-- A minimal finite deterministic lens from a finite domain to a finite image. -/
structure FinLens where
  domSize : Nat
  imgSize : Nat
  toImage : Fin domSize → Fin imgSize
  surj : ∀ y : Fin imgSize, ∃ x : Fin domSize, toImage x = y

/-- A Boolean assignment vector over a finite index set. -/
abbrev BoolVec (n : Nat) := Fin n → Bool

namespace BoolVec

/-- Lookup in a Boolean assignment vector. -/
def get {n : Nat} (v : BoolVec n) (i : Fin n) : Bool :=
  v i

end BoolVec

/-- Extend a Boolean assignment by fixing the new head bit. -/
def extendAssignment {n : Nat} (b : Bool) (a : BoolVec n) : BoolVec (n + 1) :=
  fun i =>
    match i with
    | ⟨0, _⟩ => b
    | ⟨Nat.succ k, h⟩ => a ⟨k, Nat.lt_of_succ_lt_succ h⟩

/-- Explicit enumeration of all Boolean assignments on `Fin n`. -/
def allAssignments : (n : Nat) → List (BoolVec n)
  | 0 => [fun i => False.elim (Nat.not_lt_zero _ i.isLt)]
  | Nat.succ n =>
      (allAssignments n).map (extendAssignment (n := n) false) ++
        (allAssignments n).map (extendAssignment (n := n) true)

@[simp] theorem allAssignments_zero :
    allAssignments 0 = [fun i : Fin 0 => False.elim (Nat.not_lt_zero _ i.isLt)] := rfl

@[simp] theorem allAssignments_succ (n : Nat) :
    allAssignments (Nat.succ n) =
      (allAssignments n).map (extendAssignment (n := n) false) ++
        (allAssignments n).map (extendAssignment (n := n) true) := rfl

theorem allAssignments_length_eq_two_pow : ∀ n : Nat, (allAssignments n).length = 2 ^ n
  | 0 => by
      simp [allAssignments]
  | Nat.succ n => by
      calc
        (allAssignments (Nat.succ n)).length
            = (allAssignments n).length + (allAssignments n).length := by
                simp [allAssignments]
        _ = 2 * (allAssignments n).length := by
              simp [Nat.two_mul]
        _ = 2 * 2 ^ n := by
              rw [allAssignments_length_eq_two_pow n]
        _ = 2 ^ (Nat.succ n) := by
              simpa [Nat.pow_succ, Nat.mul_comm, Nat.mul_left_comm, Nat.mul_assoc]

/-- The predicate induced on the domain by a Boolean assignment on the image. -/
def inducedPredicate (L : FinLens) (a : BoolVec L.imgSize) : Fin L.domSize → Bool :=
  fun x => BoolVec.get a (L.toImage x)

/-- Definable domain predicates for a fixed lens. -/
def DefinablePred (L : FinLens) : Type :=
  { p : Fin L.domSize → Bool // ∃ a : BoolVec L.imgSize, p = inducedPredicate L a }

/-- Surjective pullback is injective on image assignments. -/
theorem inducedPredicate_injective (L : FinLens)
    (a b : BoolVec L.imgSize)
    (h : inducedPredicate L a = inducedPredicate L b) :
    a = b := by
  funext y
  rcases L.surj y with ⟨x, hx⟩
  have h' := congrArg (fun p => p x) h
  simpa [inducedPredicate, hx, BoolVec.get] using h'

noncomputable def assignmentOf (L : FinLens) : DefinablePred L → BoolVec L.imgSize :=
  fun p => Classical.choose p.property

theorem assignmentOf_spec (L : FinLens) (p : DefinablePred L) :
    p.1 = inducedPredicate L (assignmentOf L p) := by
  exact Classical.choose_spec p.property

/-- Definable predicates are equivalent to Boolean assignments on the image. -/
noncomputable def definablePredEquivAssignments (L : FinLens) :
    Equiv (DefinablePred L) (BoolVec L.imgSize) where
  toFun := assignmentOf L
  invFun := fun a => ⟨inducedPredicate L a, ⟨a, rfl⟩⟩
  left_inv := by
    intro p
    apply Subtype.ext
    exact (assignmentOf_spec L p).symm
  right_inv := by
    intro a
    have h : inducedPredicate L a =
        inducedPredicate L (assignmentOf L (⟨inducedPredicate L a, ⟨a, rfl⟩⟩ : DefinablePred L)) := by
      simpa using (assignmentOf_spec L (⟨inducedPredicate L a, ⟨a, rfl⟩⟩ : DefinablePred L))
    exact (inducedPredicate_injective L a
      (assignmentOf L (⟨inducedPredicate L a, ⟨a, rfl⟩⟩ : DefinablePred L)) h).symm

/-- Direct count-core wrapper for a finite lens. -/
theorem finiteLens_definableCountCore (L : FinLens) :
    Nonempty (Equiv (DefinablePred L) (BoolVec L.imgSize)) ∧ (allAssignments L.imgSize).length = 2 ^ L.imgSize := by
  constructor
  · exact ⟨definablePredEquivAssignments L⟩
  · exact allAssignments_length_eq_two_pow L.imgSize

end SixBirdsNoGo
