# Direct-Model TPU2x512 Runtime for AMD Alveo U50

This directory contains a packaged FPGA runtime for interactive text generation
on one AMD/Xilinx Alveo U50. One XCLBIN supports two validated GGUF model
profiles: Qwen3.5-9B Q4_K_M and Gemma 4 12B IT Q4_K_S.

The runtime reads each supported GGUF file directly. It does not require an
offline weight-conversion step, a repacked sidecar image, or generated weight
caches.

## Highlights

- One U50 XCLBIN for both supported model profiles
- Interactive multi-turn chat with retained FPGA KV/SSM state
- Incremental prefill after the first turn
- Direct loading of the original, publicly downloadable GGUF files
- Text-only Qwen3.5-9B and Gemma 4 12B chat
- Measured single-card decode throughput up to 3.37 tokens/s
- Prebuilt, stripped CPython runtime modules
- Binary-only distribution with private build paths removed

## Current Release

- Packaged DATA clock: 168 MHz (300 MHz requested, automatically scaled to
  the routed timing-safe frequency by Vitis)
- Updated multi-turn runtime that commits the assistant turn ending before the
  next prompt
- Stable incremental-prefill accounting: later turns contain only the newly
  formatted user turn, while `cached_position` tracks retained FPGA state
- Verified 512-token resident contexts for both published model profiles

## Supported Models

| Launcher name | Model profile | Weight format | Default model file |
| --- | --- | --- | --- |
| `qwen` | Qwen3.5-9B Q4_K_M | GGUF | `Qwen3.5-9B-Q4_K_M.gguf` |
| `gemma` | Gemma 4 12B IT Q4_K_S | GGUF | `gemma-4-12b-it-Q4_K_S.gguf` |

Model weights and tokenizer data are not included. Download them separately and
comply with their respective licenses and usage terms. Other quantizations and
similarly named checkpoints are not guaranteed to match this runtime.

## Verified Model Downloads

The following public files were compared byte-for-byte with the files used for
U50 validation:

