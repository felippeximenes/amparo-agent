"""Leitura e fatiamento das fontes curadas de `docs/sources/`.

Funções puras (sem I/O de rede): `parse_source` separa o cabeçalho YAML do
corpo; `chunk` quebra o corpo por dispositivo (Art. / § / heading), mantendo a
metadata da fonte em cada trecho para a citação obrigatória (regra nº 2 do
CLAUDE.md).
"""

from __future__ import annotations

import re
from pathlib import Path

# Início de um novo trecho: artigo, parágrafo único, heading markdown ou
# divisão estrutural da norma.
_BOUNDARY = re.compile(
    r"^(Art\. \d|Parágrafo único|## |CAPÍTULO|SEÇÃO|SECÃO|TÍTULO|LIVRO|ANEXO)"
)
_MIN_CHUNK = 80  # trechos menores que isto são mesclados no seguinte


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


def chunk(meta: dict[str, str], body: str, arquivo: str) -> list[dict]:
    """Quebra o corpo em trechos, cada um com a metadata da fonte no payload."""
    blocks = [b.strip() for b in body.split("\n\n") if b.strip()]
    groups: list[list[str]] = []
    for block in blocks:
        if block.startswith(">"):  # nota de curadoria, não é texto-fonte
            continue
        if not groups or _BOUNDARY.match(block):
            groups.append([block])
        else:
            groups[-1].append(block)

    texts = ["\n\n".join(g).strip() for g in groups]

    # mescla trechos curtos (headings soltos) no trecho seguinte
    merged: list[str] = []
    carry = ""
    for t in texts:
        t = f"{carry}\n\n{t}".strip() if carry else t
        if len(t) < _MIN_CHUNK:
            carry = t
        else:
            merged.append(t)
            carry = ""
    if carry:
        if merged:
            merged[-1] = f"{merged[-1]}\n\n{carry}"
        else:
            merged.append(carry)

    return [
        {
            "arquivo": arquivo,
            "titulo": meta.get("titulo", ""),
            "fonte": meta.get("fonte", ""),
            "tipo": meta.get("tipo", ""),
            "coletado_em": meta.get("coletado_em", ""),
            "trecho": text.splitlines()[0].lstrip("# ").rstrip(".")[:80],
            "texto": text,
        }
        for text in merged
    ]
