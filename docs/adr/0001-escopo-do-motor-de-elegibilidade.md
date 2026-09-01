# Escopo e limites do motor de elegibilidade

O `eligibility_node` calcula de forma determinística (função pura, testável)
apenas **idade** e **renda familiar per capita** contra o critério de 1/4 do
salário mínimo, aplicando as exclusões de renda e as deduções de saúde da
Portaria Conjunta MDS/INSS 34/2025.

**Não decide sobre deficiência.** Quando a rota é por deficiência, o resultado é
sempre `depende_de_avaliacao`: o Amparo encaminha para a avaliação
biopsicossocial do INSS e nunca afirma que a pessoa tem — ou não tem —
deficiência. A deficiência para o BPC é definida por avaliação médica e social
do INSS (LOAS art. 20, §§2º e 6º); qualquer palpite do sistema seria enganoso e
poderia afastar alguém de um direito.

Dados de referência que mudam no tempo — o valor do salário mínimo e os valores
médios de dedução do Anexo I da Portaria 34/2025 — são parâmetros configuráveis
com data de vigência, não constantes espalhadas pelo código.

O cálculo oficial usa a média da renda dos 12 meses registrada no CadÚnico
(Decreto 12.534/2025, em vigor e contestado judicialmente). O Amparo, sem acesso
ao CadÚnico, aproxima com a renda mensal informada pela pessoa e deixa essa
limitação explícita na resposta. O Bolsa Família entra na renda, conforme o
decreto vigente.
