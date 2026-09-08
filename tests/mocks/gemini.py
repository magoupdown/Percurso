"""Cliente Gemini falso (SPEC §16.1): respostas válidas, inválidas, referência inventada e falha de rede."""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional


def plano_valido(duracao: int = 50, tema: str = "Nota única: tecla repetida no pulso", refs: Optional[List[str]] = None, habilidades: Optional[List[str]] = None) -> Dict[str, Any]:
    blocos = [
        {"inicio_min": 0, "fim_min": 5, "titulo": "Acolhimento", "etapa": "acolhimento", "descricao": ""},
        {"inicio_min": 5, "fim_min": 12, "titulo": "Retomada", "etapa": "introducao", "descricao": ""},
        {"inicio_min": 12, "fim_min": 22, "titulo": "Exploração", "etapa": "exploracao", "descricao": ""},
        {"inicio_min": 22, "fim_min": duracao - 13, "titulo": "Prática", "etapa": "pratica", "descricao": ""},
        {"inicio_min": duracao - 13, "fim_min": duracao - 5, "titulo": "Aplicação", "etapa": "aplicacao", "descricao": ""},
        {"inicio_min": duracao - 5, "fim_min": duracao - 3, "titulo": "Avaliação", "etapa": "avaliacao", "descricao": ""},
        {"inicio_min": duracao - 3, "fim_min": duracao, "titulo": "Fechamento", "etapa": "fechamento", "descricao": ""},
    ]
    return {
        "tema": tema,
        "objetivo_geral": f"Desenvolver {tema} com continuidade.",
        "objetivos_especificos": ["Executar com pulso estável", "Reduzir aceleração no final das frases"],
        "conteudos": [tema],
        "competencias": ["senso de pulsação"],
        "habilidades_curriculares": habilidades or [],
        "metodologia": "Orff",
        "cronograma": blocos,
        "atividades": [
            {"titulo": "Uma tecla, um pulso", "descricao": "Repetir uma tecla no pulso.", "duracao_min": 10, "bloco": "exploracao", "recursos": ["instrumentos"]},
            {"titulo": "Pergunta e resposta", "descricao": "Frases de 4 pulsos.", "duracao_min": 15, "bloco": "pratica", "recursos": ["instrumentos"]},
        ],
        "intervencoes_professor": ["Demonstrar antes de explicar"],
        "possiveis_dificuldades": ["acelerar no final das frases"],
        "adaptacoes": "Nenhuma",
        "avaliacao": "Observação com rubrica",
        "continuidade": "Avançar para cinco dedos",
        "referencias": [{"id_origem": r, "uso": "fundamenta a atividade"} for r in (refs or [])],
        "justificativa_pedagogica": {"estrutura": "Porque o aluno PCR consolidou o pulso corporal.", "adequacao": "Exercício de tecla única respeita a tessitura inicial."},
        "proximo_passo_sugerido": "Cinco dedos",
        "proximo_passo_justificativa": "Próxima etapa da progressão.",
    }


class ClienteFalso:
    """Simula `ClienteGemini`. `roteiro` é uma lista de respostas (dict, Exception ou callable) consumidas em ordem."""

    def __init__(self, roteiro: Optional[List[Any]] = None, chave: str = "falsa"):
        self.roteiro: List[Any] = list(roteiro or [])
        self.prompts: List[str] = []
        self.sistemas: List[str] = []
        self.chave = chave
        self.modelo = "mock"

    def testar(self) -> None:
        if self.chave == "invalida":
            raise RuntimeError("API key not valid")

    def _proxima(self, prompt: str) -> Any:
        self.prompts.append(prompt)
        if not self.roteiro:
            raise RuntimeError("roteiro do mock esgotado")
        item = self.roteiro.pop(0)
        if isinstance(item, Exception):
            raise item
        if callable(item):
            return item(prompt)
        return item

    def gerar_json(self, prompt: str, schema, sistema: str = "") -> Dict[str, Any]:
        self.sistemas.append(sistema)
        return self._proxima(prompt)

    def gerar_texto(self, prompt: str, sistema: str = "") -> str:
        self.sistemas.append(sistema)
        r = self._proxima(prompt)
        return r if isinstance(r, str) else str(r)

    def embeddings(self, textos: List[str]) -> List[List[float]]:
        """Embedding determinístico e barato: contagem de letras (suficiente para testar o índice)."""
        saida = []
        for t in textos:
            t = t.lower()
            v = [float(len(re.findall(ch, t))) for ch in "abcdefghijklmnopqrstuvwxyz"]
            n = sum(x * x for x in v) ** 0.5 or 1.0
            saida.append([x / n for x in v])
        return saida


def fabrica(roteiro: Optional[List[Any]] = None) -> Callable[[str], ClienteFalso]:
    def _f(chave: str) -> ClienteFalso:
        return ClienteFalso(roteiro, chave)

    return _f
