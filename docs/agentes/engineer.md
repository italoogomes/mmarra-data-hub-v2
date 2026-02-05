# 🔧 Agente Engenheiro de Dados

**Versão:** 1.0.0
**Data:** 2026-02-03
**Status:** ✅ Operacional

---

## 📋 Visão Geral

O Agente Engenheiro de Dados é responsável pelo pipeline ETL (Extract-Transform-Load) do MMarra Data Hub.

| Característica | Valor |
|----------------|-------|
| **Função** | ETL: Sankhya → Data Lake |
| **Usa LLM?** | ❌ Não |
| **Tecnologias** | Python, pandas, pyarrow, requests |
| **Destino** | Azure Data Lake Gen2 (Parquet) |

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENTE ENGENHEIRO                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │
│  │  EXTRACT    │──▶│  TRANSFORM  │──▶│    LOAD     │       │
│  │             │   │             │   │             │       │
│  │ Extractors  │   │ Cleaner     │   │ DataLake    │       │
│  │             │   │ Mapper      │   │ Loader      │       │
│  └─────────────┘   └─────────────┘   └─────────────┘       │
│         │                                    │              │
│         ▼                                    ▼              │
│  ┌─────────────┐                     ┌─────────────┐       │
│  │   SANKHYA   │                     │    AZURE    │       │
│  │     API     │                     │  DATA LAKE  │       │
│  └─────────────┘                     └─────────────┘       │
│                                                              │
│  ┌─────────────────────────────────────────────────┐       │
│  │              ORCHESTRATOR                        │       │
│  │  Coordena o fluxo E → T → L                     │       │
│  └─────────────────────────────────────────────────┘       │
│                                                              │
│  ┌─────────────────────────────────────────────────┐       │
│  │               SCHEDULER                          │       │
│  │  Agenda execuções periódicas                    │       │
│  └─────────────────────────────────────────────────┘       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Estrutura de Arquivos

```
src/agents/engineer/
├── __init__.py              # Exports: Orchestrator, Scheduler
├── config.py                # Configurações do agente
├── orchestrator.py          # Coordena E-T-L
├── scheduler.py             # Agendamento de execuções
│
├── extractors/              # EXTRACT
│   ├── __init__.py
│   ├── base.py              # Classe base abstrata
│   ├── clientes.py          # ClientesExtractor
│   ├── vendas.py            # VendasExtractor
│   ├── produtos.py          # ProdutosExtractor
│   ├── estoque.py           # EstoqueExtractor
│   └── vendedores.py        # VendedoresExtractor
│
├── transformers/            # TRANSFORM
│   ├── __init__.py
│   ├── cleaner.py           # DataCleaner
│   └── mapper.py            # DataMapper
│
└── loaders/                 # LOAD
    ├── __init__.py
    └── datalake.py          # DataLakeLoader
```

---

## 🚀 Como Usar

### Execução Completa (Pipeline Full)

```python
from src.agents.engineer import Orchestrator

orchestrator = Orchestrator()
results = orchestrator.run_full_pipeline()
```

### Entidades Específicas

```python
orchestrator = Orchestrator()
results = orchestrator.run_pipeline(entities=["clientes", "produtos"])
```

### Apenas Extração

```python
orchestrator = Orchestrator()
df = orchestrator.extract("clientes")
```

### Via Linha de Comando

```bash
# Pipeline completo
python -m src.agents.engineer.orchestrator

# Entidades específicas
python -m src.agents.engineer.orchestrator --entities clientes produtos

# Sem upload para Azure
python -m src.agents.engineer.orchestrator --no-upload

# Sem limpeza de dados
python -m src.agents.engineer.orchestrator --no-clean
```

---

## 📊 Entidades Disponíveis

| Entidade | Tabelas Sankhya | Colunas | Usa Range? |
|----------|-----------------|---------|------------|
| `vendedores` | TGFVEN | 6 | Não |
| `clientes` | TGFPAR, TSIBAI, TSICID, TGFVEN | 27 | Sim |
| `produtos` | TGFPRO, TGFGRU | 18 | Sim |
| `estoque` | TGFEST, TGFPRO, TGFLOC | 9 | Sim |
| `vendas` | TGFCAB, TGFITE, TGFPAR, TGFPRO, TGFVEN | 26 | Não |

---

## 🔧 Componentes

### Extractors

Responsáveis por extrair dados do Sankhya via API.

```python
from src.agents.engineer.extractors import ClientesExtractor

extractor = ClientesExtractor()

# Extração simples
df = extractor.extract(apenas_ativos=True)

# Extração por faixas (contorna limite de 5000)
df = extractor.extract_by_range(
    id_column="p.CODPARC",
    id_max=100000,
    range_size=5000
)
```

