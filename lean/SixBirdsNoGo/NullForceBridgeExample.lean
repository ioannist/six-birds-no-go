import SixBirdsNoGo.NullForceBridge

namespace SixBirdsNoGo

inductive NV where
  | x
  | y
  | z
  deriving Repr, DecidableEq

def nφ : NV → Int
  | .x => 2
  | .y => -1
  | .z => 4

def nℓ (u v : NV) : Int :=
  nφ v - nφ u

theorem nExact : ExactPotentialDiff nφ nℓ := by
  intro u v
  cases u <;> cases v <;> decide

def nwX : Walk NV := Walk.single NV.x
def nwXY : Walk NV := Walk.snoc nwX NV.y
def nwXYZ : Walk NV := Walk.snoc nwXY NV.z
def nwXYZX : Walk NV := Walk.snoc nwXYZ NV.x

example : edgeSum nℓ nwXYZX = 0 := by
  apply nullForce_closedWalkSum_eq_zero nφ nℓ nExact nwXYZX
  simp [nwXYZX, nwXYZ, nwXY, nwX]

end SixBirdsNoGo
