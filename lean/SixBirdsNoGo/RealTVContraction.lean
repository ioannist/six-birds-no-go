import SixBirdsNoGo.RealKLMixture
import Mathlib.Data.Finset.Max
import Mathlib.Data.Finset.Lattice.Fold

/-! Total variation and the Dobrushin estimate for genuine stochastic rows.
The minimum-row reference keeps every coefficient nonnegative; an arbitrary
reference row cannot be used when discarding negative signed masses. -/

namespace SixBirdsNoGo.RealProbability

open scoped BigOperators

noncomputable def TV {α : Type*} [Fintype α] (p q : Law α) : ℝ :=
  (∑ a, |p.mass a - q.mass a|) / 2

theorem TV_nonneg {α : Type*} [Fintype α] (p q : Law α) : 0 ≤ TV p q :=
  div_nonneg (Finset.sum_nonneg (fun _ _ => abs_nonneg _)) (by norm_num)

theorem TV_symm {α : Type*} [Fintype α] (p q : Law α) : TV p q = TV q p := by
  simp only [TV, abs_sub_comm]

theorem TV_self {α : Type*} [Fintype α] (p : Law α) : TV p p = 0 := by
  simp [TV]

theorem TV_eq_zero_iff {α : Type*} [Fintype α] (p q : Law α) :
    TV p q = 0 ↔ p = q := by
  constructor
  · intro h
    have hz : ∑ a, |p.mass a - q.mass a| = 0 := by
      unfold TV at h
      linarith
    have heach := (Finset.sum_eq_zero_iff_of_nonneg (fun a _ => abs_nonneg
      (p.mass a - q.mass a))).mp hz
    apply Law.ext
    funext a
    exact sub_eq_zero.mp (abs_eq_zero.mp (heach a (Finset.mem_univ a)))
  · intro h; subst q; exact TV_self p

theorem TV_triangle {α : Type*} [Fintype α] (p q r : Law α) :
    TV p r ≤ TV p q + TV q r := by
  have h := Finset.sum_le_sum (s := Finset.univ) (fun a _ => abs_sub_le (p.mass a)
    (q.mass a) (r.mass a))
  rw [Finset.sum_add_distrib] at h
  unfold TV
  linarith

theorem positivePart_formula (x : ℝ) : max x 0 = (|x| + x) / 2 := by
  by_cases hx : 0 ≤ x
  · rw [max_eq_left hx, abs_of_nonneg hx]; ring
  · have hx' := le_of_not_ge hx
    rw [max_eq_right hx', abs_of_nonpos hx']; ring

theorem TV_positivePart {α : Type*} [Fintype α] (p q : Law α) :
    TV p q = ∑ a, max (p.mass a - q.mass a) 0 := by
  simp_rw [positivePart_formula]
  rw [← Finset.sum_div, Finset.sum_add_distrib, Finset.sum_sub_distrib,
    p.sum_one, q.sum_one]
  simp [TV]

noncomputable def eventMass {α : Type*} [Fintype α] (p : Law α) (s : Finset α) : ℝ :=
  ∑ a ∈ s, p.mass a

theorem eventDifference_le_TV {α : Type*} [Fintype α] (p q : Law α) (s : Finset α) :
    eventMass p s - eventMass q s ≤ TV p q := by
  classical
  rw [TV_positivePart]
  unfold eventMass
  rw [← Finset.sum_sub_distrib]
  apply le_trans (Finset.sum_le_sum (fun a _ => le_max_left (p.mass a - q.mass a) 0))
  exact Finset.sum_le_sum_of_subset_of_nonneg (Finset.subset_univ s)
    (fun a _ _ => le_max_right _ _)

noncomputable def positiveSet {α : Type*} [Fintype α] (p q : Law α) : Finset α := by
  classical
  exact Finset.univ.filter (fun a => 0 < p.mass a - q.mass a)

theorem TV_attained {α : Type*} [Fintype α] (p q : Law α) :
    TV p q = eventMass p (positiveSet p q) - eventMass q (positiveSet p q) := by
  classical
  rw [TV_positivePart]
  unfold eventMass positiveSet
  rw [← Finset.sum_sub_distrib, Finset.sum_filter]
  apply Finset.sum_congr rfl
  intro a _
  split_ifs with h
  · exact max_eq_left (le_of_lt h)
  · exact max_eq_right (le_of_not_gt h)

theorem eventMass_mixture {α β : Type*} [Fintype α] [Fintype β]
    (w : Law α) (K : α → Law β) (s : Finset β) :
    eventMass (mixture w K) s = ∑ a, w.mass a * eventMass (K a) s := by
  unfold eventMass mixture
  rw [Finset.sum_comm]
  simp_rw [Finset.mul_sum]

