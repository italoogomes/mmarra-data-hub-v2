# 📊 Schema do Banco Sankhya - Mapeamento Completo

**Versão:** 1.0.0
**Data:** 2026-02-03
**Status:** ✅ Mapeamento Inicial Completo

---

## 🎯 Resumo Executivo

| Métrica | Valor |
|---------|-------|
| **Total de Tabelas** | 4.682 |
| **Módulos/Prefixos** | 96 |
| **Relacionamentos (FK)** | 500+ |
| **Views** | 100+ |
| **Registros Totais** | ~5 milhões+ |

---

## 📁 Distribuição por Módulo

### Principais Módulos

| Prefixo | Qtd Tabelas | Descrição |
|---------|-------------|-----------|
| **TGF** | 1.456 | Gestão Financeira/Comercial (CORE) |
| **TFP** | 753 | Fiscal/Produção |
| **TSI** | 243 | Sistema/Infraestrutura |
| **TDD** | 242 | Definição de Dados |
| **TRD** | 229 | Relatórios/Dashboards |
| **TIM** | 147 | Importação/Integração |
| **AD_** | 139 | Tabelas Customizadas (MMarra) |
| **TGW** | 135 | WMS (Warehouse Management) |
| **TCS** | 133 | Configuração Sistema |
| **TPR** | 119 | Produção |

### Módulos Secundários

| Prefixo | Qtd | Prefixo | Qtd | Prefixo | Qtd |
|---------|-----|---------|-----|---------|-----|
| TCB | 112 | TRI | 95 | TGA | 71 |
| TSE | 64 | CMD | 46 | TGFP | 35 |
| TFX | 32 | TMP | 32 | TLF | 29 |
| TAP | 28 | TWF | 27 | ACT | 24 |

---

## 🏆 TOP 20 Tabelas por Volume

| # | Tabela | Registros | Descrição |
|---|--------|-----------|-----------|
| 1 | **TGFITE** | 1.102.785 | Itens das Notas (produtos) |
| 2 | **TGFPRC** | 934.425 | Lista de Preços |
| 3 | **TGFPRO** | 393.667 | Cadastro de Produtos |
| 4 | **TGFEXC** | 379.177 | Exceções de Preço (preço especial por produto) |
| 5 | **TGFCAB** | 340.580 | Cabeçalho de Notas |
| 6 | **TGFCUS** | 288.208 | Histórico de Custos |
| 7 | **TGFDIN** | 226.421 | Campos Dinâmicos |
| 8 | **TGWEND** | 85.666 | Endereços WMS |
| 9 | **TGFPAR** | 57.081 | Parceiros (clientes/fornec.) |
| 10 | **TGFFIN** | 50.816 | Títulos Financeiros |
| 11 | **TGWEST** | 45.413 | Estoque WMS |
| 12 | **TGFEST** | 36.574 | Estoque ERP |
| 13 | **TGFVAR** | 23.234 | Variações/Grade |
| 14 | **TSIBAI** | 13.203 | Bairros |
| 15 | **TGFCPL** | 10.375 | Complemento de Nota |
| 16 | **TGWCON** | 8.994 | Conferência WMS |
| 17 | **TGWSEP** | 8.320 | Separação WMS |
| 18 | **TGWSXN** | 8.315 | Itens Separação WMS |
| 19 | **TSICFG** | 7.395 | Configurações |
| 20 | **TGFITC** | 6.689 | Itens de Cotação |

---

## 📋 Tabelas Principais por Área

### 🛒 Comercial (Vendas/Compras)

| Tabela | Registros | Colunas | Descrição |
|--------|-----------|---------|-----------|
| **TGFCAB** | 340.580 | 422 | Cabeçalho de todas as notas (vendas, compras, transf.) |
| **TGFITE** | 1.102.785 | 231 | Itens das notas (produtos por nota) |
| **TGFPAR** | 57.081 | 299 | Parceiros (clientes e fornecedores) |
| **TGFPRO** | 393.667 | 426 | Cadastro de produtos |
| **TGFVEN** | 111 | 44 | Vendedores |
| **TGFTOP** | 1.275 | 407 | Tipos de Operação |

**Relacionamentos principais:**
```
TGFCAB.CODPARC → TGFPAR.CODPARC
TGFITE.NUNOTA → TGFCAB.NUNOTA
TGFITE.CODPROD → TGFPRO.CODPROD
TGFCAB.CODVEND → TGFVEN.CODVEND
TGFCAB.CODTIPOPER → TGFTOP.CODTIPOPER
```

### 💰 Financeiro

| Tabela | Registros | Colunas | Descrição |
|--------|-----------|---------|-----------|
| **TGFFIN** | 50.816 | 252 | Títulos a pagar/receber |
| **TGFNAT** | 232 | 39 | Naturezas financeiras |

**Relacionamentos principais:**
```
TGFFIN.CODPARC → TGFPAR.CODPARC
TGFFIN.NUNOTA → TGFCAB.NUNOTA
TGFFIN.CODNAT → TGFNAT.CODNAT
```

