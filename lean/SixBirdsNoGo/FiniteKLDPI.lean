import SixBirdsNoGo.FiniteProbabilityCore

namespace SixBirdsNoGo

section Support

variable {α : Type} [DecidableEq α]

def supportList (μ : FinLaw α) : List α :=
  μ.entries.map Prod.fst

def AbsolutelyContinuous (μ ν : FinLaw α) : Prop :=
  ∀ a : α, pointWeight ν a = 0 → pointWeight μ a = 0

end Support

section PathReversal

variable {n : Nat}

def prependStateAux : (horizon : Nat) → Fin n → PathState n horizon → PathState n (Nat.succ horizon)
  | 0, x, y => (x, y)
  | Nat.succ h, x, s => (prependStateAux h x s.1, s.2)

def prependState {horizon : Nat} (x : Fin n) (s : PathState n horizon) : PathState n (Nat.succ horizon) :=
  prependStateAux horizon x s

def reversePathStateAux : (horizon : Nat) → PathState n horizon → PathState n horizon
  | 0, s => s
  | Nat.succ h, s => prependState s.2 (reversePathStateAux h s.1)

def reversePathState {horizon : Nat} (s : PathState n horizon) : PathState n horizon :=
  reversePathStateAux horizon s

def reversePathLaw {horizon : Nat} (μ : FinLaw (PathState n horizon)) : FinLaw (PathState n horizon) :=
  pushforward reversePathState μ

theorem reversePathLaw_sum_eq_one {horizon : Nat} (μ : FinLaw (PathState n horizon)) :
    massSum (reversePathLaw μ).entries = 1 :=
  (reversePathLaw μ).sum_eq_one

end PathReversal

section KL

/-- Minimal explicit scalar/log interface for finite KL and deterministic DPI only. -/
structure ScalarLogLayer where
  logTerm : Rat → Rat → Rat
  deterministic_dpi :
    ∀ {α β : Type} [DecidableEq α] [DecidableEq β],
      (f : α → β) → (μ ν : FinLaw α) → AbsolutelyContinuous μ ν →
        massSum ((supportList (pushforward f μ)).map (fun b => (b, pointWeight (pushforward f μ) b * logTerm (pointWeight (pushforward f μ) b) (pointWeight (pushforward f ν) b))))
          ≤ massSum ((supportList μ).map (fun a => (a, pointWeight μ a * logTerm (pointWeight μ a) (pointWeight ν a))))

variable {α β : Type} [DecidableEq α] [DecidableEq β]

/-- The exact finite mass on a pushforward fiber. -/
def fiberMass (f : α → β) (μ : FinLaw α) (b : β) : Rat :=
  pointWeight (pushforward f μ) b

omit [DecidableEq α] in
theorem pushforwardPointWeight_eq_fiberMass (f : α → β) (μ : FinLaw α) (b : β) :
    pointWeight (pushforward f μ) b = fiberMass f μ b := by
  rfl

/-- Finite KL over the explicit scalar/log layer. -/
def KL (S : ScalarLogLayer) (μ ν : FinLaw α) : Rat :=
  massSum ((supportList μ).map (fun a => (a, pointWeight μ a * S.logTerm (pointWeight μ a) (pointWeight ν a))))

theorem KL_pushforward_dpi (S : ScalarLogLayer) (f : α → β) (μ ν : FinLaw α)
    (hAC : AbsolutelyContinuous μ ν) :
    KL S (pushforward f μ) (pushforward f ν) ≤ KL S μ ν := by
  simpa [KL] using S.deterministic_dpi f μ ν hAC

section PathDPI

variable {n m horizon : Nat}

theorem pathLawPushforwardDPI (S : ScalarLogLayer) (f : Fin n → Fin m)
    (μ ν : FinLaw (PathState n horizon))
    (hAC : AbsolutelyContinuous μ ν) :
    KL S (pushforwardPathLaw f μ) (pushforwardPathLaw f ν) ≤ KL S μ ν := by
  simpa [pushforwardPathLaw] using KL_pushforward_dpi (α := PathState n horizon) (β := PathState m horizon) S (mapPathState f) μ ν hAC

end PathDPI

end KL

end SixBirdsNoGo
