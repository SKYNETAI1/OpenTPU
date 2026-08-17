# Direct-Model LLM Runtime for AMD Alveo U50

This repository contains a packaged FPGA runtime for interactive large-language-model inference on a single AMD/Xilinx Alveo U50. One XCLBIN supports all three included model profiles, and the command-line launcher can run them individually or sequentially.

The runtime reads the supported GGUF or safetensors model file directly. It does not require an offline weight-conversion step or a second, repacked weight file.

## Highlights

- One U50 XCLBIN for three model profiles
- Interactive multi-turn chat with retained FPGA KV/SSM state
- Incremental prefill after the first turn
- Direct loading of original GGUF and safetensors weights
- Q4_K_M and BF16 model support
- Eight HBM weight channels
- Measured single-card decode throughput up to 5.52 tokens/s
- Prebuilt, stripped CPython runtime modules

## Supported Models

| Launcher name | Model profile | Weight format | Default model file |
| --- | --- | --- | --- |
| `qwen9` | Qwen3.5-9B-MIO Q4_K_M | GGUF | `Qwen3.5-9B-MIO-Q4_K_M.gguf` |
| `gemma` | Gemma 4 E4B Q4_K_M | GGUF | `gemma-4-E4B-it-Q4_K_M.gguf` |
| `qwen2` | Qwen3.5-2B BF16 | safetensors | `model.safetensors-00001-of-00001.safetensors` |

Model weights and tokenizer files are not included. Obtain them separately and comply with their respective licenses and usage terms.

## Model Downloads

The following direct Hugging Face download links have been verified:

