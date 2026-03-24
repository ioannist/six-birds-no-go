import SixBirdsNoGo.ClosureDirectPack
import SixBirdsNoGo.ClosureVariationalCoreExample

namespace SixBirdsNoGo

example :
    closureDeficitValue toyClosureLayer uniformLaw idLens2 toyKernel 1 =
      variationalObjective toyClosureLayer.toScalarLogLayer uniformLaw idLens2 toyKernel 1
        (bestMacroKernel uniformLaw idLens2 toyKernel 1) :=
  closureDeficit_attainedBy_bestMacroKernel toyClosureLayer uniformLaw idLens2 toyKernel 1

example :
    closureDeficitValue toyClosureLayer uniformLaw idLens2 toyKernel 1 ≤
      variationalObjective toyClosureLayer.toScalarLogLayer uniformLaw idLens2 toyKernel 1
        (bestMacroKernel uniformLaw idLens2 toyKernel 1) := by
  exact closureDeficit_le_allKernels toyClosureLayer uniformLaw idLens2 toyKernel 1
    (bestMacroKernel uniformLaw idLens2 toyKernel 1)

example :
    (closureDeficitValue toyClosureLayer uniformLaw idLens2 toyKernel 1 =
        variationalObjective toyClosureLayer.toScalarLogLayer uniformLaw idLens2 toyKernel 1
          (bestMacroKernel uniformLaw idLens2 toyKernel 1)) ∧
      (∀ candidate : MacroKernel 2,
        closureDeficitValue toyClosureLayer uniformLaw idLens2 toyKernel 1 ≤
          variationalObjective toyClosureLayer.toScalarLogLayer uniformLaw idLens2 toyKernel 1
            candidate) :=
  closureDeficit_is_variationalMinimum toyClosureLayer uniformLaw idLens2 toyKernel 1

example
    (hpos : 0 < closureDeficitValue toyClosureLayer uniformLaw idLens2 toyKernel 1) :
    ¬ ExactClosedMacroLaw toyClosureLayer uniformLaw idLens2 toyKernel 1 :=
  positiveClosureDeficit_forbidsExactClosure toyClosureLayer uniformLaw idLens2 toyKernel 1 hpos

end SixBirdsNoGo
