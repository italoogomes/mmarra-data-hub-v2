# Agente LLM (Orquestrador) - MMarra Data Hub

**Status:** Operacional
**Versao:** 1.0.0
**Ultima Atualizacao:** 2026-02-04

---

## Visao Geral

O Agente LLM e o orquestrador inteligente do Data Hub. Ele:
- Entende perguntas em linguagem natural
- Chama os outros agentes (Cientista, Analista) via tools
- Busca documentacao via RAG
- Responde em portugues com explicacoes claras

**IMPORTANTE:** O Agente LLM e o UNICO que usa LLM (Groq). Os outros agentes (Engenheiro, Cientista, Analista) sao codigo Python puro.

---

## Arquitetura

```
src/agents/
├── orchestrator/              # Orquestrador LLM
│   ├── __init__.py
│   ├── config.py              # Configuracoes Groq/LLM
│   ├── agent.py               # Agente principal com tools
│   └── tools.py               # Tools: forecast, KPIs, etc
│
└── shared/
    └── rag/                   # Sistema RAG (usado pelo orquestrador)
        ├── __init__.py
        ├── embeddings.py      # TF-IDF embeddings (offline)
        ├── vectorstore.py     # Armazenamento e busca de docs
        └── retriever.py       # Interface de busca
```

---

## Configuracao

### Variaveis de Ambiente (.env)

```bash
# LLM Provider
GROQ_API_KEY=gsk_sua_chave_aqui
LLM_MODEL=qwen/qwen3-32b

# Alternativos (verificar disponibilidade)
# LLM_MODEL=llama-3.1-8b-instant
# LLM_MODEL=gemma2-9b-it
```

### Modelos Disponiveis no Groq

Para listar modelos ativos:
```bash
python scripts/listar_modelos_groq.py
```

Modelos testados e funcionais com tools:
- `qwen/qwen3-32b` (recomendado)
- `llama-3.1-8b-instant`

**NOTA:** Alguns modelos foram descontinuados (llama-3.3-70b-versatile, mixtral-8x7b-32768).

---

## Como Usar

### Chat Interativo

```bash
# Iniciar chat
python scripts/chat_ia.py
```

Comandos especiais no chat:
- `sair` ou `exit` - Encerra o chat
- `limpar` ou `clear` - Limpa historico

### Exemplos de Perguntas

```
# Vendas e KPIs
> Quanto vendemos essa semana?
> Quais os KPIs de vendas do mes?
> Como foi o faturamento de janeiro?

# Previsoes (chama Agente Cientista)
> Qual a previsao de vendas para os proximos 30 dias?
> Quanto vou vender do produto 261301?

# Documentacao (usa RAG)
> O que significa o campo TIPMOV?
> Quais tabelas armazenam pedidos de compra?
> Quais bugs ja encontramos no WMS?
```

### Via Codigo Python

```python
from src.agents.orchestrator import OrchestratorAgent

agent = OrchestratorAgent()

# Pergunta simples
resposta = agent.ask("Quanto vendemos essa semana?")
print(resposta)

# Com historico de conversa
agent.ask("Quais os KPIs de vendas?")
agent.ask("E do mes passado?")  # Lembra o contexto
```

---

## Tools Disponiveis

O Agente LLM tem acesso a estas ferramentas:

| Tool | Descricao | Quando Usar |
|------|-----------|-------------|
| `search_documentation` | Busca na documentacao do projeto (RAG) | "o que e TIPMOV?", "quais tabelas de pedido?" |
| `forecast_demand` | Previsao de demanda (Prophet) | "previsao de vendas", "quanto vou vender" |
| `get_kpis` | Indicadores de desempenho | "KPIs", "metricas", "faturamento" |

### search_documentation (RAG)

```python
@tool
def search_documentation(query: str) -> str:
    """
    Busca informacoes na documentacao do projeto.

    Fontes indexadas:
    - docs/de-para/sankhya/*.md (estrutura de tabelas)
    - docs/investigacoes/*.md (descobertas)
    - docs/bugs/*.md (problemas conhecidos)
    - docs/wms/*.md (documentacao WMS)
    - queries/**/*.sql (queries SQL uteis)
    - output/divergencias/*.txt (divergencias encontradas)
    """
```

### forecast_demand

```python
@tool
def forecast_demand(codprod: int, periods: int = 30) -> str:
    """
    Faz previsao de demanda usando Prophet.

    Args:
        codprod: Codigo do produto
        periods: Dias para prever (padrao: 30)

    Returns:
        Texto com previsao formatada
    """
```

### get_kpis

```python
@tool
def get_kpis(modulo: str, periodo: str = "mes_atual") -> str:
    """
    Retorna KPIs do modulo especificado.

    Args:
        modulo: 'vendas', 'estoque', 'compras', 'clientes'
        periodo: 'hoje', 'semana', 'mes_atual', 'mes_anterior'

    Returns:
        Texto com KPIs formatados
    """
```

---

## Sistema RAG

### O que e RAG?

