"""Memória de sessão (seam: `session_id_de`, `limpar_sessoes_expiradas`)."""

from datetime import datetime, timedelta, timezone

import pytest

from amparo.sessao import limpar_sessoes_expiradas, session_id_de


# --- session_id_de: HMAC, nunca o identificador cru ---------------------------

def test_session_id_e_deterministico():
    a = session_id_de("5511999999999", salt="segredo")
    b = session_id_de("5511999999999", salt="segredo")
    assert a == b


def test_session_id_varia_com_o_identificador():
    a = session_id_de("A", salt="segredo")
    b = session_id_de("B", salt="segredo")
    assert a != b


def test_session_id_varia_com_o_salt():
    a = session_id_de("A", salt="segredo1")
    b = session_id_de("A", salt="segredo2")
    assert a != b


def test_session_id_nao_e_o_identificador_cru():
    identificador = "5511999999999"
    assert session_id_de(identificador, salt="segredo") != identificador


def test_session_id_e_hex_de_64_caracteres():
    sid = session_id_de("x", salt="segredo")
    assert len(sid) == 64
    int(sid, 16)  # não lança — é hex válido


def test_session_id_falha_sem_salt_configurado(monkeypatch):
    from amparo import config as config_mod

    monkeypatch.setattr(config_mod.settings, "session_salt", "")
    with pytest.raises(ValueError):
        session_id_de("qualquer")


# --- limpar_sessoes_expiradas: varre e apaga pelo thread_id ------------------

class _CheckpointFake:
    def __init__(self, thread_id: str, ts: str):
        self.config = {"configurable": {"thread_id": thread_id}}
        self.checkpoint = {"ts": ts}


class _CheckpointerFake:
    def __init__(self, tuplas):
        self._tuplas = tuplas
        self.apagadas: list[str] = []

    def list(self, config):  # noqa: ARG002
        return iter(self._tuplas)

    def delete_thread(self, thread_id):
        self.apagadas.append(thread_id)


def _ha(horas: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=horas)).isoformat()


def test_apaga_sessao_sem_atividade_ha_mais_de_24h():
    cp = _CheckpointerFake(
        [_CheckpointFake("expirada", _ha(25)), _CheckpointFake("ativa", _ha(1))]
    )
    apagadas = limpar_sessoes_expiradas(cp, ttl_horas=24)
    assert apagadas == 1
    assert cp.apagadas == ["expirada"]


def test_nao_apaga_sessao_com_atividade_recente():
    cp = _CheckpointerFake([_CheckpointFake("ativa", _ha(1))])
    assert limpar_sessoes_expiradas(cp, ttl_horas=24) == 0
    assert cp.apagadas == []


def test_usa_o_checkpoint_mais_recente_da_thread():
    """Uma thread com um checkpoint antigo e outro recente não é apagada —
    o que conta é a última atividade, não a primeira."""
    cp = _CheckpointerFake([_CheckpointFake("t", _ha(48)), _CheckpointFake("t", _ha(1))])
    assert limpar_sessoes_expiradas(cp, ttl_horas=24) == 0
    assert cp.apagadas == []
