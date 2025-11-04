import os
from pathlib import Path
import re
import subprocess
import tempfile


def run_wasm(instrs: str) -> int:
    """Compile and run the given WebAssembly text instructions.

    The instructions should form the body of a function that returns an i32.
    Returns the integer result of running the function.

    If the DUMP_WAT environment variable is set, the generated WAT file
    will be kept in the system temp directory for inspection.
    """
    with tempfile.TemporaryDirectory() as tempdir:
        wat_path = os.path.join(tempdir, "test.wat")
        wasm_path = os.path.join(tempdir, "test.wasm")

        with open(wat_path, "w") as f:
            f.write("(module\n\n")
            f.write(r"""  (func (export "main") (result i32)""" + "\n")
            f.write(instrs)
            f.write("  )\n")
            f.write(")\n")

        # If the env var DUMP_WAT is set, keep the WAT file around.
        if os.getenv("DUMP_WAT"):
            import inspect

            # Find invoking test name from call stack
            frame_info = inspect.stack()
            test_name = None
            for frame in frame_info:
                if frame.function.startswith("test_"):
                    test_name = frame.function
                    break

            if test_name is None:
                test_name = "unknown_test"

            dump_path = os.path.join(tempfile.gettempdir(), f"{test_name}_dump.wat")
            with open(dump_path, "w") as f:
                print("Dumping WAT to", dump_path)
                f.write(Path(wat_path).read_text())

        # Use wasm-tools to produce a wasm binary from the WAT
        try:
            subprocess.run(
                ["wasm-tools", "parse", wat_path, "-o", wasm_path],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"wasm-tools failed: stdout={repr(e.stdout)} stderr={repr(e.stderr)}"
            )

        # Run the wasm with wasmtime and capture its stdout
        try:
            proc = subprocess.run(
                ["wasmtime", "-Wgc", "--invoke", "main", wasm_path],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"wasmtime failed: stdout={repr(e.stdout)} stderr={repr(e.stderr)}"
            )

        output = proc.stdout.strip()
        # Parse an integer from the program output and return it
        m = re.search(r"-?\d+", output or "")
        if not m:
            raise RuntimeError(f"No integer output from wasmtime: {repr(output)}")
        return int(m.group(0))
