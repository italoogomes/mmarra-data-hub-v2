# 🤖 Instruções para Claude - MMarra Data Hub

> Este arquivo é lido automaticamente pelo Claude Code no VS Code.

---

## 📋 REGRAS OBRIGATÓRIAS

### 1. Antes de Qualquer Coisa
- **SEMPRE** leia `PROGRESSO_ATUAL.md` para entender onde paramos (estado atual + sessao mais recente)
- **SEMPRE** consulte `PROGRESSO_HISTORICO.md` se precisar de contexto de sessoes anteriores (4-8)
- **SEMPRE** consulte `docs/` antes de modificar código
- **SEMPRE** pergunte qual tarefa o usuário quer continuar

### 2. Durante o Trabalho
- Faça **um passo de cada vez** e confirme antes de prosseguir
- **Documente tudo** que fizer em `docs/` e `PROGRESSO_ATUAL.md`
- Siga o estilo dos arquivos existentes
- Teste credenciais e tokens antes de rodar extrações

### 3. Sobre Tokens/Contexto ⚠️ CRÍTICO
- **SEMPRE INFORME** o status dos tokens quando o usuário perguntar
- **SEMPRE AVISE PROATIVAMENTE** quando atingir 60% de uso
- **SUGIRA** salvar o progresso quando atingir 70%
- **DOCUMENTE TUDO** antes de atingir 80%
- **FORMATO**: "📊 Tokens: X/200.000 (Y%) - Z tokens restantes"

### 4. Ao Finalizar Qualquer Tarefa
- Atualize `PROGRESSO_ATUAL.md` com o que foi feito
- Atualize `CHANGELOG.md` se houver mudança de versão
- Liste os próximos passos claros

### 5. Documentação Obrigatória

| O que mudou | Onde documentar |
|-------------|-----------------|
| Nova tabela mapeada | `docs/de-para/sankhya/[modulo].md` |
| Novo script | `docs/scripts/README.md` |
| Estrutura Data Lake | `docs/data-lake/estrutura.md` |
| Novo agente | `docs/agentes/[nome].md` |
| Novo modelo ML | `docs/modelos/[nome].md` |
| Qualquer mudança | `PROGRESSO_ATUAL.md` + `CHANGELOG.md` |
| Sessao finalizada | Mover sessao antiga para `PROGRESSO_HISTORICO.md`, manter apenas a mais recente em `PROGRESSO_ATUAL.md` |

---

## 📁 ORGANIZAÇÃO DE ARQUIVOS - SEMPRE SEGUIR

### Onde Salvar Cada Tipo de Arquivo

| Tipo | Pasta | Padrão de Nome | Exemplo |
|------|-------|----------------|---------|
| Mapeamento de tabelas | `docs/de-para/sankhya/` | `[tabela].md` | `tgfcab.md` |
| Investigações/Descobertas | `docs/investigacoes/` | `YYYY-MM-DD_[assunto].md` | `2026-02-04_fluxo_wms.md` |
| Bugs/Problemas encontrados | `docs/bugs/` | `YYYY-MM-DD_[descricao].md` | `2026-02-04_cfop_errado.md` |
| Queries SQL úteis | `queries/[modulo]/` | `[descricao].sql` | `queries/compras/pendentes.sql` |
| Relatórios gerados | `output/reports/` | `YYYY-MM-DD_[nome].html` | `2026-02-04_vendas_semana.html` |
| Divergências/Erros de dados | `output/divergencias/` | `YYYY-MM-DD_[descricao].txt` | `2026-02-04_precos_errados.txt` |
| Dados extraídos | `src/data/raw/[modulo]/` | `[tabela].parquet` | `src/data/raw/vendas/vendas.parquet` |
| Modelos treinados | `src/agents/scientist/models/` | `[tipo]/[nome].pkl` | `demand/produto_1001.pkl` |

### Regras Obrigatórias de Organização

