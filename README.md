# letsbuildacompiler

`tryloader.html` - helper HTML container for debugging generated WASM. For a
given WAT file with a `main` function, first translated it to binary WASM:

```
$ wasm-tools parse try.wat -o try.wasm
```

And then follow the instructions inside `tryloader.html` to serve/load it.