### Transformers

#### DataCleaner
Limpa e valida dados:
- Remove duplicatas
- Preenche valores nulos
- Normaliza strings
- Valida tipos de dados

```python
from src.agents.engineer.transformers import DataCleaner

cleaner = DataCleaner()
df_limpo = cleaner.clean(df, entity="clientes")
```

#### DataMapper
Transforma dados para o modelo de destino:
- Renomeia colunas
- Mapeia valores (códigos → descrições)
- Cria colunas calculadas

```python
from src.agents.engineer.transformers import DataMapper

mapper = DataMapper()
df_mapeado = mapper.map(df, entity="clientes")
```

### Loaders

Carrega dados no destino (Azure Data Lake).

```python
from src.agents.engineer.loaders import DataLakeLoader

loader = DataLakeLoader(upload_to_cloud=True)
result = loader.load(df, entity="clientes", layer="raw")
```

### Orchestrator

Coordena o pipeline completo.

```python
from src.agents.engineer import Orchestrator

# Com todas as opções
orchestrator = Orchestrator(
    upload_to_cloud=True,   # Upload para Azure
    clean_data=True,        # Aplicar limpeza
    map_data=False          # Não mapear colunas
)

results = orchestrator.run_full_pipeline()
```

### Scheduler

Agenda execuções periódicas.

```python
from src.agents.engineer import Scheduler

scheduler = Scheduler()

# Agendar execução diária
scheduler.schedule_daily(
    entities=["clientes", "produtos"],
    hour=6,
    minute=0
)

# Agendar execução por intervalo
scheduler.schedule_interval(
    entities=["estoque"],
    hours=1
)

# Iniciar scheduler
scheduler.start()
```

---

## ⚙️ Configuração

### Arquivo `config.py`

```python
# Configurações de extração
EXTRACTION_CONFIG = {
    "default_range_size": 5000,
    "default_timeout": 300,
    "max_retries": 3
}

# Configurações de agendamento
SCHEDULE_CONFIG = {
    "clientes": {"frequency": "daily", "hour": 6},
    "estoque": {"frequency": "hourly"}
}
```

### Variáveis de Ambiente

```bash
# mcp_sankhya/.env
SANKHYA_CLIENT_ID=...
SANKHYA_CLIENT_SECRET=...
SANKHYA_X_TOKEN=...
AZURE_STORAGE_ACCOUNT=mmarradatalake
AZURE_STORAGE_KEY=...
AZURE_CONTAINER=datahub
```

---

## 📈 Resultado de Execução

```
============================================================
AGENTE ENGENHEIRO DE DADOS - Pipeline ETL
============================================================
Início: 2026-02-03 11:00:00
Entidades: vendedores, clientes, produtos, estoque
Upload Azure: Sim
============================================================

>>> VENDEDORES
[vendedores] Extraídos 111 registros
[vendedores] Carga concluída: 111 registros (0.01 MB)

>>> CLIENTES
[clientes] Extração por faixas (0 a 100000, step 5000)
[clientes] Total extraído: 57082 registros
[clientes] Carga concluída: 57082 registros (4.02 MB)

>>> PRODUTOS
[produtos] Extração por faixas (0 a 600000, step 5000)
[produtos] Total extraído: 393356 registros
[produtos] Carga concluída: 393356 registros (9.67 MB)

>>> ESTOQUE
[estoque] Extração por faixas (0 a 600000, step 5000)
[estoque] Total extraído: 19437 registros
[estoque] Carga concluída: 19437 registros (0.46 MB)

============================================================
RESUMO
============================================================
  ✓ vendedores :        111 registros |   0.01 MB
  ✓ clientes   :     57.082 registros |   4.02 MB
  ✓ produtos   :    393.356 registros |   9.67 MB
  ✓ estoque    :     19.437 registros |   0.46 MB
------------------------------------------------------------
  TOTAL:       469.986 registros |  14.16 MB
  Duração: 45.2 segundos
  Status: 4/4 bem-sucedidas
============================================================
```

---

## 🔮 Roadmap

- [x] Extractors básicos (5 entidades)
- [x] DataCleaner
- [x] DataMapper
- [x] DataLakeLoader
- [x] Orchestrator
- [x] Scheduler básico
- [ ] Extração incremental (baseada em DTALTER)
- [ ] Alertas de falha (email/Teams)
- [ ] Dashboard de monitoramento
- [ ] Integração com Azure Data Factory

---

## 📚 Referências

- [Código fonte](../../src/agents/engineer/)
- [Configuração global](../../src/config.py)
- [Utils compartilhados](../../src/utils/)
- [Data Lake estrutura](../data-lake/estrutura.md)
