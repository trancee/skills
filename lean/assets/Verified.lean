import Std

namespace SkillDemo

def count : List α → Nat
  | [] => 0
  | _ :: xs => count xs + 1

theorem count_append (xs ys : List α) :
    count (xs ++ ys) = count xs + count ys := by
  induction xs with
  | nil => simp only [List.nil_append, count, Nat.zero_add]
  | cons x xs ih =>
    simp only [List.cons_append, count, ih]
    omega

theorem count_nonnegative (xs : List α) : 0 ≤ count xs := by
  omega

def parseCount (text : String) : Except String Nat :=
  match text.toNat? with
  | some n => .ok n
  | none => .error "expected a natural number"

#guard count ([] : List Nat) = 0
#guard count [1, 2, 3] = 3
#guard match parseCount "0" with
  | .ok n => n == 0
  | .error _ => false
#guard match parseCount "12" with
  | .ok n => n == 12
  | .error _ => false
#guard match parseCount "nope" with
  | .ok _ => false
  | .error message => message == "expected a natural number"

end SkillDemo

#print axioms SkillDemo.count_append
