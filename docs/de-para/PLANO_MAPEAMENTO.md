# 📊 Plano Completo de Mapeamento - Sankhya ERP

**Objetivo**: Documentar toda a estrutura do banco Sankhya para treinar agentes ML/LLM

**Data**: 2026-01-30
**Status**: 🔄 Em execução

---

## 🎯 Objetivo Final

Criar um **Agente LLM** que entenda profundamente o Sankhya e possa:
- Responder perguntas em linguagem natural
- Gerar queries SQL automaticamente
- Identificar padrões nos dados
- Fazer previsões (ML)

**Exemplo de uso:**
```
Usuário: "Quais pedidos de compra estão atrasados?"
Agente LLM:
  1. Identifica tabelas: TGFCAB (pedidos), VGWRECSITCAB (situação WMS)
  2. Gera SQL: WHERE COD_SITUACAO IN (3,4,5) AND DTNEG < HOJE-7
  3. Retorna: "15 pedidos atrasados, fornecedor X tem 8"
```

---

## 📋 Módulos a Mapear

### 1. COMPRAS ✅ Parcial
**Status**: 80% mapeado
**Prioridade**: Alta (MVP)

| Tabela | Descrição | Status | Doc |
|--------|-----------|--------|-----|
| TGFCAB | Cabeçalho (notas) | ✅ | compras.md |
| TGFITE | Itens | ✅ | compras.md |
| TGFPAR | Fornecedores | ✅ | compras.md |
| TGFPRO | Produtos | ✅ | compras.md |
| TGWREC | Recebimento WMS | ✅ | wms.md |
| VGWRECSITCAB | Situação WMS | ✅ | wms.md |
| TGFTOP | Tipos de Operação | 📋 | - |
| TGFVAR | Relacionamento Pedido↔Nota | 📋 | - |

**Perguntas que o LLM deve responder:**
- Quais pedidos estão atrasados?
- Qual fornecedor tem mais pedidos pendentes?
- Qual o lead time médio por fornecedor?
- Produtos com maior volume de compra?

---

### 2. ESTOQUE 🔄 Em análise
**Status**: 20% mapeado
**Prioridade**: Alta (MVP)

| Tabela | Descrição | Status | Doc |
|--------|-----------|--------|-----|
| TGFEST | Estoque geral | 🔄 | estoque.md |
| TGFRES | Reservas | 🔄 | estoque.md |
| TGFSAL | Saldo por endereço | ❌ Não existe | - |
| TCS* / *WMS* | Tabelas WMS nativas | 🔄 Investigar | - |
| TGFEND | Endereços WMS | 📋 | - |
| TGFMOV | Movimentações | 📋 | - |

**Perguntas que o LLM deve responder:**
- Qual o estoque disponível do produto X?
- Produtos com estoque abaixo do mínimo?
- Qual a diferença entre estoque físico e WMS?
- Produtos com mais reservas?
- Qual o giro de estoque por produto?

---

### 3. VENDAS 📋 Futuro
**Status**: 0% mapeado
**Prioridade**: Média

| Tabela | Descrição | Status | Doc |
|--------|-----------|--------|-----|
| TGFCAB | Cabeçalho (TIPMOV='V') | 📋 | vendas.md |
| TGFITE | Itens | 📋 | vendas.md |
| TGFPAR | Clientes | 📋 | vendas.md |
| TGFVEN | Vendedores | 📋 | vendas.md |
| TGFVEN | Comissões | 📋 | vendas.md |

**Perguntas que o LLM deve responder:**
- Quais os produtos mais vendidos?
- Qual vendedor tem melhor performance?
- Qual o ticket médio por cliente?
- Previsão de vendas para próximo mês?
- Clientes inativos (sem comprar há X dias)?

---

### 4. FINANCEIRO 📋 Futuro
**Status**: 0% mapeado
**Prioridade**: Média

| Tabela | Descrição | Status | Doc |
|--------|-----------|--------|-----|
| TGFFIN | Títulos (contas a pagar/receber) | 📋 | financeiro.md |
| TGFREC | Recebimentos | 📋 | financeiro.md |
| TGFBAN | Bancos | 📋 | financeiro.md |
| TGFNAT | Naturezas financeiras | 📋 | financeiro.md |

