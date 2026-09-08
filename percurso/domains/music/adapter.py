"""Adaptador de domínio: Música (SPEC §5).

Carrega perfis instrumentais (`instrument_profiles/*.json`), aplica cópias editadas pelo professor,
sugere progressão, seleciona exercícios, expande consultas e expõe funções determinísticas (music21).
"""
from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import DomainAdapter
from . import theory

PASTA_PERFIS = Path(__file__).resolve().parent / "instrument_profiles"

ORDEM_ESPECIALIDADES = [
    "piano", "teclado", "violao", "guitarra", "flauta_doce", "flauta_transversal", "clarinete",
    "saxofone", "trompete", "trombone", "violino", "viola", "violoncelo", "canto", "coral",
    "bateria", "percussao", "percepcao_musical", "musicalizacao", "teoria_musical",
    "pratica_conjunto", "outro",
]

NOMES_EN = {
    "piano": "piano", "teclado": "keyboard", "violao": "classical guitar", "guitarra": "electric guitar",
    "flauta_doce": "recorder", "flauta_transversal": "flute", "clarinete": "clarinet", "saxofone": "saxophone",
    "trompete": "trumpet", "trombone": "trombone", "violino": "violin", "viola": "viola", "violoncelo": "cello",
    "canto": "singing voice", "coral": "choir", "bateria": "drum kit", "percussao": "percussion",
    "percepcao_musical": "ear training", "musicalizacao": "early childhood music", "teoria_musical": "music theory",
    "pratica_conjunto": "ensemble", "outro": "music instrument",
}

RUBRICA_INSTRUMENTO = ["leitura", "ritmo", "tecnica", "coordenacao", "percepcao", "autonomia"]
RUBRICA_COLETIVA = ["participacao", "ritmo", "percepcao", "escuta", "cooperacao", "autonomia"]
RUBRICA_PERCEPCAO = ["ritmo", "percepcao", "leitura", "solfejo", "ditado", "autonomia"]

# Sinônimos pedagógicos PT/EN para expansão de busca (SPEC §9.5)
SINONIMOS: Dict[str, List[str]] = {
    "pulsacao": ["pulso regular", "senso de pulsação", "beat perception", "internalização métrica", "movimento corporal e pulso", "steady beat", "pulse"],
    "pulso": ["pulsação", "beat", "steady beat", "tempo"],
    "ritmo": ["rhythm", "figuras rítmicas", "subdivisão", "rhythmic skills", "duração"],
    "leitura": ["leitura musical", "sight reading", "music reading", "notação", "notation", "solfejo"],
    "solfejo": ["solfege", "solfeggio", "leitura cantada", "sight singing"],
    "percepcao": ["percepção musical", "ear training", "aural skills", "treinamento auditivo", "audiação"],
    "afinacao": ["intonation", "pitch accuracy", "afinação vocal", "tuning"],
    "respiracao": ["breathing", "breath support", "apoio respiratório", "respiração diafragmática"],
    "articulacao": ["articulation", "tonguing", "staccato", "legato", "ataque"],
    "tecnica": ["technique", "técnica instrumental", "instrumental technique", "mecanismo"],
    "postura": ["posture", "ergonomia", "body alignment", "posição"],
    "coordenacao": ["coordination", "independência de mãos", "hand independence", "motor skills"],
    "improvisacao": ["improvisation", "criação", "creative music making", "composição"],
    "repertorio": ["repertoire", "peças", "canções", "songs", "obras"],
    "iniciante": ["beginner", "iniciação", "primeiros passos", "elementary", "novice"],
    "crianca": ["children", "infantil", "early childhood", "kids", "young learners"],
    "avaliacao": ["assessment", "evaluation", "rubrica", "rubric", "feedback"],
    "motivacao": ["motivation", "engajamento", "engagement", "prática deliberada"],
    "metodologia": ["method", "abordagem", "approach", "pedagogy", "pedagogia"],
    "orff": ["Orff-Schulwerk", "Carl Orff", "instrumental Orff"],
    "kodaly": ["Kodály", "manossolfa", "solfa", "Kodaly method"],
    "dalcroze": ["Dalcroze", "eurhythmics", "rítmica", "euritmia"],
    "gordon": ["Music Learning Theory", "Edwin Gordon", "audiation", "audiação"],
    "swanwick": ["Keith Swanwick", "modelo C(L)A(S)P", "espiral de desenvolvimento"],
    "musicalizacao": ["musicalização infantil", "early music education", "music education children"],
    "conjunto": ["ensemble", "prática coletiva", "group music making", "band"],
    "coral": ["choir", "choral singing", "canto coral", "chorus"],
    "escala": ["scale", "escalas", "scales"],
    "dinamica": ["dynamics", "intensidade", "forte e piano"],
    "memoria": ["memorização", "memorization", "memory"],
}


