# Schema dos perfis instrumentais (`percurso/domains/music/instrument_profiles/<id>.json`)

Um arquivo por instrumento/área. Todos os textos em Português do Brasil, exceto `vocabulario_en`.
Os perfis são hipóteses pedagógicas editáveis, não verdade absoluta.

```json
{
  "id": "flauta_doce",
  "nome": "Flauta doce",
  "familia": "sopro_madeira",
  "tessitura": {"inicial": ["G4", "A4", "B4"], "ampliada": "C4–D6"},
  "postura": ["texto", "..."],
  "tecnicas_fundamentais": ["texto", "..."],
  "pre_requisitos": {"<conteudo>": ["<conteudo que deve vir antes>", "..."]},
  "progressoes": {
    "pulsacao": ["etapa 1", "etapa 2", "..."],
    "leitura": ["..."],
    "tecnica": ["..."],
    "percepcao": ["..."],
    "repertorio": ["..."]
  },
  "dificuldades_frequentes": ["texto", "..."],
  "vocabulario_pt": ["termo", "..."],
  "vocabulario_en": ["term", "..."],
  "tipos_de_exercicios": {
    "pulsacao": [
      {"titulo": "Pulso no corpo", "descricao": "...", "recursos": [], "idade_min": 6, "idade_max": 99, "duracao_min": 5, "conteudos": ["pulsação corporal"]}
    ],
    "leitura": [],
    "tecnica": [],
    "percepcao": [],
    "repertorio": [],
    "geral": []
  },
  "criterios_avaliacao": ["sonoridade", "respiracao", "articulacao", "ritmo", "leitura", "autonomia"],
  "consideracoes_etarias": {"6-8": ["..."], "9-12": ["..."], "13+": ["..."]},
  "editavel": true
}
```

Regras:
- `familia`: um de `teclado`, `cordas_dedilhadas`, `cordas_friccionadas`, `sopro_madeira`, `sopro_metal`, `percussao`, `voz`, `coletivo`, `teoria_percepcao`, `outro`.
- `tessitura` pode ser `null` para áreas sem instrumento (percepção, teoria, musicalização).
- `progressoes`: chaves = temas (mínimo `pulsacao`, `leitura`, `tecnica`, `percepcao`, `repertorio`); cada lista tem 5–8 etapas em ordem pedagógica, da mais simples para a mais complexa. As etapas são strings curtas (≤ 60 caracteres) usadas como "conteúdo" pelo planejador.
- `tipos_de_exercicios`: chaves = os mesmos temas de `progressoes` + `geral`. Cada tema tem 3–6 exercícios. `recursos` usa apenas: `quadro`, `caixa_de_som`, `instrumentos`, `projetor`, `celulares`, `impressao`, `nenhum`. Lista vazia = não exige recurso. `conteudos` lista as etapas de `progressoes` para as quais o exercício serve (strings idênticas às etapas).
- `criterios_avaliacao`: 5–7 ids em snake_case sem acento (ex.: `leitura`, `ritmo`, `tecnica`, `coordenacao`, `percepcao`, `autonomia`, `sonoridade`, `afinacao`, `respiracao`, `articulacao`, `postura`, `participacao`).
- `consideracoes_etarias`: 2–4 itens por faixa.
- `pre_requisitos`: 4–8 entradas, chaves e valores usando as mesmas strings das etapas de `progressoes`.
- `vocabulario_pt` e `vocabulario_en`: 12–25 termos cada, úteis para expansão de busca bibliográfica e acadêmica.
- Diferenciação obrigatória no tema `pulsacao`:
  - piano: corpo → nota única → cinco dedos → alternância de mãos → pequena estrutura
  - flauta_doce: corpo → respiração → ataques → nota repetida → Sol, Lá e Si → frase curta
  - percussao: movimento → pulso → ostinato → subdivisão → coordenação entre grupos
