# 📦 Mapeamento: Compras (EM DESCOBERTA)

> **Status**: 🟡 Explorando
> **Responsável**: Ítalo
> **Início**: Janeiro/2025
> **Pedido de teste**: `1176397`
> **Banco**: Oracle (Sankhya ERP)

---

## ✅ O que já sabemos

### Tipos de Operação de COMPRA
| Código | Descrição | Uso |
|--------|-----------|-----|
| `1001` | Compra para Estoque | Compra normal |
| `1301` | Compra Casada | Compra vinculada a venda |

### Tabelas principais
| Tabela | Conteúdo | Confirmado |
|--------|----------|------------|
| `TGFCAB` | Cabeçalho dos pedidos | ✅ |
| `TGFITE` | Itens dos pedidos | ✅ |
| `TGFPAR` | Fornecedores | ✅ |
| `TGFPRO` | Produtos | ✅ |
| `TGFTOP` | Tipos de operação | ✅ |
| `TGWREC` | Recebimento WMS | ✅ |
| `TGWRXN` | Relacionamento Recebimento ↔ Nota | ✅ |
| `TGWEST` | Estoque WMS por endereço | ✅ |
| `TDDOPC` | Dicionário de opções | ✅ |
| `VGWRECSITCAB` | View - Situação Recebimento | ✅ |

### Filtro para pegar só COMPRAS
```sql
WHERE CODTIPOPER IN (1001, 1301)
-- ou
WHERE TIPMOV IN ('C', 'O', 'D')  -- C=Compra, O=Ordem, D=Devolução
```

---

## 🔍 Descobertas da Exploração

### 1. Situação WMS - Campo Calculado

O campo **"Situação WMS"** exibido nas telas do Sankhya é um **campo calculado** (`SITUACAOWMS`) da tabela `TGFCAB`, não um campo físico.

**Como funciona:**
- Para Compras (TIPMOV C, O, D): consulta a view `VGWRECSITCAB`
- Para Vendas (TIPMOV P, V, E, T, J): consulta a view `VGWSEPSITCAB`

### 2. Mapeamento Completo - Situação WMS

| COD_SITUACAO | Descrição | Contexto | Grupo |
|--------------|-----------|----------|-------|
| -1 | Não Enviado | WMS não utilizado | Inicial |
| 0 | Aguardando separação | Separação (vendas) | Separação |
| 1 | Enviado para separação | Separação (vendas) | Separação |
| 2 | Em processo separação | Separação (vendas) | Separação |
| **3** | **Aguardando conferência** | **Recebimento (compras)** | Recebimento |
| 4 | Em processo conferência | Recebimento | Recebimento |
| 5 | Prob/Erro confirmação nota | Recebimento | Recebimento |
| 6 | Aguardando recontagem | Recebimento | Recebimento |
| 10 | Aguardando conferência (Separação) | Separação | Separação |
| 12 | Conferência com divergência | Recebimento | Recebimento |
| 13 | Parcialmente conferido | Recebimento | Recebimento |
| 14 | Aguardando armazenagem | Recebimento | Recebimento |
| 15 | Enviado para armazenagem | Recebimento | Recebimento |
| 16 | Concluído | Final | Final |
| 17 | Aguardando conferência volumes | Recebimento | Recebimento |
| 18 | Armazenado parcial | Recebimento | Recebimento |
| 19 | Armazenado | Final | Final |
| 100 | Cancelada | Cancelamento | Cancelamento |

**Fonte:** Tabela `TDDOPC` (NUCAMPO = 65738)

---

## 📋 Detalhamento das Tabelas WMS

### Tabela: TGWREC (Recebimento WMS)

**Descrição**: Controla o processo de recebimento de mercadorias no WMS

**Colunas importantes**:
| Coluna | Tipo | O que é |
|--------|------|---------|
| `NURECEBIMENTO` | INT | PK - Número do recebimento |
| `SITUACAO` | INT | Status interno (0-6) |
| `STATUSCONF` | INT | Status da conferência |
| `USACONFPARCIAL` | CHAR | Usa conferência parcial (S/N) |
| `CONFFINAL` | CHAR | Conferência finalizada (S/N) |
| `CODENDDOCA` | INT | Código do endereço da doca |

**Tradução TGWREC.SITUACAO → COD_SITUACAO:**
| SITUACAO | COD_SITUACAO | Descrição |
|----------|--------------|-----------|
| 0 | 3 | Aguardando conferência |
| 1 | 4 | Em processo conferência |
| 2 | 5, 6 ou 12 | Depende do STATUSCONF |
| 3 | 13 ou 14 | Depende de USACONFPARCIAL |
| 4 | 15 | Enviado para armazenagem |
| 5 | 18 ou 19 | Armazenado (parcial ou total) |
| 6 | 16 | Concluído |

---

