import io
from typing import TextIO
from wasmtime import Store, Module, Instance, Func, FuncType, ValType


def make_writer_func(output: TextIO):
    def write_i32(value: int):
        output.write(f"{value}\n")

    return write_i32


def run_wasm(code: str) -> int:
    store = Store()
    module = Module(store.engine, code)
    instance = Instance(store, module, [])
    main_func = instance.exports(store)["main"]
    result = main_func(store)
    return result


def run_wasm_with_io(code: str, output: TextIO | None = None) -> int:
    store = Store()
    module = Module(store.engine, code)
    if output is None:
        output = io.StringIO()
    write_i32_func = Func(
        store, FuncType([ValType.i32()], []), make_writer_func(output)
    )
    instance = Instance(store, module, [write_i32_func])
    main_func = instance.exports(store)["main"]
    return main_func(store)
