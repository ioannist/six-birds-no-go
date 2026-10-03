import Mathlib.Data.Fintype.Card
import Mathlib.Data.Fintype.Pi
import Mathlib.Tactic

/-! Exact predicate count and anti-ladder for arbitrary domains and codomains
with finite image. Neither packaging nor finiteness of the domain is assumed. -/

namespace SixBirdsNoGo.FiniteImage

def Pred {α β : Type*} (f : α → β) :=
  {p : α → Bool // ∃ g : β → Bool, p = g ∘ f}

noncomputable def assignment {α β : Type*} (f : α → β) (p : Pred f) :
    Set.range f → Bool := fun y => Classical.choose p.property y.val

noncomputable def pullback {α β : Type*} (f : α → β) (a : Set.range f → Bool) :
    Pred f := by
  classical
  exact ⟨fun x => a ⟨f x, ⟨x, rfl⟩⟩,
    ⟨fun y => if hy : y ∈ Set.range f then a ⟨y, hy⟩ else false,
      by funext x; simp⟩⟩

theorem assignment_spec {α β : Type*} (f : α → β) (p : Pred f) (x : α) :
    p.val x = assignment f p ⟨f x, ⟨x, rfl⟩⟩ := by
  have h := congrFun (Classical.choose_spec p.property) x
  exact h

noncomputable def predEquiv {α β : Type*} (f : α → β) :
    Pred f ≃ (Set.range f → Bool) where
  toFun := assignment f
  invFun := pullback f
  left_inv := by
    intro p
    apply Subtype.ext
    funext x
    exact (assignment_spec f p x).symm
  right_inv := by
    intro a
    funext y
    obtain ⟨x, hx⟩ := y.property
    have heq : (⟨f x, ⟨x, rfl⟩⟩ : Set.range f) = y := Subtype.ext hx
    rw [← heq]
    exact (assignment_spec f (pullback f a) x).symm

noncomputable instance {α β : Type*} (f : α → β) [Fintype (Set.range f)] :
    Fintype (Pred f) := by
  classical
  exact Fintype.ofEquiv (Set.range f → Bool) (predEquiv f).symm

theorem definable_cardinality {α β : Type*} (f : α → β) [Fintype (Set.range f)] :
    Fintype.card (Pred f) = 2 ^ Fintype.card (Set.range f) := by
  classical
  rw [Fintype.card_congr (predEquiv f)]
  simp

theorem no_infinite_distinct_sequence {α β : Type*} (f : α → β)
    [Finite (Set.range f)] (p : Nat → Pred f) : ¬ Function.Injective p := by
  classical
  letI := Fintype.ofFinite (Set.range f)
  intro hp
  have hcard : Fintype.card (Pred f) + 1 ≤ Fintype.card (Pred f) := by
    simpa using Fintype.card_le_of_injective
      (fun i : Fin (Fintype.card (Pred f) + 1) => p i.val)
      (fun i j h => Fin.ext (hp h))
  omega

end SixBirdsNoGo.FiniteImage
