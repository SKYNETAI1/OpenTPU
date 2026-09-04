# Direct-Model TPU32x32 Runtime for AMD Alveo U50

This directory is a binary-only release package for interactive text
generation on one AMD/Xilinx Alveo U50. One XCLBIN supports two validated GGUF
model profiles: Qwen3.5-9B Q4_K_M and Gemma 4 12B IT Q4_K_S.

The runtime reads the original GGUF files directly. Model weights and tokenizer
files are not included.

## Highlights

- One U50 XCLBIN for both supported model profiles
- Interactive multi-turn chat with retained device state
- Incremental prefill: prior conversation tokens are not replayed
- Direct loading of the original GGUF files
- Qwen and Gemma text chat from the same launcher
- Binary-only CPython runtime modules
- Private build paths and build commands removed from the public XCLBIN

## Release Configuration

- Target card: AMD/Xilinx Alveo U50
- Required shell: `xilinx_u50_gen3x16_xdma_5_202210_1`
- Implemented DATA clock: 160.7 MHz
- Default resident context: 128 tokens
- Default reply request: up to 128 tokens, automatically limited by the
  remaining resident context
- Host ABI: Linux x86-64, CPython 3.12

## Compute Architecture: TPU32x32 vs TPU2x512

The two U50 releases expose the same model-level workflow but organize their
1024 integer MACs differently. The names describe the physical compute shape,
not different numerical models or a 2x throughput relationship.

| Property | TPU32x32 (this package) | [TPU2x512](../tpu2x512/) |
| --- | --- | --- |
| Peak integer work | `32 x 32 = 1024` MACs/cycle | `2 x 512 = 1024` MACs/cycle |
| Physical organization | Four local `8 x 32` islands operating together | Two wide 512-MAC clusters |
| Data movement emphasis | Decode tiles, activation reads, and accumulator state stay local to each island | A shared wide streaming/alignment front end feeds the two clusters |
| Reduction style | Each island retains eight output rows locally; completed rows are reduced and serialized at the boundary | Each cluster forms wide partial dot-product contributions before accumulation |
| Main implementation tradeoff | More local state/control replication, but shorter wiring and lower global fanout | Less replicated local control, but wider shared datapaths and longer high-fanout routes |

Both designs retain the same 1024-MAC/cycle arithmetic ceiling and the same
direct-GGUF software interface. End-to-end token speed is still determined by
the implemented clock, HBM efficiency, model operation mix, and sequence
length; the array shape alone does not predict tokens per second. TPU32x32
favors placement and routing locality on the multi-region U50 fabric, whereas
TPU2x512 favors a wide streaming structure.

## Package Contents

```text
.
|-- README.md
|-- requirements.txt
|-- SHA256SUMS
|-- u50_chat.py
|-- runtime/
|   |-- tpu32x32_runtime_core.cpython-312-x86_64-linux-gnu.so
|   `-- two model-support binary modules
`-- xclbin/
    `-- tpu3_hls_full_token.xclbin
```

The package intentionally excludes RTL, HLS, Chisel/Scala, descriptor source,
Python implementation source, build projects, constraints, reports, logs,
temporary files, test fixtures, model weights, and tokenizer data. The only
Python file is the small public launcher shown above.

Binary-only packaging reduces accidental source disclosure but does not make a
distributed executable impossible to reverse engineer.

## Supported Models

| Launcher name | Model profile | Weight format |
| --- | --- | --- |
| `qwen` | Qwen3.5-9B Q4_K_M | GGUF |
| `gemma` | Gemma 4 12B IT Q4_K_S | GGUF |

The validated public files are:

| File | Download | SHA-256 |
| --- | --- | --- |
| Qwen3.5-9B Q4_K_M | [GGUF](https://huggingface.co/tinnlab/Qwen3.5-9B-GGUF/resolve/main/Qwen3.5-9B-Q4_K_M.gguf?download=true) | `03b74727a860a56338e042c4420bb3f04b2fec5734175f4cb9fa853daf52b7e8` |
| Qwen3.5-9B tokenizer | [tokenizer.json](https://huggingface.co/Qwen/Qwen3.5-9B/resolve/main/tokenizer.json?download=true) | `5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42` |
| Gemma 4 12B IT Q4_K_S | [GGUF](https://huggingface.co/unsloth/gemma-4-12b-it-GGUF/resolve/main/gemma-4-12b-it-Q4_K_S.gguf?download=true) | `8bfbcccb50049e670dcc55ba1aabf7e79c65c06eea96e42a0689baf7503aa81f` |

Other quantizations or similarly named checkpoints are not guaranteed to be
compatible.

## Installation

Install Git LFS before cloning the repository, because the XCLBIN is tracked as
an LFS object:

```bash
git lfs install
git lfs pull
```

Create a CPython 3.12 environment and install the runtime dependencies:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Confirm that XRT can see the card:

```bash
xbutil examine
```

## Model Layout

Place the downloaded files next to the launcher:

```text
models/
|-- Qwen3.5-9B-Q4_K_M.gguf
|-- gemma-4-12b-it-Q4_K_S.gguf
`-- qwen-tokenizer/
    `-- tokenizer.json
```

Explicit model, tokenizer, XCLBIN, and device paths may also be supplied on the
command line.

## Preflight Check

Check model metadata, descriptor generation, XCLBIN presence, and device-memory
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

Use `/clear` to reset the conversation and `/exit` to quit. Later turns submit
only the new turn while earlier state remains resident on the card. The
`on_u50` count therefore grows, while `history_replayed` remains zero.

The total prompt and reply history must fit the 128-token default context. The
reply limit is automatically reduced to the remaining capacity. A smaller
explicit limit can be selected for short tests:

```bash
python u50_chat.py --model qwen --interactive --max-new-tokens 16
```

Gemma channel-control markers are removed from user-visible output.

## One-Shot Prompt

```bash
python u50_chat.py --model qwen --prompt "Hello"
python u50_chat.py --model gemma --prompt "Hello" --max-new-tokens 32
```

Run `python u50_chat.py --help` for all options.

## Measured U50 Smoke Results

The packaged 160.7 MHz implementation produced coherent replies in direct
hardware tests. Decode throughput excludes the first output token.

| Model | Prompt tokens | TTFT | Decode throughput |
| --- | ---: | ---: | ---: |
| Qwen3.5-9B Q4_K_M | 13 | 5.116 s | 2.243 tokens/s |
| Gemma 4 12B IT Q4_K_S | 10 | 5.270 s | 1.610 tokens/s |

These are short smoke measurements, not batched throughput benchmarks.

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
