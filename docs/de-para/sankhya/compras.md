# DE-PARA: Sankhya → Data Hub (COMPRAS)

> **Status**: 🟡 Em mapeamento
> **Responsável**: Ítalo
> **Última atualização**: Janeiro/2026

---

## 🎯 Objetivo

Mapear todas as tabelas e campos do Sankhya relacionados a **Compras** para alimentar o Data Lake:
- `/raw/sankhya/compras/cabecalho/`
- `/raw/sankhya/compras/itens/`
- `/raw/sankhya/compras/fornecedores/`
- `/raw/sankhya/compras/wms/`

---

## 📋 Tabelas Identificadas

### 1. TGFCAB - Cabeçalho (Notas de Entrada)

| Campo Sankhya | Tipo | Descrição | Obrigatório |
|---------------|------|-----------|-------------|
| `NUNOTA` | INT | Número único da nota (PK) | ✅ |
| `NUMNOTA` | INT | Número da nota fiscal | ✅ |
| `DTNEG` | DATE | Data da negociação | ✅ |
| `DTENTSAI` | DATE | Data entrada/saída | |
| `CODPARC` | INT | Código do fornecedor (FK) | ✅ |
| `CODEMP` | INT | Código da empresa/filial | ✅ |
| `CODTIPOPER` | INT | Tipo de operação | ✅ |
| `VLRNOTA` | DECIMAL | Valor total da nota | ✅ |
| `VLRDESCTOT` | DECIMAL | Desconto total | |
| `VLRFRETE` | DECIMAL | Valor do frete | |
| `STATUSNOTA` | CHAR | Status | ✅ |
| `TIPMOV` | CHAR | Tipo movimento (C=Compra) | ✅ |
| `NUMCONTRATO` | VARCHAR | Número do contrato | |
| `CODCOMPRADOR` | INT | Código do comprador | |
| `OBSERVACAO` | VARCHAR | Observações | |

**Filtros importantes**:
```sql
WHERE TIPMOV IN ('C', 'O', 'D')  -- Compras, Ordens, Devoluções
  AND CODTIPOPER IN (1001, 1301) -- Tipos de operação de compra
```

---

### 2. TGFITE - Itens

| Campo Sankhya | Tipo | Descrição | Obrigatório |
|---------------|------|-----------|-------------|
| `NUNOTA` | INT | Número da nota (FK) | ✅ |
| `SEQUENCIA` | INT | Sequência do item | ✅ |
| `CODPROD` | INT | Código do produto | ✅ |
| `QTDNEG` | DECIMAL | Quantidade | ✅ |
| `VLRUNIT` | DECIMAL | Valor unitário | ✅ |
| `VLRTOT` | DECIMAL | Valor total | ✅ |
| `VLRDESC` | DECIMAL | Desconto | |
| `CODVOL` | VARCHAR | Unidade de medida | |

---

### 3. TGFPAR - Fornecedores

| Campo Sankhya | Tipo | Descrição | Obrigatório |
|---------------|------|-----------|-------------|
| `CODPARC` | INT | Código do parceiro (PK) | ✅ |
| `RAZAOSOCIAL` | VARCHAR | Razão social | ✅ |
| `NOMEPARC` | VARCHAR | Nome fantasia | ✅ |
| `CGC_CPF` | VARCHAR | CNPJ | ✅ |
| `FORNECEDOR` | CHAR | É fornecedor (S/N) | ✅ |
| `CODCID` | INT | Cidade | |
| `EMAIL` | VARCHAR | Email | |
| `TELEFONE` | VARCHAR | Telefone | |
| `ATIVO` | CHAR | Ativo (S/N) | ✅ |

**Filtros**:
```sql
WHERE FORNECEDOR = 'S'
```

---

### 4. TGFPRO - Produtos

| Campo Sankhya | Tipo | Descrição | Obrigatório |
|---------------|------|-----------|-------------|
| `CODPROD` | INT | Código do produto (PK) | ✅ |
| `DESCRPROD` | VARCHAR | Descrição | ✅ |
| `REFERENCIA` | VARCHAR | Referência/SKU | ✅ |
| `CODGRUPOPROD` | INT | Grupo do produto | |
| `MARCA` | VARCHAR | Marca | |
| `CODVOL` | VARCHAR | Unidade padrão | |
| `ATIVO` | CHAR | Ativo (S/N) | ✅ |

---

### 5. Tabelas WMS (Recebimento)

#### TGWREC - Recebimento WMS

| Campo Sankhya | Tipo | Descrição |
|---------------|------|-----------|
| `NURECEBIMENTO` | INT | Número do recebimento (PK) |
| `SITUACAO` | INT | Status interno (0-6) |
| `STATUSCONF` | INT | Status da conferência |
| `USACONFPARCIAL` | CHAR | Usa conferência parcial (S/N) |
| `CONFFINAL` | CHAR | Conferência finalizada (S/N) |
| `CODENDDOCA` | INT | Código do endereço da doca |

#### TGWRXN - Relacionamento Recebimento ↔ Nota

| Campo Sankhya | Tipo | Descrição |
|---------------|------|-----------|
| `NURECEBIMENTO` | INT | FK → TGWREC |
| `NUNOTA` | INT | FK → TGFCAB |

#### VGWRECSITCAB - View Situação Recebimento

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `NUNOTA` | INT | Número da nota |
| `COD_SITUACAO` | INT | Código da situação WMS |

---

## 📊 Mapeamento Situação WMS