theorem signed_product_bound {x t rho : ℝ} (ht : 0 ≤ t) (hrho : t ≤ rho) :
    x * t ≤ max x 0 * rho := by
  by_cases hx : 0 ≤ x
  · rw [max_eq_left hx]; exact mul_le_mul_of_nonneg_left hrho hx
  · rw [max_eq_right (le_of_not_ge hx), zero_mul]
    exact mul_nonpos_of_nonpos_of_nonneg (le_of_not_ge hx) ht

/-- The event proof of Dobrushin contraction, before taking the row maximum. -/
theorem TV_mixture_contraction {α β : Type*} [Fintype α] [Nonempty α] [Fintype β]
    (p q : Law α) (K : α → Law β) (rho : ℝ)
    (hrows : ∀ i j, TV (K i) (K j) ≤ rho) :
    TV (mixture p K) (mixture q K) ≤ rho * TV p q := by
  classical
  let s := positiveSet (mixture p K) (mixture q K)
  obtain ⟨j, _, hj⟩ := Finset.exists_min_image Finset.univ
    (fun i => eventMass (K i) s) Finset.univ_nonempty
  have hcoeff (i : α) : 0 ≤ eventMass (K i) s - eventMass (K j) s :=
    sub_nonneg.mpr (hj i (Finset.mem_univ i))
  have hcoeff' (i : α) : eventMass (K i) s - eventMass (K j) s ≤ rho :=
    le_trans (eventDifference_le_TV (K i) (K j) s) (hrows i j)
  have hsum : (∑ i, (p.mass i - q.mass i) * eventMass (K i) s) =
      ∑ i, (p.mass i - q.mass i) * (eventMass (K i) s - eventMass (K j) s) := by
    simp_rw [mul_sub]
    rw [Finset.sum_sub_distrib, ← Finset.sum_mul, Finset.sum_sub_distrib,
      p.sum_one, q.sum_one]
    ring
  rw [TV_attained, eventMass_mixture, eventMass_mixture, ← Finset.sum_sub_distrib]
  change (∑ i, (p.mass i * eventMass (K i) s - q.mass i * eventMass (K i) s)) ≤ _
  simp_rw [← sub_mul]
  rw [hsum, TV_positivePart, mul_comm rho, Finset.sum_mul]
  exact Finset.sum_le_sum (fun i _ => signed_product_bound (hcoeff i) (hcoeff' i))

noncomputable def dobrushin {α : Type*} [Fintype α] [Nonempty α]
    (K : α → Law α) : ℝ :=
  Finset.univ.sup' Finset.univ_nonempty (fun ij : α × α => TV (K ij.1) (K ij.2))

theorem TV_row_le_dobrushin {α : Type*} [Fintype α] [Nonempty α]
    (K : α → Law α) (i j : α) : TV (K i) (K j) ≤ dobrushin K :=
  by
  unfold dobrushin
  exact Finset.le_sup' (fun ij : α × α => TV (K ij.1) (K ij.2)) (Finset.mem_univ (i, j))

theorem dobrushin_contraction {α : Type*} [Fintype α] [Nonempty α]
    (K : α → Law α) (p q : Law α) :
    TV (mixture p K) (mixture q K) ≤ dobrushin K * TV p q :=
  TV_mixture_contraction p q K (dobrushin K) (TV_row_le_dobrushin K)

/-- The full real total-variation epsilon-stability separation theorem. -/
theorem contractive_separation {α : Type*} [Fintype α] [Nonempty α]
    (K : α → Law α) (hrho : dobrushin K < 1) (p q : Law α) (ε : ℝ)
    (hp : TV p (mixture p K) ≤ ε) (hq : TV q (mixture q K) ≤ ε) :
    TV p q ≤ 2 * ε / (1 - dobrushin K) := by
  have htriangle := TV_triangle p (mixture p K) q
  have htriangle' := TV_triangle (mixture p K) (mixture q K) q
  have hcon := dobrushin_contraction K p q
  rw [TV_symm (mixture q K) q] at htriangle'
  apply (le_div_iff₀ (sub_pos.mpr hrho)).mpr
  nlinarith

theorem contractive_stationary_unique {α : Type*} [Fintype α] [Nonempty α]
    (K : α → Law α) (hrho : dobrushin K < 1) (p q : Law α)
    (hp : mixture p K = p) (hq : mixture q K = q) : p = q := by
  have h := contractive_separation K hrho p q 0 (by rw [hp, TV_self])
    (by rw [hq, TV_self])
  simp only [mul_zero, zero_div] at h
  exact (TV_eq_zero_iff p q).mp (le_antisymm h (TV_nonneg p q))

end SixBirdsNoGo.RealProbability
