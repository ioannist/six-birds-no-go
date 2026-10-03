import SixBirdsNoGo.RealMarkovPaths

namespace SixBirdsNoGo.RealProbability

noncomputable def fairBit : Law (Fin 2) where
  mass _ := 1 / 2
  nonneg _ := by norm_num
  sum_one := by norm_num [Fin.sum_univ_succ]

noncomputable def bitZero : Law (Fin 2) where
  mass i := if i = 0 then 1 else 0
  nonneg i := by split_ifs <;> norm_num
  sum_one := by norm_num [Fin.sum_univ_succ]

noncomputable def bitOne : Law (Fin 2) where
  mass i := if i = 1 then 1 else 0
  nonneg i := by split_ifs <;> norm_num
  sum_one := by norm_num [Fin.sum_univ_succ]

theorem bitZero_fairBit_AC : AC bitZero fairBit := by
  intro a h
  norm_num [fairBit] at h

theorem genuine_positive_KL : 0 < finiteKL bitZero fairBit := by
  have hnonneg := finiteKL_nonneg bitZero fairBit bitZero_fairBit_AC
  have hne : finiteKL bitZero fairBit ≠ 0 := by
    intro hz
    have h := congrFun ((finiteKL_eq_zero_iff bitZero fairBit bitZero_fairBit_AC).mp hz) 0
    norm_num [bitZero, fairBit] at h
  exact lt_of_le_of_ne hnonneg (Ne.symm hne)

theorem genuine_infinite_KL : KL bitZero bitOne = ⊤ := by
  apply KL_eq_top_of_not_AC
  intro h
  have h0 := h 0 (by norm_num [bitOne])
  norm_num [bitZero] at h0

theorem fairBit_deterministic_collapse_zero (f : Fin 2 → Fin 1) :
    KL (pushforward f bitZero) (pushforward f fairBit) = 0 := by
  have heq : pushforward f bitZero = pushforward f fairBit := by
    apply Law.ext
    funext y
    have hf : ∀ x, f x = y := fun x => Subsingleton.elim _ _
    simp [pushforward, hf, Law.sum_one]
  rw [heq, KL_self]

noncomputable def independentFairKernel : Kernel 2 := fun _ => fairBit

theorem independentFairKernel_balance : DetailedBalance fairBit independentFairKernel := by
  intro x y
  rfl

theorem concrete_protocol_zero_all_horizons (f : Fin 2 → Fin 1) (h : Nat) :
    KL (observedLaw f (markovPathLaw fairBit independentFairKernel h))
      (reversedLaw (observedLaw f (markovPathLaw fairBit independentFairKernel h))) = 0 :=
  protocolTrap fairBit independentFairKernel independentFairKernel_balance f h

end SixBirdsNoGo.RealProbability