**Perguntas que o LLM deve responder:**
- Qual o fluxo de caixa previsto?
- Títulos vencidos por fornecedor?
- Qual o prazo médio de pagamento?
- Análise de inadimplência?

---

### 5. PRODUTOS 📋 Futuro
**Status**: 30% mapeado (básico)
**Prioridade**: Média

| Tabela | Descrição | Status | Doc |
|--------|-----------|--------|-----|
| TGFPRO | Produtos | ✅ Básico | compras.md |
| TGFGRU | Grupos de produtos | 📋 | produtos.md |
| TGFCPL | Complementos | 📋 | produtos.md |
| TGFTAB | Tabelas de preço | 📋 | produtos.md |
| TGFEXC | Exceções de preço | 📋 | produtos.md |

**Perguntas que o LLM deve responder:**
- Produtos sem grupo definido?
- Estrutura de categorias completa?
- Produtos com múltiplas unidades?
- Histórico de alterações de preço?

---

### 6. RELACIONAMENTOS (ERD) 🔥 Crítico
**Status**: 0% mapeado
**Prioridade**: Alta (para LLM entender joins)

**Objetivo**: Mapear TODOS os relacionamentos entre tabelas

```
TGFCAB ─┬─► TGFITE (NUNOTA)
        ├─► TGFPAR (CODPARC)
        ├─► TGFTOP (CODTIPOPER)
        └─► VGWRECSITCAB (NUNOTA)

TGFITE ──► TGFPRO (CODPROD)

TGFPRO ─┬─► TGFGRU (CODGRUPOPROD)
        └─► TGFEST (CODPROD)

TGFEST ──► TGFRES (CODPROD, CODEMP, CODLOCAL)
```

**Formato da documentação:**
- [ ] Criar `docs/relacionamentos.md`
- [ ] Diagrama ERD (Mermaid ou Draw.io)
- [ ] Lista de constraints (PK, FK, UNIQUE)
- [ ] Regras de negócio (quando usar INNER vs LEFT JOIN)

---

## 🔍 Queries de Exploração

### Fase 1: Descoberta de Tabelas

**Query 1: Listar TODAS as tabelas do Sankhya**
```sql
SELECT TABLE_NAME, NUM_ROWS
FROM ALL_TABLES
WHERE OWNER = 'SANKHYA' -- ajustar nome do schema
  AND TABLE_NAME LIKE 'TG%'
ORDER BY TABLE_NAME
```

**Query 2: Listar tabelas WMS**
```sql
SELECT TABLE_NAME
FROM ALL_TABLES
WHERE TABLE_NAME LIKE '%WMS%'
   OR TABLE_NAME LIKE 'TCS%'
   OR TABLE_NAME LIKE 'TGWSAL%'
ORDER BY TABLE_NAME
```

**Query 3: Listar views importantes**
```sql
SELECT VIEW_NAME
FROM ALL_VIEWS
WHERE VIEW_NAME LIKE 'VG%'
ORDER BY VIEW_NAME
```

### Fase 2: Estrutura de Cada Tabela

**Template para cada tabela:**
```sql
-- Ver colunas
SELECT
    COLUMN_NAME,
    DATA_TYPE,
    DATA_LENGTH,
    NULLABLE,
    DATA_DEFAULT
FROM ALL_TAB_COLUMNS
WHERE TABLE_NAME = 'NOME_TABELA'
ORDER BY COLUMN_ID
```

```sql
-- Ver constraints (PK, FK, UNIQUE)
SELECT
    CONSTRAINT_NAME,
    CONSTRAINT_TYPE,
    SEARCH_CONDITION
FROM ALL_CONSTRAINTS
WHERE TABLE_NAME = 'NOME_TABELA'
```

```sql
-- Ver índices
SELECT
    INDEX_NAME,
    COLUMN_NAME,
    COLUMN_POSITION
FROM ALL_IND_COLUMNS
WHERE TABLE_NAME = 'NOME_TABELA'
ORDER BY INDEX_NAME, COLUMN_POSITION
```

### Fase 3: Relacionamentos

