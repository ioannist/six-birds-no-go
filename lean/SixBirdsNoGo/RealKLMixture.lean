import SixBirdsNoGo.RealFiniteKL

/-! The concrete finite KL projection identity. Null weights are omitted in
support checks; candidates and mixture rows are genuine normalized laws. -/

namespace SixBirdsNoGo.RealProbability

open scoped BigOperators

noncomputable def mixture {α β : Type*} [Fintype α] [Fintype β]
    (w : Law α) (p : α → Law β) : Law β where
  mass b := ∑ a, w.mass a * (p a).mass b
  nonneg b := Finset.sum_nonneg (fun a _ => mul_nonneg (w.nonneg a) ((p a).nonneg b))
  sum_one := by
    rw [Finset.sum_comm]
    simp_rw [← Finset.mul_sum, Law.sum_one, mul_one]
    exact w.sum_one

def ActiveAC {α β : Type*} [Fintype α] [Fintype β]
    (w : Law α) (p : α → Law β) (q : Law β) : Prop :=
  ∀ a, 0 < w.mass a → AC (p a) q

theorem activeAC_mixture {α β : Type*} [Fintype α] [Fintype β]
    (w : Law α) (p : α → Law β) : ActiveAC w p (mixture w p) := by
  intro a ha b hb
  have heach := (Finset.sum_eq_zero_iff_of_nonneg
    (fun i _ => mul_nonneg (w.nonneg i) ((p i).nonneg b))).mp hb
  exact (mul_eq_zero.mp (heach a (Finset.mem_univ a))).resolve_left ha.ne'

theorem mixture_AC {α β : Type*} [Fintype α] [Fintype β]
    (w : Law α) (p : α → Law β) (q : Law β) (hac : ActiveAC w p q) :
    AC (mixture w p) q := by
  intro b hb
  apply Finset.sum_eq_zero
  intro a _
  by_cases ha : w.mass a = 0
  · simp [ha]
  · have hpos := lt_of_le_of_ne (w.nonneg a) (Ne.symm ha)
    rw [hac a hpos b hb]
    simp

noncomputable def weightedFiniteKL {α β : Type*} [Fintype α] [Fintype β]
    (w : Law α) (p : α → Law β) (q : Law β) : ℝ :=
  ∑ a, w.mass a * finiteKL (p a) q

noncomputable def weightedKL {α β : Type*} [Fintype α] [Fintype β]
    (w : Law α) (p : α → Law β) (q : Law β) : EReal := by
  classical
  exact if ActiveAC w p q then (weightedFiniteKL w p q : EReal) else ⊤

theorem weightedFiniteKL_nonneg {α β : Type*} [Fintype α] [Fintype β]
    (w : Law α) (p : α → Law β) (q : Law β) (hac : ActiveAC w p q) :
    0 ≤ weightedFiniteKL w p q := by
  apply Finset.sum_nonneg
  intro a _
  by_cases ha : w.mass a = 0
  · simp [ha]
  · exact mul_nonneg (w.nonneg a)
      (finiteKL_nonneg (p a) q (hac a (lt_of_le_of_ne (w.nonneg a) (Ne.symm ha))))

theorem weighted_log_split {w p r q : ℝ}
    (hr : w ≠ 0 → p ≠ 0 → r ≠ 0) (hq : w ≠ 0 → p ≠ 0 → q ≠ 0) :
    w * klTerm p q = w * klTerm p r + (w * p) * Real.log (r / q) := by
  by_cases hw0 : w = 0
  · simp [hw0]
  · by_cases hp0 : p = 0
    · simp [hp0]
    · simp only [klTerm, Real.log_div hp0 (hq hw0 hp0),
        Real.log_div hp0 (hr hw0 hp0), Real.log_div (hr hw0 hp0) (hq hw0 hp0)]
      ring