| COD_SITUACAO | Descrição | Grupo |
|--------------|-----------|-------|
| -1 | Não Enviado | Inicial |
| 3 | Aguardando conferência | Recebimento |
| 4 | Em processo conferência | Recebimento |
| 5 | Prob/Erro confirmação nota | Recebimento |
| 6 | Aguardando recontagem | Recebimento |
| 12 | Conferência com divergência | Recebimento |
| 13 | Parcialmente conferido | Recebimento |
| 14 | Aguardando armazenagem | Recebimento |
| 15 | Enviado para armazenagem | Recebimento |
| 16 | Concluído | Final |
| 17 | Aguardando conferência volumes | Recebimento |
| 18 | Armazenado parcial | Recebimento |
| 19 | Armazenado | Final |
| 100 | Cancelada | Cancelamento |

**Fonte:** `TDDOPC` (NUCAMPO = 65738)

---

## 🔗 Relacionamentos

```
TGFCAB (Nota)
    │
    ├──► TGFITE (Itens) ──► TGFPRO (Produto)
    │
    ├──► TGFPAR (Fornecedor)
    │
    ├──► TGFTOP (Tipo Operação)
    │
    └──► TGWRXN ──► TGWREC (Recebimento WMS)
```

---

## 🔍 Query Principal de Extração

```sql
SELECT
    -- Cabeçalho
    c.NUNOTA,
    c.NUMNOTA,
    c.DTNEG,
    c.DTENTSAI,
    c.CODPARC,
    c.CODEMP,
    c.VLRNOTA,
    c.VLRDESCTOT,
    c.VLRFRETE,
    c.STATUSNOTA,
    c.CODTIPOPER,
    c.TIPMOV,
    c.OBSERVACAO,

    -- Situação WMS
    NVL(wms.COD_SITUACAO, -1) AS COD_SITUACAO_WMS,

    -- Fornecedor
    f.NOMEPARC AS FORNECEDOR,
    f.CGC_CPF AS CNPJ_FORNECEDOR,

    -- Itens
    i.SEQUENCIA,
    i.CODPROD,
    i.QTDNEG,
    i.VLRUNIT,
    i.VLRTOT,

    -- Produto
    p.DESCRPROD,
    p.REFERENCIA,
    p.MARCA

FROM TGFCAB c
INNER JOIN TGFITE i ON c.NUNOTA = i.NUNOTA
INNER JOIN TGFPRO p ON i.CODPROD = p.CODPROD
INNER JOIN TGFPAR f ON c.CODPARC = f.CODPARC
LEFT JOIN VGWRECSITCAB wms ON c.NUNOTA = wms.NUNOTA

WHERE c.TIPMOV IN ('C', 'O', 'D')
  AND c.CODTIPOPER IN (1001, 1301)
  AND c.DTNEG >= :data_inicio
  AND c.DTNEG <= :data_fim
  AND f.FORNECEDOR = 'S'

ORDER BY c.DTNEG DESC, c.NUNOTA, i.SEQUENCIA
```

---

## 🔐 RLS - Row Level Security

Para implementar RLS no Data Hub, os filtros serão baseados em:

| Campo | Tipo de Restrição | Quem pode ver |
|-------|-------------------|---------------|
| `CODEMP` | Filial | Usuário só vê sua filial |
| `CODCOMPRADOR` | Comprador | Comprador só vê seus pedidos |
| `CODPARC` | Fornecedor | Fornecedor só vê seus pedidos |

**Exemplo de filtro RLS:**
```sql
-- Usuário normal: só vê sua filial
WHERE CODEMP IN (SELECT CODEMP FROM USUARIO_FILIAIS WHERE CODUSU = :usuario)

-- Comprador: só vê seus pedidos
WHERE CODCOMPRADOR = :cod_comprador

-- Gerente: vê tudo da região
WHERE CODEMP IN (SELECT CODEMP FROM FILIAIS_REGIAO WHERE CODREGIAO = :regiao)
```

---

## 📊 KPIs de Compras

| KPI | Fórmula | Descrição |
|-----|---------|-----------|
| Total Comprado | `SUM(VLRNOTA)` | Volume de compras no período |
| Ticket Médio | `AVG(VLRNOTA)` | Média por nota |
| Qtd Fornecedores | `COUNT(DISTINCT CODPARC)` | Fornecedores ativos |
| Pedidos Pendentes | `COUNT WHERE COD_SITUACAO IN (3,4,5,6)` | Aguardando recebimento |
| Taxa Conferência | `COUNT(16,19) / COUNT(*)` | % concluídos |

---

## 📁 Estrutura no Data Lake

```
/raw/sankhya/compras/
├── cabecalho/
│   └── YYYY-MM-DD/
│       └── compras_cab_YYYYMMDD.parquet
├── itens/
│   └── YYYY-MM-DD/
│       └── compras_ite_YYYYMMDD.parquet
├── wms/
│   └── YYYY-MM-DD/
│       └── compras_wms_YYYYMMDD.parquet
└── fornecedores/
    └── YYYY-MM-DD/
        └── fornecedores_YYYYMMDD.parquet
```

---

## ✅ Checklist

- [x] Identificar tipos de operação de compra (CODTIPOPER)
- [x] Mapear situação WMS completa
- [x] Identificar views importantes (VGWRECSITCAB)
- [ ] Verificar fluxo: Cotação → Pedido → Nota
- [ ] Identificar campos customizados (AD_*)
- [ ] Validar cálculo de lead time
- [ ] Testar extração completa
- [ ] Implementar script Python

---

## 📅 Histórico

| Data | Alteração | Responsável |
|------|-----------|-------------|
| Jan/2026 | Mapeamento WMS completo | Ítalo |
| Jan/2025 | Criação inicial | Ítalo |
