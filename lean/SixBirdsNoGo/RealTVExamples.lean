import SixBirdsNoGo.RealTVContraction
import SixBirdsNoGo.RealProbabilityExamples

namespace SixBirdsNoGo.RealProbability

theorem fairKernel_coefficient_zero : dobrushin independentFairKernel = 0 := by
  simp [dobrushin, independentFairKernel, TV_self]

theorem concrete_real_separation (p q : Law (Fin 2)) (ε : ℝ)
    (hp : TV p (mixture p independentFairKernel) ≤ ε)
    (hq : TV q (mixture q independentFairKernel) ≤ ε) : TV p q ≤ 2 * ε := by
  have h := contractive_separation independentFairKernel
    (by rw [fairKernel_coefficient_zero]; norm_num) p q ε hp hq
  simpa [fairKernel_coefficient_zero] using h

theorem TV_bitZero_fairBit : TV bitZero fairBit = 1 / 2 := by
  norm_num [TV, bitZero, fairBit, Fin.sum_univ_succ]

end SixBirdsNoGo.RealProbability
