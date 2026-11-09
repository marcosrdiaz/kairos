"""Partición en frases del streaming del explicador (`agents/sentences.py`)."""

import pytest

from app.agents.sentences import SentenceSplitter, split


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "Ha bajado. Te ha restado unos 470 euros.",
            ["Ha bajado.", "Te ha restado unos 470 euros."],
        ),
        (
            "Las tecnológicas de EE. UU. han caído. Te ha restado 470 euros.",
            ["Las tecnológicas de EE. UU. han caído.", "Te ha restado 470 euros."],
        ),
        (
            "El BCE baja los tipos 0,25 puntos. Poco.",
            ["El BCE baja los tipos 0,25 puntos.", "Poco."],
        ),
        ("Tu cartera vale 1.295 euros. Bien.", ["Tu cartera vale 1.295 euros.", "Bien."]),
        ("Por ejemplo, p. ej. un fondo. Otra.", ["Por ejemplo, p. ej. un fondo.", "Otra."]),
        ("¿Vas bien? Sí. 2040 queda lejos.", ["¿Vas bien?", "Sí.", "2040 queda lejos."]),
        ("Sube… y baja. Fin", ["Sube… y baja.", "Fin"]),
        ("**Poco.** Unos 90 euros.", ["Poco.", "Unos 90 euros."]),
        ("Una frase\ncon salto. Y otra.", ["Una frase con salto.", "Y otra."]),
        ("", []),
    ],
)
def test_split(text: str, expected: list[str]) -> None:
    assert split(text) == expected


def test_streaming_waits_for_the_next_character() -> None:
    splitter = SentenceSplitter()
    assert splitter.feed("Ha bajado.") == []
    assert splitter.feed(" ") == []
    assert splitter.feed("Te") == ["Ha bajado."]
    assert splitter.feed(" ha restado 0,") == []
    assert splitter.feed("25 %. Fin") == ["Te ha restado 0,25 %."]
    assert splitter.flush() == ["Fin"]
    assert splitter.flush() == []


def test_streaming_by_single_characters_matches_whole_text() -> None:
    text = "Las tecnológicas de EE. UU. han caído. Te ha restado 1.295 euros. ¿Y el BCE? Poco."
    splitter = SentenceSplitter()
    sentences = [s for char in text for s in splitter.feed(char)] + splitter.flush()
    assert sentences == split(text)
    assert len(sentences) == 4
