namespace SixBirdsNoGo

def massSum {α : Type} : List (α × Rat) → Rat
  | [] => 0
  | (_, q) :: xs => q + massSum xs

@[simp] theorem massSum_nil {α : Type} : massSum ([] : List (α × Rat)) = 0 := rfl
@[simp] theorem massSum_cons {α : Type} (x : α) (q : Rat) (xs : List (α × Rat)) :
    massSum ((x, q) :: xs) = q + massSum xs := rfl

theorem massSum_append {α : Type} (xs ys : List (α × Rat)) :
    massSum (xs ++ ys) = massSum xs + massSum ys := by
  induction xs with
  | nil =>
      exact (Rat.zero_add _).symm
  | cons x xs ih =>
      cases x
      simp [massSum, ih, Rat.add_assoc]

theorem massSum_map_preserved {α β : Type} (f : α → β) (xs : List (α × Rat)) :
    massSum (xs.map (fun e => (f e.1, e.2))) = massSum xs := by
  induction xs with
  | nil =>
      simp [massSum]
  | cons x xs ih =>
      cases x
      simp [massSum, ih]

theorem massSum_scale_map {α β : Type} (c : Rat) (f : α → β) (xs : List (α × Rat)) :
    massSum (xs.map (fun e => (f e.1, c * e.2))) = c * massSum xs := by
  induction xs with
  | nil =>
      simp [massSum]
  | cons x xs ih =>
      cases x
      simp [massSum, ih, Rat.mul_add]

structure FinLaw (α : Type) where
  entries : List (α × Rat)
  nonneg : ∀ e, e ∈ entries → 0 ≤ e.2
  sum_eq_one : massSum entries = 1

theorem FinLaw.ext_entries {α : Type} {μ ν : FinLaw α} (h : μ.entries = ν.entries) : μ = ν := by
  cases μ
  cases ν
  cases h
  simp

abbrev FiniteKernel (α β : Type) := α → FinLaw β

def PathState (n : Nat) : Nat → Type
  | 0 => Fin n
  | Nat.succ h => PathState n h × Fin n

instance instDecidableEqPathState (n horizon : Nat) : DecidableEq (PathState n horizon) := by
  induction horizon with
  | zero =>
      dsimp [PathState]
      infer_instance
  | succ h ih =>
      dsimp [PathState]
      infer_instance

def lastStateAux {n : Nat} : (horizon : Nat) → PathState n horizon → Fin n
  | 0, s => s
  | Nat.succ _, s => s.2

def lastState {n horizon : Nat} (s : PathState n horizon) : Fin n :=
  lastStateAux horizon s

def stateAtAux {n : Nat} : (horizon : Nat) → PathState n horizon → Fin (horizon + 1) → Fin n
  | 0, s, _ => s
  | Nat.succ h, s, i =>
      if hEq : i.1 = h + 1 then s.2
      else stateAtAux h s.1 ⟨i.1, Nat.lt_of_le_of_ne (Nat.le_of_lt_succ i.2) hEq⟩

def stateAt {n horizon : Nat} (s : PathState n horizon) (i : Fin (horizon + 1)) : Fin n :=
  stateAtAux horizon s i

def mapPathStateAux {n m : Nat} (f : Fin n → Fin m) :
    (horizon : Nat) → PathState n horizon → PathState m horizon
  | 0, s => f s
  | Nat.succ h, s => (mapPathStateAux f h s.1, f s.2)

def mapPathState {n m horizon : Nat} (f : Fin n → Fin m) (s : PathState n horizon) : PathState m horizon :=
  mapPathStateAux f horizon s

def pointWeight [DecidableEq α] (μ : FinLaw α) (a : α) : Rat :=
  massSum (μ.entries.map (fun e => if e.1 = a then (a, e.2) else (a, 0)))

def pushforward {α β : Type} (f : α → β) (μ : FinLaw α) : FinLaw β where
  entries := μ.entries.map (fun e => (f e.1, e.2))
  nonneg := by
    intro e hmem
    rcases List.mem_map.mp hmem with ⟨x, hx, hEq⟩
    cases x with
    | mk a q =>
        cases hEq
        simpa using μ.nonneg (a, q) hx
  sum_eq_one := by
    simpa using (massSum_map_preserved f μ.entries).trans μ.sum_eq_one

def pushforwardPathLaw {n m horizon : Nat}
    (f : Fin n → Fin m) (μ : FinLaw (PathState n horizon)) :
    FinLaw (PathState m horizon) :=
  pushforward (mapPathState f) μ

def firstMarginal {α β : Type} (μ : FinLaw (α × β)) : FinLaw α :=
  pushforward Prod.fst μ

def secondMarginal {α β : Type} (μ : FinLaw (α × β)) : FinLaw β :=
  pushforward Prod.snd μ

def timeMarginal {n horizon : Nat} (μ : FinLaw (PathState n horizon)) (t : Fin (horizon + 1)) : FinLaw (Fin n) :=
  pushforward (fun s => stateAt s t) μ

