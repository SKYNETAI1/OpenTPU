# Binary LLM Runtime for AMD Alveo U50

This directory is a binary-only runtime package for interactive inference on
an AMD/Xilinx Alveo U50. It intentionally excludes RTL, HLS, Chisel/Scala,
build scripts, descriptor-generator source, implementation reports, logs,
model weights, tokenizer files, and test fixtures.

The XCLBIN retains its executable runtime sections, while private build-command
metadata and local filesystem paths are redacted from the public copy.

## Included files

~~~text
.
├── README.md
├── requirements.txt
├── SHA256SUMS
├── u50_chat.py
├── runtime/
│   └── stripped CPython 3.12 extension modules
└── xclbin/
    └── tpu3_hls_full_token.xclbin
~~~

The Python launcher only loads the compiled runtime. No implementation Python
modules are distributed as source.

## Requirements

- AMD/Xilinx Alveo U50
- U50 shell compatible with `xilinx_u50_gen3x16_xdma_5_202210_1`
- Linux x86-64
- CPython 3.12 exactly
- XRT with Python/pyxrt support
- Git LFS for the XCLBIN

Install Python dependencies:

~~~bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
~~~

Verify the package:

~~~bash
git lfs pull
sha256sum -c SHA256SUMS
~~~

## Models

Model weights and tokenizer data are not included. The default local layout is:

~~~text
models/
├── Qwen3.5-9B-Q4_K_M.gguf
├── gemma-4-12b-it-Q4_K_S.gguf
└── qwen-tokenizer/
    └── tokenizer.json
~~~

Set `U50_MODEL_DIR` to use a different model directory.

## Run

Qwen one-shot:

~~~bash
python u50_chat.py --model qwen --prompt "你好" --max-new-tokens 16
~~~

Qwen multi-turn:

~~~bash
python u50_chat.py --model qwen --interactive
~~~

Gemma one-shot or multi-turn:

~~~bash
python u50_chat.py --model gemma --prompt "你好" --max-new-tokens 32
python u50_chat.py --model gemma --interactive
~~~

During interactive chat, use `/clear` to reset conversation state and `/exit`
to quit. Use `python u50_chat.py --help` for path, device, context, generation,
and timeout options.

## Compatibility

The packaged extensions require CPython 3.12 on Linux x86-64. The XCLBIN
targets the U50 platform named above. Binary packaging raises the
reverse-engineering barrier but is not a guarantee against reverse
engineering.
