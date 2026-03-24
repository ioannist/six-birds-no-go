namespace SixBirdsNoGo

namespace Function

def iterate {α : Type} (f : α → α) : Nat → α → α
  | 0 => id
  | Nat.succ n => fun x => f (iterate f n x)

end Function

/-- `e` is idempotent when one additional application does nothing. -/
def Idempotent {α : Type} (e : α → α) : Prop :=
  ∀ x, e (e x) = e x

/-- Pointwise stabilization: once `e` is idempotent, all `(n+1)` iterates equal one step. -/
theorem iterate_stabilizes_pointwise {α : Type} (e : α → α)
    (h : Idempotent e) :
    ∀ n x, (Function.iterate e (n + 1)) x = e x := by
  intro n
  induction n with
  | zero =>
      intro x
      simp [Function.iterate]
  | succ n ih =>
      intro x
      change e ((Function.iterate e (n + 1)) x) = e x
      rw [ih x]
      exact h x

/-- Extensional stabilization: every `(n+1)` iterate is the same map `e`. -/
theorem iterate_stabilizes_ext {α : Type} (e : α → α)
    (h : Idempotent e) (n : Nat) :
    Function.iterate e (n + 1) = e := by
  funext x
  exact iterate_stabilizes_pointwise e h n x

end SixBirdsNoGo