1. **SEMPRE** usar data no início (YYYY-MM-DD) para investigações, bugs, relatórios e divergências
2. **SEMPRE** salvar descobertas em `docs/investigacoes/`
3. **SEMPRE** salvar problemas encontrados em `docs/bugs/`
4. **SEMPRE** salvar queries úteis em `queries/[modulo]/`
5. **NUNCA** criar pastas novas sem documentar aqui
6. **SEMPRE** atualizar `PROGRESSO_ATUAL.md` com o que descobriu

### Para RAG/Aprendizado da IA

A IA aprende consultando estas pastas:
- `docs/de-para/` → Estrutura das tabelas
- `docs/investigacoes/` → Descobertas anteriores
- `docs/bugs/` → Problemas conhecidos
- `queries/` → Queries que funcionam
- `output/divergencias/` → Erros já identificados

**IMPORTANTE:** Sempre que descobrir algo novo, documente na pasta correta para a IA aprender!

---

## 🤖 ARQUITETURA: AGENTES 100% AUTÔNOMOS (CRÍTICO 🔥)

### Conceito Principal

**TODOS os agentes são autônomos** — cada um tem um LLM que decide o que fazer.
Não são scripts pré-configurados. São agentes que **pensam e decidem**.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SISTEMA MULTI-AGENTE AUTÔNOMO                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                         ┌─────────────────────┐                            │
│                         │    ORQUESTRADOR     │                            │
│                         │      (LLM)          │                            │
│                         │                     │                            │
│                         │ "Quem deve agir     │                            │
│                         │  agora?"            │                            │
│                         └──────────┬──────────┘                            │
│                                    │                                        │
│          ┌─────────────────────────┼─────────────────────────┐             │
│          │                         │                         │             │
│          ▼                         ▼                         ▼             │
│  ┌───────────────┐        ┌───────────────┐        ┌───────────────┐      │
│  │  ENGENHEIRO   │        │   ANALISTA    │        │   CIENTISTA   │      │
│  │   AUTÔNOMO    │        │   AUTÔNOMO    │        │   AUTÔNOMO    │      │
│  │               │        │               │        │               │      │
│  │  🧠 LLM +     │        │  🧠 LLM +     │        │  🧠 LLM +     │      │
│  │  Python/SQL   │        │  Python/KPIs  │        │  Python/ML    │      │
│  │               │        │               │        │               │      │
│  │ "Detectei     │        │ "Dados novos  │        │ "Padrão       │      │
│  │  dados novos, │        │  chegaram,    │        │  estranho,    │      │
│  │  vou extrair  │        │  vou analisar │        │  vou treinar  │      │
│  │  e carregar"  │        │  e calcular"  │        │  modelo"      │      │
│  └───────┬───────┘        └───────┬───────┘        └───────┬───────┘      │
│          │                        │                        │               │
│          └────────────────────────┴────────────────────────┘               │
│                                   │                                         │
│                                   ▼                                         │
│                    ┌─────────────────────────────┐                         │
│                    │      AZURE DATA LAKE        │                         │
│                    │         (Parquet)           │                         │
│                    └─────────────────────────────┘                         │
│                                   ▲                                         │
│                                   │                                         │
│                    ┌─────────────────────────────┐                         │
│                    │       SANKHYA ERP           │                         │
│                    │          (API)              │                         │
│                    └─────────────────────────────┘                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 🧠 Como Cada Agente Funciona

Cada agente tem:
1. **LLM** — Para pensar e decidir
2. **Tools** — Funções Python que ele pode chamar
3. **Memória** — Contexto do que já fez

