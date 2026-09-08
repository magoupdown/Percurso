"""Funções determinísticas de teoria musical via music21 (SPEC §5.5, D8).

Sem renderização de imagem na V1: saída em MIDI e MusicXML.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

NOMES_PT = {
    "C": "Dó", "D": "Ré", "E": "Mi", "F": "Fá", "G": "Sol", "A": "Lá", "B": "Si",
}
ACIDENTES_PT = {"#": "♯", "-": "♭", "##": "𝄪", "--": "𝄫"}
MODOS_PT = {"major": "maior", "minor": "menor"}

ESCALAS = {
    "maior": "major",
    "menor_natural": "minor",
    "menor_harmonica": "harmonic_minor",
    "menor_melodica": "melodic_minor",
    "pentatonica_maior": "pentatonic_major",
    "pentatonica_menor": "pentatonic_minor",
    "cromatica": "chromatic",
}


def nome_nota_pt(nome: str) -> str:
    """'C#4' → 'Dó♯4'."""
    m = re.match(r"^([A-Ga-g])([#\-]{0,2})(-?\d+)?$", nome.strip())
    if not m:
        return nome
    letra, acid, oit = m.groups()
    return f"{NOMES_PT[letra.upper()]}{ACIDENTES_PT.get(acid, '')}{oit or ''}"


def tonalidade_pt(nome: str) -> str:
    """'G major' / 'g' / 'e minor' → 'Sol maior' / 'Mi menor'."""
    from music21 import key

    k = key.Key(nome) if not isinstance(nome, key.Key) else nome
    return f"{nome_nota_pt(k.tonic.name)} {MODOS_PT.get(k.mode, k.mode)}"


def notas_escala(tonica: str, tipo: str = "maior", oitava: int = 4) -> List[str]:
    from music21 import pitch, scale

    tipo_m21 = ESCALAS.get(tipo, tipo)
    cls = {
        "major": scale.MajorScale,
        "minor": scale.MinorScale,
        "harmonic_minor": scale.HarmonicMinorScale,
        "melodic_minor": scale.MelodicMinorScale,
        "pentatonic_major": None,
        "pentatonic_minor": None,
        "chromatic": scale.ChromaticScale,
    }.get(tipo_m21)
    base = pitch.Pitch(f"{tonica}{oitava}")
    if tipo_m21 == "pentatonic_major":
        maior = scale.MajorScale(base).getPitches(base, base.transpose("P8"))
        sel = [maior[i] for i in (0, 1, 2, 4, 5)] + [maior[7]]
        return [p.nameWithOctave for p in sel]
    if tipo_m21 == "pentatonic_minor":
        menor = scale.MinorScale(base).getPitches(base, base.transpose("P8"))
        sel = [menor[i] for i in (0, 2, 3, 4, 6)] + [menor[7]]
        return [p.nameWithOctave for p in sel]
    if cls is None:
        raise ValueError(f"Escala desconhecida: {tipo}")
    sc = cls(base)
    return [p.nameWithOctave for p in sc.getPitches(base, base.transpose("P8"))]


def intervalo(nota_a: str, nota_b: str) -> Dict[str, Any]:
    from music21 import interval, note

    i = interval.Interval(note.Note(nota_a), note.Note(nota_b))
    return {"nome": i.name, "nome_completo": i.niceName, "semitons": i.semitones, "direcao": i.direction.name.lower()}


def acorde(notas: List[str]) -> Dict[str, Any]:
    from music21 import chord

    c = chord.Chord(notas)
    return {
        "nome": c.pitchedCommonName,
        "fundamental": c.root().name if c.root() else "",
        "qualidade": c.quality,
        "inversao": c.inversion(),
        "notas": [p.nameWithOctave for p in c.pitches],
    }


def transpor(notas: List[str], intervalo_nome: str) -> List[str]:
    from music21 import pitch

    return [pitch.Pitch(n).transpose(intervalo_nome).nameWithOctave for n in notas]


def graus_romanos(notas_acordes: List[List[str]], tonalidade: str) -> List[str]:
    from music21 import chord, key, roman

    k = key.Key(tonalidade)
    return [roman.romanNumeralFromChord(chord.Chord(n), k).figure for n in notas_acordes]


def detectar_tonalidade_de_notas(notas: List[str]) -> Dict[str, Any]:
    from music21 import note, stream

    s = stream.Stream()
    for n in notas:
        s.append(note.Note(n))
    k = s.analyze("key")
    return {"tonalidade": f"{k.tonic.name} {k.mode}", "tonalidade_pt": tonalidade_pt(k), "confianca": round(float(k.correlationCoefficient), 3)}


def tessitura_ok(notas: List[str], minimo: str, maximo: str) -> List[str]:
    """Notas fora da tessitura [minimo, maximo]. Vazio = tudo dentro."""
    from music21 import pitch

    lo, hi = pitch.Pitch(minimo).midi, pitch.Pitch(maximo).midi
    return [n for n in notas if not (lo <= pitch.Pitch(n).midi <= hi)]


def _stream_de_notas(notas: List[str], duracao: float = 1.0, tonalidade: Optional[str] = None, compasso: str = "4/4"):
    from music21 import key, meter, metadata, note, stream, tempo

    s = stream.Stream()
    s.insert(0, metadata.Metadata(title="Percurso"))
    s.append(tempo.MetronomeMark(number=80))
    s.append(meter.TimeSignature(compasso))
    if tonalidade:
        s.append(key.Key(tonalidade))
    for n in notas:
        nt = note.Note(n)
        nt.quarterLength = duracao
        s.append(nt)
    return s


def gerar_escala_arquivos(tonica: str, tipo: str, oitava: int, destino: Path, nome_base: str) -> Dict[str, str]:
    """Gera <nome_base>.mid e <nome_base>.musicxml. Devolve caminhos."""
    notas = notas_escala(tonica, tipo, oitava)
    subida = notas + list(reversed(notas[:-1]))
    tonal = f"{tonica}" if tipo == "maior" else (f"{tonica.lower()}" if tipo.startswith("menor") else None)
    s = _stream_de_notas(subida, 1.0, tonal)
    return _exportar(s, destino, nome_base)


def gerar_arpejo_arquivos(tonica: str, qualidade: str, oitava: int, destino: Path, nome_base: str) -> Dict[str, str]:
    from music21 import chord as m21chord, pitch

    base = pitch.Pitch(f"{tonica}{oitava}")
    intervalos = {"maior": ["P1", "M3", "P5", "P8"], "menor": ["P1", "m3", "P5", "P8"]}[qualidade]
    notas = [base.transpose(i).nameWithOctave for i in intervalos]
    _ = m21chord.Chord(notas[:3])
    s = _stream_de_notas(notas + list(reversed(notas[:-1])), 1.0)
    return _exportar(s, destino, nome_base)


def gerar_padrao_ritmico_arquivos(figuras: List[float], compasso: str, destino: Path, nome_base: str, nota: str = "C4") -> Dict[str, str]:
    from music21 import meter, metadata, note, stream

    s = stream.Stream()
    s.insert(0, metadata.Metadata(title="Percurso — padrão rítmico"))
    s.append(meter.TimeSignature(compasso))
    for f in figuras:
        n = note.Note(nota)
        n.quarterLength = f
        s.append(n)
    return _exportar(s, destino, nome_base)


def _exportar(s, destino: Path, nome_base: str) -> Dict[str, str]:
    destino.mkdir(parents=True, exist_ok=True)
    midi = destino / f"{nome_base}.mid"
    xml = destino / f"{nome_base}.musicxml"
    s.write("midi", fp=str(midi))
    s.write("musicxml", fp=str(xml))
    return {"midi": str(midi), "musicxml": str(xml)}


def validar_texto_musical(texto: str) -> List[str]:
    """Checagens determinísticas simples em texto gerado (ex.: 'escala de Sol maior tem Fá♯').

    Procura afirmações do tipo 'escala de X maior/menor' e verifica alterações citadas.
    Devolve avisos; vazio = nada a corrigir.
    """
    avisos: List[str] = []
    mapa = {"dó": "C", "do": "C", "ré": "D", "re": "D", "mi": "E", "fá": "F", "fa": "F", "sol": "G", "lá": "A", "la": "A", "si": "B"}
    for m in re.finditer(r"escala de (dó|do|ré|re|mi|fá|fa|sol|lá|la|si)\s*(#|♯|b|♭)?\s*(maior|menor)", texto, flags=re.I):
        nome, acid, modo = m.groups()
        tonica = mapa[nome.lower()] + ({"#": "#", "♯": "#", "b": "-", "♭": "-"}.get(acid, "") if acid else "")
        try:
            notas = notas_escala(tonica, "maior" if modo.lower() == "maior" else "menor_natural")
        except Exception:
            continue
        alteradas = [nome_nota_pt(re.sub(r"\d", "", n)) for n in notas if "#" in n or "-" in n]
        janela = texto[m.end(): m.end() + 160].lower()
        for alt in alteradas:
            base = alt[:-1] if alt[-1] in "♯♭" else alt
            if base.lower() in janela and alt.lower() not in janela:
                avisos.append(f"Na escala de {nome_nota_pt(tonica)} {modo.lower()}, a nota {base} é alterada ({alt}).")
    return avisos
