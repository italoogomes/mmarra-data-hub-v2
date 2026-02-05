# 📊 Data Lake - Estrutura

**Versão:** 2.0.0
**Data:** 2026-02-03
**Status:** ✅ Operacional

> **Storage**: Azure Data Lake Gen2
> **Account**: mmarradatalake
> **Container**: datahub
> **Formato**: Parquet
> **Responsável**: Ítalo

---

## 🎯 Visão Geral

```
┌─────────────────────────────────────────────────────────────────┐
│                    AZURE DATA LAKE GEN2                          │
│                  Storage: mmarradatalake                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Container: datahub                                             │
│   │                                                              │
│   ├── /raw/                    ← Dados brutos (Bronze) ✅        │
│   │   ├── vendedores/                     111 registros          │
│   │   ├── clientes/                    57.082 registros          │
│   │   ├── produtos/                   393.356 registros          │
│   │   ├── estoque/                     19.437 registros          │
│   │   └── vendas/             [Futuro]                           │
│   │                                                              │
│   ├── /processed/              ← Dados limpos (Silver) [Futuro]  │
│   │                                                              │
│   └── /curated/                ← Dados agregados (Gold) [Futuro] │
│                                                                  │
│   TOTAL: 469.986 registros | 14.16 MB                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✅ Estrutura Atual (Operacional)

### Camada RAW (Bronze)

```
datahub/
└── raw/
    ├── vendedores/
    │   └── vendedores.parquet        # 111 registros | 0.01 MB
    │
    ├── clientes/
    │   └── clientes.parquet          # 57.082 registros | 4.02 MB
    │
    ├── produtos/
    │   └── produtos.parquet          # 393.356 registros | 9.67 MB
    │
    └── estoque/
        └── estoque.parquet           # 19.437 registros | 0.46 MB
```

---

## 📋 Schema dos Arquivos

### vendedores.parquet

| Campo | Tipo | Descrição |
|-------|------|-----------|
| CODVEND | INT64 | Código do vendedor (PK) |
| APELIDO | STRING | Nome/apelido |
| ATIVO | STRING | Ativo (S/N) |
| TIPVEND | STRING | Tipo (V=Vendedor, C=Comprador, R=Representante) |
| EMAIL | STRING | Email |
| CODGER | INT64 | Código do gerente |

### clientes.parquet

| Campo | Tipo | Descrição |
|-------|------|-----------|
| CODPARC | INT64 | Código do parceiro (PK) |
| NOMEPARC | STRING | Nome fantasia |
| RAZAOSOCIAL | STRING | Razão social |
| CGC_CPF | STRING | CNPJ/CPF |
| TIPPESSOA | STRING | Tipo (J=Jurídica, F=Física) |
| CLIENTE | STRING | É cliente (S/N) |
| FORNECEDOR | STRING | É fornecedor (S/N) |
| ATIVO | STRING | Ativo (S/N) |
| EMAIL | STRING | Email |
| TELEFONE | STRING | Telefone |
| CEP | STRING | CEP |
| CODCID | INT64 | Código da cidade |
| CODVEND | INT64 | Código do vendedor |
| LIMCRED | DECIMAL | Limite de crédito |

### produtos.parquet

| Campo | Tipo | Descrição |
|-------|------|-----------|
| CODPROD | INT64 | Código do produto (PK) |
| DESCRPROD | STRING | Descrição |
| REFERENCIA | STRING | Referência/código de barras |
| MARCA | STRING | Marca |
| CODGRUPOPROD | INT64 | Código do grupo |
| ATIVO | STRING | Ativo (S/N) |
| USOPROD | STRING | Uso (R=Revenda, C=Consumo) |
| NCM | STRING | NCM fiscal |
| CODVOL | STRING | Unidade de medida |
| PESOBRUTO | DECIMAL | Peso bruto |
| PESOLIQ | DECIMAL | Peso líquido |

### estoque.parquet

| Campo | Tipo | Descrição |
|-------|------|-----------|
| CODEMP | INT64 | Código da empresa |
| CODPROD | INT64 | Código do produto |
| DESCRPROD | STRING | Descrição do produto |
| CODLOCAL | INT64 | Código do local |
| CONTROLE | STRING | Lote/controle |
| ESTOQUE | DECIMAL | Quantidade em estoque |
| RESERVADO | DECIMAL | Quantidade reservada |
| DISPONIVEL | DECIMAL | Quantidade disponível |

---

## 🔄 Pipeline de Extração

### Fluxo

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   SANKHYA   │────▶│   PYTHON    │────▶│    AZURE    │
│     ERP     │     │  PIPELINE   │     │  DATA LAKE  │
└─────────────┘     └─────────────┘     └─────────────┘
     API             Extração             Parquet
     REST            + Upload             + Storage
```

