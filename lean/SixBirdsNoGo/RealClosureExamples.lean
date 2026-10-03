import SixBirdsNoGo.RealClosure

namespace SixBirdsNoGo.RealProbability

noncomputable def closureWitnessLaw : Law (Fin 3) where
  mass x := if x.val = 2 then 0 else 1 / 2
  nonneg x := by split_ifs <;> norm_num
  sum_one := by norm_num [Fin.sum_univ_succ]

def closureWitnessLens (x : Fin 3) : Fin 2 := if x.val = 2 then 1 else 0

noncomputable def closureWitnessKernel : Kernel 3 :=
  fun x => if x.val = 0 then diracLaw 0 else diracLaw 2

theorem closureWitness_future_zero :
    (futureLaw closureWitnessLens closureWitnessKernel 1 0).mass 0 = 1 := by
  dsimp [futureLaw, pushforward, markovPathLaw, pathMass, PathState]
  rw [Fintype.sum_prod_type]
  norm_num [Fin.sum_univ_succ, diracLaw, closureWitnessKernel, closureWitnessLens,
    lastState, lastStateAux, show (0 : Fin 3) ≠ 2 by decide,
    show (1 : Fin 3) ≠ 2 by decide, show (2 : Fin 3) ≠ 1 by decide]

theorem closureWitness_future_one :
    (futureLaw closureWitnessLens closureWitnessKernel 1 1).mass 0 = 0 := by
  dsimp [futureLaw, pushforward, markovPathLaw, pathMass, PathState]
  rw [Fintype.sum_prod_type]
  norm_num [Fin.sum_univ_succ, diracLaw, closureWitnessKernel, closureWitnessLens,
    lastState, lastStateAux, show (0 : Fin 3) ≠ 2 by decide,
    show (1 : Fin 3) ≠ 2 by decide, show (2 : Fin 3) ≠ 1 by decide]

theorem closureWitness_positive :
    0 < conditionalInfo closureWitnessLaw closureWitnessLens
      (futureLaw closureWitnessLens closureWitnessKernel 1) := by
  apply conditionalInfo_positive_of_distinct_fiber_rows _ _ _ 0 1
  · norm_num [closureWitnessLaw]
  · norm_num [closureWitnessLaw]
  · norm_num [closureWitnessLens]
  · intro h
    have h0 := congrFun h 0
    rw [closureWitness_future_zero, closureWitness_future_one] at h0
    norm_num at h0

end SixBirdsNoGo.RealProbability
