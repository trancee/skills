import Verified

def main (args : List String) : IO UInt32 := do
  match args with
  | [input] =>
    match SkillDemo.parseCount input with
    | .ok n =>
      IO.println s!"count={n}"
      return 0
    | .error message =>
      (← IO.getStderr).putStrLn message
      return 1
  | _ =>
    (← IO.getStderr).putStrLn "usage: verifieddemo <natural-number>"
    return 2
