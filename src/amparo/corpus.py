"""Leitura e fatiamento das fontes curadas de `docs/sources/`.

Funções puras (sem I/O de rede): `parse_source` separa o cabeçalho YAML do
corpo; `chunk` quebra o corpo em trechos pequenos (um dispositivo ou parte de
um), cada um com a metadata da fonte no payload para a citação obrigatória
(regra nº 2 do CLAUDE.md).

Os trechos são limitados a ~`_MAX_CHARS` caracteres porque os modelos de
embedding multilíngues leves truncam em ~128 tokens — um trecho maior que isso
seria só parcialmente vetorizado.
"""

from __future__ import annotations

import re
from pathlib import Path

# Início de um novo dispositivo / divisão estrutural da norma.
_BOUNDARY = re.compile(
    r"^(Art\. \d|Parágrafo único|## |CAPÍTULO|SEÇÃO|SECÃO|TÍTULO|LIVRO|ANEXO)"
)
_MAX_CHARS = 500  # ~128 tokens do modelo de embedding
_MIN_CHARS = 80   # abaixo disto, funde no trecho seguinte


def parse_source(path: str | Path) -> tuple[dict[str, str], str]:
    """Retorna (metadata do cabeçalho, corpo em texto)."""
    text = Path(path).read_text(encoding="utf-8").replace("\r\n", "\n")
    if not text.startswith("---"):
        raise ValueError(f"{path}: sem cabeçalho YAML")
    _, front_matter, body = text.split("---\n", 2)
    meta = {}
    for line in front_matter.splitlines():
        if ": " in line:
            key, value = line.split(": ", 1)
            meta[key.strip()] = value.strip()
    return meta, body.strip()


def _split_block(block: str) -> list[str]:
    """Quebra um bloco grande em pedaços <= _MAX_CHARS, nos limites de frase."""
    if len(block) <= _MAX_CHARS:
        return [block]
    pieces, cur = [], ""
    for sentence in re.split(r"(?<=[.;:])\s+", block):
        if cur and len(cur) + len(sentence) + 1 > _MAX_CHARS:
            pieces.append(cur)
            cur = sentence
        else:
            cur = f"{cur} {sentence}".strip()
    if cur:
        pieces.append(cur)
    return pieces


def chunk(meta: dict[str, str], body: str, arquivo: str) -> list[dict]:
    """Quebra o corpo em trechos curtos, cada um com a metadata da fonte."""
    blocks = [
        b.strip()
        for b in body.split("\n\n")
        if b.strip() and not b.lstrip().startswith(">")  # ignora nota de curadoria
    ]

    texts: list[str] = []
    buf = ""
    label = ""  # "Art. 20", "O que é?", ... — repetido nos sub-trechos do dispositivo

    def flush() -> None:
        nonlocal buf
        t = buf.strip()
        if t:
            if label and not t.startswith(label):
                t = f"{label} — {t}"
            texts.append(t)
        buf = ""

    for block in blocks:
        if _BOUNDARY.match(block):
            if len(buf) >= _MIN_CHARS:
                flush()
            m = re.match(r"(Art\. \d+(?:-[A-Z])?|Parágrafo único)", block)
            label = m.group(1) if m else block.lstrip("# ").split("\n", 1)[0][:48].strip()

        for piece in _split_block(block):
            if buf and len(buf) + len(piece) + 2 > _MAX_CHARS:
                flush()
            buf = f"{buf}\n\n{piece}".strip() if buf else piece
    flush()

    return [
        {
            "arquivo": arquivo,
            "titulo": meta.get("titulo", ""),
            "fonte": meta.get("fonte", ""),
            "tipo": meta.get("tipo", ""),
            "coletado_em": meta.get("coletado_em", ""),
            "trecho": t.splitlines()[0][:80],
            "texto": t,
        }
        for t in texts
    ]