```
┌─────────────────────────────────────────────────────────────────┐
│                    ANATOMIA DE UM AGENTE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                        LLM                               │   │
│  │              (Cérebro do Agente)                         │   │
│  │                                                          │   │
│  │   "Recebi dados de vendas atualizados.                  │   │
│  │    Vou verificar se preciso recalcular KPIs.            │   │
│  │    Sim, a margem mudou. Vou atualizar."                 │   │
│  └─────────────────────────┬───────────────────────────────┘   │
│                            │                                    │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                       TOOLS                              │   │
│  │              (Mãos do Agente)                            │   │
│  │                                                          │   │
│  │   • extrair_dados()      • calcular_kpi()               │   │
│  │   • transformar()        • detectar_anomalia()          │   │
│  │   • carregar_datalake()  • treinar_modelo()             │   │
│  │   • consultar_sankhya()  • gerar_relatorio()            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Os 4 Agentes do Sistema

### 1. 🔧 Agente Engenheiro (ETL Autônomo)

**Função:** Extrai, transforma e carrega dados automaticamente.

**Comportamento Autônomo:**
- Monitora Sankhya por mudanças
- Decide quando extrair novos dados
- Identifica problemas de qualidade
- Corrige e transforma automaticamente
- Carrega no Data Lake

**Exemplo de raciocínio:**
```
LLM do Engenheiro pensa:
"Detectei que a tabela TGFCAB tem 500 registros novos desde ontem.
 Vou extrair esses registros, validar os campos obrigatórios,
 converter datas e carregar no Data Lake em formato Parquet."
```

**Tools disponíveis:**
- `verificar_atualizacoes()` — Checa novos dados no Sankhya
- `extrair_tabela()` — Extrai dados via API
- `validar_dados()` — Valida qualidade
- `transformar()` — Aplica transformações
- `carregar_datalake()` — Salva no Azure

---

### 2. 📈 Agente Analista (KPIs Autônomo)

**Função:** Analisa dados e calcula métricas automaticamente.

**Comportamento Autônomo:**
- Detecta quando dados novos chegam
- Decide quais KPIs recalcular
- Identifica mudanças significativas
- Gera alertas e relatórios

**Exemplo de raciocínio:**
```
LLM do Analista pensa:
"Dados de vendas de janeiro chegaram. Vou calcular:
 - Faturamento total
 - Margem média
 - Top 10 produtos
 - Comparativo com dezembro
 A margem caiu 5%, vou gerar um alerta."
```

**Tools disponíveis:**
- `detectar_dados_novos()` — Monitora Data Lake
- `calcular_kpi()` — Calcula métricas
- `comparar_periodos()` — Análise temporal
- `gerar_alerta()` — Notificações
- `criar_relatorio()` — Relatórios automáticos

---

### 3. 🔬 Agente Cientista (ML Autônomo)

**Função:** Aplica machine learning automaticamente.

**Comportamento Autônomo:**
- Detecta padrões e anomalias
- Decide quando treinar modelos
- Escolhe algoritmos adequados
- Gera previsões automaticamente

**Exemplo de raciocínio:**
```
LLM do Cientista pensa:
"Tenho 2 anos de dados de vendas do produto 1001.
 Vou treinar um modelo Prophet para previsão.
 Detectei sazonalidade semanal e anual.
 Previsão para março: 450 unidades, tendência alta."
```

**Tools disponíveis:**
- `analisar_padrao()` — Identifica padrões nos dados
- `detectar_anomalia()` — Isolation Forest
- `treinar_modelo()` — Prophet, sklearn
- `fazer_previsao()` — Previsões
- `segmentar()` — Clustering K-Means

---

### 4. 🎯 Orquestrador (Coordenador)

**Função:** Coordena os outros agentes e responde usuários.

**Comportamento Autônomo:**
- Recebe perguntas dos usuários
- Decide qual agente acionar
- Combina resultados de múltiplos agentes
- Formata respostas em linguagem natural

**Exemplo de raciocínio:**
```
Usuário: "Qual estoque mínimo do produto 1001?"

Orquestrador pensa:
"Para responder, preciso:
 1. Pedir ao Cientista a previsão de demanda
 2. Pedir ao Engenheiro o lead time do fornecedor
 3. Calcular: (demanda × lead_time) + segurança
 4. Formatar resposta"
