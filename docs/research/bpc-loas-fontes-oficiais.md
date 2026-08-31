# BPC/LOAS — Fontes oficiais primárias para o corpus RAG (projeto Amparo)

**O que é este documento.** Levantamento curado de fontes oficiais primárias sobre o
Benefício de Prestação Continuada da Assistência Social (BPC/LOAS), destinado a alimentar
uma etapa de validação humana antes de qualquer ingestão em `docs/sources/`.
**Data da pesquisa:** 2026-08-31.
**Método:** priorizados os textos consolidados/compilados no `planalto.gov.br`, os atos
infralegais no `in.gov.br`/`gov.br/inss` e as páginas de orientação em
`gov.br` / `gov.br/inss` / `gov.br/mds`. Todas as URLs abaixo foram testadas em 2026-08-31
(ver seção 4 para o status de cada uma).

> **Aviso de verificação.** As URLs de `planalto.gov.br`, `in.gov.br` e os PDFs de
> `mds.gov.br` retornaram HTTP 200 e o conteúdo foi inspecionado. As páginas de portal
> `gov.br/inss/pt-br/saiba-mais/...` e `gov.br/mds/pt-br/acoes-e-programas/...` respondem
> com "Conteúdo Restrito" a clientes automatizados (anti-bot), mas são públicas em
> navegador normal — a existência e o endereço foram confirmados por busca. Sinalizado
> caso a caso.

---

## 1. Panorama jurídico (o que está vigente em 2026)

- **Base constitucional:** CF/1988, art. 203, V e art. 204 — garantia de 1 salário mínimo
  a pessoa idosa e a pessoa com deficiência sem meios de subsistência.
- **Critério de renda hoje:** LOAS, art. 20, §3º = renda familiar mensal *per capita*
  **igual ou inferior a 1/4 do salário mínimo** (redação da **Lei 14.176/2021**).
  O art. 20, §11-A (também da Lei 14.176/2021) autoriza o regulamento a **ampliar o limite
  até 1/2 salário mínimo**, aplicando os elementos do **art. 20-B** (grau da deficiência,
  dependência de terceiros, comprometimento do orçamento familiar com gastos médicos,
  fraldas, alimentos especiais e medicamentos fora do SUS). A ampliação opera por
  **descontos/escalas graduais** definidos no regulamento (Decreto 6.214/2007) e nos
  valores médios do **Anexo I da Portaria Conjunta MDS/INSS nº 34/2025**.
- **Histórico do limite de renda (relevante para o corpus, mas não vigente):**
  - **Lei 13.981/2020** fixou o limite em **1/2 salário mínimo** — **nunca produziu
    efeitos**: suspensa por liminar do STF (ADI 6.357 / ADPF 662) e superada pela
    Lei 13.982/2020 e pela Lei 14.176/2021.
  - **Lei 13.982/2020** (contexto COVID) fixou 1/4 do SM até 31/12/2020, previu ampliação
    transitória a 1/2 SM e **incluiu os §§14 e 15** no art. 20 (BPC/benefício previdenciário
    de até 1 SM de outro idoso/PcD não conta na renda; BPC devido a mais de um membro da
    família). Os §§14 e 15 continuam vigentes.
  - STF, **RE 567.985 e Rcl 4.374 (2013)** e **RE 580.963 (Tema 27)**: declararam a
    inconstitucionalidade *sem pronúncia de nulidade* do critério de 1/4 e admitiram outros
    meios de prova da miserabilidade — hoje positivado no art. 20, §11.
- **Composição da renda — mudança recente e contestada:** **Decreto 12.534/2025**
  (25/06/2025) alterou o Regulamento (Decreto 6.214/2007) para (i) **incluir o Bolsa Família
  no cálculo da renda familiar *per capita*** e (ii) usar a **média da renda dos 12 meses**
  registrada no CadÚnico. Está **em vigor em 2026**, mas há decisões judiciais federais
  questionando extrapolação do poder regulamentar (ex.: notícia TRF3). Sinalizado como
  ponto sensível.
- **Valor do benefício:** 1 salário mínimo mensal; **não gera 13º**, **não deixa pensão por
  morte**, é intransferível e, em regra, não acumulável com outro benefício da seguridade
  social (LOAS, art. 20, §4º — ressalvados assistência médica, pensão especial indenizatória
  e as transferências de renda do art. 6º, parágrafo único, e art. 203, VI, da CF, incluídas
  pela Lei 14.601/2023).