RAG (Retrieval Augmented Generation) permite que o LLM busque informacoes na documentacao do projeto antes de responder.

### Como Funciona

```
1. Usuario pergunta: "O que significa TIPMOV?"
           |
           v
2. RAG busca documentos similares
   - docs/de-para/sankhya/*.md
   - queries/*.sql
           |
           v
3. Encontra: "TIPMOV = Tipo de Movimentacao (P=Pedido, V=Venda...)"
           |
           v
4. LLM recebe contexto + pergunta
           |
           v
5. LLM explica: "TIPMOV indica o tipo de movimentacao..."
```

### Fontes Indexadas

```python
DOCUMENT_SOURCES = [
    {"path": "docs/de-para/sankhya", "glob": "*.md"},    # Mapeamento tabelas
    {"path": "docs/investigacoes", "glob": "*.md"},      # Investigacoes
    {"path": "docs/bugs", "glob": "*.md"},               # Bugs conhecidos
    {"path": "docs/agentes", "glob": "*.md"},            # Specs agentes
    {"path": "docs/wms", "glob": "*.md"},                # Documentacao WMS
    {"path": "docs/api", "glob": "*.md"},                # Documentacao API
    {"path": "queries", "glob": "**/*.sql"},             # Queries SQL
    {"path": "output/divergencias", "glob": "*.txt"},    # Divergencias
]
```

### Reconstruir Indice RAG

Quando adicionar nova documentacao:

```python
from src.agents.shared.rag import DocumentStore

store = DocumentStore()
n_chunks = store.build_index(force=True)
print(f"Indice reconstruido com {n_chunks} chunks")
```

Ou via script:
```bash
python -c "from src.agents.shared.rag import build_rag_index; build_rag_index(force=True)"
```

### Embeddings TF-IDF

O RAG usa TF-IDF (Term Frequency-Inverse Document Frequency) para busca semantica.

**Vantagens:**
- 100% offline (nao precisa de API)
- Rapido e leve
- Funciona bem para portugues

**Limitacoes:**
- Menos preciso que embeddings neurais
- Nao entende sinonimos profundos

---

## Fluxo de Execucao

```
Usuario: "Quanto vendemos essa semana?"
              |
              v
    ┌──────────────────┐
    │   ORQUESTRADOR   │
    │    (agent.py)    │
    └────────┬─────────┘
             │
    Analisa pergunta e decide: usar tool get_kpis
             │
             v
    ┌──────────────────┐
    │    TOOL: KPIs    │
    │   (tools.py)     │
    └────────┬─────────┘
             │
    Busca dados no Data Lake / Sankhya
             │
             v
    ┌──────────────────┐
    │   ORQUESTRADOR   │
    │  (formata resp)  │
    └────────┬─────────┘
             │
             v
    "As vendas desta semana totalizaram R$ 125.430,00..."
```

---

## Limitacoes Conhecidas

1. **Modelo pode variar** - Modelos Groq sao descontinuados periodicamente
2. **Tools simples** - Ainda nao conecta com banco de dados real
3. **Contexto limitado** - Historico de ~10 mensagens
4. **Sem cache** - Cada pergunta faz nova chamada ao LLM

---

## Troubleshooting

### Erro: Model decommissioned

```
BadRequestError: Model has been decommissioned
```

**Solucao:** Listar modelos ativos e atualizar .env:
```bash
python scripts/listar_modelos_groq.py
# Atualizar LLM_MODEL no .env
```

### Erro: tool_use_failed

```
tool_use_failed: '<function=get_kpis...
```

**Causa:** Modelo nao suporta tool calling corretamente.
**Solucao:** Usar modelo compativel (`qwen/qwen3-32b`).

### Erro: UnicodeEncodeError (Windows)

```
UnicodeEncodeError: 'charmap' codec can't encode
```

**Solucao:** Scripts ja tratam isso, mas se persistir:
```bash
chcp 65001
set PYTHONIOENCODING=utf-8
python scripts/chat_ia.py
```

---

## Dependencias

```
# requirements.txt
langchain>=0.1.0
langchain-groq>=0.1.0
langchain-core>=0.1.0
scikit-learn>=1.3.0       # Para TF-IDF
numpy>=1.24.0
python-dotenv>=1.0.0
```

---

## Proximos Passos

- [ ] Conectar tools com banco de dados real (Sankhya/Data Lake)
- [ ] Implementar cache de respostas
- [ ] Adicionar mais tools (consulta de clientes, produtos, estoque)
- [ ] Melhorar embeddings (modelo neural quando possivel)
- [ ] Implementar historico persistente
- [ ] Adicionar interface web (Streamlit/Gradio)

---

## Changelog

### v1.0.0 (2026-02-04)
- Implementacao inicial do orquestrador
- Integracao com Groq (modelo qwen/qwen3-32b)
- Tools: search_documentation, forecast_demand, get_kpis
- Sistema RAG com TF-IDF (617 chunks indexados)
- Chat interativo via scripts/chat_ia.py
