# 🤖 Agentes do MMarra Data Hub

**Versão:** 1.0.0
**Data:** 2026-02-03

---

## 📋 Visão Geral

Agentes são **módulos Python permanentes** que executam tarefas automatizadas no Data Hub.

> ⚠️ **IMPORTANTE:** Agentes NÃO são sub-agentes do Claude Code ou comandos `/agent`. São código Python em `src/agents/`.

---

## 🎯 Agentes Disponíveis

| Agente | Função | Usa LLM? | Status |
|--------|--------|----------|--------|
| [**Engenheiro**](engineer.md) | ETL: Sankhya → Data Lake | ❌ Não | ✅ Operacional |
| **Analista** | KPIs, relatórios, dashboards | ❌ Não | 📋 Futuro |
| [**Cientista**](scientist.md) | ML, previsões, anomalias | ❌ Não | ✅ Operacional |
| [**LLM**](llm.md) | Chat natural, tools, RAG | ✅ Sim | ✅ Operacional |

---

## 📁 Estrutura

```
src/agents/
├── __init__.py
│
├── engineer/              # 🔧 Agente Engenheiro ✅
│   ├── extractors/
│   ├── transformers/
│   ├── loaders/
│   ├── orchestrator.py
│   └── scheduler.py
│
├── analyst/               # 📈 Agente Analista (futuro)
│   ├── kpis.py
│   ├── reports.py
│   └── dashboards.py
│
├── scientist/             # 🔬 Agente Cientista ✅
│   ├── forecasting/       # Prophet (previsao demanda)
│   ├── anomaly/           # Isolation Forest
│   ├── clustering/        # K-Means (clientes/produtos)
│   └── utils/             # Feriados, metricas
│
├── orchestrator/          # 🤖 Agente LLM ✅
│   ├── config.py          # Configuracoes Groq
│   ├── agent.py           # Orquestrador principal
│   └── tools.py           # Tools (forecast, KPIs)
│
└── shared/
    └── rag/               # 📚 Sistema RAG ✅
        ├── embeddings.py  # TF-IDF
        ├── vectorstore.py # Busca vetorial
        └── retriever.py   # Interface de busca
```

---

## 🚀 Como Usar

### Agente Engenheiro

```python
from src.agents.engineer import Orchestrator

# Pipeline completo
orchestrator = Orchestrator()
results = orchestrator.run_full_pipeline()
```

### Agente Cientista

```python
from src.agents.scientist import DemandForecastModel

model = DemandForecastModel()
model.fit(df_vendas, codprod=12345)
resultado = model.get_forecast_summary(periods=30)
```

### Agente LLM (Chat)

```bash
# Chat interativo
python scripts/chat_ia.py
```

```python
from src.agents.orchestrator import OrchestratorAgent

agent = OrchestratorAgent()
resposta = agent.ask("Quanto vendemos essa semana?")
```

### Via CLI

```bash
# Engenheiro
python -m src.agents.engineer.orchestrator
python -m src.agents.engineer.scheduler --run-once

# Chat IA
python scripts/chat_ia.py
```

---

## 🛠️ Tecnologias

| Agente | Bibliotecas |
|--------|-------------|
| Engenheiro | requests, pandas, pyarrow |
| Analista | pandas, plotly, jinja2 |
| Cientista | scikit-learn, prophet |
| LLM | langchain, langchain-groq |
| RAG | scikit-learn (TF-IDF) |

---

## 📚 Documentação

- [Agente Engenheiro](engineer.md) - ETL Sankhya -> Data Lake
- Agente Analista (em breve)
- [Agente Cientista](scientist.md) - ML: Prophet, Isolation Forest, K-Means
- [Agente LLM](llm.md) - Chat com Groq + RAG
