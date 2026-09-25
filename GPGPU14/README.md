# GPUTensor14: ASIC-First SIMT + Tensor LLM Accelerator

## AI Authorship Notice

OpenTPU is an AI-built, ASIC-first accelerator project. Every architecture in
this repository was conceived and engineered by AI for eventual ASIC
implementation, including the system architecture, compute and memory
dataflows, RTL/HLS, host runtimes, integration, verification, release
packaging, and documentation. The FPGA packages are validation vehicles used
to prove functionality, numerical behavior, interfaces, memory operation, and
end-to-end execution on real hardware; FPGA deployment is not the final
architectural target. Human participation was limited to providing objectives,
hardware access, and executing physical-board operations when required.

## Architecture Positioning

GPUTensor14 is designed as an ASIC accelerator architecture, not as an
FPGA-only product. Its programmable architecture combines 14 SIMT cores, one
quantized Tensor cluster, a 128-bit uploadable instruction format, and 16
wide memory interfaces. The AMD/Xilinx Alveo U50 is used as a physical
validation platform to exercise the hardware/software stack with real model
weights, real memory traffic, multi-token generation, and retained state.

The project currently has two implementation layers at different integration
stages:

- The programmable `GeneralGpuCore` path demonstrates the 14-core SIMT ISA,
  Tensor cooperation, graph lowering, quantized data handling, and RTL
  verification needed for the ASIC architecture.
- The published full-token U50 image closes the end-to-end Qwen and Gemma
  inference loop and provides the measured token rates reported below.

Performance figures in this README belong to the published full-token U50
validation image. They are measured FPGA validation results, not projected
ASIC performance and not a claim that the programmable 14-core path has
already completed the same board-level multi-token loop.

## Results at a Glance

| Item | Result |
| --- | --- |
| Final architecture target | ASIC |
| Physical validation platform | AMD/Xilinx Alveo U50 FPGA |
| Programmable compute | 14 SIMT cores; 32-thread warps; up to 4 resident warps per core |
| Tensor compute | One quantized packed-GEMV Tensor cluster |
| Memory system | 16 x 256-bit HBM-side interfaces |
| Program model | Up to 4,096 uploaded 128-bit instructions |
| Quantized formats verified | Q4_K, Q5_K, Q6_K, and Q8_0 |
| Published model validation | Qwen3.5-9B Q4_K_M and Gemma 4 12B IT Q4_K_S |
| Measured U50 decode | Qwen: **1.312 tok/s**; Gemma: **1.781 tok/s** |
| Implemented U50 clocks | 157.8 MHz DATA; 500 MHz kernel |

## Measured Token Generation on U50

These are real single-card measurements from the published full-token
validation path, not simulation estimates. Decode throughput uses elapsed wall
time, includes host work performed during inference, excludes the one-time
model upload, and excludes the first output token produced by prefill.

| Model / scenario | Output | First token | Decode throughput | Result |
| --- | ---: | ---: | ---: | --- |
| Qwen3.5-9B Q4_K_M, raw input token `[109266]` | 32 tokens | 0.753 s | **1.312 tok/s** | Completed without a hardware fault |
| Gemma 4 12B IT Q4_K_S, templated `你好` | 21 tokens | 4.637 s | **1.781 tok/s** | Reached EOS |
| Gemma multi-turn, `你好` then `你是谁？` | 53 tokens total | Incremental prefill | **1.781 / 1.390 tok/s** | Zero history replay across the two turns |

The Gemma second-turn rate is lower because the retained context is longer.
Both model paths completed real U50 multi-token inference, and the multi-turn
path retained accelerator state instead of recomputing the full conversation.

## Technical Evidence

| Engineering layer | Verifiable result |
| --- | --- |
| SIMT microarchitecture | 14 cores, 32-thread warps, round-robin scheduling, 4 resident warps per core, and 32 x 32-bit registers per thread |
| Instruction system | 128-bit uploaded instructions covering integer, bitwise, FP32, predicate, branch, vote, shuffle, and global-memory operations |
| Tensor and memory path | One packed-GEMV Tensor cluster with 16 weight-read paths and 64-bit global addressing |
| Graph compiler | Captured Qwen prefill graph: 1,831 nodes, 22 GGML operation types, 1,890 launches, 31 programs, and zero CPU fallback for the captured graph |
| Quantized arithmetic | Q4_K/Q5_K/Q6_K/Q8_0 block decoding verified; maximum absolute decode difference of zero in the recorded fixtures |
| RTL verification | Seven suites and 32 tests spanning single-core, multi-core, Tensor, and HBM behavior |
| Representative RTL results | 32-thread and 29-thread programs completed in 276 and 269 cycles; a 4 x 4,096 Q5 GEMV completed in 3,236 cycles |
| End-to-end validation | Qwen and Gemma multi-token inference on a physical U50, including retained multi-turn state |

This directory is a binary-only GitHub release package for text generation on
one AMD/Xilinx Alveo U50. One XCLBIN supports two GGUF model profiles:
Qwen3.5-9B Q4_K_M and Gemma 4 12B IT Q4_K_S.

The runtime reads the original GGUF files directly. Model weights and tokenizer
files are not included.

## Highlights

- ASIC-first architecture with FPGA used strictly as the current validation
  and prototyping platform
- Fourteen programmable SIMT cores plus a dedicated quantized Tensor cluster
- Uploadable 128-bit instruction programs and software graph lowering
- One U50 XCLBIN for both supported model profiles
- Sixteen HBM weight ports
- Interactive multi-turn chat with retained device state
- Incremental prefill without replaying earlier conversation tokens
- Direct loading of the original GGUF files
- Exact full-vocabulary greedy selection on the host by default
- Binary-only CPython runtime modules
- Private build paths and build commands removed from the public XCLBIN

## Release Configuration

- Architecture target: ASIC
- FPGA validation card: AMD/Xilinx Alveo U50
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
|   |-- gputensor14_runtime_core.cpython-312-x86_64-linux-gnu.so
|   |-- u50_software.cpython-312-x86_64-linux-gnu.so
|   `-- two model-support binary modules
`-- xclbin/
    `-- tpu3_rtl_full_token.xclbin
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

- This repository publishes an FPGA validation image, not an ASIC tape-out or
  a projection of final ASIC frequency, power, area, or token throughput.
- The measured U50 rates describe the published full-token validation path;
  the programmable 14-core `GeneralGpuCore` path remains a distinct
  integration stage as described above.
- Only the exact model profiles above were validated.
- Text prompts are supported; multimodal input is not exposed.
- One model and one generation stream run at a time.
- The XCLBIN requires the stated U50 shell.
- The packaged extensions require CPython 3.12 on Linux x86-64.
