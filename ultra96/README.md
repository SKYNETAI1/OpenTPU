# Qwen3.5-2B on Ultra96

This package runs `Qwen3.5-2B-Q3_K_S.gguf` directly on an Ultra96-V2 board.
Quantized matrix weights remain in the original GGUF representation and are
decoded by the programmable-logic engine. The ARM handles the tokenizer,
session control, and final token sampling.

The public Python module is intentionally a small API. The optimized runtime
is distributed as an AArch64 CPython 3.10 binary, and the FPGA implementation
is distributed as an Ultra96 overlay.

## Requirements

- Ultra96-V2 with the PYNQ 3.0 image
- Python 3.10 on AArch64
- `numpy`, `pynq`, and `tokenizers`
- `Qwen3.5-2B-Q3_K_S.gguf`, downloaded separately
- The included `tokenizer.json`

The GGUF model is not stored in this repository. Download it from:

<https://huggingface.co/unsloth/Qwen3.5-2B-GGUF/resolve/main/Qwen3.5-2B-Q3_K_S.gguf?download=true>

Place it in the same `ultra96` directory as `qwen35.py`:

```bash
cd ultra96
wget -O Qwen3.5-2B-Q3_K_S.gguf \
  'https://huggingface.co/unsloth/Qwen3.5-2B-GGUF/resolve/main/Qwen3.5-2B-Q3_K_S.gguf?download=true'
```

## Board setup

Copy or clone this directory to the board, then download the GGUF as shown
above:

```bash
cd /home/xilinx/jupyter_notebooks/qwen35_public
sudo -E /usr/bin/python3 qwen35.py --chat
```

Enter `/clear` to clear the conversation or `/exit` to stop.

## Python API

```python
from qwen35 import ChatSession

session = ChatSession(
    model_path="Qwen3.5-2B-Q3_K_S.gguf",
    tokenizer_path="tokenizer.json",
)
result = session.ask("What is 2 to the power of 3?", max_new_tokens=32)
print(result.tokens_per_second)
session.close()
```

Only `qwen35_token.bit` is portable as-is to an Ultra96-V2. A build for
another Zynq UltraScale+ device requires a compatible overlay/runtime release.

## Repository contents

- `qwen35.py`: public high-level Python API and command-line interface
- `_qwen35_*.so`: AArch64 runtime binaries for CPython 3.10
- `qwen35_token.bit`: Ultra96-V2 FPGA configuration
- `qwen35_token.hwh`: PYNQ overlay metadata
- `Qwen3.5_Ultra96_Chat.ipynb`: interactive notebook
- `Qwen3.5-2B-Q3_K_S.gguf`: downloaded model; intentionally ignored by Git
- `tokenizer.json`: local tokenizer definition

All runtime files, including the downloaded GGUF, intentionally live in the
same directory.

The HLS sources, generated RTL, Vivado project, and private runtime sources are
not part of this repository.
