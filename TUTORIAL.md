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
function, emits the compiled expression into it, and uses the `wasmtime-py`
bindings to execute it and report the result, which can then be compared
to an expected value.

## Part 3: More Expressions

This part extends the compiler to properly handle whitespace and support
multi-digit numbers and multi-character variable names. The compiler it
constructs is somewhat incomplete, however, since it only handles a single
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
(using `wasmtime-py`, like in part 2), since the emitted code
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
this together in the test harness because the language our tutorial is handling
doesn't have any notion of variable declarations yet, and WASM requires us to
pre-declare locals at the top of the function. I expect this won't be necessary
in future parts of the tutorial, once variable declarations and procedures are
covered.

Finally, there are some bugs in the original tutorial our code works around;
for example, the `Factor` procedure in the tutorial should invoke
`BoolExpression` after `Match('(')`, not `Expression` (the BNF presented by the
tutorial is actually correct, but the code isn't).

Also, in the original tutorial `TO` is not matched in the FOR loop (probably
because it's not single-character), so we omit it too.

Finally, the original tutorial defines `Fin` to separate "statements"
with newlines. We do this slightly differently, by calling `skip_white` after
every call to `get_char`; in effect, any whitespace can separate our statements.

## Part 7: Lexical Scanning

This part of the original tutorial went back and forth about representing
tokens, and the final code is using single characters. I oped for the more
traditional enum-based approach (also described in the original tutorial). IMHO
single character token kinds aren't particularly readable (especially if they
are duplicated -- in the original tutorial 'e' represents both END and ENDIF).

Also, Pascal's lack of built-in hash tables makes for a fairly convoluted
and inefficient lookup of keywords -- the `Lookup` function performs a linear
scan every time it's invoked.

In our Python implementation, tokens are represented as:

```python
@dataclass
class Token:
    kind: TokenKind
    value: str

class TokenKind(Enum):
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    # ... more kinds
```

There's a single method to scan the next token - `advance_scanner`; it also
takes care of skipping all whitespace between tokens. And just like in the
original tutorial, the parsing code doesn't change much, except:

* Using `advance_scanner` instead of `get_char`
* Matching on `self.token.kind` instead of `self.look` to figure out what
  kind of token the parser is looking at

Another design decision in our code is representing keywords as just `NAME`
tokens, without dedicated tokens for each one. While this makes matching them
very slightly more verbose, it also enables using them in places where keywords
are not expected (such as variables), similarly to the original tutorial.

The code in the original tutorial has a number of issues we were careful not
to replicate:

* `DoIf` doesn't consume the IF token ('i') and calls `Block`, which will
  just see the same token and invoke `DoIf` again - this will probably get into
  an infinite recursion. Our `do_if` calls `self.advance_scanner` right at
  the start to consume the IF token.
* `GetNum` uses '#' for "number", but this isn't used anywhere; moreover, it
  conflicts with the "not equal" operator which is also '#'. In our code,
  numbers are represented by the `NUMBER` token kind (see `advance_scanner`
  for how they're scanned).

Our code for this part implements the entire language covered so far except a
few of the loop kinds (to avoid too much code); IF statements, assignments, all
expressions (boolean and arithmetic) and REPEAT...UNTIL loops are supported.
Adding support for additional loop kinds should be trivial - copy the
appropriate `do_...` method from Part 6 and adjust it to be token-based instead
of character-based.

## Part 8: A Little Philosophy

No code in this part of the original tutorial.

## Part 9: A Top View

This part demonstartes how to approach building a compiler for an entire
language using the same approach taken in previous parts. It's back to
single-character tokens, and mostly creates scaffolding functions that call each
other in the proper nesting structure.

Our version implements the simplified Pascal parsing as described; it doesn't
actually *do* anything, but it's a good exercise to show how recursive-descent
parsers are planned from top-down.

It does address one important topic neglected in previous parts: creating
a complete output structure with a prolog and epilog. In our case, these
are simply the WASM module block:

```python
def prolog(self, name: str):
    self.emit_ln(f"; Module {name}")
    self.emit_ln("(module")

def epilog(self):
    self.emit_ln(")")
```

Previously, we had to do this in the test harness because there was no natural
place in the parser (which was focusing on small snippets of code, like
individual expressions or sequences of statements). In this part, we finally get
to see a top-level `prog` method responsible for compiling the entire program,
so it's a natural place to include the prolog + epilog calls.

## Part 10: Introducing "Tiny"

This part combines all the learnings from the previous parts to create a
small language named TINY. It starts with a single-char version and proceeds
to incorporate the lexical scanner from part 7 to support multi-char tokens.
That said, it still sticks to single-character keywords (like `i` for IF,
`w` for WHILE and so on).

In our code, you can find the single-char version in the commit history; the
final code includes the lexical scanner and supports multi-character operators
and variable names.

TINY is a more complete environment than previous attempts, so we can finally
tie together how variables are declared and used. Variable declarations
(names following `v`) in TINY are translated to `$global` declarations in
WASM, and all variables are mapped to globals. Generally, this is the scaffold
of the WASM module we emit:

```
(module
  (func $read_i32 (import "" "read_i32") (result i32))
  (func $write_i32 (import "" "write_i32") (param i32))
  (global $X (mut i32) (i32.const 8))
  ;; ... more globals
  (func $main (export "main") (result i32)
    ;; ... code
    global.get $X  ;; implicit return of $X, for testing
  )
)
```

Reference to variables like `y` in the TINY code are translated to global
fetches (`global.get $Y`) or assignments (`global.set $Y`).

TINY also supports IO: reading variable values from stdin and writing them
to stdout. WASM is designed for embedding in a host environment, so we handle
these by importing the special `read_i32` and `write_i32` functions, which
are then provided by the testing harness. Thus only the host Python code
has to deal with IO (alternatively we could use WASI to do IO directly from
the WASM, but this would result in much more code and would be less flexible).

Our code uses `read` and `write` for the IO functions, rather than `R` and `W`,
so code looks like:

```
  p
      v x,y,z
  b
      read(x, y)
      z = x + y
      write(z, x * 2, y * 3)
  e.
```

## Part 11: Lexical Scan Revisited

In this part the author fixes the lexical scanner of TINY to overcome several
limitations.

The choices we made for Part 7 pay off really well now, because our scanner
is already structured in the right way and doesn't require any changes.
Our `advance_scanner` method is exactly `Next` in the original tutorial - it
similarly skips whitespace first, doesn't give newlines a special treatment,
etc.

Now parsing methods look the same as well, e.g.:

```python
def add(self):
    self.advance_scanner()
    self.term()
    self.emit_ln("i32.add")
```

Even methods like `block` are more aligned now: since our scanner already
places a complete `Token` in `self.token`, `block` doesn't have to consume
anything before identifying the kind of statement.

So there's no code required for this part: the original tutorial made some
slight modifications like getting rid of the `PROGRAM` keyword (or rather `p`),
but that doesn't really justify copying over the 500-line compiler from our
part 10.

## Part 12: Miscellany

This part discusses some options for implementing semicolons and comments, and
settles on the following decisions:

1. Semicolons are TERMINATORS, not separators
2. Semicolons are OPTIONAL
3. Comments are delimited by curly braces
4. Comments MAY be nested

Our implementation for this part follows these, with the expected slight adjustments
for our scanner structure. Since semicolons are optional anyway, we allow them
at the end of *each* statement in a block; this is much simpler to implement.
Having split `statement` into a separate method as in the original tutorial, our
`block` is just:

```python
def block(self, breakloop_label: str = ""):
    while self.token.kind != TokenKind.EOF:
        if self.statement(breakloop_label):
            break
        self.semi()
```

And `statement` doesn't have to deal with semicolons at all. Since `statement`
now is a separate method, it returns `True` when it encounters an ending keyword
(`E` or `L`), so that `block` knows to exit.

Comments are implemented exactly like in the original tutorial, in
`skip_white` (no other methods need changes). It can be educational to diff
`part10_introducing_tiny.py` and `part12_miscellany.py` to see exactly what
changes are required.

## Part 13: Procedures

This part is a significant jump in functionality and complexity, as it adds
procedures with by-value and by-reference parameters. What we have now is
resembling a real programming language:

```
procedure divmod(dividend, divisor, ref quotient, ref remainder)
    quotient = dividend / divisor
    remainder = dividend - (quotient * divisor)
end
```

(we support multi-character tokens)

The original tutorial goes back and forth between passing parameters to value
and reference; I've decided to support both, for maximal flexibility. A `ref`
prefix token in the parameter declaration implies a by-ref parameter, otherwise
it's by-value.

For by-ref parameters to work, we employ the WASM linear stack similarly to
the way it's used in the [WASM Basic C
ABI](https://eli.thegreenplace.net/2025/notes-on-the-wasm-basic-c-abi/). The
variable is copied to linear memory, and its address is passed to the function.
When the function accesses such variables, it uses `i32.load` and `i32.store`
instructions to interact with memory.

Here's the WASM emitted for the `divmod` procedure as shown above:

```
(func $DIVMOD (param $DIVIDEND i32) (param $DIVISOR i32) (param $QUOTIENT i32) (param $REMAINDER i32)
  local.get $QUOTIENT
  local.get $DIVIDEND
  local.get $DIVISOR
  i32.div_s
  i32.store
  local.get $REMAINDER
  local.get $DIVIDEND
  local.get $QUOTIENT
  i32.load
  local.get $DIVISOR
  i32.mul
  i32.sub
  i32.store
)
```

Our compiler now has a symbol table to distinguish local variables from globals
and from procedures, and also mark local variables as by-ref or by-value. Local
variables are supported, just like in the original tutorial. The symbol table
has a parent link, so it also supports shadowing of globals by locals, as is
usual in languages like C. Later on when the original tutorial describes types,
our symbol table is natural to extend with type information for variables. We
can also easily support lexical scopes using this infrastructure.

Note that this also means we require procedures to be defined before their
use (because the call sites needs to know about the procedure's parameters,
their number and whether they are by-ref). This is a common limitation in
programming languages, and it can be later mitigated by either using multiple
compiler passes or having forward declarations.

Our compiler still follows the "syntax directed translation" approach of the
original tutorial: the parser emits code as it goes. At this level of
complexity, however, I'm starting to feel it would be better to separate the
compiler into distinct phases. At the very least, the parser would produce
and AST, and then a distinct step would take the AST and emit code from it.

As things stand now, it's difficult to emit tight code because we don't know
what's ahead - and we can't just peek without emitting code or doing some sort
of backpatching. For example, when we emit arguments for calls, we have to make
space for each ref argument on the stack separately. It's difficult to count
arguments ahead of time and emit a single stack size increase because parsing
arguments also emits the code for them.

This is an interesting lesson in compiler construction; syntax directed
translation is a great way to get started because it's easy to see results very
quickly for a simple language. However, as the complexity of the input language
grows, this method becomes a hindrance and it's worth switching to a more
advanced, layered compiler architecture.

## Part 14: Types

TODO: ...

To simplify type handling, use LONG and QUAD types

Once again, the original tutorial states:

  As I did in the last segment, I will NOT incorporate
  these  features directly into the TINY  compiler  at  this  time.
  Instead, I'll be using the same approach that has worked  so well
  for  us  in the past: using only  fragments  of  the  parser  and
  single-character  tokens.

However, we *will* be incorporating the feature into our compiler, as before,
and will emerge with a type-capable version of the language from part 13
(including procedure definitions and calls).

