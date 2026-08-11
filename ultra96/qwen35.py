#!/usr/bin/env python3
"""Public Python API for the Qwen3.5 Ultra96 accelerator."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from _qwen35_runtime import RuntimeSession


PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL = Path(os.environ.get(
    "QWEN35_MODEL",
    str(PACKAGE_DIR / "Qwen3.5-2B-Q3_K_S.gguf"),
))
DEFAULT_TOKENIZER = Path(os.environ.get(
    "QWEN35_TOKENIZER",
    str(PACKAGE_DIR / "tokenizer.json"),
))
DEFAULT_BITSTREAM = PACKAGE_DIR / "qwen35_token.bit"


@dataclass(frozen=True)
class GenerationResult:
    text: str
    input_tokens: int
    output_tokens: int
    prefill_seconds: float
    generation_seconds: float
    tokens_per_second: float
    context_tokens: int
    context_was_cleared: bool


class ChatSession:
    """High-level chat interface for the prebuilt Ultra96 overlay."""

    def __init__(
        self,
        model_path: Path | str = DEFAULT_MODEL,
        tokenizer_path: Path | str = DEFAULT_TOKENIZER,
        bitstream_path: Path | str = DEFAULT_BITSTREAM,
        max_context: int = 256,
        preload_chunk_mib: int = 8,
        seed: int = 1234,
    ) -> None:
        self._runtime = RuntimeSession(
            str(model_path),
            str(bitstream_path),
            str(tokenizer_path),
            max_context,
            preload_chunk_mib,
            seed,
        )

    @property
    def context_tokens(self) -> int:
        return self._runtime.position

    @property
    def model_size_bytes(self) -> int:
        return self._runtime.model_size_bytes

    @property
    def history(self) -> tuple[dict, ...]:
        return tuple(dict(item) for item in self._runtime.history)

    def clear(self) -> None:
        self._runtime.clear()

    def ask(
        self,
        prompt: str,
        max_new_tokens: int = 32,
        temperature: float = 0.0,
        top_p: float = 0.9,
        stream: bool = True,
        on_text: Optional[Callable[[str], None]] = None,
    ) -> GenerationResult:
        def show_prefill(current: int, total: int) -> None:
            if stream:
                print(f"\rPrefill {current}/{total}", end="", flush=True)

        def show_text(piece: str) -> None:
            if stream:
                print(piece, end="", flush=True)
            if on_text is not None:
                on_text(piece)

        if stream:
            print("", end="", flush=True)
        values = self._runtime.ask(
            prompt,
            max_new_tokens,
            temperature,
            top_p,
            show_text,
            show_prefill,
        )
        result = GenerationResult(**values)
        if stream:
            print(
                f"\n[Prefill: {result.input_tokens} tokens in "
                f"{result.prefill_seconds:.1f}s; generation: "
                f"{result.output_tokens} tokens at "
                f"{result.tokens_per_second:.3f} token/s; context: "
                f"{result.context_tokens}]"
            )
        return result

    def close(self) -> None:
        self._runtime.close()

    def __enter__(self) -> "ChatSession":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


def chat_loop(session: ChatSession, max_new_tokens: int = 32,
              temperature: float = 0.0, top_p: float = 0.9) -> None:
    print("Enter /clear to clear history or /exit to quit.")
    while True:
        try:
            prompt = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nChat ended.")
            return
        if prompt.lower() in ("/exit", "exit", "quit"):
            return
        if prompt.lower() == "/clear":
            session.clear()
            print("Conversation history cleared.")
        elif prompt:
            print("Qwen: ", end="", flush=True)
            session.ask(prompt, max_new_tokens, temperature, top_p)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Qwen3.5-2B Q3_K_S on the Ultra96 FPGA overlay")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--tokenizer", type=Path, default=DEFAULT_TOKENIZER)
    parser.add_argument("--bitstream", type=Path, default=DEFAULT_BITSTREAM)
    parser.add_argument("--max-context", type=int, default=256)
    parser.add_argument("--max-tokens", type=int, default=32)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--prompt", default="Hello. Introduce yourself briefly.")
    parser.add_argument("--chat", action="store_true")
    args = parser.parse_args()

    session = ChatSession(
        model_path=args.model,
        tokenizer_path=args.tokenizer,
        bitstream_path=args.bitstream,
        max_context=args.max_context,
        seed=args.seed,
    )
    try:
        if args.chat:
            chat_loop(
                session, args.max_tokens, args.temperature, args.top_p)
        else:
            print("Qwen: ", end="", flush=True)
            session.ask(
                args.prompt,
                args.max_tokens,
                args.temperature,
                args.top_p,
            )
    finally:
        session.close()


if __name__ == "__main__":
    main()
