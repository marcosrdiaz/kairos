"""Partición en frases del texto que llega en streaming (validación frase a frase, D-010).

Una frase acaba en `.`, `!`, `?` o `…` (con un cierre opcional: `*`, `»`, `)`…) seguido de espacio
y de algo que empieza frase (mayúscula, dígito, `¿`, `¡`, comillas, viñeta). También acaba en un
salto de línea seguido de una línea en blanco, una viñeta, un número de lista o un encabezado.
No cortan: los decimales y miles ("0,25", "1.295", sin espacio detrás), las abreviaturas
("EE. UU.", "p. ej.", "S.A.", "aprox.") ni un punto seguido de minúscula ("etc. y más").
Mientras no llega el carácter siguiente, la frase se queda en el búfer: se decide con él.

Cada frase se limpia de Markdown línea a línea (viñetas, números de lista, encabezados, negrita,
cursiva, código) y se descarta si no tiene letras ("1.").
"""

import re

_END = re.compile(r"[.!?…]+[*_»\"”')]*(?=\s)")
_LIST_ITEM = r"(?:[-*•]|\d{1,2}[.)])\s"
_LINE_BREAK = re.compile(rf"\n(?=[ \t]*(?:\n|{_LIST_ITEM}|#))")
_ABBREVIATION = re.compile(
    r"(?:\b(?:ee\.\s?uu|s\.\s?a|s\.\s?l|p\.\s?ej|ee|uu|p|ej|sr|sra|srta|dr|dra|num|núm|pag|pág"
    r"|aprox))$",
    re.IGNORECASE,
)
_HEADING = re.compile(r"(?m)^[ \t]*#[^\n]*\n")
_STARTERS = "¿¡«\"'(“-*•#"
_LINE_MARKERS = re.compile(rf"^\s*{_LIST_ITEM}\s*")
_EMPHASIS = re.compile(r"(?<!\w)[*_](?=\S)(.+?)(?<=\S)[*_](?!\w)")
_LETTER = re.compile(r"[^\W\d_]")


def _clean(text: str) -> str:
    """Quita el Markdown de cada línea (los encabezados, enteros) y une las líneas."""
    lines = [
        _LINE_MARKERS.sub("", line)
        for line in text.split("\n")
        if not line.lstrip().startswith("#")
    ]
    joined = " ".join(" ".join(lines).split())
    joined = _EMPHASIS.sub(r"\1", joined.replace("**", "").replace("__", "").replace("`", ""))
    return joined.strip(" *_") if _LETTER.search(joined) else ""


def _starts_sentence(char: str) -> bool:
    return char.isupper() or char.isdigit() or char in _STARTERS


def _is_abbreviation(text: str) -> bool:
    return bool(_ABBREVIATION.search(text))


class SentenceSplitter:
    def __init__(self) -> None:
        self._buffer = ""

    def _boundaries(self) -> list[tuple[int, int, bool]]:
        """(inicio, fin, si es fin de frase por puntuación) de cada posible corte, en orden."""
        found = [(m.start(), m.end(), True) for m in _END.finditer(self._buffer)]
        found += [(m.start(), m.end(), False) for m in _LINE_BREAK.finditer(self._buffer)]
        found += [(m.end() - 1, m.end(), False) for m in _HEADING.finditer(self._buffer)]
        return sorted(found)

    def feed(self, chunk: str) -> list[str]:
        """Añade texto y devuelve las frases que ya se pueden cerrar."""
        self._buffer += chunk
        sentences: list[str] = []
        start = 0
        for begin, end, punctuation in self._boundaries():
            if begin < start:
                continue
            rest = self._buffer[end:].lstrip(" \t\n")
            if not rest:
                break  # falta el carácter que decide
            if punctuation:
                if not _starts_sentence(rest[0]):
                    continue
                if self._buffer[begin] == "." and _is_abbreviation(self._buffer[start:begin]):
                    continue
            sentence = _clean(self._buffer[start:end])
            if sentence:
                sentences.append(sentence)
            start = end
        self._buffer = self._buffer[start:]
        return sentences

    def flush(self) -> list[str]:
        """Lo que queda al acabar el texto, como última frase."""
        sentence = _clean(self._buffer)
        self._buffer = ""
        return [sentence] if sentence else []


def split(text: str) -> list[str]:
    splitter = SentenceSplitter()
    return [*splitter.feed(text), *splitter.flush()]
