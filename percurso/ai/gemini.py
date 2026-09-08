"""Cliente Gemini (SPEC D6, §7.3): SDK `google-genai`, chave via Colab Secrets ou memória de sessão.

A chave nunca é gravada, logada, exportada nem enviada a outro serviço.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional, Type

from .. import config
from ..ui import texts as T
from ..utils.logging import obter

log = obter("gemini")


@dataclass
class ResultadoAtivacao:
    ok: bool
    motivo: str = ""  # sem_chave | chave_invalida | rede | ok
    mensagem: str = ""


class ClienteGemini:
    """Envoltório fino sobre google-genai com saída estruturada (JSON + schema pydantic)."""

    def __init__(self, chave: str, cfg: Optional[Dict[str, Any]] = None):
        from google import genai  # type: ignore

        self._cfg = cfg or config.gemini()
        self._client = genai.Client(api_key=chave)
        self.modelo = self._cfg.get("modelo", "gemini-2.5-flash")
        self.modelo_embeddings = self._cfg.get("modelo_embeddings", "gemini-embedding-001")
        self.timeout_s = int(self._cfg.get("timeout_s", 60))
        self.temperatura = float(self._cfg.get("temperatura", 0.4))

    def testar(self) -> None:
        """Chamada mínima de teste após validar a chave (SPEC §7.3)."""
        from google.genai import types  # type: ignore

        self._client.models.generate_content(
            model=self.modelo,
            contents="Responda apenas: ok",
            config=types.GenerateContentConfig(max_output_tokens=5, temperature=0, http_options=types.HttpOptions(timeout=self.timeout_s * 1000)),
        )

    def gerar_texto(self, prompt: str, sistema: str = "") -> str:
        from google.genai import types  # type: ignore

        r = self._client.models.generate_content(
            model=self.modelo,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=sistema or None,
                temperature=self.temperatura,
                http_options=types.HttpOptions(timeout=self.timeout_s * 1000),
            ),
        )
        return (r.text or "").strip()

    def gerar_json(self, prompt: str, schema: Type, sistema: str = "") -> Dict[str, Any]:
        """Saída estruturada: response_mime_type=application/json + response_schema (SPEC §7.5)."""
        from google.genai import types  # type: ignore

        r = self._client.models.generate_content(
            model=self.modelo,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=sistema or None,
                temperature=self.temperatura,
                response_mime_type="application/json",
                response_schema=schema,
                http_options=types.HttpOptions(timeout=self.timeout_s * 1000),
            ),
        )
        texto = r.text or ""
        return json.loads(texto)

    def embeddings(self, textos: list) -> list:
        r = self._client.models.embed_content(model=self.modelo_embeddings, contents=textos)
        return [list(e.values) for e in r.embeddings]


def _obter_chave(sessao, chave_sessao: Optional[str]) -> Optional[str]:
    if chave_sessao:
        return chave_sessao
    if sessao.chave_temporaria:
        return sessao.chave_temporaria
    nome = config.gemini().get("nome_segredo", "GEMINI_API_KEY")
    return sessao.plataforma.obter_segredo(nome)


def ativar(sessao, chave_sessao: Optional[str] = None, fabrica_cliente=None) -> ResultadoAtivacao:
    """Tenta ativar o Modo Inteligente na sessão. Nunca grava a chave."""
    chave = _obter_chave(sessao, chave_sessao)
    if not chave:
        sessao.modo_ia = "essencial"
        sessao.gemini_pronto = False
        return ResultadoAtivacao(False, "sem_chave", T.GEMINI_NAO_CONFIGURADO)
    fabrica = fabrica_cliente or ClienteGemini
    try:
        cliente = fabrica(chave)
        cliente.testar()
    except Exception as e:  # noqa: BLE001
        msg = str(e).lower()
        log.warning("ativação Gemini falhou: %s", e.__class__.__name__)
        sessao.modo_ia = "essencial"
        sessao.gemini_pronto = False
        sessao.cliente_gemini = None
        if any(k in msg for k in ("api key", "api_key", "permission", "unauthenticated", "invalid", "401", "403", "400")):
            return ResultadoAtivacao(False, "chave_invalida", T.GEMINI_CHAVE_INVALIDA)
        return ResultadoAtivacao(False, "rede", T.GEMINI_SEM_RESPOSTA)
    sessao.cliente_gemini = cliente
    sessao.chave_temporaria = chave if chave_sessao else sessao.chave_temporaria
    sessao.modo_ia = "gemini"
    sessao.gemini_pronto = True
    return ResultadoAtivacao(True, "ok", T.GEMINI_ATIVADO)


def hash_prompt(*partes: Any) -> str:
    return hashlib.sha256(json.dumps(partes, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()