def twoTimeMarginal {n horizon : Nat}
    (μ : FinLaw (PathState n horizon))
    (i j : Fin (horizon + 1)) : FinLaw (Fin n × Fin n) :=
  pushforward (fun s => (stateAt s i, stateAt s j)) μ

def extendEntry {n horizon : Nat}
    (entry : PathState n horizon × Rat)
    (K : FiniteKernel (Fin n) (Fin n)) :
    List (PathState n (Nat.succ horizon) × Rat) :=
  (K (lastState entry.1)).entries.map (fun nxt => ((entry.1, nxt.1), entry.2 * nxt.2))

def extendEntries {n horizon : Nat}
    (entries : List (PathState n horizon × Rat))
    (K : FiniteKernel (Fin n) (Fin n)) :
    List (PathState n (Nat.succ horizon) × Rat) :=
  match entries with
  | [] => []
  | e :: es => extendEntry e K ++ extendEntries es K

theorem extendEntries_nonneg {n horizon : Nat}
    (entries : List (PathState n horizon × Rat))
    (hentries : ∀ e, e ∈ entries → 0 ≤ e.2)
    (K : FiniteKernel (Fin n) (Fin n)) :
    ∀ e, e ∈ extendEntries entries K → 0 ≤ e.2 := by
  intro e hmem
  induction entries with
  | nil =>
      simp [extendEntries] at hmem
  | cons entry entries ih =>
      simp [extendEntries] at hmem
      rcases hmem with hmem | hmem
      · rcases List.mem_map.mp hmem with ⟨nxt, hnxt, hEq⟩
        cases entry with
        | mk path p =>
            cases nxt with
            | mk s q =>
                cases hEq
                exact Rat.mul_nonneg (hentries (path, p) (by simp)) ((K (lastState path)).nonneg (s, q) hnxt)
      · have htail : ∀ x, x ∈ entries → 0 ≤ x.2 := by
            intro x hx
            exact hentries x (by simp [hx])
        exact ih htail hmem

theorem massSum_extendEntry {n horizon : Nat}
    (entry : PathState n horizon × Rat)
    (K : FiniteKernel (Fin n) (Fin n)) :
    massSum (extendEntry entry K) = entry.2 * massSum (K (lastState entry.1)).entries := by
  cases entry with
  | mk path p =>
      simpa [extendEntry] using massSum_scale_map p (fun s : Fin n => (path, s)) (K (lastState path)).entries

theorem massSum_extendEntries {n horizon : Nat}
    (entries : List (PathState n horizon × Rat))
    (K : FiniteKernel (Fin n) (Fin n)) :
    massSum (extendEntries entries K) = massSum entries := by
  induction entries with
  | nil =>
      simp [extendEntries, massSum]
  | cons entry entries ih =>
      calc
        massSum (extendEntries (entry :: entries) K)
            = massSum (extendEntry entry K) + massSum (extendEntries entries K) := by
                simp [extendEntries, massSum_append]
        _ = entry.2 * massSum (K (lastState entry.1)).entries + massSum (extendEntries entries K) := by
              rw [massSum_extendEntry]
        _ = entry.2 * 1 + massSum entries := by
              rw [(K (lastState entry.1)).sum_eq_one, ih]
        _ = massSum (entry :: entries) := by
              cases entry
              simp [massSum]

def pathLawStep {n horizon : Nat}
    (μ : FinLaw (PathState n horizon))
    (K : FiniteKernel (Fin n) (Fin n)) :
    FinLaw (PathState n (Nat.succ horizon)) where
  entries := extendEntries μ.entries K
  nonneg := extendEntries_nonneg μ.entries μ.nonneg K
  sum_eq_one := by
    rw [massSum_extendEntries]
    exact μ.sum_eq_one

def pathLaw {n : Nat} (initial : FinLaw (Fin n)) (K : FiniteKernel (Fin n) (Fin n)) :
    (horizon : Nat) → FinLaw (PathState n horizon)
  | 0 => initial
  | Nat.succ h => pathLawStep (pathLaw initial K h) K

theorem pushforward_sum_eq_one {α β : Type} (f : α → β) (μ : FinLaw α) :
    massSum (pushforward f μ).entries = 1 :=
  (pushforward f μ).sum_eq_one

theorem firstMarginal_sum_eq_one {α β : Type} (μ : FinLaw (α × β)) :
    massSum (firstMarginal μ).entries = 1 :=
  (firstMarginal μ).sum_eq_one

theorem secondMarginal_sum_eq_one {α β : Type} (μ : FinLaw (α × β)) :
    massSum (secondMarginal μ).entries = 1 :=
  (secondMarginal μ).sum_eq_one

theorem timeMarginal_sum_eq_one {n horizon : Nat}
    (μ : FinLaw (PathState n horizon)) (t : Fin (horizon + 1)) :
    massSum (timeMarginal μ t).entries = 1 :=
  (timeMarginal μ t).sum_eq_one

theorem pathLaw_sum_eq_one {n : Nat}
    (initial : FinLaw (Fin n)) (K : FiniteKernel (Fin n) (Fin n)) (horizon : Nat) :
    massSum (pathLaw initial K horizon).entries = 1 :=
  (pathLaw initial K horizon).sum_eq_one

end SixBirdsNoGo
