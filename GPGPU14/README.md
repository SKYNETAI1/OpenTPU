# Direct-Model GPUTensor16 Runtime for AMD Alveo U50

This directory is a binary-only GitHub release package for text generation on
one AMD/Xilinx Alveo U50. One XCLBIN supports two GGUF model profiles:
Qwen3.5-9B Q4_K_M and Gemma 4 12B IT Q4_K_S.

The runtime reads the original GGUF files directly. Model weights and tokenizer
files are not included.

## Highlights

- One U50 XCLBIN for both supported model profiles
- Sixteen HBM weight ports
- Interactive multi-turn chat with retained device state
- Incremental prefill without replaying earlier conversation tokens
- Direct loading of the original GGUF files
- Exact full-vocabulary greedy selection on the host by default
- Binary-only CPython runtime modules
- Private build paths and build commands removed from the public XCLBIN

## Release Configuration

- Target card: AMD/Xilinx Alveo U50
- Required shell: `xilinx_u50_gen3x16_xdma_5_202210_1`
- Implemented DATA clock: 157.8 MHz (XRT displays 157 MHz)
- Kernel clock: 500 MHz
- Device-reported HBM clock: 376 MHz
- Default resident context: 128 tokens
- Default reply request: up to 128 tokens, limited by remaining context
- Host ABI: Linux x86-64, CPython 3.12

## Package Contents

```text
.
|-- README.md
|-- requirements.txt
|-- SHA256SUMS
|-- u50_chat.py
|-- u50_multi_turn_chat.py
|-- runtime/
|   |-- gputensor16_runtime_core.cpython-312-x86_64-linux-gnu.so
|   |-- u50_software.cpython-312-x86_64-linux-gnu.so
|   `-- two model-support binary modules
`-- xclbin/
    `-- tpu3_hls_full_token.xclbin
```

The package excludes RTL, HLS and Python implementation source, build
projects, constraints, reports, logs, temporary files, test fixtures, model
weights, and tokenizer data. The two Python files are small launchers.

Binary-only packaging reduces accidental source disclosure but does not make a
distributed executable impossible to reverse engineer.

## Supported Models

| Launcher name | Model profile | Weight format |
| --- | --- | --- |
| `qwen` | Qwen3.5-9B Q4_K_M | GGUF |
| `gemma` | Gemma 4 12B IT Q4_K_S | GGUF |

The validated model files are:

| File | Download | SHA-256 |
| --- | --- | --- |
| Qwen3.5-9B Q4_K_M | [GGUF](https://huggingface.co/tinnlab/Qwen3.5-9B-GGUF/resolve/main/Qwen3.5-9B-Q4_K_M.gguf?download=true) | `03b74727a860a56338e042c4420bb3f04b2fec5734175f4cb9fa853daf52b7e8` |
| Qwen3.5-9B tokenizer | [tokenizer.json](https://huggingface.co/Qwen/Qwen3.5-9B/resolve/main/tokenizer.json?download=true) | `5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42` |
| Gemma 4 12B IT Q4_K_S | [GGUF](https://huggingface.co/unsloth/gemma-4-12b-it-GGUF/resolve/main/gemma-4-12b-it-Q4_K_S.gguf?download=true) | `8bfbcccb50049e670dcc55ba1aabf7e79c65c06eea96e42a0689baf7503aa81f` |

Other quantizations or similarly named checkpoints are not guaranteed to be
compatible.

## Installation

Install Git LFS before cloning the repository because the XCLBIN is tracked as
an LFS object:

```bash
git lfs install
git lfs pull
```

Create a CPython 3.12 environment and install the dependencies:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Install AMD XRT and confirm that it sees the card:

```bash
xrt-smi examine
```

## Model Layout

Place the downloaded files next to the launchers:

```text
models/
|-- Qwen3.5-9B-Q4_K_M.gguf
|-- gemma-4-12b-it-Q4_K_S.gguf
`-- qwen-tokenizer/
    `-- tokenizer.json
```

Explicit model, tokenizer, XCLBIN, and device paths may also be supplied.

## Preflight Check

Check model metadata, descriptor generation, XCLBIN presence, and memory
capacity without programming the card:

```bash
python u50_chat.py --model qwen --check-only
python u50_chat.py --model gemma --check-only
```

## Interactive Chat

```bash
python u50_chat.py --model qwen --interactive
python u50_chat.py --model gemma --interactive
```

The dedicated multi-turn entry point uses the same packaged runtime:

```bash
python u50_multi_turn_chat.py --model qwen
python u50_multi_turn_chat.py --model gemma
```

Use `/clear` to reset the conversation and `/exit` to quit. Later turns submit
only the new turn while earlier state remains resident on the card. The total
prompt and reply history must fit the 128-token default context.

Use a smaller reply limit for short tests:

```bash
python u50_chat.py --model qwen --interactive --max-new-tokens 16
```

## One-Shot Prompt

```bash
python u50_chat.py --model qwen --prompt "Hello"
python u50_chat.py --model gemma --prompt "Hello" --max-new-tokens 32
```

The default `--sampling host` path copies the final BF16 logits from U50 and
applies the same NaN, tie, and Gemma softcap rules as the FPGA. Use
`--sampling fpga` to run the final sampling descriptors on the card.

Run `python u50_chat.py --help` for all options.

## Integrity

Verify every executable payload before use:

```bash
sha256sum -c SHA256SUMS
```

## Limitations

- Only the exact model profiles above were validated.
- Text prompts are supported; multimodal input is not exposed.
- One model and one generation stream run at a time.
- The XCLBIN requires the stated U50 shell.
- The packaged extensions require CPython 3.12 on Linux x86-64.
