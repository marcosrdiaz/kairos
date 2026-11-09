"""Cifras a palabras antes del TTS (T1-21, D-043): función pura y determinista."""

import pytest

from app.voice.numbers import integer_to_words, spell_out


@pytest.mark.parametrize(
    ("n", "words"),
    [
        (0, "cero"),
        (1, "uno"),
        (16, "dieciséis"),
        (21, "veintiuno"),
        (22, "veintidós"),
        (30, "treinta"),
        (45, "cuarenta y cinco"),
        (100, "cien"),
        (101, "ciento uno"),
        (470, "cuatrocientos setenta"),
        (500, "quinientos"),
        (999, "novecientos noventa y nueve"),
        (1000, "mil"),
        (1001, "mil uno"),
        (2025, "dos mil veinticinco"),
        (21000, "veintiún mil"),
        (42380, "cuarenta y dos mil trescientos ochenta"),
        (101000, "ciento un mil"),
        (1_000_000, "un millón"),
        (2_500_000, "dos millones quinientos mil"),
        (21_000_000, "veintiún millones"),
        (1_500_000_000, "mil quinientos millones"),
    ],
)
def test_integer_to_words(n: int, words: str) -> None:
    assert integer_to_words(n) == words


@pytest.mark.parametrize(
    ("text", "spoken"),
    [
        # Importes en euros
        ("Te ha restado unos 470 €.", "Te ha restado unos cuatrocientos setenta euros."),
        ("Vale 42.380 euros.", "Vale cuarenta y dos mil trescientos ochenta euros."),
        ("Vale 42 380 €.", "Vale cuarenta y dos mil trescientos ochenta euros."),
        ("Son 1 €.", "Son un euro."),
        ("Son 21 €.", "Son veintiún euros."),
        ("Pagas 12,50 €.", "Pagas doce euros con cincuenta céntimos."),
        ("Pagas 1.234,05 €.", "Pagas mil doscientos treinta y cuatro euros con cinco céntimos."),
        ("Pagas 3,00 €.", "Pagas tres euros."),
        ("Unos 5M€ en total.", "Unos cinco millones de euros en total."),
        ("Unos 1,2 millones de euros.", "Unos un millón doscientos mil euros."),
        ("Ganó 2 mil euros.", "Ganó dos mil euros."),
        ("Entre 300 y 640 €.", "Entre trescientos y seiscientos cuarenta euros."),
        ("Entre 300–640 €.", "Entre trescientos a seiscientos cuarenta euros."),
        ("Bajó −250 €.", "Bajó menos doscientos cincuenta euros."),
        ("Cuesta 15 $.", "Cuesta quince dólares."),
        # Porcentajes y puntos
        ("Pesa un 61 %.", "Pesa un sesenta y uno por ciento."),
        ("Pesa un 61%.", "Pesa un sesenta y uno por ciento."),
        ("Cayó un -3,2 %.", "Cayó un menos tres coma dos por ciento."),
        ("Subió un +1,5 %.", "Subió un más uno coma cinco por ciento."),
        ("Bajó 0,25 puntos.", "Bajó cero coma veinticinco puntos."),
        ("Bajó 0,05 puntos.", "Bajó cero coma cero cinco puntos."),
        ("Subió 21 puntos.", "Subió veintiún puntos."),
        ("Bajó 25 pb.", "Bajó veinticinco puntos básicos."),
        ("Subió 2 pp.", "Subió dos puntos porcentuales."),
        # Género del sustantivo que sigue
        ("Tienes 21 participaciones.", "Tienes veintiuna participaciones."),
        ("Tienes 200 acciones.", "Tienes doscientas acciones."),
        # Fechas y horas
        ("El 5 de junio de 2025.", "El cinco de junio de dos mil veinticinco."),
        ("El 26/02/2025.", "El veintiséis de febrero de dos mil veinticinco."),
        ("El 2025-06-13.", "El trece de junio de dos mil veinticinco."),
        ("A las 18:00.", "A las dieciocho horas."),
        ("A las 9:30.", "A las nueve y treinta."),
        # Lo que no son cifras se queda igual
        ("Sin cifras aquí.", "Sin cifras aquí."),
        ("El índice S&P 500.", "El índice S&P quinientos."),
        ("ISIN IE00B4L5Y983.", "ISIN IE00B4L5Y983."),
        ("La tarea T1-21.", "La tarea T1-21."),
    ],
)
def test_spell_out(text: str, spoken: str) -> None:
    assert spell_out(text) == spoken


def test_spell_out_leaves_no_digits_in_typical_sentence() -> None:
    text = "El 26 de febrero tu cartera bajó entre 310 y 640 € (un −1,4 %), con confianza media."
    spoken = spell_out(text)
    assert not any(ch.isdigit() for ch in spoken)
    assert "trescientos diez y seiscientos cuarenta euros" in spoken
