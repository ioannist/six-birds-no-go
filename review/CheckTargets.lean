import SixBirdsNoGo

/-! These explicit target types check the coverage bridge, separately from
compiling the implementation modules. The semantic definitions are audited
in mathematical-review.txt. -/

open SixBirdsNoGo
open SixBirdsNoGo.RealProbability

example {n m h : Nat} (w : Law (Fin n)) (K : Kernel n) (f : Fin n → Fin m) :
    KL (observedLaw f (markovPathLaw w K h))
      (reversedLaw (observedLaw f (markovPathLaw w K h))) ≤
    KL (markovPathLaw w K h) (reversedLaw (markovPathLaw w K h)) :=
  markovArrowDPI w K f

example {n m : Nat} (π : Law (Fin n)) (K : Kernel n)
    (hDB : ∀ x y, π.mass x * (K x).mass y = π.mass y * (K y).mass x)
    (f : Fin n → Fin m) (h : Nat) :
    KL (observedLaw f (markovPathLaw π K h))
      (reversedLaw (observedLaw f (markovPathLaw π K h))) = 0 :=
  protocolTrap π K hDB f h

example {V : Type*} (G : SimpleGraph V) (hG : G.IsAcyclic) (a : V → V → ℝ)
    (hanti : ∀ u v, G.Adj u v → a u v = -a v u) :
    ∃ φ : V → ℝ, ∀ u v, G.Adj u v → a u v = φ v - φ u :=
  RealGraph.forest_exact hG a hanti

example {V : Type*} (G : SimpleGraph V) (a : V → V → ℝ) (φ : V → ℝ)
    (hexact : ∀ u v, G.Adj u v → a u v = φ v - φ u)
    (u : V) (p : G.Walk u u) : RealGraph.integral a p = 0 :=
  RealGraph.exact_closedWalk_zero a φ hexact p

example {n m : Nat} (w : Law (Fin n)) (f : Fin n → Fin m) (K : Kernel n) (τ : Nat) :
    (objective w f (futureLaw f K τ) (conditionalKernel w f (futureLaw f K τ)) =
      (conditionalInfo w f (futureLaw f K τ) : EReal)) ∧
    (∀ k, (conditionalInfo w f (futureLaw f K τ) : EReal) ≤ objective w f (futureLaw f K τ) k) ∧
    (∀ x x', 0 < w.mass x → 0 < w.mass x' → f x = f x' →
      (futureLaw f K τ x).mass ≠ (futureLaw f K τ x').mass →
      0 < conditionalInfo w f (futureLaw f K τ)) :=
  closureTheorem w f K τ

example {α : Type*} [Fintype α] [Nonempty α] (K : α → Law α)
    (h : dobrushin K < 1) (p q : Law α) (ε : ℝ)
    (hp : TV p (mixture p K) ≤ ε) (hq : TV q (mixture q K) ≤ ε) :
    TV p q ≤ 2 * ε / (1 - dobrushin K) :=
  contractive_separation K h p q ε hp hq

example {α : Type} (e : α → α) (h : ∀ x, e (e x) = e x) (n : Nat) :
    SixBirdsNoGo.Function.iterate e (n + 1) = e :=
  iterate_stabilizes_ext e h n

example {α β : Type*} (f : α → β) [Fintype (Set.range f)] :
    Fintype.card (FiniteImage.Pred f) = 2 ^ Fintype.card (Set.range f) :=
  FiniteImage.definable_cardinality f

example {α β : Type*} (f : α → β) [Finite (Set.range f)] (p : Nat → FiniteImage.Pred f) :
    ¬ Function.Injective p := FiniteImage.no_infinite_distinct_sequence f p
