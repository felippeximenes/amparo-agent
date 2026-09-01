# Amparo — Contexto

Amparo orienta pessoas sobre o BPC/LOAS. Este documento fixa a linguagem do
domínio de **elegibilidade** — o que cada termo significa, não como é calculado.

## Linguagem

### Pessoas e núcleo

**Requerente**:
A pessoa que quer saber se tem direito ao BPC. Só vira beneficiário depois de o
INSS conceder.
_Avoid_: beneficiário, usuário, cliente, segurado.

**Grupo familiar**:
Enumeração fechada da LOAS (art. 20, §1º) — requerente, cônjuge ou
companheiro(a), pais (ou madrasta/padrasto na ausência de um deles), irmãos
solteiros, filhos e enteados solteiros, menores tutelados — que vivam sob o
mesmo teto. Não é o domicílio nem a composição familiar do CadÚnico.
_Avoid_: família, núcleo familiar, domicílio, unidade familiar.

**Pessoa idosa**:
Para o BPC, quem tem 65 anos completos ou mais (LOAS art. 20; Estatuto da
Pessoa Idosa art. 34). Não é o "idoso" de 60+ do Estatuto em geral.
_Avoid_: idoso.

**Pessoa com deficiência (para o BPC)**:
Quem tem impedimento de longo prazo reconhecido pela avaliação biopsicossocial
do INSS.
_Avoid_: PcD inválido, incapaz, deficiente.

### Elegibilidade

**Impedimento de longo prazo**:
Impedimento de natureza física, mental, intelectual ou sensorial com efeitos
pelo prazo mínimo de 2 anos que, em interação com barreiras, pode obstruir a
participação plena e efetiva na sociedade (LOAS art. 20, §§2º e 10).
_Avoid_: incapacidade, invalidez.

**Avaliação biopsicossocial**:
Avaliação médica e social feita por perito e assistente social do INSS que
reconhece (ou não) a deficiência para o BPC. Fora do alcance do Amparo — o
motor apenas sinaliza quando ela é necessária.
_Avoid_: perícia, laudo, exame.

**Renda mensal bruta do grupo familiar**:
Soma dos rendimentos mensais dos membros do grupo familiar, já retiradas as
exclusões legais.
_Avoid_: renda líquida, renda declarada, renda do domicílio.

**Renda familiar per capita**:
Renda mensal bruta do grupo familiar dividida pelo número de membros do grupo
familiar (LOAS art. 20, §3º).
_Avoid_: renda por pessoa, renda média.

**Critério de renda**:
Renda familiar per capita igual ou inferior a 1/4 do salário mínimo de
referência (Lei 14.176/2021; Portaria Conjunta MDS/INSS 34/2025 art. 11).
"Igual ou inferior" — exatamente 1/4 atende.

**Salário mínimo de referência**:
O valor do salário mínimo nacional vigente na data do cálculo. O domínio nunca
fixa valor em reais; trabalha com a fração.
_Avoid_: piso, salário base.

**Exclusões de renda**:
Rendimentos que não entram na renda mensal bruta — em especial um benefício
previdenciário ou BPC de até 1 salário mínimo por membro idoso 65+ ou com
deficiência, bolsa de estágio, contrato de aprendizagem, auxílio ou indenização
de barragens, auxílio-inclusão (LOAS art. 20, §§9º e 14; Portaria 34/2025
art. 8º, I).

**Deduções de saúde**:
Gastos contínuos e comprovados do requerente idoso ou com deficiência com itens
não cobertos pelo SUS/SUAS (medicamentos, consultas, fraldas, alimentos
especiais, Centro-Dia) abatidos da renda bruta, uma vez por categoria, pelo
valor médio oficial (Portaria 34/2025 art. 8º, §§4º-6º e Anexo I).
_Avoid_: descontos, despesas.

**Resultado de elegibilidade**:
A conclusão do motor determinístico — `atende`, `nao_atende`,
`depende_de_avaliacao` (idade e renda ok, mas a deficiência precisa da
avaliação do INSS) ou `indeterminado` (dados insuficientes). Vem sempre com a
regra aplicada e a fonte. Não é uma decisão do INSS.
_Avoid_: aprovado, negado, deferido, indeferido, concedido.
