# OpenTPU

OpenTPU is an FPGA large-language-model inference project with deployable
runtime packages for AMD/Xilinx Alveo U50 and Ultra96-V2 hardware. The current
releases execute supported model files directly, without requiring users to
create a second converted or repacked model image.

The repository contains hardware-specific binary releases, launchers,
integrity manifests, and board documentation. Model weights are downloaded
separately and remain subject to their original licenses.

## Choose a Release

| Directory | Hardware | Supported models | Runtime | Status |
| --- | --- | --- | --- | --- |
| [`GPGPU14`](./GPGPU14) | AMD/Xilinx Alveo U50 | Qwen3.5-9B Q4_K_M; Gemma 4 12B IT Q4_K_S | Linux x86-64, CPython 3.12, XRT | GPUTensor14 direct-model U50 release with 16 HBM weight ports |
| [`tpu2x512`](./tpu2x512) | AMD/Xilinx Alveo U50 | Qwen3.5-9B Q4_K_M; Gemma 4 12B IT Q4_K_S | Linux x86-64, CPython 3.12, XRT | Wide-streaming U50 release |
| [`tpu32x32`](./tpu32x32) | AMD/Xilinx Alveo U50 | Qwen3.5-9B Q4_K_M; Gemma 4 12B IT Q4_K_S | Linux x86-64, CPython 3.12, XRT | Locality-oriented U50 release with four compute islands |
| [`U50HLS`](./U50HLS) | AMD/Xilinx Alveo U50 | Qwen3.5-9B-MIO Q4_K_M; Gemma 4 E4B Q4_K_M; Qwen3.5-2B BF16 | Linux x86-64, CPython 3.12, XRT | Earlier HLS-based U50 release |
| [`ultra96`](./ultra96) | Ultra96-V2 | Qwen3.5-2B Q3_K_S | PYNQ 3.0, AArch64, CPython 3.10 | Embedded-board release |

Compare the measured results below when choosing between the wide-streaming
`tpu2x512` and placement-local, square-array `tpu32x32` releases. The updated
`tpu32x32` package includes the HBM prefetch scheduling fix and a dedicated
multi-turn launcher. `GPGPU14` provides the GPUTensor14 direct-model runtime
and exact host-side greedy sampling. The earlier HLS development line is
preserved in `U50HLS` so its three-model release remains reproducible.

## U50 Compute Architecture Choices

The two current U50 packages perform the same validated model computations and
have the same peak integer arithmetic count. Their difference is how those
resources are physically organized and connected.

| Property | [`tpu2x512`](./tpu2x512) | [`tpu32x32`](./tpu32x32) |
| --- | --- | --- |
| Peak integer work | `2 x 512 = 1024` MACs/cycle | `32 x 32 = 1024` MACs/cycle |
| Physical organization | Two wide 512-MAC clusters | Four local `8 x 32` islands operating together |
| Data movement | Shared wide streaming and alignment front end | Decode tiles, activation reads, and accumulators remain island-local |
| Result handling | Wide partial dot products are accumulated after each cluster | Eight local output rows per island are reduced and serialized at the boundary |
| Implementation emphasis | Less replicated control and high streaming width | Shorter local wiring and lower global fanout |

The array name alone does not determine token throughput. Implemented clock,
HBM efficiency, model operation mix, and sequence length remain decisive. See
the architecture section inside each release README for more detail.

## Project Highlights

- Direct use of the validated GGUF model files
- FPGA-side execution of the model datapath
- Interactive and one-shot text generation
- Multi-turn U50 chat with resident FPGA KV/SSM state
- Incremental prefill that processes only newly appended turn tokens
- Prebuilt board images and stripped Python runtime extensions
- SHA-256 manifests for every published launcher, runtime, and FPGA image
- Model weights excluded from Git to keep licensing and distribution explicit

## TPU Array Alveo U50 Releases

Both [`tpu2x512`](./tpu2x512) and [`tpu32x32`](./tpu32x32) contain one XCLBIN
for the two validated model profiles. They target
`xilinx_u50_gen3x16_xdma_5_202210_1` and share the same direct-GGUF host
workflow.

Both current runtimes support:

- Qwen3.5-9B Q4_K_M
- Gemma 4 12B IT Q4_K_S
- Interactive multi-turn sessions
- Retained conversation state on the FPGA
- Stable delta-prefill accounting across turns
- Binary-only distribution with private source and build paths excluded

`tpu2x512` has an implemented DATA clock of 168 MHz and has passed the
runtime HBM-capacity check with 512-token resident contexts for both profiles.
`tpu32x32` has an implemented DATA clock of 146.5 MHz (XRT displays 146 MHz)
and defaults to a 128-token resident context. Its release was updated on
2026-09-05.

### Measured U50 Results

The following single-card measurements use a short greeting prompt, a
128-token context, and one generation stream. Decode throughput excludes the
first output token. TPU32x32 prompt time is the summed FPGA kernel wait time
for prefill, excluding model upload, initialization, and host-side descriptor
preparation; TPU2x512 retains its previously reported TTFT values.