- **CadÚnico e CPF:** obrigatórios para concessão, manutenção e revisão (LOAS, art. 20, §12,
  e art. 21-B; regulamentados pelo Decreto 6.214/2007 e pelo Decreto 11.016/2022). Prazo de
  atualização do CadÚnico reduzido para **24 meses** pela **Lei 15.077/2024**.
- **Revisão bienal:** LOAS, art. 21 (revisão a cada 2 anos) + Decreto 6.214/2007, art. 42.
  A **Lei 15.157/2025** dispensou a **perícia médica periódica** quando o impedimento for
  permanente, irreversível ou irrecuperável (salvo suspeita fundada de fraude/erro).
- **Avaliação da deficiência:** avaliação **biopsicossocial** (médica + social), baseada na
  CIF, feita por perito médico e assistente social do INSS — LOAS, art. 20, §§2º e 6º;
  Lei 13.146/2015 (LBI), art. 2º; instrumento da **Portaria Conjunta MDS/INSS nº 2/2015**;
  reavaliação regida pela **Portaria Conjunta MDS/MPS/INSS nº 33/2025**.
- **Ato operacional consolidado atual:** **Portaria Conjunta MDS/INSS nº 34/2025**
  (09/10/2025) — regras e procedimentos de requerimento, concessão, manutenção e revisão do
  BPC; **revogou a Portaria Conjunta MDS/INSS nº 3/2018** e as portarias conjuntas
  nº 7/2020, 14/2021, 18/2021, 22/2022 e 28/2024.
- **IN consolidada do INSS:** **IN PRES/INSS nº 128/2022** segue como a instrução normativa
  consolidada em 2026 (texto compilado, última alteração 12/08/2026); alterada, entre outras,
  pela **IN PRES/INSS nº 188/2025**.

---

## 2. Lista proposta de fontes (20 entradas)

Legenda de `tipo`: `lei` | `decreto` | `instrucao_normativa` | `manual`.
Portarias Conjuntas foram classificadas como `instrucao_normativa` (ato normativo infralegal);
ver nota na seção 3.

### A. Leis (Planalto — texto compilado/consolidado)