| Model | Download | Runtime compatibility |
| --- | --- | --- |
| Gemma 4 E4B Q4_K_M | [Download `gemma-4-E4B-it-Q4_K_M.gguf`](https://huggingface.co/unsloth/gemma-4-E4B-it-GGUF/resolve/main/gemma-4-E4B-it-Q4_K_M.gguf?download=true) | Supported directly by the `gemma` profile |
| Qwen3.5-9B Q4_K_M | [Download `Qwen3.5-9B.Q4_K_M.gguf`](https://huggingface.co/mradermacher/Qwen3.5-9B-GGUF/resolve/main/Qwen3.5-9B.Q4_K_M.gguf?download=true) | Supported by the `qwen9` profile when supplied with `--qwen9-model` |
| Qwen3.5-2B BF16 | [Download `model.safetensors-00001-of-00001.safetensors`](https://huggingface.co/Qwen/Qwen3.5-2B/resolve/main/model.safetensors-00001-of-00001.safetensors?download=true) | Supported directly by the `qwen2` profile |

For Qwen3.5-9B, pass the downloaded public file explicitly because its filename differs from the legacy default:

```bash
python u50_three_model_chat.py \
  --model qwen9 \
  --qwen9-model "$PWD/models/Qwen3.5-9B.Q4_K_M.gguf" \
  --interactive
```

The Qwen3.5-9B public file has the same 427 tensor descriptors and tensor layout as the legacy `Qwen3.5-9B-MIO-Q4_K_M.gguf`; only GGUF metadata fields differ.

The Qwen3.5-2B direct link downloads the model weight file. Its tokenizer files must also be downloaded from the [Qwen/Qwen3.5-2B repository](https://huggingface.co/Qwen/Qwen3.5-2B) and placed in the configured `qwen352b` tokenizer directory.

## Package Contents

```text
.
├── README.md
├── requirements.txt
├── SHA256SUMS
├── u50_three_model_chat.py
├── runtime/
│   ├── u50_runtime_core.cpython-312-x86_64-linux-gnu.so
│   └── model-specific runtime modules
└── xclbin/
    └── full_token_rtl_probe_auto.xclbin
```

This is a binary runtime distribution. It intentionally does not include HLS/RTL source code, build projects, model weights, test fixtures, implementation reports, or development logs.

## Hardware and Software Requirements

- AMD/Xilinx Alveo U50
- U50 platform shell `xilinx_u50_gen3x16_xdma_5_202210_1`
- 64-bit x86 Linux with glibc 2.14 or newer
- AMD Xilinx Runtime (XRT) with Python `pyxrt` support; XRT 2.19 is recommended
- CPython 3.12 exactly, because the packaged extension modules use the CPython 3.12 ABI
- Git LFS for downloading the XCLBIN
- Sufficient local storage for the selected model and its tokenizer

The packaged XCLBIN contains kernel `full_token_rtl_probe`. Its implemented data clock is 186 MHz (186.8 MHz achieved during implementation). It was built with Vitis 2025.2.

## Installation

Clone the repository with Git LFS enabled:

```bash
git lfs install
git clone <repository-url>
cd <repository-directory>
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

The default layout is a `models` directory next to the launcher:

```text
models/
├── Qwen3.5-9B-MIO-Q4_K_M.gguf
├── gemma-4-E4B-it-Q4_K_M.gguf
├── model.safetensors-00001-of-00001.safetensors
└── qwen352b/
    └── tokenizer files
```

Alternatively, set a common model directory:

```bash
export U50_MODEL_DIR=/absolute/path/to/models
```

Individual model and tokenizer paths can also be supplied on the command line.

## Interactive Chat

Start one model in interactive mode:

```bash
python u50_three_model_chat.py --model qwen9 --interactive
python u50_three_model_chat.py --model gemma --interactive
python u50_three_model_chat.py --model qwen2 --interactive
```

At the prompt, type a message such as `Hello`. Use `/clear` to reset the conversation and its FPGA state, or `/exit` to quit.

To use explicit paths:

```bash
python u50_three_model_chat.py \
  --model qwen9 \
  --qwen9-model /models/Qwen3.5-9B-MIO-Q4_K_M.gguf \
  --xclbin /opt/u50/full_token_rtl_probe_auto.xclbin \
  --interactive
```

Select a different U50 with `--device`. Run `python u50_three_model_chat.py --help` for all path, generation, device, and output options.

## One-Shot and Sequential Runs

Run a single prompt:

```bash
python u50_three_model_chat.py \
  --model qwen9 \
  --prompt "Hello" \
  --max-new-tokens 16
```

Run the same prompt on all three profiles, one after another:

```bash
python u50_three_model_chat.py \
  --model all \
  --prompt "Hello" \
  --max-new-tokens 16
```

`--model all` is serial, not concurrent. Only one model is resident and executing at a time.

Machine-readable one-shot results can be written with `--json results.json`.

## Conversation State and Prefill

The first turn prefills the complete formatted prompt. On later turns, the runtime retains the model's FPGA KV/SSM state and prefills only the newly appended user-turn tokens. The progress counter therefore reports `new_prefill_tokens`, not the total historical conversation length.

Starting a different model, restarting the process, or entering `/clear` creates fresh state and requires a new full prefill.

## Performance

The following results were measured on one Alveo U50 with the packaged 186 MHz XCLBIN. Each test used a short two-turn conversation and generated eight tokens per reply. Throughput is single-stream decode throughput; it is not a batched aggregate.

| Model | Original weight size | Startup load | First-turn TTFT | Measured decode |
| --- | ---: | ---: | ---: | ---: |
| Qwen3.5-9B-MIO Q4_K_M | 5.627 GB | 2.03 s* | 2.86 s | 3.81-4.01 tokens/s |
| Gemma 4 E4B Q4_K_M | 4.977 GB | 6.43 s | 2.01 s | 3.66-4.17 tokens/s |
| Qwen3.5-2B BF16 | 4.548 GB | 5.93 s | 1.80 s | 5.38-5.52 tokens/s |

*Startup loading depends heavily on host storage, PCIe state, and the operating-system page cache. The 2.03-second result may include a warm file cache and should not be treated as steady-state inference throughput.

The architecture-level cycle model gives the following ideal no-stall estimates:

| Model | Estimated cycles/token | Ideal throughput at 186 MHz | Clock required for 8 tokens/s |
| --- | ---: | ---: | ---: |
| Qwen3.5-9B-MIO Q4_K_M | 34,580,751 | 5.38 tokens/s | 276.65 MHz |
| Gemma 4 E4B Q4_K_M | 32,934,036 | 5.65 tokens/s | 263.47 MHz |
| Qwen3.5-2B BF16 | 34,558,858 | 5.38 tokens/s | 276.47 MHz |

These cycle-derived values describe an ideal schedule without external stalls. Actual board throughput also includes HBM access, kernel launch, control, synchronization, and host-runtime overhead. They are design estimates, not additional benchmark results.

## Direct Weight Loading

For supported models, the runtime reads the original GGUF or safetensors file and transfers its weight bytes to eight U50 HBM buffers. The transfer stripes unchanged 32-byte beats by address across the HBM channels. Quantized values are decoded by the FPGA operators during execution.

There is no offline numerical conversion, no generated weight cache, and no converted sidecar image. Runtime diagnostics report `transformed_weight_bytes=0`. Loading into device HBM at startup is still required.

## Compatibility and Limitations

- The packaged runtime targets the exact model profiles and file formats listed above; similarly named checkpoints are not guaranteed to work.
- The XCLBIN targets the specified U50 shell. A shell mismatch can prevent programming or execution.
- The binary Python modules require Linux x86-64 and CPython 3.12.
- The current launcher executes one model and one generation stream at a time; it does not implement request batching.
- Model context limits and generation limits remain profile-specific.
- Performance varies with prompt length, sequence position, sampling configuration, host system, XRT version, and board clock behavior.
- Binary packaging raises the reverse-engineering barrier but does not provide absolute source-code secrecy.

## Troubleshooting

### The XCLBIN is only a small text file

Git LFS content has not been downloaded. Run:

```bash
git lfs pull
```

### No U50 device is found

Check device and driver status:

```bash
xbutil examine
```

Then select the correct index with `--device` if it is not device `0`.

### The packaged runtime cannot be imported

Confirm the interpreter and architecture:

```bash
python --version
uname -m
```

The current package requires CPython 3.12 on Linux x86-64. Also confirm that XRT and `pyxrt` are installed in the active environment.

### XCLBIN programming fails

Verify that the installed U50 platform shell matches `xilinx_u50_gen3x16_xdma_5_202210_1`, and inspect the XRT diagnostics reported by `xbutil examine`.

### A model or tokenizer cannot be found

Check the default `models` layout, set `U50_MODEL_DIR`, or pass an explicit model/tokenizer path. Paths should be absolute when diagnosing lookup problems.

## Integrity

`SHA256SUMS` covers the launcher, compiled runtime modules, and XCLBIN:

```bash
sha256sum -c SHA256SUMS
```

Run this command after cloning, transferring, or publishing the package.
