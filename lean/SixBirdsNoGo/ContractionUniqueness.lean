namespace SixBirdsNoGo

/-- A fixed point of a self-map. -/
def FixedPoint {α : Type} (f : α → α) (x : α) : Prop :=
  f x = x

/-- Strict contraction on unequal points, measured by a natural-valued distance. -/
def StrictlyContractiveOnNe {α : Type} (d : α → α → Nat) (f : α → α) : Prop :=
  ∀ ⦃x y : α⦄, x ≠ y → d (f x) (f y) < d x y

/-- Fixed points of a strict contraction must coincide. -/
theorem fixed_eq_of_strictContraction
    {α : Type}
    (d : α → α → Nat)
    (f : α → α)
    (h : StrictlyContractiveOnNe d f)
    {x y : α}
    (hx : FixedPoint f x)
    (hy : FixedPoint f y) :
    x = y := by
  by_cases hxy : x = y
  · exact hxy
  · exfalso
    have hlt := h (x := x) (y := y) hxy
    rw [hx, hy] at hlt
    exact Nat.lt_irrefl _ hlt

/-- Any strict contraction has at most one fixed point. -/
theorem atMostOneFixedPoint_of_strictContraction
    {α : Type}
    (d : α → α → Nat)
    (f : α → α)
    (h : StrictlyContractiveOnNe d f) :
    ∀ x y : α, FixedPoint f x → FixedPoint f y → x = y := by
  intro x y hx hy
  exact fixed_eq_of_strictContraction d f h hx hy

end SixBirdsNoGo