```

**Tools disponíveis:**
- `acionar_engenheiro()` — Delega para Engenheiro
- `acionar_analista()` — Delega para Analista
- `acionar_cientista()` — Delega para Cientista
- `combinar_resultados()` — Junta informações
- `responder_usuario()` — Formata resposta

---


## 🔄 Fluxo de Comunicação Entre Agentes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  CENÁRIO: Usuário pergunta "Quais produtos vão faltar semana que vem?"     │
│                                                                             │
│  ┌─────────────┐                                                           │
│  │  USUÁRIO    │                                                           │
│  └──────┬──────┘                                                           │
│         │ "Quais produtos vão faltar?"                                     │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        ORQUESTRADOR                                  │   │
│  │                                                                      │   │
│  │  Pensa: "Preciso de previsão + estoque atual. Vou acionar           │   │
│  │          Cientista e Engenheiro."                                   │   │
│  └──────────────────────────┬──────────────────────────────────────────┘   │
│                             │                                               │
│            ┌────────────────┴────────────────┐                             │
│            ▼                                 ▼                              │
│  ┌──────────────────┐              ┌──────────────────┐                    │
│  │    CIENTISTA     │              │    ENGENHEIRO    │                    │
│  │                  │              │                  │                    │
│  │ "Vou prever      │              │ "Vou buscar      │                    │
│  │  demanda de      │              │  estoque atual   │                    │
│  │  cada produto"   │              │  no Sankhya"     │                    │
│  │                  │              │                  │                    │
│  │ Retorna:         │              │ Retorna:         │                    │
│  │ {1001: 150/sem}  │              │ {1001: 50 un}    │                    │
│  │ {1002: 80/sem}   │              │ {1002: 100 un}   │                    │
│  └────────┬─────────┘              └────────┬─────────┘                    │
│           │                                 │                               │
│           └─────────────┬───────────────────┘                              │
│                         ▼                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        ORQUESTRADOR                                  │   │
│  │                                                                      │   │
│  │  Combina: "Produto 1001 precisa 150, tem 50 → VAI FALTAR           │   │
│  │           Produto 1002 precisa 80, tem 100 → OK"                    │   │
│  └──────────────────────────┬──────────────────────────────────────────┘   │
│                             │                                               │
│                             ▼                                               │
│  ┌─────────────┐                                                           │
│  │  USUÁRIO    │ ◄── "O produto 1001 (Pastilha Freio) vai faltar.        │
│  └─────────────┘      Estoque: 50 un. Demanda prevista: 150 un.          │
│                        Recomendo comprar 100+ unidades urgente."          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Estrutura de Pastas

```
src/agents/
├── __init__.py
├── base.py                    # Classe base para todos os agentes
├── config.py                  # Configurações compartilhadas
│
├── orchestrator/              # 🎯 Orquestrador
│   ├── __init__.py
│   ├── agent.py               # Agente principal
│   ├── prompts.py             # Prompts do orquestrador
│   └── tools.py               # Tools de coordenação
│
├── engineer/                  # 🔧 Engenheiro Autônomo
│   ├── __init__.py
│   ├── agent.py               # Agente com LLM
│   ├── prompts.py             # Prompts específicos
│   ├── tools/                 # Tools de ETL
│   │   ├── __init__.py
│   │   ├── extract.py
│   │   ├── transform.py
│   │   └── load.py
│   └── monitors/              # Monitoramento de dados
│       └── sankhya_monitor.py
│
├── analyst/                   # 📈 Analista Autônomo
│   ├── __init__.py
│   ├── agent.py               # Agente com LLM
│   ├── prompts.py             # Prompts específicos
│   ├── tools/                 # Tools de análise
│   │   ├── __init__.py
│   │   ├── kpis.py
│   │   ├── reports.py
│   │   └── alerts.py
│   └── monitors/              # Monitoramento de KPIs
│       └── datalake_monitor.py
│
├── scientist/                 # 🔬 Cientista Autônomo
│   ├── __init__.py
│   ├── agent.py               # Agente com LLM
│   ├── prompts.py             # Prompts específicos
│   ├── tools/                 # Tools de ML
│   │   ├── __init__.py
│   │   ├── forecasting.py     # Prophet
│   │   ├── anomaly.py         # Isolation Forest
│   │   └── clustering.py      # K-Means
│   ├── models/                # Modelos treinados
│   │   ├── demand/
│   │   └── anomaly/
│   └── utils/
│       ├── holidays.py
│       └── metrics.py
│
└── shared/                    # Compartilhado entre agentes
    ├── __init__.py
    ├── memory.py              # Memória compartilhada
    ├── communication.py       # Comunicação entre agentes
    └── tools/
        ├── sankhya.py         # Acesso ao Sankhya
        └── datalake.py        # Acesso ao Data Lake
