import SixBirdsNoGo.RealKLMixture
import SixBirdsNoGo.RealMarkovPaths

namespace SixBirdsNoGo.RealProbability

open scoped BigOperators
open scoped Classical

noncomputable def fiberWeight {α β : Type*} [Fintype α] [Fintype β]
    (w : Law α) (f : α → β) (y : β) : ℝ := (pushforward f w).mass y

theorem fiberWeight_nonneg {α β : Type*} [Fintype α] [Fintype β]
    (w : Law α) (f : α → β) (y : β) : 0 ≤ fiberWeight w f y :=
  (pushforward f w).nonneg y

theorem fiberWeight_pos {α β : Type*} [Fintype α] [Fintype β]
    (w : Law α) (f : α → β) (x : α) (hx : 0 < w.mass x) :
    0 < fiberWeight w f (f x) := by
  classical
  have h := Finset.single_le_sum (s := Finset.univ)
    (f := fun a => if f a = f x then w.mass a else 0)
    (fun a _ => by dsimp only; split_ifs <;> simp [w.nonneg]) (Finset.mem_univ x)
  exact hx.trans_le (by simpa [fiberWeight, pushforward] using h)

noncomputable def conditionalWeights {α β : Type*} [Fintype α] [Fintype β]
    (w : Law α) (f : α → β) (y : β) : Law α := by
  classical
  exact if h : 0 < fiberWeight w f y then
    ⟨fun a => if f a = y then w.mass a / fiberWeight w f y else 0,
      fun a => by dsimp only; split_ifs <;> simp [div_nonneg (w.nonneg a) h.le],
      by
        have heq (a : α) : (if f a = y then w.mass a / fiberWeight w f y else 0) =
            (if f a = y then w.mass a else 0) / fiberWeight w f y := by split_ifs <;> simp
        simp_rw [heq]
        rw [← Finset.sum_div]
        exact div_self h.ne'⟩
  else w

noncomputable def conditionalKernel {α β γ : Type*} [Fintype α] [Fintype β] [Fintype γ]
    (w : Law α) (f : α → β) (p : α → Law γ) (y : β) : Law γ :=
  mixture (conditionalWeights w f y) p

noncomputable def pairMass {α β γ : Type*} [Fintype α] [Fintype β] [Fintype γ]
    (w : Law α) (f : α → β) (p : α → Law γ) (y : β) (z : γ) : ℝ := by
  classical
  exact ∑ a, if f a = y then w.mass a * (p a).mass z else 0

theorem conditionalKernel_mass {α β γ : Type*} [Fintype α] [Fintype β] [Fintype γ]
    (w : Law α) (f : α → β) (p : α → Law γ) (y : β) (z : γ)
    (hy : 0 < fiberWeight w f y) :
    (conditionalKernel w f p y).mass z = pairMass w f p y z / fiberWeight w f y := by
  classical
  simp only [conditionalKernel, mixture, conditionalWeights, dif_pos hy]
  have heq (a : α) : (if f a = y then w.mass a / fiberWeight w f y else 0) * (p a).mass z =
      (if f a = y then w.mass a * (p a).mass z else 0) / fiberWeight w f y := by
    split_ifs <;> simp [div_mul_eq_mul_div]
  simp_rw [heq]
  exact (Finset.sum_div _ _ _).symm

def KernelAC {α β γ : Type*} [Fintype α] [Fintype β] [Fintype γ]
    (w : Law α) (f : α → β) (p : α → Law γ) (k : β → Law γ) : Prop :=
  ∀ a, 0 < w.mass a → AC (p a) (k (f a))

theorem conditionalKernel_AC {α β γ : Type*} [Fintype α] [Fintype β] [Fintype γ]
    (w : Law α) (f : α → β) (p : α → Law γ) : KernelAC w f p (conditionalKernel w f p) := by
  classical
  intro a ha
  have hy := fiberWeight_pos w f a ha
  have hcond : 0 < (conditionalWeights w f (f a)).mass a := by
    simp only [conditionalWeights, dif_pos hy, if_true]
    exact div_pos ha hy
  exact activeAC_mixture (conditionalWeights w f (f a)) p a hcond

