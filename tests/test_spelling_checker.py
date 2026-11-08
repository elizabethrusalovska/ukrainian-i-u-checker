
"""Автоматичні тести правописного аналізатора."""

from pathlib import Path

import pytest

from spelling_checker import (
    MAX_TEXT_LENGTH,
    analyze_text,
    validate_text,
)


SAMPLES = Path(__file__).resolve().parents[1] / "samples"


def read_sample(filename):
    """Зчитування тексту з файлу."""
    return (SAMPLES / filename).read_text(encoding="utf-8")


def test_samples_exist():
    files = list(SAMPLES.glob("*.txt"))
    assert len(files) >= 3


@pytest.mark.parametrize(
    "filename, status, expected",
    [
        ("01_typical_errors.txt", "review", 5),
        ("02_exceptions.txt", "exception", 5),
        ("03_variants.txt", "variant", 4),
        ("04_mixed_names.txt", "exception", 3),
    ],
)
def test_sample_results(filename, status, expected):
    text = read_sample(filename)
    result = analyze_text(text)

    assert result.counts[status] == expected


def test_typical_corrections():
    text = read_sample("01_typical_errors.txt")
    result = analyze_text(text)

    assert "Іван" in result.suggested_text
    assert "іграшку" in result.suggested_text
    assert "Ірини" in result.suggested_text
    assert "індик" in result.suggested_text
    assert "Іноді" in result.suggested_text


def test_exceptions_unchanged():
    text = read_sample("02_exceptions.txt")
    result = analyze_text(text)

    assert result.suggested_text == text


def test_variants_unchanged():
    text = read_sample("03_variants.txt")
    result = analyze_text(text)

    assert result.counts["variant"] == 4
    assert result.suggested_text == text


def test_proper_names():
    text = read_sample("04_mixed_names.txt")
    result = analyze_text(text)

    statuses = {
        item.word: item.status
        for item in result.findings
    }

    assert statuses["Ин"] == "exception"
    assert statuses["Ий"] == "exception"
    assert statuses["Ич-оба"] == "exception"
    assert statuses["Иван"] == "review"


@pytest.mark.parametrize(
    "text",
    [
        "",
        "   ",
        "Hello, world!",
    ],
)
def test_invalid_input(text):
    with pytest.raises(ValueError):
        validate_text(text)


def test_text_too_long():
    text = "і" * (MAX_TEXT_LENGTH + 1)

    with pytest.raises(ValueError):
        analyze_text(text)


def test_maximum_length():
    text = "і" * MAX_TEXT_LENGTH

    result = analyze_text(text)

    assert result.original_text == text


def test_no_target_words():
    text = "Сонце світить. День прекрасний."
    result = analyze_text(text)

    assert len(result.findings) == 0
    assert result.suggested_text == text


def test_uppercase_correction():
    text = "Иван і ирій."
    result = analyze_text(text)

    assert result.suggested_text == "Іван і ирій."


def test_word_positions():
    text = "Иван побачив индика."
    result = analyze_text(text)

    for item in result.findings:
        assert text[item.start:item.end] == item.word


def test_original_text_preserved():
    text = "Ич! Иван читає."
    result = analyze_text(text)

    assert result.original_text == text
