# 🏢 MMarra Data Hub

**Plataforma de Dados Inteligente para MMarra Distribuidora Automotiva**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Sankhya](https://img.shields.io/badge/ERP-Sankhya-orange.svg)](https://sankhya.com.br)
[![Azure](https://img.shields.io/badge/Cloud-Azure-0078D4.svg)](https://azure.microsoft.com)

> *"O centro de conexão entre dados, análises e decisões"*

---

## 📋 Visão Geral

O **MMarra Data Hub** é uma plataforma que integra o **Sankhya ERP** com **Azure Data Lake**, permitindo:

- 🔄 **ETL automatizado** - Extração diária de dados do ERP
- 🤖 **Agentes de IA** - Análises inteligentes e previsões
- 💬 **Chat Natural** - Perguntas em linguagem natural sobre o negócio
- 📊 **Relatórios** - Geração automática de insights

```
"Qual o total de vendas do último mês?"
"Quantos pedidos de compra estão pendentes?"
"Previsão de demanda para o produto X?"
```

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MMARRA DATA HUB v2.0                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   FONTES                           ARMAZENAMENTO                            │
│   ┌──────────┐                     ┌─────────────────────────────────────┐  │
│   │ SANKHYA  │──── Python ────────►│  AZURE DATA LAKE                    │  │
│   │   API    │     Extractor       │                                     │  │
│   └──────────┘                     │  /raw/vendas/                       │  │
│                                    │  /raw/compras/                      │  │
│                                    │  /raw/estoque/                      │  │
│                                    │  /raw/clientes/                     │  │
│                                    └──────────────┬──────────────────────┘  │
│                                                   │                         │
│                                                   ▼                         │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    AGENTES DE IA (100% Autônomos)                   │   │
│   │                                                                     │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │   │
│   │  │  ENGENHEIRO │  │   ANALISTA  │  │  CIENTISTA  │                  │   │
│   │  │             │  │             │  │             │                  │   │
│   │  │ • Extrai    │  │ • KPIs      │  │ • Previsões │                  │   │
│   │  │ • Valida    │  │ • Relatórios│  │ • Anomalias │                  │   │
│   │  │ • Carrega   │  │ • Dashboards│  │ • Clusters  │                  │   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘                  │   │
│   │                          │                                          │   │
│   │                          ▼                                          │   │
│   │               ┌─────────────────────┐                               │   │
│   │               │   ORQUESTRADOR LLM  │                               │   │
│   │               │   (Groq + RAG)      │                               │   │
│   │               └─────────────────────┘                               │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Estrutura do Projeto

```
mmarra-data-hub/
│
├── 📄 README.md                 # Este arquivo
├── 📄 CLAUDE.md                 # Instruções para IA (507 linhas)
├── 📄 PROGRESSO_ATUAL.md        # Estado atual do projeto
├── 📄 CHANGELOG.md              # Histórico de versões
├── 📄 .env.example              # Template de credenciais
│
├── 📁 data/                     # 🆕 DADOS (fora do src)
│   ├── raw/                     # Dados brutos extraídos
│   └── processed/               # Dados processados
│
├── 📁 docs/                     # 📚 DOCUMENTAÇÃO
│   ├── agentes/                 # Specs dos agentes
│   ├── api/                     # Documentação API Sankhya
│   ├── bugs/                    # Bugs conhecidos
│   ├── de-para/                 # Mapeamento de tabelas
│   │   └── sankhya/             # Tabelas do Sankhya
│   ├── erros/                   # Erros comuns e soluções
│   ├── guias/                   # Guias práticos
│   ├── investigacoes/           # 🆕 Descobertas documentadas
│   ├── modelos/                 # Documentação ML
│   └── wms/                     # Documentação WMS
│
├── 📁 mcp_sankhya/              # 🔌 MCP Server (Claude Code)
│   ├── server.py
│   └── .env.example
│
├── 📁 output/                   # 📤 OUTPUTS GERADOS
│   ├── divergencias/            # Erros e divergências
│   ├── json/                    # Resultados em JSON
│   └── reports/                 # Relatórios HTML
│
├── 📁 queries/                  # 📝 SQL REUTILIZÁVEIS
│   ├── compras/
│   ├── vendas/
│   ├── estoque/
│   └── financeiro/
│
├── 📁 scripts/                  # 🔧 SCRIPTS UTILITÁRIOS
│   ├── extracao/                # Extração de dados
│   ├── investigacao/            # Análises ad-hoc
│   ├── relatorios/              # Geração de relatórios
│   └── testes/                  # Testes manuais
│
├── 📁 src/                      # 📦 CÓDIGO FONTE
│   ├── agents/                  # Agentes de IA
│   │   ├── analyst/             # Agente Analista
│   │   ├── engineer/            # Agente Engenheiro
│   │   ├── llm/                 # Agente LLM
│   │   ├── orchestrator/        # Orquestrador
│   │   ├── scientist/           # Agente Cientista
│   │   └── shared/              # Compartilhado (RAG)
│   ├── pipelines/               # Pipelines de dados
│   └── utils/                   # Utilitários
│
├── 📁 tests/                    # 🧪 TESTES
│
└── 📁 postman/                  # 📮 COLLECTIONS POSTMAN
```

---

## 🚀 Quick Start

### 1. Clonar e configurar ambiente

```bash
# Clonar
git clone https://github.com/italoogomes/mmarra-data-hub.git
cd mmarra-data-hub

# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar credenciais

```bash
# Copiar template
cp .env.example .env
cp mcp_sankhya/.env.example mcp_sankhya/.env

# Editar com suas credenciais
# SANKHYA_CLIENT_ID=...
# SANKHYA_CLIENT_SECRET=...
# SANKHYA_X_TOKEN=...
```

### 3. Executar

```bash
# Chat com IA
python scripts/chat_ia.py "Qual o faturamento do mês?"

# ETL completo
python scripts/extracao/extrair_tudo.py

# MCP Server (para Claude Code)
python -m mcp_sankhya.server
```

---

## 🤖 Agentes

| Agente | Função | LLM? | Status |
|--------|--------|------|--------|
| **Engenheiro** | ETL: Sankhya → Data Lake | ❌ | ✅ Operacional |
| **Analista** | KPIs, relatórios, dashboards | ❌ | ✅ Operacional |
| **Cientista** | ML: Prophet, Clustering | ❌ | ✅ Operacional |
| **LLM** | Chat natural + RAG | ✅ Groq | ✅ Operacional |

### Como funciona o Chat IA

```python
from src.agents.orchestrator import OrchestratorAgent

agent = OrchestratorAgent()
resposta = agent.ask("Quanto vendemos essa semana?")
print(resposta)
```

---

## 📊 Dados Disponíveis

| Dataset | Tabela Sankhya | Descrição |
|---------|---------------|-----------|
| Vendas | TGFCAB + TGFITE | Notas de venda |
| Compras | TGFCAB + TGFITE | Pedidos de compra |
| Clientes | TGFPAR | Parceiros (clientes/fornecedores) |
| Produtos | TGFPRO | Catálogo de produtos |
| Estoque | TGFEST + TGWEST | Posição de estoque |
| Financeiro | TGFFIN | Títulos a pagar/receber |

---

## 🔧 Tecnologias

| Camada | Tecnologia |
|--------|------------|
| **Linguagem** | Python 3.10+ |
| **ERP** | Sankhya (API REST) |
| **Cloud** | Azure Data Lake Gen2 |
| **ML** | Prophet, scikit-learn |
| **LLM** | Groq (Qwen 32B) |
| **RAG** | TF-IDF + Cosine Similarity |
| **Formato** | Parquet |

---

## 📚 Documentação

| Documento | Descrição |
|-----------|-----------|
| [CLAUDE.md](CLAUDE.md) | Instruções para IA |
| [PROGRESSO_ATUAL.md](PROGRESSO_ATUAL.md) | Estado atual |
| [docs/api/sankhya.md](docs/api/sankhya.md) | API Sankhya |
| [docs/de-para/sankhya/](docs/de-para/sankhya/) | Mapeamento tabelas |
| [docs/investigacoes/](docs/investigacoes/) | Descobertas |

---

## 👨‍💻 Autor

**Ítalo Gomes** - MMarra Distribuidora Automotiva

---

## 📄 Licença

MIT License - veja [LICENSE](LICENSE)

---

*Versão 2.0 - Fevereiro 2026*
