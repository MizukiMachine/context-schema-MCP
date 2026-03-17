from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

import tiktoken


class TokenCounter:
    DEFAULT_ENCODING = "cl100k_base"
    _TOKENS_PER_MESSAGE = 3
    _TOKENS_PER_NAME = 1
    _REPLY_PRIMER_TOKENS = 3
    _CL100K_PAT_STR = (
        r"""'(?i:[sdmt]|ll|ve|re)|[^\r\n\p{L}\p{N}]?+\p{L}++|\p{N}{1,3}+| ?[^\s\p{L}\p{N}]++"""
        r"""[\r\n]*+|\s++$|\s*[\r\n]|\s+(?!\S)|\s"""
    )
    _CL100K_SPECIAL_TOKENS = {
        "<|endoftext|>": 100257,
        "<|fim_prefix|>": 100258,
        "<|fim_middle|>": 100259,
        "<|fim_suffix|>": 100260,
        "<|endofprompt|>": 100276,
    }
    _BUNDLED_VOCAB_PATH = (
        Path(__file__).resolve().parent / "encodings" / "cl100k_base_vocab.go"
    )
    _GO_VOCAB_ENTRY_PATTERN = re.compile(r'^\s*"((?:[^"\\]|\\.)*)":\s+(\d+),$')

    def __init__(self, encoding_name: str = DEFAULT_ENCODING) -> None:
        self._encoding_name = encoding_name
        self._encoding = self._load_encoding(encoding_name)

    def count(self, text: str) -> int:
        if not text:
            return 0

        return len(self._encoding.encode(text))

    def count_messages(self, messages: list[dict[str, Any]]) -> int:
        if not messages:
            return 0

        token_count = self._REPLY_PRIMER_TOKENS

        for message in messages:
            token_count += self._TOKENS_PER_MESSAGE

            for key, value in message.items():
                token_count += self.count(self._stringify_value(value))

                if key == "name":
                    token_count += self._TOKENS_PER_NAME

        return token_count

    def truncate(self, text: str, max_tokens: int) -> str:
        if max_tokens < 0:
            raise ValueError("max_tokens must be greater than or equal to 0")

        if not text or max_tokens == 0:
            return ""

        encoded = self._encoding.encode(text)
        if len(encoded) <= max_tokens:
            return text

        return self._encoding.decode(encoded[:max_tokens])

    def get_encoding(self) -> tiktoken.Encoding:
        return self._encoding

    @classmethod
    def _load_encoding(cls, encoding_name: str) -> tiktoken.Encoding:
        try:
            return tiktoken.get_encoding(encoding_name)
        except Exception:
            if encoding_name != cls.DEFAULT_ENCODING:
                raise

            mergeable_ranks: dict[bytes, int] = {}
            with cls._BUNDLED_VOCAB_PATH.open(encoding="utf-8") as file:
                for line in file:
                    match = cls._GO_VOCAB_ENTRY_PATTERN.match(line)
                    if not match:
                        continue

                    token_literal, rank = match.groups()
                    mergeable_ranks[cls._decode_go_string_literal(token_literal)] = int(rank)

            return tiktoken.Encoding(
                name=cls.DEFAULT_ENCODING,
                pat_str=cls._CL100K_PAT_STR,
                mergeable_ranks=mergeable_ranks,
                special_tokens=cls._CL100K_SPECIAL_TOKENS,
            )

    @staticmethod
    def _decode_go_string_literal(token_literal: str) -> bytes:
        decoded = bytearray()
        index = 0

        while index < len(token_literal):
            current = token_literal[index]
            if current != "\\":
                decoded.extend(current.encode("utf-8"))
                index += 1
                continue

            index += 1
            escape = token_literal[index]

            if escape == "a":
                decoded.append(0x07)
            elif escape == "b":
                decoded.append(0x08)
            elif escape == "f":
                decoded.append(0x0C)
            elif escape == "n":
                decoded.append(0x0A)
            elif escape == "r":
                decoded.append(0x0D)
            elif escape == "t":
                decoded.append(0x09)
            elif escape == "v":
                decoded.append(0x0B)
            elif escape in {'\\', '"', "'"}:
                decoded.extend(escape.encode("ascii"))
            elif escape == "x":
                decoded.append(int(token_literal[index + 1 : index + 3], 16))
                index += 2
            elif escape == "u":
                decoded.extend(chr(int(token_literal[index + 1 : index + 5], 16)).encode("utf-8"))
                index += 4
            elif escape == "U":
                decoded.extend(
                    chr(int(token_literal[index + 1 : index + 9], 16)).encode("utf-8")
                )
                index += 8
            else:
                decoded.append(int(token_literal[index : index + 3], 8))
                index += 2

            index += 1

        return bytes(decoded)

    @staticmethod
    def _stringify_value(value: Any) -> str:
        if value is None:
            return ""

        if isinstance(value, str):
            return value

        if isinstance(value, (bool, int, float)):
            return str(value)

        return json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