/-- Weighted mixture decomposition in the finite branch. Support inclusion
is proved for the mixture; it is not assumed as an analytic bridge. -/
theorem weightedFiniteKL_decomposition {α β : Type*} [Fintype α] [Fintype β]
    (w : Law α) (p : α → Law β) (q : Law β) (hac : ActiveAC w p q) :
    weightedFiniteKL w p q = weightedFiniteKL w p (mixture w p) + finiteKL (mixture w p) q := by
  have hrow (b : β) : (∑ a, w.mass a * klTerm ((p a).mass b) (q.mass b)) =
      (∑ a, w.mass a * klTerm ((p a).mass b) ((mixture w p).mass b)) +
        klTerm ((mixture w p).mass b) (q.mass b) := by
    have hr (a : α) : w.mass a ≠ 0 → (p a).mass b ≠ 0 → (mixture w p).mass b ≠ 0 := by
      intro hw hp hzero
      exact hp (activeAC_mixture w p a (lt_of_le_of_ne (w.nonneg a) (Ne.symm hw)) b hzero)
    have hq (a : α) : w.mass a ≠ 0 → (p a).mass b ≠ 0 → q.mass b ≠ 0 := by
      intro hw hp hzero
      exact hp (hac a (lt_of_le_of_ne (w.nonneg a) (Ne.symm hw)) b hzero)
    simp_rw [weighted_log_split (hr _) (hq _)]
    rw [Finset.sum_add_distrib, ← Finset.sum_mul]
    rfl
  unfold weightedFiniteKL finiteKL
  simp_rw [Finset.mul_sum]
  rw [Finset.sum_comm]
  simp_rw [hrow, Finset.sum_add_distrib]
  rw [Finset.sum_comm]

theorem mixture_minimizes_weightedKL {α β : Type*} [Fintype α] [Fintype β]
    (w : Law α) (p : α → Law β) (q : Law β) :
    weightedKL w p (mixture w p) ≤ weightedKL w p q := by
  classical
  by_cases hac : ActiveAC w p q
  · simp only [weightedKL, hac, activeAC_mixture, if_true]
    have h := finiteKL_nonneg (mixture w p) q (mixture_AC w p q hac)
    have hle : weightedFiniteKL w p (mixture w p) ≤ weightedFiniteKL w p q := by
      rw [weightedFiniteKL_decomposition w p q hac]
      linarith
    exact_mod_cast hle
  · simp [weightedKL, hac]

theorem weightedFiniteKL_eq_zero_iff {α β : Type*} [Fintype α] [Fintype β]
    (w : Law α) (p : α → Law β) (q : Law β) (hac : ActiveAC w p q) :
    weightedFiniteKL w p q = 0 ↔ ∀ a, 0 < w.mass a → (p a).mass = q.mass := by
  classical
  have hterm (a : α) : 0 ≤ w.mass a * finiteKL (p a) q := by
    by_cases ha : w.mass a = 0
    · simp [ha]
    · exact mul_nonneg (w.nonneg a)
        (finiteKL_nonneg (p a) q (hac a (lt_of_le_of_ne (w.nonneg a) (Ne.symm ha))))
  constructor
  · intro hzero a ha
    have hz := (Finset.sum_eq_zero_iff_of_nonneg (fun i _ => hterm i)).mp hzero
    have hkl := (mul_eq_zero.mp (hz a (Finset.mem_univ a))).resolve_left ha.ne'
    exact (finiteKL_eq_zero_iff (p a) q (hac a ha)).mp hkl
  · intro hsame
    apply Finset.sum_eq_zero
    intro a _
    by_cases ha : w.mass a = 0
    · simp [ha]
    · have ha' := lt_of_le_of_ne (w.nonneg a) (Ne.symm ha)
      rw [(finiteKL_eq_zero_iff (p a) q (hac a ha')).mpr (hsame a ha')]
      simp

theorem distinct_positive_rows_force_positive_gap {α β : Type*} [Fintype α] [Fintype β]
    (w : Law α) (p : α → Law β) (a a' : α)
    (ha : 0 < w.mass a) (ha' : 0 < w.mass a') (hne : (p a).mass ≠ (p a').mass) :
    0 < weightedFiniteKL w p (mixture w p) := by
  have hnonneg := weightedFiniteKL_nonneg w p (mixture w p) (activeAC_mixture w p)
  have hzero : weightedFiniteKL w p (mixture w p) ≠ 0 := by
    intro h
    have hall := (weightedFiniteKL_eq_zero_iff w p (mixture w p) (activeAC_mixture w p)).mp h
    exact hne ((hall a ha).trans (hall a' ha').symm)
  exact lt_of_le_of_ne hnonneg (Ne.symm hzero)

end SixBirdsNoGo.RealProbability
