import SixBirdsNoGo.RealArrowDPI

namespace SixBirdsNoGo.RealProbability

open scoped BigOperators

abbrev Kernel (n : Nat) := Fin n → Law (Fin n)

noncomputable def pathMass {n : Nat} (initial : Law (Fin n)) (K : Kernel n) :
    (h : Nat) → PathState n h → ℝ
  | 0, s => initial.mass s
  | h + 1, s => pathMass initial K h s.1 * (K (lastState s.1)).mass s.2

theorem pathMass_nonneg {n : Nat} (initial : Law (Fin n)) (K : Kernel n) :
    ∀ h (s : PathState n h), 0 ≤ pathMass initial K h s := by
  intro h
  induction h with
  | zero => exact initial.nonneg
  | succ h ih => intro s; exact mul_nonneg (ih s.1) ((K (lastState s.1)).nonneg s.2)

theorem pathMass_sum_one {n : Nat} (initial : Law (Fin n)) (K : Kernel n) :
    ∀ h, ∑ s : PathState n h, pathMass initial K h s = 1 := by
  intro h
  induction h with
  | zero => exact initial.sum_one
  | succ h ih =>
    change (∑ s : PathState n h × Fin n,
      pathMass initial K h s.1 * (K (lastState s.1)).mass s.2) = 1
    rw [Fintype.sum_prod_type]
    simp_rw [← Finset.mul_sum, Law.sum_one, mul_one]
    exact ih

noncomputable def markovPathLaw {n : Nat} (initial : Law (Fin n)) (K : Kernel n)
    (h : Nat) : Law (PathState n h) :=
  ⟨pathMass initial K h, pathMass_nonneg initial K h, pathMass_sum_one initial K h⟩

theorem markovArrowDPI {n m h : Nat} (initial : Law (Fin n)) (K : Kernel n)
    (f : Fin n → Fin m) :
    KL (observedLaw f (markovPathLaw initial K h))
        (reversedLaw (observedLaw f (markovPathLaw initial K h))) ≤
      KL (markovPathLaw initial K h) (reversedLaw (markovPathLaw initial K h)) :=
  arrowDPI f (markovPathLaw initial K h)

def pathStates {n : Nat} : (h : Nat) → PathState n h → List (Fin n)
  | 0, s => [s]
  | h + 1, s => pathStates h s.1 ++ [s.2]

noncomputable def followWeight {α : Type*} (K : α → α → ℝ) : α → List α → ℝ
  | _, [] => 1
  | x, y :: ys => K x y * followWeight K y ys

noncomputable def listPathWeight {α : Type*} (π : α → ℝ) (K : α → α → ℝ) :
    List α → ℝ
  | [] => 0
  | x :: xs => π x * followWeight K x xs

theorem followWeight_append_single {α : Type*} (K : α → α → ℝ)
    (xs : List α) (x y : α) :
    followWeight K x (xs ++ [y]) = followWeight K x xs *
      K ((x :: xs).getLast (by simp)) y := by
  induction xs generalizing x with
  | nil => simp [followWeight]
  | cons z zs ih => simp [followWeight, ih, mul_assoc]

theorem listPathWeight_append_single {α : Type*} (π : α → ℝ) (K : α → α → ℝ)
    (xs : List α) (hne : xs ≠ []) (y : α) :
    listPathWeight π K (xs ++ [y]) =
      listPathWeight π K xs * K (xs.getLast hne) y := by
  cases xs with
  | nil => exact False.elim (hne rfl)
  | cons x xs => simp [listPathWeight, followWeight_append_single, mul_assoc]

/-- Detailed balance proves path-weight reversal without cancelling any
stationary masses, so null states are covered. -/
theorem detailedBalance_listPathWeight_reverse {α : Type*}
    (π : α → ℝ) (K : α → α → ℝ)
    (hDB : ∀ x y, π x * K x y = π y * K y x) (xs : List α) :
    listPathWeight π K xs.reverse = listPathWeight π K xs := by
  cases xs with
  | nil => rfl
  | cons x xs =>
    induction xs generalizing x with
    | nil => simp
    | cons y ys ih =>
      rw [List.reverse_cons, listPathWeight_append_single π K _ (by simp)]
      simp only [List.getLast_reverse, List.head_cons]
      rw [ih]
      simp only [listPathWeight, followWeight]
      rw [← mul_assoc, hDB x y]
      ring