noncomputable def finiteObjective {α β γ : Type*} [Fintype α] [Fintype β] [Fintype γ]
    (w : Law α) (f : α → β) (p : α → Law γ) (k : β → Law γ) : ℝ :=
  ∑ a, w.mass a * finiteKL (p a) (k (f a))

noncomputable def objective {α β γ : Type*} [Fintype α] [Fintype β] [Fintype γ]
    (w : Law α) (f : α → β) (p : α → Law γ) (k : β → Law γ) : EReal := by
  classical
  exact if KernelAC w f p k then (finiteObjective w f p k : EReal) else ⊤

/-- Independent joint-law definition of deterministic conditional mutual
information. On its only possible current macro label y=f(a), the joint
masses are P(a,y,z)=w(a)p_a(z), P(a,y)=w(a), P(y)=fiberWeight(y), and
P(y,z)=pairMass(y,z). Zero joint masses contribute zero. No minimizer or
variational objective occurs in this definition. -/
noncomputable def conditionalInfo {α β γ : Type*} [Fintype α] [Fintype β] [Fintype γ]
    (w : Law α) (f : α → β) (p : α → Law γ) : ℝ :=
  ∑ a, ∑ z, (w.mass a * (p a).mass z) *
    Real.log (((w.mass a * (p a).mass z) * fiberWeight w f (f a)) /
      (w.mass a * pairMass w f p (f a) z))