```

---

## 🔧 Tecnologias

| Componente | Tecnologia |
|------------|------------|
| **LLM** | OpenAI GPT-4 ou Anthropic Claude (via LangChain) |
| **Framework Agentes** | LangChain Agents ou LangGraph |
| **ETL** | pandas, requests, pyarrow |
| **ML** | Prophet, scikit-learn, numpy |
| **Armazenamento** | Azure Data Lake Gen2 (Parquet) |
| **Fonte** | Sankhya API |

---

## ❌ O que NÃO fazer

1. **NÃO criar scripts pré-configurados** — Agentes decidem sozinhos
2. **NÃO hardcodar extrações** — Engenheiro detecta e decide
3. **NÃO listar KPIs fixos** — Analista identifica o que calcular
4. **NÃO treinar modelos manualmente** — Cientista decide quando treinar

---

## ✅ O que FAZER

1. **Cada agente tem LLM** — Todos pensam e decidem
2. **Tools são genéricas** — Agente escolhe qual usar
3. **Comunicação via Orquestrador** — Coordena os outros
4. **Monitoramento contínuo** — Agentes observam mudanças
5. **Documentar prompts** — Prompts definem personalidade do agente

---

## 🎯 Roadmap

### Fase 1: Fundação ✅
- [x] Estrutura do projeto
- [x] Cliente Sankhya API
- [x] Cliente Azure Data Lake
- [x] MCP Server

### Fase 2: Agente Engenheiro Autônomo 🔄
- [ ] Criar classe base do agente
- [ ] Implementar LLM + Tools
- [ ] Criar monitor de Sankhya
- [ ] Testar extração autônoma

### Fase 3: Agente Analista Autônomo 📋
- [ ] Implementar LLM + Tools
- [ ] Criar monitor de Data Lake
- [ ] Implementar cálculo de KPIs
- [ ] Testar análise autônoma

### Fase 4: Agente Cientista Autônomo 📋
- [ ] Implementar LLM + Tools
- [ ] Criar detecção de padrões
- [ ] Implementar Prophet/sklearn
- [ ] Testar previsões autônomas

### Fase 5: Orquestrador 📋
- [ ] Implementar coordenação
- [ ] Criar comunicação entre agentes
- [ ] Implementar interface de chat
- [ ] Testar sistema completo

---

## 🔐 Variáveis de Ambiente (.env)

```bash
# Sankhya
SANKHYA_BASE_URL=https://api.sankhya.com.br/gateway/v1
SANKHYA_TOKEN=seu_token
SANKHYA_APP_KEY=sua_app_key

# Azure Data Lake
AZURE_STORAGE_ACCOUNT=sua_conta
AZURE_STORAGE_KEY=sua_chave
AZURE_CONTAINER=datahub

# LLM (todos os agentes usam)
LLM_PROVIDER=openai  # ou anthropic
LLM_API_KEY=sua_chave
LLM_MODEL=gpt-4      # ou claude-3-opus
```

---

## 📞 Contato

**Projeto:** MMarra Data Hub
**Responsável:** Ítalo Gomes
**Arquitetura:** Agentes 100% Autônomos

---

**Última atualização:** 2026-02-04
**Versão:** v0.4.0 (Agentes Autônomos)