### Tabela: TGWRXN (Relacionamento Recebimento ↔ Nota)

**Descrição**: Liga o recebimento WMS à nota fiscal

| Coluna | Tipo | O que é |
|--------|------|---------|
| `NURECEBIMENTO` | INT | FK → TGWREC |
| `NUNOTA` | INT | FK → TGFCAB |

---

### Tabela: TDDOPC (Dicionário de Opções)

**Descrição**: Contém os mapeamentos código → descrição

**Query para listar opções:**
```sql
SELECT VALOR AS COD_SITUACAO, OPCAO AS DESCRICAO
FROM TDDOPC
WHERE NUCAMPO = 65738
ORDER BY VALOR
```

---

## 🔗 Relacionamentos Descobertos

```
TGFCAB (Nota)
    │
    ├──► TGFITE (Itens)
    │       └──► TGFPRO (Produto)
    │
    ├──► TGFPAR (Fornecedor)
    │
    ├──► TGFTOP (Tipo Operação)
    │
    └──► TGWRXN ──► TGWREC (Recebimento WMS)
                        │
                        └──► TGWEST (Estoque por endereço)
```

---

## 📊 Queries Úteis

### Consultar situação WMS de um pedido
```sql
SELECT NUNOTA, COD_SITUACAO
FROM VGWRECSITCAB
WHERE NUNOTA = 1176397
```

### Listar pedidos por situação WMS
```sql
SELECT V.NUNOTA, V.COD_SITUACAO, O.OPCAO AS DESCRICAO
FROM VGWRECSITCAB V
JOIN TDDOPC O ON O.NUCAMPO = 65738 AND O.VALOR = V.COD_SITUACAO
WHERE V.COD_SITUACAO = 3  -- Aguardando conferência
```

### Ver mapeamento completo de opções
```sql
SELECT VALOR AS COD_SITUACAO, OPCAO AS DESCRICAO
FROM TDDOPC
WHERE NUCAMPO = 65738
ORDER BY VALOR
```

### Query completa de pedidos de compra com situação WMS
```sql
SELECT
    c.NUNOTA,
    c.NUMNOTA,
    c.DTNEG,
    c.CODPARC,
    c.CODEMP,
    c.VLRNOTA,
    c.STATUSNOTA,
    c.CODTIPOPER,

    -- Situação WMS
    NVL(v.COD_SITUACAO, -1) AS COD_SITUACAO_WMS,
    NVL(o.OPCAO, 'Não Enviado') AS SITUACAO_WMS,

    -- Fornecedor
    p.NOMEPARC AS FORNECEDOR,
    p.CGC_CPF AS CNPJ_FORNECEDOR

FROM TGFCAB c
INNER JOIN TGFPAR p ON c.CODPARC = p.CODPARC
LEFT JOIN VGWRECSITCAB v ON c.NUNOTA = v.NUNOTA
LEFT JOIN TDDOPC o ON o.NUCAMPO = 65738 AND o.VALOR = v.COD_SITUACAO

WHERE c.CODTIPOPER IN (1001, 1301)
  AND c.DTNEG >= :data_inicio

ORDER BY c.DTNEG DESC
```

---

## ❓ Dúvidas / A Descobrir

- [x] Como funciona o campo Situação WMS? → **Campo calculado via views**
- [x] Quais são os status possíveis? → **Mapeado na TDDOPC (NUCAMPO=65738)**
- [ ] Quais campos `AD_*` customizados existem para compras?
- [ ] Tem campo de `DTENTRADA` (data real de entrada)?
- [ ] Tem campo de observação/justificativa?
- [ ] Tem outros tipos de operação além de 1001 e 1301?
- [ ] Como funciona o fluxo Cotação → Pedido → Nota?

---

## 💡 Campos Customizados (AD_*)

| Campo | Tabela | O que parece ser |
|-------|--------|------------------|
| AD_   |        | A descobrir      |
| AD_   |        | A descobrir      |

---

## ✅ Progresso

- [x] Login funcionando no Postman
- [x] Encontrei tabela principal de compras (TGFCAB)
- [x] Encontrei tabela de itens (TGFITE)
- [x] Encontrei tabela de fornecedores (TGFPAR)
- [x] Mapeei situação WMS completa
- [x] Identifiquei views importantes (VGWRECSITCAB)
- [x] Documentei os campos importantes do WMS
- [ ] Identificar campos customizados AD_*
- [ ] Testar query completa de extração
- [ ] Mapear cotações (TGFCOT)
- [ ] Mapear pedidos de compra (TGFPCO)

---

## ✅ Validação

| Campo | Valor |
|-------|-------|
| Pedido teste | 1176397 |
| COD_SITUACAO | 3 |
| Descrição esperada | Aguardando conferência |
| Descrição na tela | ✅ Aguardando conferência |

---

*Última atualização: Janeiro/2026*
