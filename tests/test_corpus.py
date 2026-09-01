from amparo.corpus import chunk, parse_source

SAMPLE = """---
titulo: Lei Teste
fonte: https://exemplo.gov.br/lei
tipo: lei
tag: Lei Teste
coletado_em: 2026-08-31
---

> Curadoria: esta nota não deve entrar em nenhum trecho.

Art. 1º Primeiro artigo do exemplo, com texto suficientemente longo para
não ser mesclado com o trecho seguinte pela regra de tamanho mínimo.

§ 1º Parágrafo que pertence ao primeiro artigo.

Art. 2º Segundo artigo, também com corpo longo o bastante para figurar
como um trecho próprio na saída da função de chunk.
"""


def test_parse_source(tmp_path):
    p = tmp_path / "x.md"
    p.write_text(SAMPLE, encoding="utf-8")
    meta, body = parse_source(p)
    assert meta["titulo"] == "Lei Teste"
    assert meta["fonte"] == "https://exemplo.gov.br/lei"
    assert meta["tipo"] == "lei"
    assert meta["tag"] == "Lei Teste"
    assert body.startswith(">")  # nota ainda no corpo; filtrada só no chunk


def test_chunk_por_dispositivo(tmp_path):
    p = tmp_path / "x.md"
    p.write_text(SAMPLE, encoding="utf-8")
    meta, body = parse_source(p)
    chunks = chunk(meta, body, arquivo="x.md")

    assert len(chunks) == 2
    assert chunks[0]["trecho"].startswith("Art. 1")
    assert chunks[1]["trecho"].startswith("Art. 2")
    assert "§ 1º" in chunks[0]["texto"]
    assert all(c["texto"].startswith("[Lei Teste] ") for c in chunks)
    assert all(c["fonte"] == "https://exemplo.gov.br/lei" for c in chunks)
    assert all(c["arquivo"] == "x.md" for c in chunks)
    assert all("Curadoria" not in c["texto"] for c in chunks)
    assert all(len(c["texto"]) <= 700 for c in chunks)
