# Fontes curadas (RAG)

Cada arquivo aqui representa uma fonte oficial curada manualmente sobre
BPC/LOAS — nunca um crawl automático. Precisão importa mais que cobertura
neste domínio.

Cabeçalho obrigatório em cada arquivo:

```
---
titulo: <nome completo da norma ou manual>
fonte: <URL ou referência oficial>
tipo: lei | decreto | instrucao_normativa | portaria | manual
tag: <rótulo curto — 2 a 6 palavras — prefixado em cada trecho na ingestão>
coletado_em: <YYYY-MM-DD>
---
```

Toda coleta desta rodada foi feita a partir de fontes primárias (texto
compilado no `planalto.gov.br`, PDFs oficiais do INSS/MDS e páginas de serviço
do `gov.br`). O levantamento e a análise de vigência estão em
[`../research/bpc-loas-fontes-oficiais.md`](../research/bpc-loas-fontes-oficiais.md).

## Índice de fontes (Fase 1)

| # | Arquivo | tipo | Recorte |
|---|---------|------|---------|
| 01 | `01-constituicao-1988-arts-203-204.md` | lei | CF/1988, arts. 203–204 |
| 02 | `02-lei-8742-1993-loas-bpc.md` | lei | LOAS, arts. 20 a 21-B (texto compilado) |
| 03 | `03-lei-13146-2015-lbi.md` | lei | LBI, arts. 2º, 40 e 105 |
| 04 | `04-lei-14176-2021.md` | lei | critério de renda (1/4 SM) e art. 20-B |
| 05 | `05-lei-13982-2020.md` | lei | art. 20 da LOAS, §§ 14 e 15 |
| 06 | `06-lei-10741-2003-estatuto-pessoa-idosa.md` | lei | arts. 33 e 34 (BPC ao idoso 65+) |
| 07 | `07-lei-15077-2024.md` | lei | biometria, prazo do CadÚnico, alterações na LOAS |
| 08 | `08-decreto-6214-2007-regulamento-bpc.md` | decreto | Regulamento do BPC (recorte) |
| 09 | `09-decreto-12534-2025.md` | decreto | Bolsa Família na renda / média 12 meses (contestado) |
| 10 | `10-decreto-11016-2022-cadunico.md` | decreto | Regulamento do CadÚnico |
| 11 | `11-in-pres-inss-128-2022-bpc.md` | instrucao_normativa | dispositivos da IN que citam o BPC (recorte temático) |
| 12 | `12-portaria-conjunta-mds-inss-34-2025.md` | portaria | ato operacional consolidado atual do BPC |
| 13 | `13-portaria-conjunta-mds-inss-2-2015.md` | portaria | instrumento de avaliação biopsicossocial (arts. 1º–13) |
| 14 | `14-carta-servicos-bpc-idoso.md` | manual | Carta de Serviços gov.br — BPC ao idoso |
| 15 | `15-carta-servicos-bpc-pcd.md` | manual | Carta de Serviços gov.br — BPC à PcD |

### Pendências de coleta

- **Portaria Conjunta MDS/MPS/INSS nº 33/2025** (reavaliação biopsicossocial,
  art. 21 da LOAS): não foi localizada URL oficial com o texto integral
  (DOU de 07/08/2025, Seção 1). Coletar manualmente antes de incluir.
- **Página MDS "BPC" e página INSS "Saiba mais"**: bloqueadas a acesso
  automatizado; opcionais, coletar em navegador se quisermos reforço da visão
  SUAS/CRAS.
