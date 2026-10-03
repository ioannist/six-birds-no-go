import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Data.EReal.Basic
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Tactic

/-! Concrete finite KL foundations. Each state occurs once in a finite sum;
the logarithm is `Real.log`, and support mismatch gives positive infinity.
No information-theoretic conclusion is an input record field. -/

namespace SixBirdsNoGo.RealProbability

open scoped BigOperators

structure Law (α : Type*) [Fintype α] where
  mass : α → ℝ
  nonneg : ∀ a, 0 ≤ mass a
  sum_one : ∑ a, mass a = 1

@[ext] theorem Law.ext {α : Type*} [Fintype α] {p q : Law α}
    (h : p.mass = q.mass) : p = q := by
  cases p; cases q; cases h; rfl

def AC {α : Type*} [Fintype α] (p q : Law α) : Prop :=
  ∀ a, q.mass a = 0 → p.mass a = 0

noncomputable def klTerm (p q : ℝ) : ℝ := p * Real.log (p / q)

noncomputable def finiteKL {α : Type*} [Fintype α] (p q : Law α) : ℝ :=
  ∑ a, klTerm (p.mass a) (q.mass a)

noncomputable def KL {α : Type*} [Fintype α] (p q : Law α) : EReal := by
  classical
  exact if AC p q then (finiteKL p q : EReal) else ⊤

@[simp] theorem klTerm_zero_left (q : ℝ) : klTerm 0 q = 0 := by
  simp [klTerm]

@[simp] theorem klTerm_self (p : ℝ) : klTerm p p = 0 := by
  by_cases hp : p = 0
  · simp [hp]
  · simp [klTerm, hp]

theorem klTerm_ge_sub {p q : ℝ} (hp : 0 ≤ p) (hq : 0 ≤ q)
    (hac : q = 0 → p = 0) : p - q ≤ klTerm p q := by
  by_cases hp0 : p = 0
  · simp [hp0, hq]
  · have hp' : 0 < p := lt_of_le_of_ne hp (Ne.symm hp0)
    have hq0 : q ≠ 0 := fun h => hp0 (hac h)
    have hq' : 0 < q := lt_of_le_of_ne hq (Ne.symm hq0)
    have hlog := Real.log_le_sub_one_of_pos (div_pos hq' hp')
    have hmul := mul_le_mul_of_nonneg_left hlog hp
    rw [Real.log_div hq0 hp0] at hmul
    dsimp [klTerm]
    rw [Real.log_div hp0 hq0]
    have hcancel : p * (q / p - 1) = q - p := by field_simp
    rw [hcancel] at hmul
    nlinarith

theorem finiteKL_nonneg {α : Type*} [Fintype α] (p q : Law α)
    (hac : AC p q) : 0 ≤ finiteKL p q := by
  have h := Finset.sum_le_sum (s := Finset.univ)
    (fun a _ => klTerm_ge_sub (p.nonneg a) (q.nonneg a) (hac a))
  simpa [finiteKL, Finset.sum_sub_distrib, p.sum_one, q.sum_one] using h

@[simp] theorem finiteKL_self {α : Type*} [Fintype α] (p : Law α) :
    finiteKL p p = 0 := by simp [finiteKL]

@[simp] theorem KL_self {α : Type*} [Fintype α] (p : Law α) : KL p p = 0 := by
  have hac : AC p p := fun _ h => h
  simp [KL, hac]

theorem KL_eq_top_of_not_AC {α : Type*} [Fintype α] (p q : Law α)
    (h : ¬ AC p q) : KL p q = ⊤ := by simp [KL, h]

