from __future__ import annotations

from app.utils.token_counter import TokenCounter


def test_count_basic() -> None:
    counter = TokenCounter()
    text = "Hello world"

    assert counter.count(text) == len(counter.get_encoding().encode(text))


def test_count_empty() -> None:
    counter = TokenCounter()

    assert counter.count("") == 0


def test_count_japanese() -> None:
    counter = TokenCounter()
    text = "これは日本語のトークン数を確認するテストです。"

    assert counter.count(text) == len(counter.get_encoding().encode(text))


def test_count_messages() -> None:
    counter = TokenCounter()
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "name": "mizuki", "content": "こんにちは"},
    ]

    expected = 3
    expected += 3 + counter.count("system") + counter.count("You are a helpful assistant.")
    expected += (
        3
        + counter.count("user")
        + counter.count("mizuki")
        + 1
        + counter.count("こんにちは")
    )

    assert counter.count_messages(messages) == expected


def test_truncate() -> None:
    counter = TokenCounter()
    text = "OpenAI develops useful AI systems for many languages."
    max_tokens = 5

    truncated = counter.truncate(text, max_tokens)

    assert counter.count(truncated) <= max_tokens
    assert truncated == counter.get_encoding().decode(
        counter.get_encoding().encode(text)[:max_tokens]
    )
