VAR background = "Test"
VAR x = 1
VAR y = x + 2
VAR z = 2 * y - 1
VAR running = true

Hello, world!
* op1 -> op1
* op2 -> op2

=== op1 ===
~ x = x + 1
~ background = background + "-op1"
-> END

=== op2 ===
~ x = x + 2
~ y = -23
-> END
