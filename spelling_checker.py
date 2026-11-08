
"""Перевірка вживання І / И на початку українських слів."""

from __future__ import annotations

import re
from dataclasses import dataclass

MAX_TEXT_LENGTH = 5000

UKRAINIAN_LETTERS = r"А-Яа-яҐґЄєІіЇї"

WORD_RE = re.compile(
    rf"(?<![{UKRAINIAN_LETTERS}’'ʼ-])"
    rf"[{UKRAINIAN_LETTERS}]+(?:[-’'ʼ][{UKRAINIAN_LETTERS}]+)*"
)

UKRAINIAN_RE = re.compile(rf"[{UKRAINIAN_LETTERS}]")


VARIANT_ENDINGS = {
    "рій", "рію", "рієм", "рії", "рієві",
    "ріям", "ріями", "ріях",
    "род", "рода", "родові", "роду",
    "родом", "роді", "роди", "родів",
    "родам", "родами", "родах",
}


YKAT_FORMS = {
    "икати", "икаю", "икаєш", "икає",
    "икаємо", "икаєте", "икають",
    "икав", "икала", "икало", "икали",
    "икатиму", "икатимеш", "икатиме",
    "икатимемо", "икатимете", "икатимуть",
    "икай", "икайте", "икаючи",
    "икання", "иканням", "иканню",
    "иканні", "иканнями",
}

EXCEPTION_WORDS = {
    "ич", "ийбен", "ир", "ич-оба"
} | YKAT_FORMS


STATUS_LABELS = {
    "normal": "Норма",
    "exception": "Виняток",
    "variant": "Варіант",
    "review": "Перевірити",
}


@dataclass(frozen=True)
class Finding:
    """Інформація про знайдене слово."""

    word: str
    start: int
    end: int
    status: str
    suggestion: str
    explanation: str

    @property
    def label(self) -> str:
        return STATUS_LABELS[self.status]


@dataclass(frozen=True)
class AnalysisResult:
    """Загальний результат перевірки тексту."""

    original_text: str
    findings: list[Finding]
    suggested_text: str
    total_words: int

    @property
    def counts(self) -> dict[str, int]:
        return {
            status: sum(
                f.status == status for f in self.findings
            )
            for status in STATUS_LABELS
        }


def validate_text(text: str) -> None:
    """Перевірка правильності вхідних даних."""

    if not isinstance(text, str) or not text.strip():
        raise ValueError(
            "Введіть текст українською мовою, "
            "перш ніж натискати «Перевірити»."
        )

    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError(
            f"Текст завеликий: {len(text)} символів. "
            f"Максимум — {MAX_TEXT_LENGTH}."
        )

    if not UKRAINIAN_RE.search(text):
        raise ValueError(
            "Не знайдено української кирилиці. "
            "Введіть текст українською мовою."
        )


def _proper_name_exception(
    word: str, prefix: str
) -> bool:
    """Перевірка окремих іншомовних власних назв."""

    left = prefix.casefold()

    if word.casefold() == "ин":
        return bool(
            re.search(
                r"\b(?:пак|кім)\s+чен\s+$", left
            )
        )

    if word.casefold() == "ий":
        return bool(
            re.search(r"\bкім\s+$", left)
        )

    return False


def _classify(
    word: str, preceding_text: str
) -> tuple[str, str, str]:
    """Визначення статусу слова."""

    lower = word.casefold()

    if lower[1:] in VARIANT_ENDINGS:
        return (
            "variant",
            "—",
            "§ 2, п. 2: слова «ірій / ирій» "
            "та «ірод / ирод» мають варіантні "
            "написання (залежно від значення).",
        )

    if lower[0] == "і":
        return (
            "normal",
            "—",
            "§ 2, п. 1: на початку українських "
            "слів зазвичай пишемо «і».",
        )

    if lower in EXCEPTION_WORDS:
        rule = (
            "§ 2, п. 4"
            if lower in {"ийбен", "ир", "ич-оба"}
            else "§ 2, п. 3"
        )

        return (
            "exception",
            "—",
            f"{rule}: нормативне написання "
            "з початковою «и».",
        )

    if _proper_name_exception(
        word, preceding_text
    ):
        return (
            "exception",
            "—",
            "§ 2, п. 4: допустима початкова "
            "«И» в іншомовній власній назві.",
        )

    suggestion = (
        ("І" if word[0].isupper() else "і")
        + word[1:]
    )

    return (
        "review",
        suggestion,
        "§ 2, п. 1: зазвичай пишемо «і». "
        "Перевірте запропоноване виправлення "
        "за словником, особливо власні назви.",
    )


def analyze_text(text: str) -> AnalysisResult:
    """Аналіз українського тексту."""

    validate_text(text)

    tokens = list(WORD_RE.finditer(text))

    findings: list[Finding] = []
    replacements: list[tuple[int, int, str]] = []

    for match in tokens:
        word = match.group()

        # Пропускаємо слова, що не починаються на І/И
        if word[0].casefold() not in {"і", "и"}:
            continue

        status, suggestion, explanation = _classify(
            word, text[:match.start()]
        )

        findings.append(
            Finding(
                word,
                match.start(),
                match.end(),
                status,
                suggestion,
                explanation,
            )
        )

        if status == "review":
            replacements.append(
                (match.start(), match.end(), suggestion)
            )

    # Формування тексту із запропонованими змінами
    suggested_text = text

    for start, end, new_word in reversed(replacements):
        suggested_text = (
            suggested_text[:start]
            + new_word
            + suggested_text[end:]
        )

    return AnalysisResult(
        text,
        findings,
        suggested_text,
        total_words=len(tokens),
    )
