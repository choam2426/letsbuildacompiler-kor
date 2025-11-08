This document describes how the orignal
[Let's Build a Compiler](https://compilers.iecc.com/crenshaw/) tutorial is
translated to our Python-based compiler that emits WASM text. The best way to
follow along is, starting with Part 1:

1. Read Part N in the original tutorial.
2. Read the Part N section in this document.
3. Review the code in `partN_<name>.py` and the corresponding tests in the
   `tests` directory.

## Part 1: Introduction

This is a translation of the "Cradle", and the basic structure of our compiler.
Rather than using global variables, we define the `Compiler` class. Its
constructor takes the input source code and a stream to which assembly code will
be emitted. It does the work of the `Init` function in the original tutorial
by "priming" the parser (calling `get_char`).

Otherwise, small differences due to the built-in capabilities of Python:

* We don't need to implement the `IsAlpha` or `IsDigit` functions, since these
  exist as the `isalpha` and `isdigit` methods on `str`.
* We don't need two separate functions for `Error` and `Abort`, since we raise
  a Python exception in `abort`.

## Part 2: Expression Parsing

This is the first actual compiler for very simple arithmetic expressions made
up from single-digit numbers. Our code matches the final version of the tutorial
code that uses the stack for nested computations.

Using the stack is very natural for WASM, because it's a stack-based machine.
Each compiler method (such as `expression`, `subttract`, `term` and so on)
leaves its result as a single 32-bit integer on TOS (top of stack). For example,
the expression `2+3*4` will compile down to:

```
  i32.const 2
  i32.const 3
  i32.const 4
  i32.mul
  i32.add
```

The tests for this part (in `tests/test_02_expression_parsing.py`) include a
full testing harness that constructs a WASM module with a single "main"
function, emits the compiled expression into it, and uses `wasm-tools` and
`wasmtime` to execute it and report the result, which can then be compared
to an expected value.

## Part 3: More Expressions

This part extends the compiler to properly handle whitespace and support
multi-digit numbers and multi-character variable names. The compiler it
constructs is somewhat incomplete, however, since it only hanldes a single
assignment statement which has no side effects. It also supports function
calls (with no arguments), but these are emitted without linkage to any actual
function. All of this is left for later.

Our translation is very faithful to the original tutorial's Pascal code, using
WASM constructs. Specifically, for the assignment `foo = 42`, we emit:

```
  (local $FOO i32)
  i32.const 42
  local.set $FOO
```

For a function call such as `foo()`, we emit:

```
  call $foo
```

But no such function is defined anywhere. Therefore, the tests for this part
don't actually execute anything but just do some sanity checking on the
text of the emitted WASM. We expect that future parts - building on top of
the base implemented here - will be more amenable to automatic execution
testing.

## Part 4: Interpreters

This part is a slight detour into interpretation, showing how (little) the
structure of the parser changes if it has to evaluate expressions on the fly
rather than emitting code for them. To align with this goal, the main class
in this part is called `Interpreter` rather than `Compiler`.

To support the input (?) and output (!) operations, `Interpreter` takes
an input and output stream as parameters (these are the executed program's
"stdin" and "stdout"). As opposed to the `Compiler`, we don't emit code to
the output stream; rather, the only output sent there is from the ! operation.

Otherwise, the structure of our interpreter follows the original tutorial very
closely, as usual. There are some slight improvements, like a more general
variable table (working for arbitrary variable names, not just single
characters). There are also some bug fixes; the original tutorial neglects to
properly implement nesting of recursive-descent calls. For example, in `Term` it
starts by obtaining the value with `GetNum` rather than with `Factor`. This
means nested expressions (with parentheses) won't be supported. Our
`Interpreter` fixes this and similar issues.

## Part 5: Control Constructs

This part is another detour, into parsing / emitting code for control
structures. The parser is back to accepting single-character tokens, and
therefore the front-end is only useful for experimentation. Here's some
sample input:

```
wixbyeze
```

This means:

```
while <condition>
  if <condition>
    x
    break
    y
  else
    z
  end
end
```

There is a lot this part leaves out, such as actually parsing / emitting
conditions, expressions and so on. It focuses on how to properly emit loops
of many different kinds.

Our code follows this closely, translated to WASM looping constructs. The basic
WASM loop structure is:

```
loop $looplabel
  block $breaklooplabel
    # branching to $breaklooplabel exits the loop
    # branching to $looplabel continues to the next iteration    
  end
end
```

Whereas for `IF...THEN...ELSE` the situation is even simpler, since WASM
supports blocks like:

```
if
  # code
else
  # code
end
```

This lets us implement all the different conditional and loop constructs, as
well as BREAK statements.

Another tricky issue this part demonstrates is local variable management.
WASM doesn't permit pushing values to the stack outside a block and accessing
them inside the block. Therefore, for each loop that needs it (like DO and FOR)
we generate a local to hold the loop variable. For FOR we also generate another
local that's used for the loop limit.

The original tutorial also has several bugs (like forgetting to emit certain
expressions and matching TO in FOR loops). I'm fairly certain Jack Crenshaw
didn't run the code emitted in this part; rather it's preparation for future
parts. I expect the code here will be thoroughly tested later; for now, we only
have textual emission tests for sanity checking.

## Part 6: Boolean Expressions

This part adds boolean expressions (such as '>' comparisons) and integrates
them into the overall expression parsing structure. The BNF for expressions
is copied to our Python implementation (the final BNF, which goes through
a couple of iterations in the original tutorial), and the code is integrated
into the compiler.

This part also unifies expression parsing with the control constructs
introduced in part 5. All tokens are still limited to a single character,
but we can now write code that's somewhat reminiscent of real programming:

```
Y = 3
X = 0
w Y > 3
  X = X + 2
  Y = Y - 1
e
```

For this part, it was important for me to get back to full execution testing
(using `wasm-tools` and `wasmtime`, like in part 2), since the emitted code
is becoming increasingly complex and full testing is essential to ensure that
we're emitting valid code that works.

To this end, I had to add some provisions to the test harness; specifically,
it declares a few local variables for every program:

```
(local $X i32)
(local $Y i32)
(local $Z i32)
(local $loopvar1 i32)
(local $looplimit1 i32)
```

`$loopvar1` and `$looplimit1` are used for a single emitted FOR loop. `X`,
`Y` and `Z` are some variable names for the input code to use. I had to hack
this together in the test harness becase the language our tutorial is handling
doesn't have any notion of variable declarations yet, and WASM requires us to
pre-declare locals at the top of the function. I expect this won't be necessary
in future parts of the tutorial, once variable declarations and procedures are
covered.

Finally, there are some bugs in the original tutorial our code works aroud;
for example, the `Factor` procedure in the tutorial should invoke
`BoolExpression` after `Match('(')`, not `Expression` (the BNF presented by the
tutorial is actually coorect, but the code isn't).

Also, in the original tutorial `TO` is not matched in the FOR loop (probably
because it's not single-character), so we omit it too.

Finally, the original tutorial defines `Fin` to separate "statements"
with newlines. We do this slightly differently, by calling `skip_white` after
every call to `get_char`; in effect, any whitespace can separate our statements.
