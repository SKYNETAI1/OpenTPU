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
| [`U50HLS`](./U50HLS) | AMD/Xilinx Alveo U50 | Qwen3.5-9B Q4_K_M; Gemma 4 12B IT Q4_K_S | Linux x86-64, CPython 3.12, XRT | Recommended U50 release |
| [`tpu2x512`](./tpu2x512) | AMD/Xilinx Alveo U50 | Qwen3.5-9B Q4_K_M; Gemma 4 12B IT Q4_K_S | Linux x86-64, CPython 3.12, XRT | Earlier U50 release snapshot |
| [`ultra96`](./ultra96) | Ultra96-V2 | Qwen3.5-2B Q3_K_S | PYNQ 3.0, AArch64, CPython 3.10 | Embedded-board release |

The local HLS development line is published as the binary-only `U50HLS`
release. New Alveo U50 users should start there. The `tpu2x512` directory is
retained so earlier deployments remain reproducible.

## Project Highlights

- Direct use of the validated GGUF model files
- FPGA-side execution of the model datapath
- Interactive and one-shot text generation
- Multi-turn U50 chat with resident FPGA KV/SSM state
- Incremental prefill that processes only newly appended turn tokens
- Prebuilt board images and stripped Python runtime extensions
- SHA-256 manifests for every published launcher, runtime, and FPGA image
- Model weights excluded from Git to keep licensing and distribution explicit

## Current Alveo U50 Release

The recommended [`U50HLS`](./U50HLS) package contains one XCLBIN for both
validated U50 model profiles. It was built with Vitis 2025.2 for the
`xilinx_u50_gen3x16_xdma_5_202210_1` platform and has an implemented DATA clock
of 168 MHz.

The current runtime supports:

- Qwen3.5-9B Q4_K_M
- Gemma 4 12B IT Q4_K_S
- Interactive multi-turn sessions
- Retained conversation state on the FPGA
- Stable delta-prefill accounting across turns
- Resident contexts up to 512 tokens for both published profiles, as verified
  by the runtime HBM-capacity check

### Measured U50 Results

The following single-card measurements use the packaged 168 MHz XCLBIN, a
short greeting prompt, a 128-token context, and one generation stream. TTFT
includes prompt prefill. Decode throughput excludes the first output token.

| Model | Prefill | Generated | TTFT | Decode throughput | Total time |
| --- | ---: | ---: | ---: | ---: | ---: |
| Qwen3.5-9B Q4_K_M | 13 tokens | 9 tokens, EOS | 3.403 s | 3.374 tokens/s | 5.778 s |
| Gemma 4 12B IT Q4_K_S | 10 tokens | 21 tokens, EOS | 3.560 s | 2.255 tokens/s | 12.639 s |

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

Read the model download and platform instructions in
[`U50HLS/README.md`](./U50HLS/README.md), then create the required CPython 3.12
environment:

```bash
cd U50HLS
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
  --max-new-tokens 64 \
  --max-context 512
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
|-- U50HLS/         Current Alveo U50 binary release
|-- tpu2x512/       Earlier Alveo U50 release snapshot
`-- ultra96/        Ultra96-V2 binary release and notebook
```

Each release directory is self-contained and has its own requirements,
download links, board commands, compatibility notes, and integrity checks.

## Compatibility Notes

- U50 runtime extensions require 64-bit Linux on x86-64 with CPython 3.12.
- The current U50 XCLBIN targets
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
