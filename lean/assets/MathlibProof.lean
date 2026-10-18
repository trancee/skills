module

import Mathlib.Tactic.Ring

public section

namespace SkillMathDemo

theorem binomialSquare (x y : Int) :
    (x + y) ^ 2 = x ^ 2 + 2 * x * y + y ^ 2 := by
  ring

end SkillMathDemo

#print axioms SkillMathDemo.binomialSquare