theorem conditionalInfo_eq_bestObjective {α β γ : Type*}
    [Fintype α] [Fintype β] [Fintype γ]
    (w : Law α) (f : α → β) (p : α → Law γ) :
    conditionalInfo w f p = finiteObjective w f p (conditionalKernel w f p) := by
  classical
  unfold conditionalInfo finiteObjective finiteKL
  apply Finset.sum_congr rfl
  intro a _
  rw [Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro z _
  by_cases hw : w.mass a = 0
  · simp [hw]
  · by_cases hp : (p a).mass z = 0
    · simp [hp]
    · have ha := lt_of_le_of_ne (w.nonneg a) (Ne.symm hw)
      have hy := fiberWeight_pos w f a ha
      have hr : (conditionalKernel w f p (f a)).mass z ≠ 0 := by
        intro hz
        exact hp (conditionalKernel_AC w f p a ha z hz)
      have hpair : pairMass w f p (f a) z ≠ 0 := by
        intro hz
        rw [conditionalKernel_mass w f p (f a) z hy, hz, zero_div] at hr
        exact hr rfl
      rw [klTerm, conditionalKernel_mass w f p (f a) z hy]
      have hratio : ((w.mass a * (p a).mass z) * fiberWeight w f (f a)) /
          (w.mass a * pairMass w f p (f a) z) =
          (p a).mass z / (pairMass w f p (f a) z / fiberWeight w f (f a)) := by
        field_simp
      rw [hratio]
      ring

theorem conditionalWeights_active {α β : Type*} [Fintype α] [Fintype β]
    (w : Law α) (f : α → β) (y : β) (hy : 0 < fiberWeight w f y)
    (a : α) (ha : 0 < (conditionalWeights w f y).mass a) :
    f a = y ∧ 0 < w.mass a := by
  classical
  simp only [conditionalWeights, dif_pos hy] at ha
  by_cases hfy : f a = y
  · simp only [if_pos hfy] at ha
    exact ⟨hfy, (div_pos_iff_of_pos_right hy).mp ha⟩
  · simp [hfy] at ha

theorem fiber_objective_formula {α β γ : Type*}
    [Fintype α] [Fintype β] [Fintype γ]
    (w : Law α) (f : α → β) (p : α → Law γ) (y : β) (q : Law γ) :
    fiberWeight w f y * weightedFiniteKL (conditionalWeights w f y) p q =
      ∑ a, if f a = y then w.mass a * finiteKL (p a) q else 0 := by
  classical
  by_cases hy : 0 < fiberWeight w f y
  · simp only [weightedFiniteKL, conditionalWeights, dif_pos hy]
    rw [Finset.mul_sum]
    apply Finset.sum_congr rfl
    intro a _
    split_ifs
    · field_simp
    · simp
  · have hz : fiberWeight w f y = 0 := le_antisymm (le_of_not_gt hy) (fiberWeight_nonneg w f y)
    rw [hz, zero_mul]
    have hsum : (∑ a, if f a = y then w.mass a else 0) = 0 := by
      simpa only [fiberWeight, pushforward] using hz
    have heach := (Finset.sum_eq_zero_iff_of_nonneg
      (fun a _ => show 0 ≤ (if f a = y then w.mass a else 0) by
        split_ifs <;> simp [w.nonneg])).mp hsum
    symm
    apply Finset.sum_eq_zero
    intro a _
    by_cases hfy : f a = y
    · have hw : w.mass a = 0 := by simpa only [if_pos hfy] using heach a (Finset.mem_univ a)
      simp [hfy, hw]
    · simp [hfy]

theorem finiteObjective_fibers {α β γ : Type*} [Fintype α] [Fintype β] [Fintype γ]
    (w : Law α) (f : α → β) (p : α → Law γ) (k : β → Law γ) :
    finiteObjective w f p k = ∑ y, fiberWeight w f y *
      weightedFiniteKL (conditionalWeights w f y) p (k y) := by
  classical
  simp_rw [fiber_objective_formula]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro a _
  simp

theorem finiteObjective_minimum {α β γ : Type*} [Fintype α] [Fintype β] [Fintype γ]
    (w : Law α) (f : α → β) (p : α → Law γ) (k : β → Law γ)
    (hac : KernelAC w f p k) :
    finiteObjective w f p (conditionalKernel w f p) ≤ finiteObjective w f p k := by
  classical
  rw [finiteObjective_fibers, finiteObjective_fibers]
  apply Finset.sum_le_sum
  intro y _
  by_cases hy : 0 < fiberWeight w f y
  · have hrow : ActiveAC (conditionalWeights w f y) p (k y) := by
      intro a ha
      obtain ⟨hfy, hw⟩ := conditionalWeights_active w f y hy a ha
      simpa [hfy] using hac a hw
    apply mul_le_mul_of_nonneg_left _ (fiberWeight_nonneg w f y)
    have hnonneg := finiteKL_nonneg (mixture (conditionalWeights w f y) p) (k y)
      (mixture_AC (conditionalWeights w f y) p (k y) hrow)
    rw [weightedFiniteKL_decomposition _ _ _ hrow]
    change weightedFiniteKL _ _ (mixture _ _) ≤ _
    linarith
  · have hz : fiberWeight w f y = 0 := le_antisymm (le_of_not_gt hy) (fiberWeight_nonneg w f y)
    simp [hz]

theorem closure_variational_minimum {α β γ : Type*} [Fintype α] [Fintype β] [Fintype γ]
    (w : Law α) (f : α → β) (p : α → Law γ) :
    objective w f p (conditionalKernel w f p) = (conditionalInfo w f p : EReal) ∧
      ∀ k, (conditionalInfo w f p : EReal) ≤ objective w f p k := by
  classical
  constructor
  · simp only [objective, conditionalKernel_AC, if_true, conditionalInfo_eq_bestObjective]
  · intro k
    by_cases hac : KernelAC w f p k
    · simp only [objective, hac, if_true, conditionalInfo_eq_bestObjective]
      exact_mod_cast finiteObjective_minimum w f p k hac
    · simp [objective, hac]

theorem finiteObjective_nonneg {α β γ : Type*} [Fintype α] [Fintype β] [Fintype γ]
    (w : Law α) (f : α → β) (p : α → Law γ) (k : β → Law γ)
    (hac : KernelAC w f p k) : 0 ≤ finiteObjective w f p k := by
  apply Finset.sum_nonneg
  intro a _
  by_cases ha : w.mass a = 0
  · simp [ha]
  · exact mul_nonneg (w.nonneg a)
      (finiteKL_nonneg (p a) (k (f a)) (hac a (lt_of_le_of_ne (w.nonneg a) (Ne.symm ha))))

theorem finiteObjective_eq_zero_iff {α β γ : Type*} [Fintype α] [Fintype β] [Fintype γ]
    (w : Law α) (f : α → β) (p : α → Law γ) (k : β → Law γ)
    (hac : KernelAC w f p k) :
    finiteObjective w f p k = 0 ↔ ∀ a, 0 < w.mass a → (p a).mass = (k (f a)).mass := by
  classical
  have hterm (a : α) : 0 ≤ w.mass a * finiteKL (p a) (k (f a)) := by
    by_cases ha : w.mass a = 0
    · simp [ha]
    · exact mul_nonneg (w.nonneg a)
        (finiteKL_nonneg (p a) (k (f a)) (hac a (lt_of_le_of_ne (w.nonneg a) (Ne.symm ha))))
  constructor
  · intro hzero a ha
    have hz := (Finset.sum_eq_zero_iff_of_nonneg (fun i _ => hterm i)).mp hzero
    have hkl := (mul_eq_zero.mp (hz a (Finset.mem_univ a))).resolve_left ha.ne'
    exact (finiteKL_eq_zero_iff (p a) (k (f a)) (hac a ha)).mp hkl
  · intro hsame
    apply Finset.sum_eq_zero
    intro a _
    by_cases ha : w.mass a = 0
    · simp [ha]
    · have ha' := lt_of_le_of_ne (w.nonneg a) (Ne.symm ha)
      rw [(finiteKL_eq_zero_iff (p a) (k (f a)) (hac a ha')).mpr (hsame a ha')]
      simp

theorem conditionalInfo_nonneg {α β γ : Type*} [Fintype α] [Fintype β] [Fintype γ]
    (w : Law α) (f : α → β) (p : α → Law γ) : 0 ≤ conditionalInfo w f p := by
  rw [conditionalInfo_eq_bestObjective]
  exact finiteObjective_nonneg w f p _ (conditionalKernel_AC w f p)

theorem conditionalInfo_positive_of_distinct_fiber_rows {α β γ : Type*}
    [Fintype α] [Fintype β] [Fintype γ]
    (w : Law α) (f : α → β) (p : α → Law γ) (a a' : α)
    (ha : 0 < w.mass a) (ha' : 0 < w.mass a')
    (hf : f a = f a') (hne : (p a).mass ≠ (p a').mass) : 0 < conditionalInfo w f p := by
  have hnonneg := conditionalInfo_nonneg w f p
  have hzero : conditionalInfo w f p ≠ 0 := by
    intro h
    rw [conditionalInfo_eq_bestObjective] at h
    have hall := (finiteObjective_eq_zero_iff w f p _ (conditionalKernel_AC w f p)).mp h
    have hsame := (hall a ha).trans (by simpa [hf] using (hall a' ha').symm)
    exact hne hsame
  exact lt_of_le_of_ne hnonneg (Ne.symm hzero)

noncomputable def diracLaw {α : Type*} [Fintype α] (x : α) : Law α := by
  classical
  exact ⟨fun a => if a = x then 1 else 0,
    fun a => by dsimp only; split_ifs <;> norm_num, by simp⟩

noncomputable def futureLaw {n m : Nat} (f : Fin n → Fin m) (K : Kernel n)
    (tau : Nat) (x : Fin n) : Law (Fin m) :=
  pushforward (fun s => f (lastState s)) (markovPathLaw (diracLaw x) K tau)

/-- The closure theorem at any finite lag and arbitrary current micro law.
The candidate domain is exactly stochastic macro kernels. The information
quantity is independently defined from the joint law, and its positivity is
derived from two distinct positive-mass future rows in the same fiber. -/
theorem closureTheorem {n m : Nat} (w : Law (Fin n)) (f : Fin n → Fin m)
    (K : Kernel n) (tau : Nat) :
    (objective w f (futureLaw f K tau) (conditionalKernel w f (futureLaw f K tau)) =
      (conditionalInfo w f (futureLaw f K tau) : EReal)) ∧
    (∀ k, (conditionalInfo w f (futureLaw f K tau) : EReal) ≤ objective w f (futureLaw f K tau) k) ∧
    (∀ x x', 0 < w.mass x → 0 < w.mass x' → f x = f x' →
      (futureLaw f K tau x).mass ≠ (futureLaw f K tau x').mass →
      0 < conditionalInfo w f (futureLaw f K tau)) := by
  have hmin := closure_variational_minimum w f (futureLaw f K tau)
  exact ⟨hmin.1, hmin.2, fun x x' hx hx' hf hne =>
    conditionalInfo_positive_of_distinct_fiber_rows w f (futureLaw f K tau) x x' hx hx' hf hne⟩

end SixBirdsNoGo.RealProbability
