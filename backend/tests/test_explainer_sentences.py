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
        # Abreviaturas
        ("Aprox. 470 euros. Bien.", ["Aprox. 470 euros.", "Bien."]),
        ("Unos 470 euros (aprox.). Bien.", ["Unos 470 euros (aprox.).", "Bien."]),
        ("Iberdrola S.A. sube. Otra.", ["Iberdrola S.A. sube.", "Otra."]),
        ("Bonos, acciones, etc. Tu cartera baja.", ["Bonos, acciones, etc.", "Tu cartera baja."]),
        ("Bonos, acciones, etc. y más cosas.", ["Bonos, acciones, etc. y más cosas."]),
        (
            "Las tecnológicas de EE.UU. han caído. Bien.",
            ["Las tecnológicas de EE.UU. han caído.", "Bien."],
        ),
        ("La Sra. García invierte. Bien.", ["La Sra. García invierte.", "Bien."]),
        # Markdown
        (
            "- **Patrimonio**: 42.380 euros\n- **Semana**: 514 euros",
            ["Patrimonio: 42.380 euros", "Semana: 514 euros"],
        ),
        (
            "Ha bajado 514 euros.\n\n- **NVIDIA**: resta.\n- **BCE**: suma.",
            ["Ha bajado 514 euros.", "NVIDIA: resta.", "BCE: suma."],
        ),
        (
            "Ha bajado 514 euros. 1. Por NVIDIA. 2. Por el BCE.",
            ["Ha bajado 514 euros.", "Por NVIDIA.", "Por el BCE."],
        ),
        ("1. Tu cartera baja. 2. Tu fondo sube.", ["Tu cartera baja.", "Tu fondo sube."]),
        ("## Título\nTexto. Otro.", ["Texto.", "Otro."]),
        ("Tu fondo *MSCI* sube. Bien.", ["Tu fondo MSCI sube.", "Bien."]),
        ("Tu fondo _MSCI_ sube `ya`. Bien.", ["Tu fondo MSCI sube ya.", "Bien."]),
        ("Resumen:\n- Uno baja.\n- Otro sube.", ["Resumen:", "Uno baja.", "Otro sube."]),
        ("Línea uno\n\nLínea dos. Fin.", ["Línea uno", "Línea dos.", "Fin."]),
        ("*Poco.* Unos 90 euros.", ["Poco.", "Unos 90 euros."]),
    ],
)
def test_split(text: str, expected: list[str]) -> None:
    assert split(text) == expected
    splitter = SentenceSplitter()
    by_char = [s for char in text for s in splitter.feed(char)] + splitter.flush()
    assert by_char == expected, "el streaming carácter a carácter debe dar lo mismo"


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
