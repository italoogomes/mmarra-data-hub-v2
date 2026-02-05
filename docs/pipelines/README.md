# 🔄 Pipelines de Dados - MMarra Data Hub

**Versão:** 1.0.0
**Data:** 2026-02-03
**Status:** ✅ Operacional

---

## 📋 Visão Geral

Pipelines são fluxos automatizados de dados que movem informações do ERP Sankhya para o Azure Data Lake, seguindo a arquitetura **Medallion** (Bronze/Silver/Gold).

### Arquitetura de Dados

```
┌─────────────────────────────────────────────────────────────┐
│                      SANKHYA ERP                             │
│                    (Fonte de Dados)                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  PIPELINE DE EXTRAÇÃO                        │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ Clientes │    │ Produtos │    │ Estoque  │    ...       │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘              │
│       │               │               │                     │
│       └───────────────┼───────────────┘                     │
│                       ▼                                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   AZURE DATA LAKE                            │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  RAW (Bronze)                                        │   │
│  │  - Dados brutos do Sankhya                          │   │
│  │  - Formato: Parquet                                 │   │
│  │  - Sem transformação                                │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  PROCESSED (Silver) [Futuro]                        │   │
│  │  - Dados limpos e validados                         │   │
│  │  - Deduplicação                                     │   │
│  │  - Tipagem correta                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  CURATED (Gold) [Futuro]                            │   │
│  │  - Dados agregados                                  │   │
│  │  - Métricas calculadas                              │   │
│  │  - Prontos para BI                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Pipelines Disponíveis

### 1. Pipeline de Extração

**Arquivo:** `src/pipelines/extracao.py`

**Função:** Extrair dados do Sankhya e carregar no Data Lake (camada RAW).

**Entidades extraídas:**

| Entidade | Registros | Tamanho | Frequência sugerida |
|----------|-----------|---------|---------------------|
| Vendedores | ~111 | 0.01 MB | Semanal |
| Clientes | ~57.000 | 4.02 MB | Diário |
| Produtos | ~393.000 | 9.67 MB | Diário |
| Estoque | ~19.000 | 0.46 MB | Horário |
| **TOTAL** | **~470.000** | **~14 MB** | - |

**Características:**
- Contorna limite de 5000 registros da API usando faixas
- Sobrescreve arquivos anteriores (sem versionamento)
- Salva cópia local + upload para Azure

---

## 🚀 Como Usar

### Execução Completa

```bash
cd mmarra-data-hub
python src/pipelines/extracao.py
```

### Via Código Python

```python
from src.pipelines import PipelineExtracao

# Criar pipeline
pipeline = PipelineExtracao()

# Executar todas as entidades
resultados = pipeline.executar()

# Ou executar entidades específicas
resultados = pipeline.executar(entidades=["clientes", "estoque"])
```

### Via Script Dedicado

```bash
# Extrair tudo
python scripts/extrair_tudo.py

# Extrair entidade específica
python scripts/extrair_para_datalake.py --extrator clientes
```

---

## ⚙️ Configuração

### Variáveis de Ambiente

```bash
# mcp_sankhya/.env

# Sankhya API
SANKHYA_CLIENT_ID=...
SANKHYA_CLIENT_SECRET=...
SANKHYA_X_TOKEN=...

# Azure Data Lake
AZURE_STORAGE_ACCOUNT=mmarradatalake
AZURE_STORAGE_KEY=...
AZURE_CONTAINER=datahub
```

### Configuração de Entidades

Cada entidade pode ser configurada em `PipelineExtracao.ENTIDADES`:

```python
"clientes": {
    "query_template": "SELECT ... WHERE {WHERE_FAIXA}",
    "colunas": ["CODPARC", "NOMEPARC", ...],
    "caminho_datalake": "raw/clientes/clientes.parquet",
    "usa_faixa": True,
    "campo_id": "p.CODPARC",
    "id_max": 100000,
    "faixa_size": 5000
}
```

---

## 📁 Estrutura no Data Lake

```
datahub/
├── raw/                          # Camada Bronze
│   ├── vendedores/
│   │   └── vendedores.parquet
│   ├── clientes/
│   │   └── clientes.parquet
│   ├── produtos/
│   │   └── produtos.parquet
│   ├── estoque/
│   │   └── estoque.parquet
│   └── vendas/                   # [Futuro]
│       └── vendas.parquet
│
├── processed/                    # Camada Silver [Futuro]
│   ├── dim_clientes/
│   ├── dim_produtos/
│   └── fact_vendas/
│
└── curated/                      # Camada Gold [Futuro]
    ├── metricas_vendas/
    ├── metricas_estoque/
    └── dashboards/
```

---

## 📊 Monitoramento

### Resultado da Execução

Cada execução retorna uma lista de resultados:

```python
[
    {
        "entidade": "clientes",
        "registros": 57082,
        "sucesso": True,
        "tamanho_mb": 4.02
    },
    ...
]
```

### Logs

Os pipelines usam `logging` do Python:

```
2026-02-03 11:00:00 - INFO - Autenticando no Sankhya...
2026-02-03 11:00:01 - INFO - Autenticado com sucesso
2026-02-03 11:00:02 - INFO - Conectando ao Azure Data Lake...
2026-02-03 11:00:03 - INFO - clientes: 57082 registros (4.02 MB)
2026-02-03 11:00:04 - INFO - clientes: Upload concluído
```

---

## 🔮 Roadmap

### Implementado
- [x] Pipeline de extração (RAW)
- [x] Extração por faixas (contorna limite API)
- [x] Upload para Azure Data Lake

### Próximos Passos
- [ ] Pipeline de transformação (PROCESSED)
  - Limpeza de dados
  - Deduplicação
  - Validação de tipos
- [ ] Pipeline de agregação (CURATED)
  - Métricas de vendas
  - Indicadores de estoque
- [ ] Agendamento automático
  - Azure Functions
  - Cron job
- [ ] Alertas de falha
  - Email
  - Teams/Slack
- [ ] Extração incremental
  - Apenas registros alterados
  - Baseado em DTALTER

---

## 🛠️ Troubleshooting

### Erro: Timeout na API

**Problema:** Query demora mais de 180 segundos.

**Solução:** Reduzir `faixa_size` para 2000 ou 1000.

### Erro: Limite de 5000 registros

**Problema:** API retorna apenas 5000 registros.

**Solução:** Já contornado com extração por faixas. Verificar se `usa_faixa=True`.

### Erro: Upload falhou

**Problema:** Falha ao enviar para Azure.

**Solução:**
1. Verificar credenciais no `.env`
2. Verificar conexão com internet
3. Verificar permissões no container

---

## 📚 Referências

- [Azure Data Lake Documentation](https://docs.microsoft.com/azure/storage/blobs/data-lake-storage-introduction)
- [Medallion Architecture](https://www.databricks.com/glossary/medallion-architecture)
- [Documentação Sankhya API](docs/api/sankhya.md)