| # | titulo | fonte | tipo | cobertura | vigência |
|---|--------|-------|------|-----------|----------|
| 1 | **Constituição da República Federativa do Brasil de 1988 — arts. 203 e 204** | https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm | lei | Fundamento constitucional do BPC (art. 203, V) e das diretrizes da assistência social (art. 204). Base para interpretação de todo o restante do corpus. | Vigente. |
| 2 | **Lei nº 8.742, de 7 de dezembro de 1993 — Lei Orgânica da Assistência Social (LOAS)** | https://www.planalto.gov.br/ccivil_03/leis/l8742.htm (compilado: http://www.planalto.gov.br/ccivil_03/leis/l8742compilado.htm) | lei | Núcleo do corpus. Arts. 20, 20-A, 20-B, 21, 21-A, 21-B: conceito de BPC, público (idoso 65+, PcD), conceito de deficiência e impedimento de longo prazo, renda *per capita* de 1/4 SM e ampliação a 1/2 SM, composição do grupo familiar, avaliação biopsicossocial, vedação de acúmulo, CadÚnico/CPF, revisão bienal, suspensão por atividade remunerada. | Vigente (2026), com dezenas de alterações incorporadas ao texto compilado — ver seção 3 para a lista completa de leis alteradoras. |
| 3 | **Lei nº 13.146, de 6 de julho de 2015 — Lei Brasileira de Inclusão / Estatuto da Pessoa com Deficiência (LBI)** | https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13146.htm | lei | Art. 2º e §§1º–2º: define pessoa com deficiência e determina que a avaliação, quando necessária, seja **biopsicossocial**, por equipe multiprofissional e interdisciplinar. Deu a redação atual do conceito de deficiência no art. 20, §2º, da LOAS e alterou os §§9º e 11. Referência conceitual para o critério de deficiência do BPC. | Vigente. A regulamentação do instrumento único de avaliação biopsicossocial previsto no art. 2º, §2º, ainda é objeto de normas setoriais (no BPC, a Portaria Conjunta MDS/INSS nº 2/2015). |
| 4 | **Lei nº 14.176, de 22 de junho de 2021** | https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14176.htm | lei | Lei que define o **critério econômico atual** do BPC: fixa a renda *per capita* em 1/4 do SM (art. 20, §3º), cria o §11-A (ampliação a até 1/2 SM por regulamento) e o **art. 20-B** (elementos para ampliação: grau de deficiência, dependência de terceiros, gastos médicos), além de regras de CadÚnico, convocação para reavaliação e prazos administrativos. | Vigente. Conteúdo já incorporado ao texto compilado da LOAS (entrada #2). |
| 5 | **Lei nº 13.982, de 2 de abril de 2020** | https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2020/lei/l13982.htm | lei | Alterou o art. 20 da LOAS em contexto de calamidade (COVID-19): critério de renda transitório, e — de forma permanente — **§14** (BPC/benefício previdenciário de até 1 SM de outro idoso/PcD da família não entra no cálculo da renda) e **§15** (BPC devido a mais de um membro da mesma família). Também instituiu o auxílio emergencial. | Parcialmente vigente: os §§14 e 15 seguem em vigor; as regras transitórias de renda (2020) estão superadas pela Lei 14.176/2021. |
| 6 | **Lei nº 10.741, de 1º de outubro de 2003 — Estatuto da Pessoa Idosa (ex-Estatuto do Idoso)** | https://www.planalto.gov.br/ccivil_03/leis/2003/l10.741.htm (compilado: https://www.planalto.gov.br/ccivil_03/leis/2003/l10.741compilado.htm) | lei | Art. 34 e parágrafo único: assegura o BPC ao idoso a partir de 65 anos e determina que **o BPC já concedido a outro idoso da família não seja computado** na renda para novo pedido. Regra citada expressamente no Decreto 6.214/2007. Renomeado "Estatuto da Pessoa Idosa" pela Lei 14.423/2022. | Vigente. |
| 7 | **Lei nº 15.077, de 27 de dezembro de 2024** | https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/lei/l15077.htm | lei | Alteração recente do art. 20 da LOAS: inclui o **§2º-A** (concessão administrativa/judicial sujeita a avaliação nos termos de regulamento), o **§3º-A** (regras de cálculo da renda familiar — soma dos rendimentos, vedadas deduções não previstas em lei), o **§12-B** (registro biométrico do responsável legal) e reduz para **24 meses** o prazo de desatualização do CadÚnico no art. 21-B. | Vigente. Conteúdo incorporado ao texto compilado da LOAS (entrada #2). **Verificar a URL exata no Planalto** (padrão `_ato2023-2026/2024/lei/l15077.htm`); confirmar em `legislacao.planalto.gov.br`. |

### B. Decretos (Planalto — texto compilado)

| # | titulo | fonte | tipo | cobertura | vigência |
|---|--------|-------|------|-----------|----------|
| 8 | **Decreto nº 6.214, de 26 de setembro de 2007 — Regulamento do BPC** | https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2007/decreto/d6214.htm | decreto | Regulamento operacional do BPC (Anexo). Detalha: conceito de família e de renda mensal bruta familiar (art. 4º e ss.), rendas excluídas do cálculo, documentação, papel do INSS e do SUAS, avaliação da deficiência, acúmulo e vedações, **revisão a cada 2 anos (art. 42)**, suspensão/cessação, CadÚnico e CPF. Fonte central junto com a LOAS. | Vigente (texto compilado). Alterado pelos Decretos 6.564/2008, 7.617/2011, 8.805/2016, 9.462/2018 e **12.534/2025** — todos já refletidos no compilado. |
| 9 | **Decreto nº 12.534, de 25 de junho de 2025** | https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/decreto/d12534.htm | decreto | Altera o Regulamento do BPC (Decreto 6.214/2007) e o Decreto 11.016/2022: passa a **incluir o Bolsa Família na renda familiar *per capita*** para fins de BPC e adota a **média da renda dos últimos 12 meses** do CadÚnico; ajusta requisitos de CadÚnico/registro familiar. | Vigente em 2026, **contestado judicialmente** (alegada extrapolação do poder regulamentar; decisões federais divergentes). Manter no corpus com anotação de litígio em curso. |
| 10 | **Decreto nº 11.016, de 29 de março de 2022 — Regulamento do Cadastro Único** | https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2022/decreto/d11016.htm | decreto | Regulamenta o CadÚnico (art. 6º-F da LOAS). Define família, renda, responsável familiar, atualização cadastral e uso dos dados — pré-requisito para concessão e manutenção do BPC. Revogou o Decreto 6.135/2007. | Vigente; alterado pelo Decreto 12.534/2025. |

### C. Atos infralegais — INSS / Portarias Conjuntas

| # | titulo | fonte | tipo | cobertura | vigência |
|---|--------|-------|------|-----------|----------|
| 11 | **Instrução Normativa PRES/INSS nº 128, de 28 de março de 2022** | https://www.gov.br/inss/pt-br/centrais-de-conteudo/legislacao/instrucao-normativa/2022 · DOU: https://portal.in.gov.br/web/dou/-/instrucao-normativa-pres/inss-n-128-de-28-de-marco-de-2022-389275446 | instrucao_normativa | IN consolidada do INSS sobre reconhecimento, manutenção e revisão de benefícios do RGPS e **benefícios assistenciais**. Contém o capítulo/seção do BPC (requisitos, avaliação da deficiência, renda, acúmulo, revisão, suspensão). | Vigente em 2026 (texto compilado; última alteração 12/08/2026). Alterada pela IN PRES/INSS nº 188/2025, entre outras. **Verificar os artigos exatos do capítulo do BPC** no texto compilado publicado pelo INSS (a numeração muda a cada alteração). |
| 12 | **Instrução Normativa PRES/INSS nº 188, de 8 de julho de 2025** | https://www.gov.br/inss/pt-br/centrais-de-conteudo/legislacao/instrucao-normativa/2025 · DOU: https://www.in.gov.br/web/dou (buscar "Instrução Normativa PRES/INSS nº 188 de 2025") | instrucao_normativa | Altera a IN 128/2022 (carência, salário-maternidade, aposentadoria híbrida e outros pontos). Impacto pequeno no BPC, mas é a alteração mais recente da IN consolidada — necessária para manter o corpus sincronizado. | Vigente. **Confirmar o permalink DOU** (não foi possível resolver a URL canônica automaticamente). |
| 13 | **Portaria Conjunta MDS/INSS nº 34, de 9 de outubro de 2025** | https://www.gov.br/inss/pt-br/centrais-de-conteudo/legislacao/portarias-conjuntas/2025/ptcj34mds-inss.pdf | instrucao_normativa | **Ato operacional consolidado atual do BPC**: regras e procedimentos de requerimento, concessão, manutenção e revisão; requisitos (biometria, CPF, CadÚnico), descontos por gastos médicos com valores médios no Anexo I, revisão periódica e reavaliação biopsicossocial a cada 2 anos, hipóteses de bloqueio/suspensão/cessação. **Revogou a Portaria Conjunta MDS/INSS nº 3/2018** e as portarias conjuntas nº 7/2020, 14/2021, 18/2021, 22/2022 e 28/2024. | Vigente (publicada em 10/2025). |
| 14 | **Portaria Conjunta MDS/INSS nº 2, de 30 de março de 2015** | https://www.mds.gov.br/webarquivos/legislacao/assistencia_social/portarias/2015/portaria_conjunta_INSS_2_2015_BPC.pdf · DOU nº 67, Seção 1, de 09/04/2015 (retificação DOU nº 123, de 01/07/2015) | instrucao_normativa | Define **critérios, procedimentos e o instrumento de avaliação social e médica da pessoa com deficiência** para acesso ao BPC, baseado na CIF: componentes Fatores Ambientais, Funções e Estruturas do Corpo, Atividades e Participação; qualificadores 0–4; Tabela de Qualificadores Conclusiva (TCQ). | Vigente em 2026 — **não** foi revogada pela Portaria 34/2025 nem pela 33/2025; o instrumento de 2015 segue em uso e é referenciado pelas normas de 2025. |
| 15 | **Portaria Conjunta MDS/MPS/INSS nº 33, de 5 de agosto de 2025** | https://www.gov.br/inss/pt-br/centrais-de-conteudo/legislacao/portarias-conjuntas/2025 (arquivo "ptcj33...") · DOU de 07/08/2025 | instrucao_normativa | Diretrizes e procedimentos para a **reavaliação biopsicossocial** de beneficiários PcD do BPC (art. 21 da LOAS): duas etapas (perícia médica do MPS + avaliação social do INSS), hipóteses de dispensa de perícia para impedimento permanente/irreversível, escalonamento de bloqueio (30 dias) → suspensão (30 dias) → cessação, e prazo recursal de 30 dias ao CRPS. | Vigente. **Confirmar a URL exata do PDF/permalink DOU** (o diretório `portarias-conjuntas/2025` do INSS foi confirmado; o nome do arquivo da nº 33 precisa ser verificado). |

### D. Manuais e páginas oficiais de orientação (`gov.br`)

| # | titulo | fonte | tipo | cobertura | vigência |
|---|--------|-------|------|-----------|----------|
| 16 | **"Solicitar Benefício Assistencial ao Idoso" (Carta de Serviços gov.br)** | https://www.gov.br/pt-br/servicos/solicitar-beneficio-assistencial-ao-idoso | manual | Página oficial "como solicitar" do BPC ao idoso: quem pode (65+, brasileiro/naturalizado/português, renda até 1/4 do SM calculada com CadÚnico + sistemas do INSS), CadÚnico atualizado há menos de 2 anos com CPF de toda a família, passo a passo no Meu INSS, canais (app, web, 135), documentação, prazo (~30 dias), valor de 1 SM **sem 13º e sem pensão por morte**. | Vigente (última modificação 12/08/2026). Verificação automatizada OK (HTTP 200). |
| 17 | **"Solicitar Benefício Assistencial à Pessoa com Deficiência (BPC/LOAS)" (Carta de Serviços gov.br)** | https://www.gov.br/pt-br/servicos/solicitar-beneficio-assistencial-a-pessoa-com-deficiencia | manual | Página oficial "como solicitar" do BPC à PcD: requisitos, avaliação médica e social (biopsicossocial) pelo INSS, CadÚnico obrigatório, passo a passo no Meu INSS, documentação e laudos, prazos e canais. Complementa a entrada #16 para o público PcD. | Vigente. Verificação automatizada OK (HTTP 200). |
| 18 | **INSS — "Benefício Assistencial ao Idoso (BPC)" e "Benefício Assistencial à Pessoa com Deficiência (BPC)" (Saiba mais)** | https://www.gov.br/inss/pt-br/saiba-mais/beneficios-assistenciais/beneficio-assistencial-ao-idoso-bpc · https://www.gov.br/inss/pt-br/saiba-mais/beneficios-assistenciais/beneficio-assistencial-a-pessoa-com-deficiencia-bpc | manual | Páginas explicativas do INSS sobre conceito, requisitos, renda, avaliação, revisão bienal, hipóteses de cessação e diferença entre BPC e benefícios previdenciários. | Vigente. **Não verificável por robô** (portal retorna "Conteúdo Restrito"/login a clientes automatizados; público em navegador). Confirmar o endereço final na navegação do `gov.br/inss` antes da ingestão; considerar também o mirror `antigo.inss.gov.br/beneficios/beneficio-assistencia-a-pessoa-com-deficiencia-bpc/`. |
| 19 | **MDS — "Benefício de Prestação Continuada (BPC)"** | https://www.gov.br/mds/pt-br/acoes-e-programas/suas/beneficios-assistenciais/beneficio-assistencial-ao-idoso-e-a-pessoa-com-deficiencia-bpc | manual | Página institucional do MDS/Secretaria Nacional de Benefícios Assistenciais: definição, público, critério de renda, papel do SUAS/CRAS no CadÚnico e no acompanhamento, gestão e financiamento do benefício, dados de cobertura. Visão da assistência social (complementa a visão previdenciária do INSS). | Vigente. **Não verificável por robô** (mesma limitação anti-bot do `gov.br`); endereço confirmado por busca. Validar em navegador. |
| 20 | **MDS — "BPC: Guia para Técnicos e Gestores" (2018) e "BPC — Perguntas Frequentes"** | https://www.mds.gov.br/webarquivos/publicacao/assistencia_social/Guia/Guia_BPC_2018.pdf · https://www.mds.gov.br/webarquivos/assistencia_social/bpc/Perguntas%20Frequentes%20BPC.pdf | manual | Materiais de orientação operacional do MDS: fluxos de requerimento, papel do CRAS, revisão, CadÚnico, casos-limite de renda e de composição familiar, perguntas frequentes. Úteis como linguagem "de atendimento" para o RAG. | PDFs disponíveis (HTTP 200). **Datados (2018)** — anteriores à Lei 14.176/2021, ao Decreto 12.534/2025 e às Portarias de 2025. Incluir apenas com aviso de desatualização, ou preferir as páginas #16–#19. |

---

## 3. Notas e questões em aberto

### 3.1 Incluir como entrada própria ou consolidar ("fold")?

**Leis alteradoras da LOAS (art. 20 e correlatos).** O texto compilado da LOAS (entrada #2)
já incorpora todas as alterações. Recomendação:

- **Manter entrada própria** (têm conteúdo transitório, vetos, contexto ou são a "lei de
  referência" de um critério): **Lei 14.176/2021** (#4, critério econômico atual + art. 20-B),
  **Lei 13.982/2020** (#5, §§14–15 permanentes + regime COVID), **Lei 13.146/2015** (#3, LBI —
  vale por si, muito além da LOAS), **Lei 15.077/2024** (#7, alteração recente ainda pouco
  comentada). **Lei 10.741/2003** (#6) entra por causa do art. 34.
- **Consolidar (fold) no texto da LOAS — citar na seção 4, não criar documento próprio:**
  - **Lei 12.435/2011** — reformou o SUAS e deu a redação de vários dispositivos do art. 20;
    integralmente absorvida.
  - **Lei 12.470/2011** — regras de deficiência, MEI, aprendiz, suspensão por trabalho
    (art. 21-A); absorvida.
  - **Lei 13.981/2020** — o "1/2 salário mínimo" que nunca vigorou; relevante só como
    história do critério (tratada na seção 1). Não ingerir como norma vigente.
  - **Lei 13.846/2019** (conversão da MP 871/2019) — introduziu CPF/CadÚnico/dados bancários
    (art. 20, §§12–13); absorvida.
  - **Lei 14.441/2022** (§6º-A, parcerias para avaliação social), **Lei 14.601/2023**
    (§4º, acúmulo com transferências de renda), **Lei 14.809/2024** (§9º, rendas de
    barragens/estágio/aprendizagem), **Lei 14.973/2024** (§12-A biometria e art. 21-B, em
    parte já revogados pela Lei 15.077/2024), **Lei 15.156/2025** (dispensa de revisão em
    síndrome congênita do Zika) e **Lei 15.157/2025** (§16, infectologista em perícia de
    HIV/aids; dispensa de perícia periódica no art. 21, §5º) — todas absorvidas no compilado;
    citar, não duplicar.

**Decretos alteradores do Decreto 6.214/2007.** Recomendação: **fold** de
**6.564/2008, 7.617/2011, 8.805/2016 e 9.462/2018** (absorvidos no texto compilado);
**manter entrada própria** apenas do **Decreto 12.534/2025** (#9), por ser recente,
substantivo e litigioso. O **Decreto 8.805/2016** especificamente tornou CadÚnico/CPF
requisito e revisou prazos — se o time quiser um documento dedicado à "história do CadÚnico
no BPC", ele é o candidato; caso contrário, fold.

### 3.2 Classificação `tipo` das Portarias Conjuntas
O enum pedido (`lei | decreto | instrucao_normativa | manual`) não tem rótulo para
"portaria". As entradas #13–#15 foram marcadas `instrucao_normativa` por serem atos
normativos infralegais de efeito equivalente. **Decisão do usuário:** aceitar essa
aproximação ou acrescentar um valor `portaria` ao esquema.

### 3.3 Qual é a IN do INSS vigente para o BPC?
**IN PRES/INSS nº 128/2022** continua sendo a IN consolidada em 2026 (texto compilado no
site do INSS, última alteração registrada em 12/08/2026), alterada pela **IN PRES/INSS
nº 188/2025** e por outras. Não há indício de uma IN nova que a substitua integralmente.
**Pendência:** localizar, no texto compilado, os **artigos exatos do capítulo do BPC** — a
numeração mudou entre versões; candidatos observados em fontes secundárias giram em torno
dos arts. 370–450, mas isso precisa ser confirmado na fonte primária antes de fatiar o
documento para o RAG.

### 3.4 Critério de deficiência / avaliação biopsicossocial — normas e instrumento
- **Instrumento vigente:** o da **Portaria Conjunta MDS/INSS nº 2/2015** (#14), ancorado na
  CIF, com qualificadores 0–4 e Tabela de Qualificadores Conclusiva. **Não** confundir com o
  **IF-Br / IF-BrM (Índice de Funcionalidade Brasileiro / Modificado)**: o IF-Br foi
  concebido para a avaliação da deficiência prevista na LBI (art. 2º, §2º) de forma geral e
  sua adoção uniforme ainda depende de regulamentação; o instrumento operacional do BPC é o
  da Portaria 2/2015. **Confirmar** se alguma norma de 2025 (Portaria 33 ou 34) já remete
  formalmente ao IF-BrM — a leitura feita aqui indica que **não**, mas vale checar o texto
  integral da Portaria 33/2025.
- **Reavaliação:** **Portaria Conjunta MDS/MPS/INSS nº 33/2025** (#15). **Pendência:** obter
  o **PDF oficial no `gov.br/inss`** (diretório `.../portarias-conjuntas/2025/` confirmado;
  nome do arquivo da nº 33 a verificar) e/ou o **permalink DOU** de 07/08/2025.
- **Portaria Conjunta MDS/INSS nº 3/2018:** **revogada** pela Portaria 34/2025 — não incluir
  no corpus como norma vigente (pode entrar como referência histórica, se desejado).

### 3.5 Páginas `gov.br` e verificação
As URLs de serviço `gov.br/pt-br/servicos/...` (#16, #17) responderam 200 e o conteúdo foi
lido. As páginas `gov.br/inss/pt-br/saiba-mais/...` (#18) e `gov.br/mds/pt-br/acoes-e-programas/...`
(#19) retornam "Conteúdo Restrito" a acesso automatizado — **precisam de conferência manual
em navegador** para (a) confirmar a URL final e (b) decidir se o valor para o RAG está mais
na Carta de Serviços (#16/#17), que é mais estável e objetiva. Sugestão: priorizar #16/#17
como fonte "how-to" e usar #18/#19 como reforço conceitual.

### 3.6 Ponto sensível: Decreto 12.534/2025 (Bolsa Família na renda)
Está vigente, mas com forte contestação judicial e possível reversão. Se entrar no corpus,
**anotar explicitamente** a controvérsia e a data de corte, para o agente Amparo não afirmar
como pacífico que o Bolsa Família compõe a renda do BPC.

### 3.7 Salário mínimo de referência
Evitar fixar valores em reais no corpus (o SM muda anualmente). Em 2025 o teto de 1/4 do SM
foi citado oficialmente como R$ 379,50; em 2026 muda. Preferir a fração ("1/4 do salário
mínimo") e deixar o cálculo do valor para runtime.

### 3.8 Itens que o usuário precisa decidir
1. Aceitar Portarias como `instrucao_normativa` ou criar `tipo: portaria`.
2. Incluir ou não os PDFs datados do MDS (2018) — recomendação: só com aviso.
3. Incluir Decreto 12.534/2025 (recomendado incluir, com anotação de litígio).
4. Incluir normas históricas revogadas/suspensas (Lei 13.981/2020, Portaria 3/2018) como
   contexto ou deixá-las de fora — recomendação: deixar de fora do corpus de "regras
   vigentes"; mencionar apenas em nota de contexto.
5. Confirmar a URL do Planalto da Lei 15.077/2024 e os permalinks DOU das Portarias 33/2025
   e da IN 188/2025.

---

## 4. Citações completas (todas as URLs consultadas em 2026-08-31)

### Primárias — verificadas com HTTP 200 e conteúdo inspecionado
- LOAS (original): https://www.planalto.gov.br/ccivil_03/leis/l8742.htm
- LOAS (compilado): http://www.planalto.gov.br/ccivil_03/leis/l8742compilado.htm
- Decreto 6.214/2007 (Regulamento do BPC, compilado): https://www.planalto.gov.br/ccivil_03/_ato2007-2010/2007/decreto/d6214.htm
- Decreto 12.534/2025: https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/decreto/d12534.htm
- Decreto 11.016/2022 (CadÚnico): https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2022/decreto/d11016.htm
- Lei 12.435/2011: https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2011/lei/l12435.htm
- Lei 12.470/2011: https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2011/lei/l12470.htm
- Lei 13.146/2015 (LBI): https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13146.htm
- Lei 13.981/2020: https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2020/lei/l13981.htm
- Lei 13.982/2020: https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2020/lei/l13982.htm
- Lei 14.176/2021: https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14176.htm
- Lei 10.741/2003 (Estatuto da Pessoa Idosa): https://www.planalto.gov.br/ccivil_03/leis/2003/l10.741.htm — compilado: https://www.planalto.gov.br/ccivil_03/leis/2003/l10.741compilado.htm
- Constituição de 1988: https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm
- Decreto 8.805/2016: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2016/decreto/d8805.htm
- Portaria Conjunta MDS/INSS nº 34/2025 (PDF INSS): https://www.gov.br/inss/pt-br/centrais-de-conteudo/legislacao/portarias-conjuntas/2025/ptcj34mds-inss.pdf
- Portaria Conjunta MDS/INSS nº 2/2015 (PDF MDS): https://www.mds.gov.br/webarquivos/legislacao/assistencia_social/portarias/2015/portaria_conjunta_INSS_2_2015_BPC.pdf
- Decreto 6.214/2007 (PDF MDS): https://www.mds.gov.br/webarquivos/legislacao/assistencia_social/decreto/decreto_6214.pdf
- "Guia BPC" MDS 2018 (PDF): https://www.mds.gov.br/webarquivos/publicacao/assistencia_social/Guia/Guia_BPC_2018.pdf
- "BPC — Perguntas Frequentes" MDS (PDF): https://www.mds.gov.br/webarquivos/assistencia_social/bpc/Perguntas%20Frequentes%20BPC.pdf
- Carta de Serviços — BPC ao idoso: https://www.gov.br/pt-br/servicos/solicitar-beneficio-assistencial-ao-idoso
- Carta de Serviços — BPC à pessoa com deficiência: https://www.gov.br/pt-br/servicos/solicitar-beneficio-assistencial-a-pessoa-com-deficiencia
- INSS — legislação / Instruções Normativas 2022: https://www.gov.br/inss/pt-br/centrais-de-conteudo/legislacao/instrucao-normativa/2022

### Primárias — endereço confirmado, conteúdo NÃO verificável por robô (anti-bot / permalink a confirmar)
- INSS — BPC ao idoso (Saiba mais): https://www.gov.br/inss/pt-br/saiba-mais/beneficios-assistenciais/beneficio-assistencial-ao-idoso-bpc
- INSS — BPC à pessoa com deficiência (Saiba mais): https://www.gov.br/inss/pt-br/saiba-mais/beneficios-assistenciais/beneficio-assistencial-a-pessoa-com-deficiencia-bpc
- MDS — BPC: https://www.gov.br/mds/pt-br/acoes-e-programas/suas/beneficios-assistenciais/beneficio-assistencial-ao-idoso-e-a-pessoa-com-deficiencia-bpc
- IN PRES/INSS nº 128/2022 (DOU / Imprensa Nacional): https://portal.in.gov.br/web/dou/-/instrucao-normativa-pres/inss-n-128-de-28-de-marco-de-2022-389275446
- INSS — Instruções Normativas 2025 (para a IN 188/2025): https://www.gov.br/inss/pt-br/centrais-de-conteudo/legislacao/instrucao-normativa/2025
- INSS — Portarias Conjuntas 2025 (para a Portaria 33/2025): https://www.gov.br/inss/pt-br/centrais-de-conteudo/legislacao/portarias-conjuntas/2025
- Lei 15.077/2024 (URL a confirmar no Planalto): https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2024/lei/l15077.htm

### Secundárias consultadas apenas para localizar/datar as normas (NÃO entram no corpus)
- Senado Notícias — sanção da Lei 14.176/2021: https://www12.senado.leg.br/noticias/materias/2021/06/23/sancionada-lei-com-criterios-para-concessao-de-bpc
- MDS — notícia "LOAS 30 anos": https://www.gov.br/mds/pt-br/noticias-e-conteudos/desenvolvimento-social/noticias-desenvolvimento-social/lei-organica-da-assistencia-social-completa-30-anos-em-7-de-dezembro
- Agência Brasil — regra de reavaliação do BPC PcD (Portaria 33/2025): https://agenciabrasil.ebc.com.br/geral/noticia/2025-08/governo-define-regra-para-reavaliacao-de-bpc-de-pessoa-com-deficiencia
- TRF3 — notícia sobre Bolsa Família fora do cálculo do BPC (litígio Decreto 12.534/2025): https://web.trf3.jus.br/noticias-sjsp/Noticiar/ExibirNoticia/1891-bolsa-familia-nao-deve-integrar-calculo-da-renda-familiar
- LegisWeb — Portaria Conjunta MDS/INSS nº 34/2025 (ficha): https://www.legisweb.com.br/legislacao/?id=484781
- LegisWeb — Portaria Conjunta MPS/INSS/MDS nº 33/2025 (ficha): https://www.legisweb.com.br/legislacao/?id=482044
- LEX — Portaria Conjunta MDS/INSS nº 34/2025 (ementa): https://www.lex.com.br/portaria-conjunta-mds-e-inss-no-34-de-9-de-outubro-de-2025/
- COAD — resumo da IN 188/2025: https://www.coad.com.br/home/noticias-detalhe/132765/inss-altera-instrucao-normativa-que-disciplina-regras-de-direito-previdenciario

---

*Fim do levantamento. Próximo passo: validação humana desta lista e, só então, criação dos
arquivos em `docs/sources/`.*