**Query 4: Ver Foreign Keys**
```sql
SELECT
    a.constraint_name AS fk_name,
    a.table_name AS tabela_origem,
    a.column_name AS coluna_origem,
    c_pk.table_name AS tabela_destino,
    b.column_name AS coluna_destino
FROM all_cons_columns a
JOIN all_constraints c ON a.constraint_name = c.constraint_name
JOIN all_constraints c_pk ON c.r_constraint_name = c_pk.constraint_name
JOIN all_cons_columns b ON c_pk.constraint_name = b.constraint_name
WHERE c.constraint_type = 'R'
  AND a.table_name LIKE 'TGF%'
ORDER BY a.table_name, a.constraint_name
```

### Fase 4: Campos Customizados

**Query 5: Listar campos AD_***
```sql
SELECT
    TABLE_NAME,
    COLUMN_NAME,
    DATA_TYPE
FROM ALL_TAB_COLUMNS
WHERE COLUMN_NAME LIKE 'AD_%'
  AND TABLE_NAME IN ('TGFCAB', 'TGFITE', 'TGFPAR', 'TGFPRO')
ORDER BY TABLE_NAME, COLUMN_NAME
```

**Query 6: Ver metadados dos campos customizados**
```sql
-- Sankhya armazena descrição dos campos customizados em TDDCAD
SELECT
    NUMCAMPO,
    NOME,
    DESCRICAO,
    TIPO
FROM TDDCAD
WHERE NOME LIKE 'AD_%'
ORDER BY NOME
```

---

## 📝 Template de Documentação

Para cada tabela, criar documento seguindo este template:

```markdown
# NOME_TABELA - Descrição

**Módulo**: Compras / Vendas / Estoque / Financeiro
**Tipo**: Transacional / Cadastro / View
**Relacionamentos**: X tabelas filhas, Y tabelas pai

---

## 📊 Estrutura

| Campo | Tipo | Null | PK/FK | Descrição |
|-------|------|------|-------|-----------|
| CAMPO1 | INT | NOT NULL | PK | ... |
| CAMPO2 | VARCHAR | NULL | FK → TABELA | ... |

## 🔗 Relacionamentos

### Tabelas Pai (Foreign Keys)
- `CAMPO → TABELA_PAI.CAMPO_PAI`

### Tabelas Filhas
- `TABELA_FILHA.CAMPO → CAMPO`

## 📋 Queries Comuns

### Listar registros ativos
```sql
SELECT ...
```

### Join com tabelas relacionadas
```sql
SELECT ...
```

## 🔍 Campos Customizados (AD_*)

| Campo | Tipo | Descrição | Uso |
|-------|------|-----------|-----|
| AD_CAMPO1 | VARCHAR | ... | ... |

## 💡 Regras de Negócio

- Regra 1
- Regra 2

## 🎯 Para o LLM Saber

**Esta tabela é usada para:**
- [ ] Listar pedidos
- [ ] Calcular totais
- [ ] Filtrar por período
- [ ] Join com produtos

**Campos-chave para filtros:**
- `CAMPO1` - Descrição
- `CAMPO2` - Descrição

**Exemplos de perguntas:**
- "Quantos registros há nesta tabela?"
- "Qual o total por período?"
```

---

## 🤖 Estrutura de Metadados para ML/LLM

Criar arquivo JSON com toda a estrutura do banco:

```json
{
  "database": "sankhya",
  "version": "1.0",
  "tables": [
    {
      "name": "TGFCAB",
      "description": "Cabeçalho de notas fiscais",
      "module": "compras",
      "type": "transactional",
      "columns": [
        {
          "name": "NUNOTA",
          "type": "INT",
          "nullable": false,
          "primary_key": true,
          "description": "Número único da nota"
        },
        {
          "name": "CODPARC",
          "type": "INT",
          "nullable": false,
          "foreign_key": {
            "table": "TGFPAR",
            "column": "CODPARC"
          },
          "description": "Código do parceiro (fornecedor/cliente)"
        }
      ],
      "relationships": {
        "parents": ["TGFPAR", "TGFTOP"],
        "children": ["TGFITE", "VGWRECSITCAB"]
      },
      "common_queries": [
        {
          "question": "Listar pedidos de compra",
          "sql": "SELECT * FROM TGFCAB WHERE TIPMOV = 'C'",
          "filters": ["DTNEG", "CODPARC", "CODEMP"]
        }
      ]
    }
  ],
  "business_rules": [
    {
      "rule": "Estoque disponível = ESTOQUE - RESERVADO",
      "tables": ["TGFEST", "TGFRES"]
    }
  ]
}
```