theorem pathStates_nonempty {n : Nat} : ∀ h (s : PathState n h), pathStates h s ≠ [] := by
  intro h
  cases h <;> simp [pathStates]

theorem pathStates_last {n : Nat} : ∀ h (s : PathState n h),
    (pathStates h s).getLast (pathStates_nonempty h s) = lastState s := by
  intro h
  cases h <;> simp [pathStates, lastState, lastStateAux]

theorem pathStates_injective {n : Nat} : ∀ h, Function.Injective (@pathStates n h) := by
  intro h
  induction h with
  | zero => intro s t heq; simpa [pathStates] using heq
  | succ h ih =>
    intro s t heq
    have hp := List.append_inj' (show pathStates h s.1 ++ [s.2] = pathStates h t.1 ++ [t.2] from heq) rfl
    exact Prod.ext (ih hp.1) (by simpa using hp.2)

theorem pathStates_prepend {n : Nat} : ∀ h (x : Fin n) (s : PathState n h),
    pathStates (h + 1) (prependState x s) = x :: pathStates h s := by
  intro h
  induction h with
  | zero => intro x s; rfl
  | succ h ih =>
    intro x s
    cases s with
    | mk s y =>
      change pathStates (h + 1) (prependState x s) ++ [y] = x :: (pathStates h s ++ [y])
      rw [ih]
      rfl

theorem pathStates_reverse {n : Nat} : ∀ h (s : PathState n h),
    pathStates h (reversePathState s) = (pathStates h s).reverse := by
  intro h
  induction h with
  | zero => intro s; rfl
  | succ h ih =>
    intro s
    change pathStates (h + 1) (prependState s.2 (reversePathState s.1)) =
      (pathStates h s.1 ++ [s.2]).reverse
    rw [pathStates_prepend, ih]
    simp

theorem reversePathState_involutive {n h : Nat} (s : PathState n h) :
    reversePathState (reversePathState s) = s := by
  apply pathStates_injective h
  rw [pathStates_reverse, pathStates_reverse, List.reverse_reverse]

theorem pathMass_eq_listPathWeight {n : Nat} (initial : Law (Fin n)) (K : Kernel n) :
    ∀ h (s : PathState n h), pathMass initial K h s =
      listPathWeight initial.mass (fun x y => (K x).mass y) (pathStates h s) := by
  intro h
  induction h with
  | zero => intro s; simp [pathMass, listPathWeight, followWeight, pathStates]
  | succ h ih =>
    intro s
    rw [pathStates, listPathWeight_append_single _ _ _ (pathStates_nonempty h s.1),
      pathStates_last]
    change pathMass initial K h s.1 * _ = _
    rw [ih]

def DetailedBalance {n : Nat} (π : Law (Fin n)) (K : Kernel n) : Prop :=
  ∀ x y, π.mass x * (K x).mass y = π.mass y * (K y).mass x

theorem detailedBalance_pathMass_reverse {n : Nat} (π : Law (Fin n)) (K : Kernel n)
    (hDB : DetailedBalance π K) (h : Nat) (s : PathState n h) :
    pathMass π K h (reversePathState s) = pathMass π K h s := by
  rw [pathMass_eq_listPathWeight, pathStates_reverse, pathMass_eq_listPathWeight]
  exact detailedBalance_listPathWeight_reverse π.mass (fun x y => (K x).mass y) hDB _

theorem detailedBalance_pathLaw_reversible {n : Nat} (π : Law (Fin n)) (K : Kernel n)
    (hDB : DetailedBalance π K) (h : Nat) :
    reversedLaw (markovPathLaw π K h) = markovPathLaw π K h := by
  apply Law.ext
  funext s
  rw [reversedLaw, pushforward_involution_mass reversePathState reversePathState_involutive]
  exact detailedBalance_pathMass_reverse π K hDB h s

/-- The protocol no-go theorem from detailed balance, with no path-symmetry
assumption and with actual logarithms. Stationarity is implied by balance. -/
theorem protocolTrap {n m : Nat} (π : Law (Fin n)) (K : Kernel n)
    (hDB : DetailedBalance π K) (f : Fin n → Fin m) (h : Nat) :
    KL (observedLaw f (markovPathLaw π K h))
      (reversedLaw (observedLaw f (markovPathLaw π K h))) = 0 :=
  reversible_observation_zeroArrow f _ (detailedBalance_pathLaw_reversible π K hDB h)

end SixBirdsNoGo.RealProbability