| File | Download | SHA-256 |
| --- | --- | --- |
| Qwen3.5-9B Q4_K_M | [Download `Qwen3.5-9B-Q4_K_M.gguf`](https://huggingface.co/tinnlab/Qwen3.5-9B-GGUF/resolve/main/Qwen3.5-9B-Q4_K_M.gguf?download=true) | `03b74727a860a56338e042c4420bb3f04b2fec5734175f4cb9fa853daf52b7e8` |
| Qwen3.5-9B tokenizer | [Download `tokenizer.json`](https://huggingface.co/Qwen/Qwen3.5-9B/resolve/main/tokenizer.json?download=true) | `5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42` |
| Gemma 4 12B IT Q4_K_S | [Download `gemma-4-12b-it-Q4_K_S.gguf`](https://huggingface.co/unsloth/gemma-4-12b-it-GGUF/resolve/main/gemma-4-12b-it-Q4_K_S.gguf?download=true) | `8bfbcccb50049e670dcc55ba1aabf7e79c65c06eea96e42a0689baf7503aa81f` |

Download directly into the default layout:

```bash
mkdir -p models/qwen-tokenizer

wget -O models/Qwen3.5-9B-Q4_K_M.gguf \
  'https://huggingface.co/tinnlab/Qwen3.5-9B-GGUF/resolve/main/Qwen3.5-9B-Q4_K_M.gguf?download=true'

wget -O models/qwen-tokenizer/tokenizer.json \
  'https://huggingface.co/Qwen/Qwen3.5-9B/resolve/main/tokenizer.json?download=true'

wget -O models/gemma-4-12b-it-Q4_K_S.gguf \
  'https://huggingface.co/unsloth/gemma-4-12b-it-GGUF/resolve/main/gemma-4-12b-it-Q4_K_S.gguf?download=true'
```

## Package Contents

```text
.
|-- README.md
|-- requirements.txt
|-- SHA256SUMS
|-- u50_chat.py
|-- runtime/
|   |-- tpu2x512_runtime_core.cpython-312-x86_64-linux-gnu.so
|   `-- model-specific compiled runtime modules
`-- xclbin/
    `-- tpu3_hls_full_token.xclbin
```

This release intentionally excludes RTL, HLS, Chisel/Scala, descriptor-generator
source, build projects, model weights, tokenizer files, test fixtures,
implementation reports, and development logs. The XCLBIN retains the sections
required by XRT, while private build-command metadata and local filesystem paths
are redacted from the public copy.

## Hardware and Software Requirements

- AMD/Xilinx Alveo U50
- U50 shell compatible with `xilinx_u50_gen3x16_xdma_5_202210_1`
- 64-bit x86 Linux
- AMD Xilinx Runtime (XRT) with Python `pyxrt` support; XRT 2.21 was used for validation
- CPython 3.12 exactly, because the packaged extensions use the CPython 3.12 ABI
- Git LFS for downloading the XCLBIN
- Sufficient host storage for the selected GGUF and tokenizer

The packaged XCLBIN contains kernel `tpu3_hls_full_token`. It was built with
Vitis 2025.2 and its implemented DATA clock is 168 MHz. The default resident
context is 128 tokens; both model profiles also pass the HBM-capacity check at
512 tokens.

## Installation

Clone the repository with Git LFS enabled:

```bash
git lfs install
git clone https://github.com/SKYNETAI1/OpenTPU.git
cd OpenTPU/tpu2x512
git lfs pull
```

Create a Python 3.12 environment and install the Python dependencies:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Confirm that XRT can see the U50:

```bash
xbutil examine
```

Verify the published binaries before use:

```bash
sha256sum -c SHA256SUMS
```

## Model Setup

The default model layout is next to the launcher:

```text
models/
|-- Qwen3.5-9B-Q4_K_M.gguf
|-- gemma-4-12b-it-Q4_K_S.gguf
`-- qwen-tokenizer/
    `-- tokenizer.json
```

Alternatively, set a common model directory:

```bash
export U50_MODEL_DIR=/absolute/path/to/models
```

Individual model, tokenizer, and XCLBIN paths can also be supplied on the
command line.

## Preflight Validation

Validate model metadata, descriptor generation, XCLBIN presence, and U50 HBM
capacity without programming the card:

```bash
python u50_chat.py --model qwen --check-only
python u50_chat.py --model gemma --check-only
```

Both published profiles passed this check with the files and hashes listed
above.

## Interactive Chat

Start Qwen or Gemma in multi-turn mode:

```bash
python u50_chat.py --model qwen --interactive
python u50_chat.py --model gemma --interactive
```

At the prompt, type a message such as `Hello`. Use `/clear` to reset
the conversation and its FPGA state, or `/exit` to quit.

For longer replies and a larger retained conversation window:

```bash
python u50_chat.py \
  --model gemma \
  --interactive \
  --max-new-tokens 64 \
  --max-context 512
```

`--max-new-tokens` limits newly generated tokens per assistant reply; it does
not control prefill. A value such as 16 is useful for a quick hardware test but
can truncate a normal reply. `--max-context` covers the complete retained
conversation, including prompts, replies, and turn delimiters.

To use explicit paths:

```bash
python u50_chat.py \
  --model qwen \
  --qwen-model /models/Qwen3.5-9B-Q4_K_M.gguf \
  --qwen-tokenizer /models/qwen-tokenizer/tokenizer.json \
  --xclbin /opt/u50/tpu3_hls_full_token.xclbin \
  --interactive
```

Select another U50 with `--device`. Run `python u50_chat.py --help` for all
model, path, context, generation, timeout, and output options.

## One-Shot Runs

Run a single prompt:

```bash
python u50_chat.py \
  --model qwen \
  --prompt "Hello" \
  --max-new-tokens 64
```

Run Gemma and write a machine-readable result:

```bash
python u50_chat.py \
  --model gemma \
  --prompt "Hello" \
  --max-new-tokens 32 \
  --json gemma-result.json
```

## Conversation State and Prefill

The first turn prefills the complete formatted prompt. Later turns retain the
model's FPGA KV/SSM state and prefill only the newly appended turn tokens. The
interactive progress line therefore reports `new_prefill_tokens`, not the
total historical conversation length.

The assistant's final generated token and the turn-ending token are committed
to FPGA state immediately after each reply. They are not deferred to, or
counted as part of, the next turn's prefill. Repeating the same user message
therefore produces a stable `new_prefill_tokens` count instead of a count that
grows with conversation history. `cached_position` is expected to increase: it
is the retained context position and confirms that earlier state was reused.

Entering `/clear`, switching models, or restarting the process creates fresh
state and requires a new full prefill. Token execution time can still increase
with sequence position because attention operates over a longer retained
context even though historical tokens are not re-prefilled.

## Measured U50 Performance

These results were measured on one Alveo U50 with the packaged 168 MHz XCLBIN
and the exact model files listed above. The benchmark used a two-character
Chinese greeting, context was 128, and inference used one model and one
generation stream. Decode throughput excludes the first output token; TTFT
includes prompt prefill.

| Model | Prefill tokens | Generated tokens | Stop condition | TTFT | Decode time | Decode throughput | Total time |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| Qwen3.5-9B Q4_K_M | 13 | 9 | EOS | 3.403 s | 2.371 s | 3.374 tokens/s | 5.778 s |
| Gemma 4 12B IT Q4_K_S | 10 | 21 | EOS | 3.560 s | 8.868 s | 2.255 tokens/s | 12.639 s |

The measured replies were coherent greeting responses. These are short-prompt,
single-run measurements rather than batched throughput or a statistical
benchmark. Performance varies with prompt length, sequence position, host
storage, PCIe state, XRT version, and board clock behavior.

## Direct Weight Loading

For both supported profiles, the runtime reads the original GGUF bytes and
loads them directly into U50 HBM at startup. Quantized values are consumed by
the FPGA runtime without creating a converted model file. Runtime diagnostics
therefore report `transformed_weight_bytes=0`.

Device upload is still required whenever a model is started. Host storage and
operating-system page-cache state can materially affect startup time.

## Compatibility and Limitations

- Only the exact model profiles and file hashes listed above were validated.
- The launcher currently supports text prompts; multimodal inputs are not exposed.
- The XCLBIN targets the specified U50 shell. A shell mismatch can prevent programming or execution.
- The binary Python modules require Linux x86-64 and CPython 3.12.
- One model and one generation stream execute at a time; request batching is not implemented.
- The default context is 128. Larger values must pass `--check-only` HBM-capacity validation.
- Binary packaging raises the reverse-engineering barrier but does not guarantee absolute secrecy.

## Troubleshooting

### The XCLBIN is only a small text file

Git LFS content has not been downloaded. Run:

```bash
git lfs pull
```

### No U50 device is found

Check the PCIe device and XRT driver status:

```bash
xbutil examine
```

If the card is not device `0`, select its index with `--device`.

### The packaged runtime cannot be imported

Confirm the interpreter and host architecture:

```bash
python --version
uname -m
```

This package requires CPython 3.12 on Linux x86-64. Also confirm that XRT and
`pyxrt` are available in the active environment.

### XCLBIN programming fails

Verify that the installed U50 platform shell matches
`xilinx_u50_gen3x16_xdma_5_202210_1`, then inspect `xbutil examine` output.

### A model or tokenizer cannot be found

Check the default `models` layout, set `U50_MODEL_DIR`, or pass explicit paths.
Use absolute paths while diagnosing lookup problems.

### A model fails the preflight check

Confirm its filename and SHA-256 against the verified download table. A GGUF
with a different quantization, tensor layout, or revision may not be compatible.

## Integrity

`SHA256SUMS` covers the launcher, compiled runtime modules, and XCLBIN:

```bash
sha256sum -c SHA256SUMS
```

Run this command after cloning, transferring, or publishing the package.
