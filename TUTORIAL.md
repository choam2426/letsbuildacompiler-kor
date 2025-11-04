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
