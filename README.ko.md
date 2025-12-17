# letsbuildacompiler

[English](./README.md) | 한국어

이 저장소는 Jack Crenshaw의 유서 깊은 ["Let's Build a Compiler" 튜토리얼](https://compilers.iecc.com/crenshaw/)을 매우 가깝게 따라갑니다.

원 튜토리얼의 각 *Part*는 이 저장소의 `partNN_xxx.py` 파일 하나에 대응하며, 동일한 언어를 대상으로 하는 컴파일러를 구현합니다. 자세한 내용은 [TUTORIAL.ko.md](./TUTORIAL.ko.md)를 참고하세요.

각 Python 파일은 자체 포함(self-contained)이며 의존성이 없습니다. 이 저장소에서 사용하는 유일한 의존성은 테스트를 위한 [wasmtime 바인딩](https://pypi.org/project/wasmtime/)입니다.

이 저장소의 컴파일러는 원 튜토리얼과 비교해 큰 차이가 두 가지 있습니다:

1. Turbo Pascal 대신 Python으로 구현되어 있습니다.
2. Motorola 68000 어셈블리 대신 WASM을 출력합니다.

## Testing

각 컴파일러 파트에는 `tests` 디렉터리 안에 대응하는 `test_NN_xxx.py` 테스트 파일이 있습니다. 컴파일러를 단독 모드로 어떻게 사용하는지 궁금하다면, 테스트 코드를 참고하세요. 특히 테스트에 있는 `compile_and_run` 메서드를 보면 좋습니다. 여기에 `show=True`를 넘기면 생성된 WASM 텍스트도 stdout으로 덤프되어 확인할 수 있습니다.

어느 시점부터는 테스트가 실제로 생성된 WASM을 실행하고 결과를 검증합니다. 즉, 입력 언어(원 튜토리얼의 파트에 따라 KISS 또는 TINY의 변형)에서 실행까지 이어지는 “완전한 컴파일러”가 됩니다.

## Developing

이 저장소에서는 `uv`를 사용해 프로젝트를 설정하고 `ty`, `ruff` 같은 도구를 실행합니다.

필요한 명령은 함께 제공되는 `Makefile`을 참고하세요. 단일 테스트 파일을 실행하려면 예를 들어 다음과 같이 실행합니다:

```
uv run python -m unittest discover -s tests -p "test_14*"
```

## Debugging helper

`tryloader.html` - 생성된 WASM을 디버깅하기 위한 HTML 컨테이너(Chrome DevTools에 내장된 디버거 사용). `main` 함수를 가진 WAT 파일이 있다면, 먼저 이를 바이너리 WASM으로 변환합니다:

```
$ wasm-tools parse try.wat -o try.wasm
```

그 다음 `tryloader.html` 안의 안내에 따라 이를 서빙/로딩하면 됩니다.


