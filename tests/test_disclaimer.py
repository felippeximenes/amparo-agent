from amparo.disclaimer import DISCLAIMER


def test_disclaimer_menciona_pontos_obrigatorios():
    texto = DISCLAIMER.lower()
    assert "não é um canal oficial" in texto
    assert "inss" in texto
    assert "defensoria pública" in texto