### 📦 Estoque

| Tabela | Registros | Colunas | Descrição |
|--------|-----------|---------|-----------|
| **TGFEST** | 36.574 | 24 | Estoque ERP (por empresa/local) |
| **TGWEST** | 45.413 | 17 | Estoque WMS (por endereço) |
| **TGWEND** | 85.666 | 46 | Endereços físicos WMS |

**Relacionamentos principais:**
```
TGFEST.CODPROD → TGFPRO.CODPROD
TGFEST.CODEMP → TGFEMP.CODEMP
TGWEST.CODPROD → TGFPRO.CODPROD
TGWEST.CODEND → TGWEND.CODEND
```

### 🏭 WMS (Warehouse Management)

| Tabela | Registros | Colunas | Descrição |
|--------|-----------|---------|-----------|
| **TGWREC** | 1.025 | 20 | Recebimento |
| **TGWSEP** | 8.320 | 36 | Separação (cabeçalho) |
| **TGWSXN** | 8.315 | - | Separação (itens) |
| **TGWCON** | 8.994 | - | Conferência |
| **TGWEMPE** | 1.337 | 12 | Empenho (venda→compra) |
| **TGWRXN** | 1.025 | - | Recebimento×Nota |

**Relacionamentos principais:**
```
TGWEMPE.NUNOTAPEDVEN → TGFCAB.NUNOTA (venda)
TGWEMPE.NUNOTA → TGFCAB.NUNOTA (compra)
TGWEMPE.CODPROD → TGFPRO.CODPROD
TGWREC.NUNOTA → TGFCAB.NUNOTA
TGWSEP.NUNOTA → TGFCAB.NUNOTA
```

### 📝 Cotação

| Tabela | Registros | Colunas | Descrição |
|--------|-----------|---------|-----------|
| **TGFCOT** | 2.488 | 36 | Cabeçalho da cotação |
| **TGFITC** | 6.689 | 78 | Itens por fornecedor |

**Relacionamentos principais:**
```
TGFITC.NUMCOTACAO → TGFCOT.NUMCOTACAO
TGFITC.CODPARC → TGFPAR.CODPARC
TGFITC.CODPROD → TGFPRO.CODPROD
TGFCOT.CODUSURESP → TSIUSU.CODUSU
```

### 🏢 Sistema/Infraestrutura

| Tabela | Registros | Colunas | Descrição |
|--------|-----------|---------|-----------|
| **TSIUSU** | 228 | 141 | Usuários |
| **TSIEMP** | 10 | 102 | Empresas |
| **TGFEMP** | 9 | 645 | Configuração de Empresas |
| **TSICID** | 5.608 | - | Cidades |
| **TSIBAI** | 13.203 | - | Bairros |
| **TSICFG** | 7.395 | - | Configurações |

---

## 🔗 Modelo de Relacionamentos (Simplificado)

```
                    ┌─────────────┐
                    │   TSIUSU    │
                    │  (usuarios) │
                    └──────┬──────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    │                      │                      │
    ▼                      ▼                      ▼
┌─────────┐          ┌─────────┐          ┌─────────┐
│ TGFCOT  │          │ TGFCAB  │          │ TGWSEP  │
│(cotação)│          │ (notas) │          │  (sep)  │
└────┬────┘          └────┬────┘          └────┬────┘
     │                    │                    │
     ▼                    ▼                    ▼
┌─────────┐          ┌─────────┐          ┌─────────┐
│ TGFITC  │◄────────►│ TGFITE  │◄────────►│ TGWSXN  │
│(it.cot) │          │ (itens) │          │(it.sep) │
└────┬────┘          └────┬────┘          └─────────┘
     │                    │
     │         ┌──────────┴──────────┐
     │         │                     │
     ▼         ▼                     ▼
┌─────────────────┐          ┌─────────────┐
│     TGFPRO      │          │   TGFPAR    │
│   (produtos)    │          │ (parceiros) │
└────────┬────────┘          └─────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌───────┐
│TGFEST │ │TGWEST │
│(est)  │ │(wms)  │
└───────┘ └───┬───┘
              │
              ▼
         ┌───────┐
         │TGWEND │
         │(ender)│
         └───────┘

              TGWEMPE
         ┌──────────────┐
         │   (empenho)  │
         │ venda→compra │
         └──────────────┘
```

---

## 📊 Campos Comuns (Chaves)

### Chaves Primárias Principais

| Campo | Tabelas | Descrição |
|-------|---------|-----------|
| `NUNOTA` | TGFCAB, TGFITE, TGFFIN, TGWREC, TGWSEP | Número único da nota |
| `CODPROD` | TGFPRO, TGFITE, TGFEST, TGWEST, TGFITC | Código do produto |
| `CODPARC` | TGFPAR, TGFCAB, TGFITC, TGFFIN | Código do parceiro |
| `CODEMP` | TGFEMP, TSIEMP, TGFCAB, TGFEST | Código da empresa |
| `CODUSU` | TSIUSU, TGFCOT | Código do usuário |
| `CODEND` | TGWEND, TGWEST | Código do endereço WMS |
| `NUMCOTACAO` | TGFCOT, TGFITC | Número da cotação |
| `CODTIPOPER` | TGFTOP, TGFCAB | Código tipo operação |