**Este JSON será usado para:**
- Treinar o LLM sobre a estrutura do banco
- Gerar queries SQL automaticamente
- Validar relacionamentos
- Sugerir filtros e agregações

---

## 📅 Cronograma de Execução

### Semana 1 (Atual): Compras + Estoque
- [ ] Executar queries de exploração
- [ ] Documentar TGFCAB completo
- [ ] Documentar TGFITE completo
- [ ] Documentar TGFPAR completo
- [ ] Documentar TGFPRO completo
- [ ] Mapear todas as tabelas WMS
- [ ] Documentar TGFEST + reservas
- [ ] Criar diagrama ERD (Compras)

### Semana 2: Vendas + Produtos
- [ ] Documentar TGFCAB (vendas)
- [ ] Documentar TGFVEN (vendedores)
- [ ] Documentar TGFGRU (grupos)
- [ ] Documentar TGFTAB (preços)
- [ ] Criar diagrama ERD (Vendas)

### Semana 3: Financeiro
- [ ] Documentar TGFFIN
- [ ] Documentar TGFREC
- [ ] Documentar TGFBAN
- [ ] Criar diagrama ERD (Financeiro)

### Semana 4: Consolidação
- [ ] Criar metadata.json completo
- [ ] Revisar toda documentação
- [ ] Criar índice de tabelas
- [ ] Preparar para integração com LLM

---

## 🎯 Entregáveis Finais

1. **Documentação Completa**
   - [ ] `docs/tabelas/` - Um arquivo .md por tabela
   - [ ] `docs/relacionamentos.md` - ERD completo
   - [ ] `docs/campos_customizados.md` - Todos os AD_*
   - [ ] `docs/regras_negocio.md` - Lógicas importantes

2. **Metadados Estruturados**
   - [ ] `metadata/database_schema.json` - Estrutura completa
   - [ ] `metadata/relationships.json` - Todos os relacionamentos
   - [ ] `metadata/common_queries.json` - Queries frequentes
   - [ ] `metadata/business_rules.json` - Regras de negócio

3. **Scripts de Extração**
   - [ ] `src/extractors/` - Scripts Python por módulo
   - [ ] `src/utils/metadata_generator.py` - Gera JSON automático

4. **Testes e Validação**
   - [ ] `tests/test_relationships.py` - Valida FKs
   - [ ] `tests/test_queries.py` - Valida queries comuns

---

## 🔧 Ferramentas Recomendadas

### Para Documentação
- **Markdown**: Documentos técnicos
- **Mermaid**: Diagramas ERD
- **Draw.io**: Diagramas complexos

### Para Metadados
- **Python**: Gerar JSON automaticamente
- **SQLAlchemy**: Introspecção do banco
- **Pydantic**: Validação de schemas

### Para LLM
- **LangChain**: Framework de agentes
- **ChromaDB**: Vector database para embeddings
- **OpenAI / Anthropic**: APIs de LLM

---

## 📊 Métricas de Progresso

| Módulo | Tabelas Mapeadas | % Completo | Status |
|--------|------------------|------------|--------|
| Compras | 6/8 | 75% | 🔄 |
| Estoque | 1/6 | 16% | 🔄 |
| Vendas | 0/5 | 0% | 📋 |
| Financeiro | 0/4 | 0% | 📋 |
| Produtos | 1/5 | 20% | 📋 |
| **TOTAL** | **8/28** | **28%** | 🔄 |

**Meta**: 100% até final de Fevereiro/2026

---

## 💬 Próximos Passos Imediatos

1. **Rodar queries de exploração** (ver seção "Queries de Exploração")
2. **Criar pasta** `docs/tabelas/`
3. **Documentar primeira tabela completa** usando template
4. **Gerar metadata.json** com estrutura inicial
5. **Atualizar PROGRESSO_SESSAO.md** com descobertas

---

**Última atualização:** 2026-01-30
**Responsável:** Ítalo Gomes
**Status:** 🔄 Plano criado, iniciando execução
