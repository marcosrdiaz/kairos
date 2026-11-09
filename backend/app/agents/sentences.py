"""Partición en frases del texto que llega en streaming (validación frase a frase, D-010).

Una frase acaba en `.`, `!`, `?` o `…` seguido de espacio y de algo que empieza frase (mayúscula,
dígito, `¿`, `¡`, comillas). No cortan: los decimales y miles ("0,25", "1.295", sin espacio
detrás), las abreviaturas ("EE. UU.", "p. ej.", "Sr.") ni un punto seguido de minúscula.
Mientras no llega el carácter siguiente, la frase se queda en el búfer: se decide con él.
"""

import re

_END = re.compile(r"[.!?…]+(?=\s)")
_ABBREVIATIONS = frozenset({"ee", "uu", "p", "ej", "sr", "sra", "srta", "dr", "dra", "núm", "pág"})
_STARTERS = "¿¡«\"'(“"
_MARKDOWN = re.compile(r"\*\*|__|^#+\s*|^[-•]\s+")


def _clean(text: str) -> str:
    return _MARKDOWN.sub("", " ".join(text.split())).strip()


def _starts_sentence(char: str) -> bool:
    return char.isupper() or char.isdigit() or char in _STARTERS


def _is_abbreviation(text: str, end: int) -> bool:
    words = re.findall(r"[^\W\d_]+$", text[:end])
    return bool(words) and words[-1].lower() in _ABBREVIATIONS


class SentenceSplitter:
    def __init__(self) -> None:
        self._buffer = ""

    def feed(self, chunk: str) -> list[str]:
        """Añade texto y devuelve las frases que ya se pueden cerrar."""
        self._buffer = (self._buffer + chunk).replace("**", "")
        sentences: list[str] = []
        start = 0
        for match in _END.finditer(self._buffer):
            if match.start() < start:
                continue
            rest = self._buffer[match.end() :].lstrip()
            if not rest:
                break  # falta el carácter que decide
            if not _starts_sentence(rest[0]):
                continue
            if match.group() == "." and _is_abbreviation(self._buffer, match.start()):
                continue
            sentence = _clean(self._buffer[start : match.end()])
            if sentence:
                sentences.append(sentence)
            start = match.end()
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