### Comandos de Extração

```bash
# Extração completa
python src/pipelines/extracao.py

# Via script dedicado
python scripts/extrair_tudo.py

# Entidade específica
python scripts/extrair_para_datalake.py --extrator clientes
```

### Frequência Sugerida

| Entidade | Frequência | Horário |
|----------|------------|---------|
| Vendedores | Semanal | Domingo 06:00 |
| Clientes | Diário | 06:00 |
| Produtos | Diário | 06:15 |
| Estoque | Horário | A cada 1h |
| Vendas | Diário | 06:30 |

---

## 🔮 Estrutura Futura

### Camada PROCESSED (Silver)

```
datahub/
└── processed/
    ├── dim_clientes/           # Dimensão clientes limpa
    ├── dim_produtos/           # Dimensão produtos limpa
    ├── dim_vendedores/         # Dimensão vendedores
    ├── dim_tempo/              # Dimensão tempo
    └── fact_vendas/            # Fato vendas
```

### Camada CURATED (Gold)

```
datahub/
└── curated/
    ├── vendas_diarias/         # Vendas por dia
    ├── vendas_mensais/         # Vendas por mês
    ├── estoque_critico/        # Produtos com estoque baixo
    ├── performance_vendedores/ # Métricas de vendedores
    └── dashboards/             # Dados para BI
```

---

## ⚙️ Configuração

### Variáveis de Ambiente

```bash
# mcp_sankhya/.env
AZURE_STORAGE_ACCOUNT=mmarradatalake
AZURE_STORAGE_KEY=<sua-key>
AZURE_CONTAINER=datahub
```

### Conexão via Python

```python
from src.utils.azure_storage import AzureDataLakeClient

azure = AzureDataLakeClient()

# Testar conexão
azure.testar_conexao()

# Upload
azure.upload_arquivo(arquivo_local, "raw/clientes/clientes.parquet")

# Listar arquivos
azure.listar_arquivos("raw/")
```

---

## 🔒 Segurança

### Permissões

| Recurso | Quem | Permissão |
|---------|------|-----------|
| Container datahub | Pipeline Python | Read/Write |
| Container datahub | Agentes IA | Read |
| Container datahub | Power BI | Read |

### Credenciais

- ❌ NUNCA commitar chaves no git
- ✅ Usar variáveis de ambiente (.env)
- ✅ Considerar Azure Key Vault para produção

---

## 📊 Estatísticas Atuais

| Métrica | Valor |
|---------|-------|
| Total de registros | 469.986 |
| Tamanho total | 14.16 MB |
| Última extração | 2026-02-03 11:07 |
| Formato | Parquet |
| Compressão | Snappy |

---

## ✅ Checklist de Setup

- [x] Criar container `datahub`
- [x] Criar estrutura de pastas `raw/`
- [x] Configurar credenciais no `.env`
- [x] Testar upload de arquivos Parquet
- [x] Extrair dados de cadastros
- [ ] Configurar extração agendada
- [ ] Implementar camada `processed/`
- [ ] Implementar camada `curated/`
- [ ] Configurar alertas de falha

---

## 📚 Histórico

| Data | Versão | Alteração | Responsável |
|------|--------|-----------|-------------|
| Jan/2026 | 1.0.0 | Estrutura inicial (planejamento) | Ítalo |
| Fev/2026 | 2.0.0 | Data Lake operacional com 470k registros | Ítalo + Claude |