def _sem_acento(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")


def _norm(t: str) -> str:
    return " ".join(_sem_acento((t or "").lower()).split())


class MusicAdapter(DomainAdapter):
    id = "musica"
    nome = "Música"

    def __init__(self, pasta_perfis_editados: Optional[Path] = None):
        self.pasta_perfis_editados = Path(pasta_perfis_editados) if pasta_perfis_editados else None
        self._perfis_base: Dict[str, Dict[str, Any]] = {}
        self._carregar_base()

    # ------------------------------------------------------------ perfis
    def _carregar_base(self) -> None:
        for arq in sorted(PASTA_PERFIS.glob("*.json")):
            try:
                with open(arq, "r", encoding="utf-8") as f:
                    p = json.load(f)
                self._perfis_base[p["id"]] = p
            except (OSError, ValueError, KeyError):
                continue

    def listar_especialidades(self) -> List[Dict[str, str]]:
        ids = [i for i in ORDEM_ESPECIALIDADES if i in self._perfis_base]
        ids += [i for i in sorted(self._perfis_base) if i not in ids]
        return [{"id": i, "nome": self._perfis_base[i].get("nome", i)} for i in ids]

    def nome_especialidade(self, id_especialidade: str) -> str:
        p = self._perfis_base.get(id_especialidade)
        return p.get("nome", id_especialidade) if p else id_especialidade

    def perfil_base(self, id_especialidade: str) -> Dict[str, Any]:
        p = self._perfis_base.get(id_especialidade) or self._perfis_base.get("outro")
        if p is None:
            raise ValueError("Nenhum perfil instrumental disponível.")
        return json.loads(json.dumps(p))

    def perfil_especialidade(self, id_especialidade: str) -> Dict[str, Any]:
        base = self.perfil_base(id_especialidade)
        if self.pasta_perfis_editados:
            arq = self.pasta_perfis_editados / f"{id_especialidade}.json"
            if arq.exists():
                try:
                    with open(arq, "r", encoding="utf-8") as f:
                        editado = json.load(f)
                    base.update({k: v for k, v in editado.items() if k != "id"})
                    base["editado_pelo_professor"] = True
                except (OSError, ValueError):
                    pass
        return base

    # ----------------------------------------------------------- rubrica
    def rubrica_padrao(self, especialidade: str, modalidade: str, idade: Optional[int]) -> List[str]:
        perfil = self.perfil_especialidade(especialidade)
        do_perfil = list(perfil.get("criterios_avaliacao") or [])
        if modalidade in ("turma", "coral", "banda", "pratica_conjunto", "oficina", "musicalizacao"):
            base = RUBRICA_COLETIVA if not do_perfil or especialidade == "outro" else do_perfil
            if "participacao" not in base:
                base = ["participacao"] + base
        elif especialidade in ("percepcao_musical", "teoria_musical"):
            base = do_perfil or RUBRICA_PERCEPCAO
        else:
            base = do_perfil or RUBRICA_INSTRUMENTO
        if idade is not None and idade <= 8 and "autonomia" in base:
            base = [c for c in base if c != "autonomia"] + ["participacao"] if "participacao" not in base else base
        return list(dict.fromkeys(base))[:7]

    # -------------------------------------------------------- progressão
    def tema_do_conteudo(self, perfil: Dict[str, Any], conteudo: str) -> Optional[str]:
        k = _norm(conteudo)
        if not k:
            return None
        for tema, etapas in (perfil.get("progressoes") or {}).items():
            for e in etapas:
                if _norm(e) == k:
                    return tema
        for tema, etapas in (perfil.get("progressoes") or {}).items():
            for e in etapas:
                ne = _norm(e)
                if k in ne or ne in k:
                    return tema
        for tema in (perfil.get("progressoes") or {}):
            if _norm(tema) in k or k in _norm(tema):
                return tema
        return None

    def progressao_sugerida(self, estado_atual: Dict[str, Any], perfil: Dict[str, Any], curriculo: str) -> Dict[str, str]:
        consolidados = {_norm(c) for c in estado_atual.get("conteudos_consolidados", [])}
        em_dev = [c for c in estado_atual.get("em_desenvolvimento", [])]
        recorrentes = estado_atual.get("dificuldades_recorrentes", [])
        proximo = (estado_atual.get("proximo_objetivo") or "").strip()
        progressoes: Dict[str, List[str]] = perfil.get("progressoes") or {}
        prereqs: Dict[str, List[str]] = perfil.get("pre_requisitos") or {}

        # 1) dificuldade recorrente que é um CONTEÚDO da progressão → consolidar antes de ampliar
        for d in recorrentes:
            tema_d = self.tema_do_conteudo(perfil, d)
            if tema_d and _norm(d) not in consolidados:
                return {
                    "conteudo": d,
                    "tema": tema_d,
                    "justificativa": (
                        f"'{d}' apareceu como dificuldade em duas ou mais aulas. "
                        "Consolidar antes de ampliar evita acumular instabilidade nos próximos conteúdos."
                    ),
                }
        # dificuldade recorrente descritiva (ex.: "acelera no final das frases") orienta a justificativa
        sufixo_dif = ""
        if recorrentes:
            sufixo_dif = (
                f" A dificuldade recorrente '{recorrentes[0]}' deve ser trabalhada dentro deste conteúdo, "
                "consolidando antes de ampliar."
            )
        # 2) próximo objetivo declarado pelo professor
        if proximo and _norm(proximo) not in consolidados:
            return {
                "conteudo": proximo,
                "tema": self.tema_do_conteudo(perfil, proximo) or "",
                "justificativa": "Objetivo indicado pelo professor na última aula registrada." + sufixo_dif,
            }
        # 3) conteúdo em desenvolvimento mais recente
        if em_dev:
            alvo = em_dev[-1]
            return {
                "conteudo": alvo,
                "tema": self.tema_do_conteudo(perfil, alvo) or "",
                "justificativa": f"'{alvo}' ainda está em desenvolvimento; retomar garante continuidade antes de introduzir algo novo." + sufixo_dif,
            }
        # 4) próximo item da progressão do perfil ainda não consolidado, respeitando pré-requisitos
        ordem_temas = ["pulsacao", "tecnica", "leitura", "percepcao", "repertorio"]
        temas = [t for t in ordem_temas if t in progressoes] + [t for t in progressoes if t not in ordem_temas]
        for tema in temas:
            for etapa in progressoes[tema]:
                if _norm(etapa) in consolidados:
                    continue
                faltam = [p for p in prereqs.get(etapa, []) if _norm(p) not in consolidados]
                if faltam:
                    # sugere o pré-requisito pendente
                    return {
                        "conteudo": faltam[0],
                        "tema": self.tema_do_conteudo(perfil, faltam[0]) or tema,
                        "justificativa": f"'{faltam[0]}' é pré-requisito de '{etapa}' e ainda não está consolidado.",
                    }
                return {
                    "conteudo": etapa,
                    "tema": tema,
                    "justificativa": f"Próxima etapa da progressão de {tema.replace('_', ' ')} do perfil de {perfil.get('nome', 'instrumento')} ainda não consolidada.",
                }
        return {"conteudo": "revisão geral", "tema": "", "justificativa": "Todas as etapas do perfil constam como consolidadas; sugerimos revisão e ampliação de repertório."}

    # -------------------------------------------------------- exercícios
    def exercicios_para(self, perfil: Dict[str, Any], conteudo: str, recursos: List[str], idade: Optional[int], maximo: int = 4) -> List[Dict[str, Any]]:
        tema = self.tema_do_conteudo(perfil, conteudo)
        todos: Dict[str, List[Dict[str, Any]]] = perfil.get("tipos_de_exercicios") or {}
        candidatos: List[Dict[str, Any]] = []
        k = _norm(conteudo)
        if tema and tema in todos:
            exatos = [e for e in todos[tema] if any(_norm(c) == k for c in e.get("conteudos", []))]
            outros = [e for e in todos[tema] if e not in exatos]
            candidatos = exatos + outros
        candidatos += todos.get("geral", [])
        rec = set(recursos or [])
        sem_restricao = not rec or "nenhum" in rec
        saida = []
        for e in candidatos:
            exig = set(e.get("recursos") or [])
            if exig and not sem_restricao and not exig <= rec:
                continue
            if exig and sem_restricao and rec == {"nenhum"} and exig - {"nenhum"}:
                continue
            if idade is not None:
                if idade < int(e.get("idade_min", 0)) or idade > int(e.get("idade_max", 999)):
                    continue
            saida.append(e)
            if len(saida) >= maximo:
                break
        if not saida:
            saida = candidatos[:maximo]
        return saida

    def dificuldades_esperadas(self, perfil: Dict[str, Any], conteudo: str) -> List[str]:
        lista = list(perfil.get("dificuldades_frequentes") or [])
        k = _norm(conteudo)
        relacionadas = [d for d in lista if any(w in _norm(d) for w in k.split() if len(w) > 3)]
        return (relacionadas + [d for d in lista if d not in relacionadas])[:3]

    # ------------------------------------------------------- vocabulário
    def vocabulario(self, especialidade: str) -> Dict[str, List[str]]:
        p = self.perfil_especialidade(especialidade)
        return {"pt": list(p.get("vocabulario_pt") or []), "en": list(p.get("vocabulario_en") or [])}

    def sinonimos_pedagogicos(self) -> Dict[str, List[str]]:
        return SINONIMOS

    def expandir_consulta(self, tema: str, especialidade: str, nivel: str) -> List[str]:
        p = self.perfil_especialidade(especialidade)
        nome_pt = p.get("nome", especialidade)
        nome_en = NOMES_EN.get(especialidade) or p.get("nome_en") or nome_pt
        nivel_pt = {"iniciante": "iniciante", "basico": "básico", "intermediario": "intermediário", "avancado": "avançado"}.get(nivel, nivel)
        nivel_en = {"iniciante": "beginner", "basico": "elementary", "intermediario": "intermediate", "avancado": "advanced"}.get(nivel, "")
        tema_n = _norm(tema)
        sin: List[str] = []
        for chave, lista in SINONIMOS.items():
            if chave in tema_n.replace(" ", "") or chave in tema_n:
                sin.extend(lista)
        tema_en = next((s for s in sin if all(ord(c) < 128 for c in s) and s.lower() != tema_n), "")
        consultas = [
            f"{tema} {nome_pt} ensino",
            f"{tema} {nome_pt} {nivel_pt}",
            f"{tema} pedagogia musical",
        ]
        if tema_en:
            consultas += [f"{tema_en} {nome_en} pedagogy", f"{nivel_en} {nome_en} {tema_en}".strip(), f"{nome_en} teaching {tema_en}"]
        else:
            consultas += [f"{tema} {nome_en} pedagogy", f"{nivel_en} {nome_en} {tema}".strip()]
        vistos = set()
        saida = []
        for c in consultas:
            c = " ".join(c.split())
            if c.lower() not in vistos:
                vistos.add(c.lower())
                saida.append(c)
        return saida

    # ----------------------------------------------------- determinístico
    def gerar_material_deterministico(self, tipo: str, parametros: Dict[str, Any]) -> Dict[str, Any]:
        destino = Path(parametros.get("destino", "."))
        nome = parametros.get("nome_base", tipo)
        if tipo == "escala":
            arquivos = theory.gerar_escala_arquivos(
                parametros.get("tonica", "C"), parametros.get("tipo_escala", "maior"), int(parametros.get("oitava", 4)), destino, nome
            )
            notas = theory.notas_escala(parametros.get("tonica", "C"), parametros.get("tipo_escala", "maior"), int(parametros.get("oitava", 4)))
            return {"arquivos": arquivos, "descricao": "Escala " + ", ".join(theory.nome_nota_pt(n) for n in notas)}
        if tipo == "arpejo":
            arquivos = theory.gerar_arpejo_arquivos(
                parametros.get("tonica", "C"), parametros.get("qualidade", "maior"), int(parametros.get("oitava", 4)), destino, nome
            )
            return {"arquivos": arquivos, "descricao": f"Arpejo de {theory.nome_nota_pt(parametros.get('tonica', 'C'))} {parametros.get('qualidade', 'maior')}"}
        if tipo == "padrao_ritmico":
            figs = [float(x) for x in parametros.get("figuras", [1, 1, 0.5, 0.5, 1])]
            arquivos = theory.gerar_padrao_ritmico_arquivos(figs, parametros.get("compasso", "4/4"), destino, nome)
            return {"arquivos": arquivos, "descricao": f"Padrão rítmico em {parametros.get('compasso', '4/4')}"}
        raise ValueError(f"Tipo de material desconhecido: {tipo}")

    def validar_conteudo(self, texto: str) -> List[str]:
        try:
            return theory.validar_texto_musical(texto or "")
        except Exception:
            return []

    def rotulo_criterio(self, id_criterio: str) -> str:
        from ...core import grading

        return grading.rotulo(id_criterio)
