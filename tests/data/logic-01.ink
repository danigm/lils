VAR opts = 0

Hello, world!
 * { opts + 1 == 1 } opt1 -> END
 * { opts == 1 } opt2 # with some tag
   -> END
 * { opts >= 2 } opt3[], with more text -> END
 * { opts > 3 || opts == 3 } [opt4] -> END
 * { opts < 6 && opts > 4 } opt5
   With content inside
   -> END