| Release | Model | Clock | Prompt | Reported prompt time | Decode throughput |
| --- | --- | ---: | ---: | ---: | ---: |
| TPU2x512 | Qwen3.5-9B Q4_K_M | 168 MHz | 13 tokens | 3.403 s | 3.374 tokens/s |
| TPU2x512 | Gemma 4 12B IT Q4_K_S | 168 MHz | 10 tokens | 3.560 s | 2.255 tokens/s |
| TPU32x32 | Qwen3.5-9B Q4_K_M | 146.5 MHz | 13 tokens | 3.116 s | 3.635 tokens/s |
| TPU32x32 | Gemma 4 12B IT Q4_K_S | 146.5 MHz | 10 tokens | 3.280 s | 2.363 tokens/s |

These are board measurements from short single runs, not idealized estimates
or batched throughput. Results vary with prompt length, sequence position,
host storage, PCIe state, XRT version, and board conditions.

## Ultra96-V2 Release

The [`ultra96`](./ultra96) package runs `Qwen3.5-2B-Q3_K_S.gguf` on an
Ultra96-V2. It includes the PYNQ overlay, AArch64 CPython 3.10 runtime modules,
a command-line API, tokenizer data, and a Jupyter notebook.

The ARM processing system handles tokenization and session control, while the
programmable-logic engine consumes quantized matrix weights from the original
GGUF representation. The model file itself is not included.

## Quick Start

Install Git LFS before cloning so FPGA images are downloaded rather than left
as small pointer files:

```bash
git lfs install
git clone https://github.com/SKYNETAI1/OpenTPU.git
cd OpenTPU
git lfs pull
```

### Alveo U50

Choose [`GPGPU14`](./GPGPU14), [`tpu2x512`](./tpu2x512), or
[`tpu32x32`](./tpu32x32), read that directory's README, and create the
required CPython 3.12 environment. The following example selects TPU2x512;
substitute another directory name to use that release:

```bash
cd tpu2x512
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
sha256sum -c SHA256SUMS
```

After placing the validated model files in the documented `models` layout,
check the selected profile without programming the card:

```bash
python u50_chat.py --model qwen --check-only
python u50_chat.py --model gemma --check-only
```

Start an interactive session:

```bash
python u50_chat.py \
  --model qwen \
  --interactive \
  --max-new-tokens 32 \
  --max-context 128
```

`--max-new-tokens` is the maximum number of newly generated tokens in one
assistant reply. It is not a prefill limit. Use `/clear` to reset retained
conversation state and `/exit` to quit.

### Ultra96-V2

Follow [`ultra96/README.md`](./ultra96/README.md) for PYNQ deployment, download
the documented Qwen3.5-2B GGUF file, and run the launcher on the board:

```bash
cd /home/xilinx/jupyter_notebooks/qwen35_public
sudo -E /usr/bin/python3 qwen35.py --chat
```

## How Model Files Are Handled

Each release accepts only the model profile and quantization documented in its
own README. A similarly named checkpoint can have different tensor metadata,
quantization blocks, or tokenizer IDs and may not be compatible.

The U50 runtime reads the validated GGUF bytes directly and loads them into
device memory at startup. The Ultra96 runtime stages native GGUF tensor data
for the programmable-logic engine. Neither release requires users to generate
a persistent converted-weight sidecar file.

## Repository Layout

```text
OpenTPU/
|-- README.md       Project overview and release selector
|-- GPGPU14/        GPUTensor14 direct-model Alveo U50 binary release
|-- tpu2x512/       Wide-streaming Alveo U50 binary release
|-- tpu32x32/       Locality-oriented Alveo U50 binary release
|-- U50HLS/         Earlier HLS-based Alveo U50 release
`-- ultra96/        Ultra96-V2 binary release and notebook
```

Each release directory is self-contained and has its own requirements,
download links, board commands, compatibility notes, and integrity checks.

## Compatibility Notes

- U50 runtime extensions require 64-bit Linux on x86-64 with CPython 3.12.
- The current U50 XCLBINs target
  `xilinx_u50_gen3x16_xdma_5_202210_1`; another shell may not program or run.
- Ultra96 runtime extensions require AArch64 CPython 3.10 and the documented
  PYNQ image.
- FPGA images are hardware-specific and are not portable to unrelated boards.
- Only the exact model profiles listed by each release have been validated.
- Current launchers execute one model and one generation stream at a time.

## Distribution and Integrity

The public packages intentionally exclude model weights, private runtime
source, HLS/RTL source, build projects, implementation reports, test fixtures,
and development logs. Published runtime modules are stripped binaries, and
private filesystem paths are removed from release artifacts.

Run the manifest check from inside a release directory after cloning,
transferring, or updating it:

```bash
sha256sum -c SHA256SUMS
```

Binary packaging raises the reverse-engineering barrier but does not guarantee
absolute secrecy. Review each model's license and usage terms before use.
