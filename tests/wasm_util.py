import io
from typing import TextIO
from wasmtime import Store, Module, Instance, Func, FuncType, ValType


def make_writer_func(output: TextIO):
    def write_i32(value: int):
        output.write(f"{value}\n")

    return write_i32


def make_reader_func(input: TextIO):
    def read_i32() -> int:
        line = input.readline()
        return int(line.strip())

    return read_i32


def run_wasm(code: str) -> int:
    store = Store()
    module = Module(store.engine, code)
    instance = Instance(store, module, [])
    main_func = instance.exports(store)["main"]
    assert isinstance(main_func, Func)
    result = main_func(store)
    return result


def run_wasm_with_io(
    code: str, instream: TextIO | None = None, outstream: TextIO | None = None
) -> int:
    store = Store()
    module = Module(store.engine, code)

    if instream is None:
        instream = io.StringIO()
    read_i32_func = Func(
        store, FuncType([], [ValType.i32()]), make_reader_func(instream)
    )

    if outstream is None:
        outstream = io.StringIO()
    write_i32_func = Func(
        store, FuncType([ValType.i32()], []), make_writer_func(outstream)
    )

    instance = Instance(store, module, [read_i32_func, write_i32_func])
    main_func = instance.exports(store)["main"]
    assert isinstance(main_func, Func)
    return main_func(store)