theorem klTerm_gt_sub {p q : ℝ} (hp : 0 ≤ p) (hq : 0 ≤ q)
    (hac : q = 0 → p = 0) (hne : p ≠ q) : p - q < klTerm p q := by
  by_cases hp0 : p = 0
  · have hq' : 0 < q := lt_of_le_of_ne hq (by simpa [hp0] using hne)
    simp [hp0, hq']
  · have hp' : 0 < p := lt_of_le_of_ne hp (Ne.symm hp0)
    have hq0 : q ≠ 0 := fun h => hp0 (hac h)
    have hq' : 0 < q := lt_of_le_of_ne hq (Ne.symm hq0)
    have hratio : q / p ≠ 1 := by
      intro h
      have hqp : q = p := (div_eq_one_iff_eq hp0).mp h
      exact hne hqp.symm
    have hlog := Real.log_lt_sub_one_of_pos (div_pos hq' hp') hratio
    have hmul := mul_lt_mul_of_pos_left hlog hp'
    rw [Real.log_div hq0 hp0] at hmul
    dsimp [klTerm]
    rw [Real.log_div hp0 hq0]
    have hcancel : p * (q / p - 1) = q - p := by field_simp
    rw [hcancel] at hmul
    nlinarith

theorem finiteKL_eq_zero_iff {α : Type*} [Fintype α] (p q : Law α)
    (hac : AC p q) : finiteKL p q = 0 ↔ p.mass = q.mass := by
  classical
  constructor
  · intro hzero
    have hsum : (∑ a, (klTerm (p.mass a) (q.mass a) - (p.mass a - q.mass a))) = 0 := by
      simpa [Finset.sum_sub_distrib, finiteKL, p.sum_one, q.sum_one] using hzero
    have heach := (Finset.sum_eq_zero_iff_of_nonneg
      (fun a _ => sub_nonneg.mpr (klTerm_ge_sub (p.nonneg a) (q.nonneg a) (hac a)))).mp hsum
    funext a
    by_contra hne
    have hstrict := klTerm_gt_sub (p.nonneg a) (q.nonneg a) (hac a) hne
    have hz := heach a (Finset.mem_univ a)
    linarith
  · intro h
    unfold finiteKL
    rw [h]
    simp

theorem KL_nonneg {α : Type*} [Fintype α] (p q : Law α) : 0 ≤ KL p q := by
  classical
  by_cases hac : AC p q
  · simp only [KL, hac, if_true]
    exact_mod_cast finiteKL_nonneg p q hac
  · simp [KL, hac]

theorem klTerm_normalize {p q P Q : ℝ}
    (hP : 0 < P) (hQ : 0 < Q)
    (hac : q = 0 → p = 0) :
    klTerm p q = p * Real.log (P / Q) + P * klTerm (p / P) (q / Q) := by
  by_cases hp0 : p = 0
  · simp [hp0, klTerm]
  · have hq0 : q ≠ 0 := fun h => hp0 (hac h)
    simp only [klTerm, Real.log_div hp0 hq0,
      Real.log_div hP.ne' hQ.ne',
      Real.log_div (div_ne_zero hp0 hP.ne') (div_ne_zero hq0 hQ.ne')]
    rw [Real.log_div hp0 hP.ne', Real.log_div hq0 hQ.ne']
    field_simp
    ring

/-- The log-sum inequality derived from Gibbs' scalar inequality, including
zero entries. Only nonnegativity and support inclusion are assumed. -/
theorem logSum {α : Type*} [Fintype α] (p q : α → ℝ)
    (hp : ∀ a, 0 ≤ p a) (hq : ∀ a, 0 ≤ q a)
    (hac : ∀ a, q a = 0 → p a = 0) :
    klTerm (∑ a, p a) (∑ a, q a) ≤ ∑ a, klTerm (p a) (q a) := by
  classical
  let P := ∑ a, p a
  let Q := ∑ a, q a
  have hP : 0 ≤ P := Finset.sum_nonneg (fun a _ => hp a)
  have hQ : 0 ≤ Q := Finset.sum_nonneg (fun a _ => hq a)
  by_cases hP0 : P = 0
  · have hp0 : ∀ a, p a = 0 := by
      have h := (Finset.sum_eq_zero_iff_of_nonneg (fun a _ => hp a)).mp hP0
      exact fun a => h a (Finset.mem_univ a)
    simp [hp0]
  · have hP' : 0 < P := lt_of_le_of_ne hP (Ne.symm hP0)
    have hQ0 : Q ≠ 0 := by
      intro hzero
      have h := (Finset.sum_eq_zero_iff_of_nonneg (fun a _ => hq a)).mp hzero
      have hp0 : ∀ a, p a = 0 := fun a => hac a (h a (Finset.mem_univ a))
      exact hP0 (by simp [P, hp0])
    have hQ' : 0 < Q := lt_of_le_of_ne hQ (Ne.symm hQ0)
    let pn : Law α := ⟨fun a => p a / P,
      fun a => div_nonneg (hp a) hP, by rw [← Finset.sum_div]; exact div_self hP0⟩
    let qn : Law α := ⟨fun a => q a / Q,
      fun a => div_nonneg (hq a) hQ, by rw [← Finset.sum_div]; exact div_self hQ0⟩
    have hn : AC pn qn := by
      intro a h
      change q a / Q = 0 at h
      change p a / P = 0
      rw [hac a ((div_eq_zero_iff).mp h |>.resolve_right hQ0)]
      simp
    have hdecomp : (∑ a, klTerm (p a) (q a)) =
        klTerm P Q + P * finiteKL pn qn := by
      calc
        _ = ∑ a, (p a * Real.log (P / Q) + P * klTerm (p a / P) (q a / Q)) :=
          Finset.sum_congr rfl (fun a _ => klTerm_normalize hP' hQ' (hac a))
        _ = klTerm P Q + P * finiteKL pn qn := by
          simp [Finset.sum_add_distrib, ← Finset.sum_mul, ← Finset.mul_sum,
            klTerm, finiteKL, pn, qn, P]
    have hnonneg := mul_nonneg hP (finiteKL_nonneg pn qn hn)
    change klTerm P Q ≤ _
    rw [hdecomp]
    linarith

noncomputable def pushforward {α β : Type*} [Fintype α] [Fintype β]
    (f : α → β) (p : Law α) : Law β := by
  classical
  exact ⟨fun b => ∑ a, if f a = b then p.mass a else 0,
    fun b => Finset.sum_nonneg (fun a _ => by split_ifs <;> simp [p.nonneg]),
    by rw [Finset.sum_comm]; simpa using p.sum_one⟩

theorem pushforward_comp {α β γ : Type*} [Fintype α] [Fintype β] [Fintype γ]
    (f : α → β) (g : β → γ) (p : Law α) :
    pushforward g (pushforward f p) = pushforward (g ∘ f) p := by
  classical
  apply Law.ext
  funext c
  change (∑ b, if g b = c then (∑ a, if f a = b then p.mass a else 0) else 0) = _
  have hmove (b : β) : (if g b = c then (∑ a, if f a = b then p.mass a else 0) else 0) =
      ∑ a, if g b = c then (if f a = b then p.mass a else 0) else 0 := by
    split_ifs <;> simp
  simp_rw [hmove]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro a _
  have heq (b : β) : (if g b = c then (if f a = b then p.mass a else 0) else 0) =
      if f a = b then (if g (f a) = c then p.mass a else 0) else 0 := by
    by_cases hab : f a = b <;> simp_all
  simp_rw [heq]
  simp

theorem pushforward_involution_mass {α : Type*} [Fintype α]
    (r : α → α) (hr : ∀ a, r (r a) = a) (p : Law α) (a : α) :
    (pushforward r p).mass a = p.mass (r a) := by
  classical
  change (∑ b, if r b = a then p.mass b else 0) = _
  have heq (b : α) : r b = a ↔ b = r a := by
    constructor
    · intro h; simpa only [hr] using congrArg r h
    · intro h; rw [h, hr]
  simp_rw [heq]
  simp

theorem pushforward_AC {α β : Type*} [Fintype α] [Fintype β]
    (f : α → β) (p q : Law α) (hac : AC p q) :
    AC (pushforward f p) (pushforward f q) := by
  classical
  intro b hzero
  have hnonneg : ∀ a, 0 ≤ (if f a = b then q.mass a else 0) := by
    intro a; split_ifs <;> simp [q.nonneg]
  have h := (Finset.sum_eq_zero_iff_of_nonneg (fun a _ => hnonneg a)).mp hzero
  change (∑ a, if f a = b then p.mass a else 0) = 0
  apply Finset.sum_eq_zero
  intro a _
  by_cases ha : f a = b
  · simp only [if_pos ha]
    exact hac a (by simpa only [if_pos ha] using h a (Finset.mem_univ a))
  · simp [ha]

theorem finiteKL_pushforward_le {α β : Type*} [Fintype α] [Fintype β]
    (f : α → β) (p q : Law α) (hac : AC p q) :
    finiteKL (pushforward f p) (pushforward f q) ≤ finiteKL p q := by
  classical
  have hfiber (b : β) := logSum
    (fun a => if f a = b then p.mass a else 0)
    (fun a => if f a = b then q.mass a else 0)
    (fun a => by dsimp only; split_ifs <;> simp [p.nonneg])
    (fun a => by dsimp only; split_ifs <;> simp [q.nonneg])
    (fun a => by dsimp only; split_ifs <;> simp_all [hac a])
  have h := Finset.sum_le_sum (s := Finset.univ) (fun b _ => hfiber b)
  calc
    _ ≤ ∑ b, ∑ a, klTerm (if f a = b then p.mass a else 0)
        (if f a = b then q.mass a else 0) := h
    _ = finiteKL p q := by
      rw [Finset.sum_comm]
      unfold finiteKL
      apply Finset.sum_congr rfl
      intro a _
      have heq : ∀ b, klTerm (if f a = b then p.mass a else 0)
          (if f a = b then q.mass a else 0) =
          if f a = b then klTerm (p.mass a) (q.mass a) else 0 := by
        intro b; split_ifs <;> simp
      simp_rw [heq]
      simp

/-- Deterministic DPI for the extended-real finite KL, without a support
restriction: the non-absolutely-continuous case has infinite source KL. -/
theorem KL_pushforward_le {α β : Type*} [Fintype α] [Fintype β]
    (f : α → β) (p q : Law α) : KL (pushforward f p) (pushforward f q) ≤ KL p q := by
  classical
  by_cases hac : AC p q
  · simp only [KL, hac, pushforward_AC f p q hac, if_true]
    exact_mod_cast finiteKL_pushforward_le f p q hac
  · simp [KL, hac]

end SixBirdsNoGo.RealProbability