### Campos de Data Importantes

| Campo | Descrição |
|-------|-----------|
| `DTNEG` | Data da negociação/emissão |
| `DTMOV` | Data do movimento |
| `DTFATUR` | Data de faturamento |
| `DTPREVENT` | Data previsão de entrega |
| `DTALTER` | Data última alteração |

### Campos de Status

| Campo | Tabela | Valores |
|-------|--------|---------|
| `PENDENTE` | TGFCAB | S=Sim, N=Não |
| `STATUSNOTA` | TGFCAB | L=Liberado, P=Pendente |
| `TIPMOV` | TGFCAB | V=Venda, C=Compra, O=Outros |
| `SITUACAO` | TGFCOT | F=Final, C=Cancel, A=Aberta |
| `STATUSPRODCOT` | TGFITC | O=Orçam, F=Final, C=Cotado |

---

## 🚀 Recomendações para Extração

### Prioridade ALTA (Core Business)

| Ordem | Tabelas | Justificativa |
|-------|---------|---------------|
| 1 | TGFCAB + TGFITE | Todas as transações comerciais |
| 2 | TGFPAR | Clientes e fornecedores |
| 3 | TGFPRO | Catálogo de produtos |
| 4 | TGFFIN | Contas a pagar/receber |
| 5 | TGFEST + TGWEST | Posição de estoque |

### Prioridade MÉDIA

| Ordem | Tabelas | Justificativa |
|-------|---------|---------------|
| 6 | TGWEMPE + TGWREC + TGWSEP | Processo WMS |
| 7 | TGFCOT + TGFITC | Cotações de compra |
| 8 | TGFPRC + TGFCUS | Preços e custos |

### Prioridade BAIXA (Auxiliares)

| Ordem | Tabelas | Justificativa |
|-------|---------|---------------|
| 9 | TSIUSU + TSIEMP | Dados de sistema |
| 10 | TGFTOP + TGFNAT | Configurações |
| 11 | TSICID + TSIBAI | Localidades |

---

## 📝 Queries de Extração Sugeridas

### 1. Vendas Completas

```sql
SELECT
    c.NUNOTA, c.NUMNOTA, c.DTNEG, c.CODEMP,
    c.CODPARC, p.NOMEPARC AS CLIENTE,
    c.VLRNOTA, c.CODVEND, v.APELIDO AS VENDEDOR,
    i.CODPROD, pr.DESCRPROD, i.QTDNEG, i.VLRUNIT, i.VLRTOT
FROM TGFCAB c
JOIN TGFITE i ON i.NUNOTA = c.NUNOTA
JOIN TGFPAR p ON p.CODPARC = c.CODPARC
LEFT JOIN TGFPRO pr ON pr.CODPROD = i.CODPROD
LEFT JOIN TGFVEN v ON v.CODVEND = c.CODVEND
WHERE c.TIPMOV = 'V'
  AND c.DTNEG >= ADD_MONTHS(SYSDATE, -1)
ORDER BY c.DTNEG DESC
```

### 2. Estoque Atual

```sql
SELECT
    e.CODPROD, p.DESCRPROD,
    e.CODEMP, emp.NOMEFANTASIA AS EMPRESA,
    e.ESTOQUE, e.RESERVADO, e.DISPONIVEL
FROM TGFEST e
JOIN TGFPRO p ON p.CODPROD = e.CODPROD
JOIN TGFEMP emp ON emp.CODEMP = e.CODEMP
WHERE e.ESTOQUE > 0
ORDER BY e.ESTOQUE DESC
```

### 3. Financeiro em Aberto

```sql
SELECT
    f.NUFIN, f.NUNOTA, f.CODPARC, p.NOMEPARC,
    f.DTVENC, f.VLRDESDOB, f.RECDESP,
    CASE f.RECDESP WHEN 1 THEN 'RECEBER' ELSE 'PAGAR' END AS TIPO
FROM TGFFIN f
JOIN TGFPAR p ON p.CODPARC = f.CODPARC
WHERE f.DHBAIXA IS NULL
  AND f.DTVENC <= SYSDATE + 30
ORDER BY f.DTVENC
```

---

## 📁 Arquivos de Referência

| Arquivo | Descrição |
|---------|-----------|
| `mapeamento_banco_sankhya.json` | JSON completo do mapeamento |
| `tabelas_por_volume.json` | Contagem de registros |
| `relatorio_schema_banco.html` | Relatório visual interativo |
| `mapear_banco_completo.py` | Script de mapeamento |
| `mapear_tabelas_volume.py` | Script de contagem |

---

**Última atualização:** 2026-02-03
**Próxima revisão:** Adicionar novas tabelas descobertas durante extrações
