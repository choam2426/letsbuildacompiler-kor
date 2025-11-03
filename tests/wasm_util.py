import os
import re
import subprocess
import tempfile


def run_wasm(testname: str, instrs: str) -> int:
    with tempfile.TemporaryDirectory() as tempdir:
        wat_path = os.path.join(tempdir, f"{testname}.wat")
        wasm_path = os.path.join(tempdir, f"{testname}.wasm")

        with open(wat_path, "w") as f:
            f.write("(module\n\n")
            f.write(r"""  (func (export "main") (result i32)""" + "\n")
            f.write(instrs)
            f.write("  )\n")
            f.write(")\n")

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
