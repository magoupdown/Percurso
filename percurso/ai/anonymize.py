"""Pseudonimização antes de qualquer chamada à IA (SPEC D7, §7.6).

Nomes de alunos nunca vão ao Gemini. No prompt, o aluno é "o aluno PCR-XXXXXX"; alunos de turma viram
"aluno A01". O mapa código↔nome vive só em memória e é usado para restaurar nomes na tela.
"""
from __future__ import annotations

import re
from typing import Dict, Iterable, List, Tuple

from ..core.models import Registro


class Pseudonimizador:
    def __init__(self, registro: Registro):
        self.registro = registro
        self.mapa: Dict[str, str] = {}  # pseudônimo → nome
        self._pares: List[Tuple[str, str]] = []
        nome = (registro.identificacao or "").strip()
        if registro.eh_turma:
            if registro.turma and registro.turma.nome.strip():
                self._pares.append((registro.turma.nome.strip(), f"a turma {registro.codigo}"))
            if nome:
                self._pares.append((nome, f"a turma {registro.codigo}"))
            if registro.turma:
                for al in registro.turma.alunos:
                    if al.identificacao.strip():
                        self._pares.append((al.identificacao.strip(), f"aluno {al.id}"))
        elif nome:
            self._pares.append((nome, f"o aluno {registro.codigo}"))
        # nomes mais longos primeiro para evitar substituição parcial
        self._pares.sort(key=lambda p: -len(p[0]))
        for n, c in self._pares:
            self.mapa.setdefault(c, n)

    def aplicar(self, texto: str) -> str:
        if not texto:
            return texto
        saida = texto
        for nome, codigo in self._pares:
            saida = re.sub(rf"(?<!\w){re.escape(nome)}(?!\w)", codigo, saida, flags=re.IGNORECASE)
        return saida

    def aplicar_lista(self, itens: Iterable[str]) -> List[str]:
        return [self.aplicar(i) for i in itens]

    def restaurar(self, texto: str) -> str:
        saida = texto or ""
        for codigo, nome in sorted(self.mapa.items(), key=lambda p: -len(p[0])):
            saida = saida.replace(codigo, nome)
            # variantes: "aluno PCR-XXXX" sem artigo, ou só o código
            if codigo.startswith(("o aluno ", "a turma ")):
                cod_puro = codigo.split(" ", 2)[2]
                saida = re.sub(rf"(?i)\b(?:o |a )?(?:aluno|turma) {re.escape(cod_puro)}\b", nome, saida)
                saida = saida.replace(cod_puro, nome)
        return saida

    def contem_nome(self, texto: str) -> bool:
        """Verificação final: nenhum nome real presente no prompt (usada nos testes e no validador)."""
        for nome, _ in self._pares:
            if re.search(rf"(?<!\w){re.escape(nome)}(?!\w)", texto or "", flags=re.IGNORECASE):
                return True
        return False
