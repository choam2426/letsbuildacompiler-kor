# letsbuildacompiler

English | [한국어](./README.ko.md)

This repository closely follows the venerable ["Let's Build a Compiler" tutorial
by Jack Crenshaw](https://compilers.iecc.com/crenshaw/).

Each _part_ of the original tutorial is mapped to a `partNN_xxx.py` file in this
repository, implementing a compiler for the same language. Please follow
[TUTORIAL.md](./TUTORIAL.md) for the details.

Each Python file
is self-contained and dependency free. The only dependency used in this repository
is the [wasmtime bindings](https://pypi.org/project/wasmtime/) for testing.

The compilers in this repository differ from the original tutorial in two major
respects:

1. They're implemented in Python instead of Turbo Pascal
2. They emit WASM instead of Motorola 68000 assembly

## Testing

Each compiler part has a corresponding `test_NN_xxx.py` test file in the `tests`
directory. If you're wondering how to use the compilers in standalone mode, let
the tests guide you. Specifically, note the `compile_and_run` method in tests.
If you pass it `show=True`, it will also dump the generated WASM text to stdout
for examination.

Starting at some point, the tests actually execute the
emitted WASM and verify the results - so this is a full compiler from the input
language (a variation of KISS or TINY depending on the part in the original
tutorial) to execution.

## Developing

`uv` is used to set up a projects and invoke tools like `ty` and `ruff`.

See the accompanying `Makefile` for the commands needed. To run a single
test file, use something like:

```
uv run python -m unittest discover -s tests -p "test_14*"
```

## Debugging helper

`tryloader.html` - helper HTML container for debugging generated WASM (using the
debugger built into Chrome dev tools). For a given WAT file with a `main`
function, first translate it to binary WASM:

```
$ wasm-tools parse try.wat -o try.wasm
```

And then follow the instructions inside `tryloader.html` to serve/load it.
