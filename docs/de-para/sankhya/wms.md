# WMS - Warehouse Management System

> **Status**: Mapeado
> **Responsável**: Ítalo
> **Descoberta concluída em**: Janeiro/2026
> **Pedido de teste**: 1176397
> **Banco**: Oracle (Sankhya ERP)

---

## Resumo

O campo **"Situação WMS"** exibido nas telas do Sankhya é um **campo calculado** (`SITUACAOWMS`) da tabela `TGFCAB`, não um campo físico. Ele consulta views diferentes dependendo do tipo de movimento:

- **Compras** (TIPMOV C, O, D): consulta `VGWRECSITCAB`
- **Vendas** (TIPMOV P, V, E, T, J): consulta `VGWSEPSITCAB`

---

## Mapeamento Completo - 22 Status

| COD_SITUACAO | Descrição | Contexto |
|--------------|-----------|----------|
| -1 | Não Enviado | WMS não utilizado |
| 0 | Aguardando separação | Separação (vendas) |
| 1 | Enviado para separação | Separação (vendas) |
| 2 | Em processo separação | Separação (vendas) |
| **3** | **Aguardando conferência** | **Recebimento (compras)** |
| 4 | Em processo conferência | Recebimento |
| 5 | Prob/Erro. confirmação nota | Recebimento |
| 6 | Aguardando recontagem | Recebimento |
| 7 | Pedido totalmente cortado | Separação |
| 8 | Pedido parcialmente cortado | Separação |
| 9 | Conferência validada | Conferência |
| 10 | Aguardando conferência (Separação) | Separação |
| 12 | Conferência com divergência | Recebimento |
| 13 | Parcialmente conferido | Recebimento |
| 14 | Aguardando armazenagem | Recebimento |
| 15 | Enviado para armazenagem | Recebimento |
| 16 | Concluído | Final |
| 17 | Aguardando conferência volumes | Recebimento |
| 18 | Armazenado parcial | Recebimento |
| 19 | Armazenado | Final |
| 98 | Aguardando formação de volumes | Separação |
| 100 | Cancelada | Cancelamento |

**Fonte:** Tabela `TDDOPC` (NUCAMPO = 65738)

---

## Status Relevantes para Compras

| Código | Descrição | Significado |
|--------|-----------|-------------|
| -1 | Não Enviado | Não usa WMS |
| 3 | Aguardando conferência | Pedido chegou, esperando conferir |
| 4 | Em processo conferência | Conferência em andamento |
| 5 | Prob/Erro confirmação | Problema na confirmação da nota |
| 6 | Aguardando recontagem | Precisa recontar |
| 9 | Conferência validada | Conferência OK |
| 12 | Conferência com divergência | Quantidade diferente do pedido |
| 13 | Parcialmente conferido | Conferência incompleta |
| 14 | Aguardando armazenagem | Conferido, aguardando guardar |
| 15 | Enviado para armazenagem | Em processo de guardar |
| 17 | Aguardando conferência volumes | Esperando conferir volumes |
| 18 | Armazenado parcial | Parte guardada |
| 19 | Armazenado | Guardado no estoque |
| 16 | Concluído | Processo finalizado |
| 100 | Cancelada | Cancelado |

---

## Fluxo de Recebimento (TGWREC.SITUACAO → COD_SITUACAO)

A view `VGWRECSITCAB` traduz o status interno da tabela `TGWREC`:

| TGWREC.SITUACAO | COD_SITUACAO | Descrição | Condição Extra |
|-----------------|--------------|-----------|----------------|
| 0 | 3 | Aguardando conferência | - |
| 1 | 4 | Em processo conferência | - |
| 2 | 5 | Prob/Erro confirmação nota | STATUSCONF = 2 |
| 2 | 6 | Aguardando recontagem | STATUSCONF = 3 |
| 2 | 12 | Conferência com divergência | Outros |
| 3 | 13 | Parcialmente conferido | USACONFPARCIAL='S' e CONFFINAL='N' |
| 3 | 14 | Aguardando armazenagem | Outros |
| 4 | 15 | Enviado para armazenagem | - |
| 5 | 18 | Armazenado parcial | Conf. parcial ou estoque pendente |
| 5 | 19 | Armazenado | Outros |
| 6 | 16 | Concluído | - |

---

## Tabelas e Views

### Tabelas Principais

| Tabela | Descrição |
|--------|-----------|
| `TGFCAB` | Cabeçalho de notas (campo calculado SITUACAOWMS) |
| `TGWREC` | Recebimento WMS (SITUACAO, STATUSCONF, USACONFPARCIAL) |
| `TGWRXN` | Relacionamento Recebimento ↔ Nota (NURECEBIMENTO, NUNOTA) |
| `TGWSEP` | Separação WMS (para vendas) |
| `TGWEST` | Estoque WMS por endereço |
| `TDDOPC` | Dicionário de opções (mapeamento código → descrição) |
| `TDDCAM` | Dicionário de campos (definição do campo calculado) |

### Views

| View | Descrição | Uso |
|------|-----------|-----|
| `VGWRECSITCAB` | Situação de Recebimento por NUNOTA | Compras (TIPMOV C, O, D) |
| `VGWSEPSITCAB` | Situação de Separação por NUNOTA | Vendas (TIPMOV P, V, E, T, J) |
| `VGWSTATUSWMS` | Status WMS geral | Consultas |

---

## Arquitetura

```
TGFCAB (Nota)
    │
    └──► TGWRXN (liga nota ao recebimento)
              │
              └──► TGWREC (status real: SITUACAO 0-6)
                        │
                        └──► VGWRECSITCAB (traduz para COD_SITUACAO 3-19)
                                    │
                                    └──► TDDOPC (traduz para descrição)
```

---

## Curls para API Sankhya

### 1. Situação WMS de um pedido específico
```bash
curl -X POST "https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN_AQUI" \
  -d '{
    "serviceName": "DbExplorerSP.executeQuery",
    "requestBody": {
      "sql": "SELECT NUNOTA, COD_SITUACAO FROM VGWRECSITCAB WHERE NUNOTA = 1176397"
    }
  }'
```

### 2. Mapeamento código → descrição (TDDOPC)
```bash
curl -X POST "https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN_AQUI" \
  -d '{
    "serviceName": "DbExplorerSP.executeQuery",
    "requestBody": {
      "sql": "SELECT VALOR, OPCAO FROM TDDOPC WHERE NUCAMPO = 65738 ORDER BY TO_NUMBER(VALOR)"
    }
  }'
```

### 3. Relatório de compras com status WMS (últimos 30 dias)
```bash
curl -X POST "https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN_AQUI" \
  -d '{
    "serviceName": "DbExplorerSP.executeQuery",
    "requestBody": {
      "sql": "SELECT C.NUNOTA, C.NUMNOTA, C.DTNEG, V.COD_SITUACAO, O.OPCAO AS SITUACAO_WMS FROM TGFCAB C LEFT JOIN VGWRECSITCAB V ON V.NUNOTA = C.NUNOTA LEFT JOIN TDDOPC O ON O.NUCAMPO = 65738 AND O.VALOR = TO_CHAR(V.COD_SITUACAO) WHERE C.TIPMOV = '\''C'\'' AND C.DTNEG >= TRUNC(SYSDATE) - 30"
    }
  }'
```

### 4. Ver SQL da view VGWRECSITCAB
```bash
curl -X POST "https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN_AQUI" \
  -d '{
    "serviceName": "DbExplorerSP.executeQuery",
    "requestBody": {
      "sql": "SELECT TEXT FROM ALL_VIEWS WHERE VIEW_NAME = '\''VGWRECSITCAB'\''"
    }
  }'
```

### 5. Estrutura da view VGWRECSITCAB
```bash
curl -X POST "https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN_AQUI" \
  -d '{
    "serviceName": "DbExplorerSP.executeQuery",
    "requestBody": {
      "sql": "SELECT COLUMN_NAME, DATA_TYPE FROM ALL_TAB_COLUMNS WHERE TABLE_NAME = '\''VGWRECSITCAB'\''"
    }
  }'
```

---

## Queries SQL Úteis

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
JOIN TDDOPC O ON O.NUCAMPO = 65738 AND O.VALOR = TO_CHAR(V.COD_SITUACAO)
WHERE V.COD_SITUACAO = 3  -- Aguardando conferência
```

### Ver mapeamento completo de opções
```sql
SELECT VALOR AS COD_SITUACAO, OPCAO AS DESCRICAO
FROM TDDOPC
WHERE NUCAMPO = 65738
ORDER BY TO_NUMBER(VALOR)
```

### Pedidos de compra com situação WMS
```sql
SELECT
    C.NUNOTA,
    C.NUMNOTA,
    C.DTNEG,
    C.CODPARC,
    C.VLRNOTA,
    NVL(V.COD_SITUACAO, -1) AS COD_SITUACAO_WMS,
    NVL(O.OPCAO, 'Não Enviado') AS SITUACAO_WMS
FROM TGFCAB C
LEFT JOIN VGWRECSITCAB V ON C.NUNOTA = V.NUNOTA
LEFT JOIN TDDOPC O ON O.NUCAMPO = 65738 AND O.VALOR = TO_CHAR(V.COD_SITUACAO)
WHERE C.CODTIPOPER IN (1001, 1301)
ORDER BY C.DTNEG DESC
```

---

## SQL do Campo Calculado SITUACAOWMS

```sql
SELECT
(nullValue(
  CASE
    WHEN (TPO.UTILIZAWMS = 'N' OR TGFCAB.TIPMOV NOT IN ('C','O','P','V','D','E','J','Q','L','T')) THEN -1
    WHEN TGFCAB.TIPMOV IN ('C','O','D') THEN
      nullValue((SELECT VREC.COD_SITUACAO FROM VGWRECSITCAB VREC WHERE VREC.NUNOTA = TGFCAB.NUNOTA), -1)
    WHEN TGFCAB.TIPMOV IN ('T') AND TPO.TIPATUALWMS = 'E' THEN
      nullValue((SELECT VREC.COD_SITUACAO FROM VGWRECSITCAB VREC WHERE VREC.NUNOTA = TGFCAB.NUNOTA), -1)
    WHEN TGFCAB.TIPMOV IN ('P','V','E','T','J') THEN
      nullValue((SELECT VSEP.COD_SITUACAO FROM VGWSEPSITCAB VSEP WHERE VSEP.NUNOTA = TGFCAB.NUNOTA), -1)
  END, -1)) AS SITUACAOWMS
FROM TGFTOP TPO
WHERE TPO.CODTIPOPER = TGFCAB.CODTIPOPER AND TPO.DHALTER = TGFCAB.DHTIPOPER
```

---

## SQL da View VGWRECSITCAB

```sql
SELECT RXN.NUNOTA,
       NVL(
         CASE MIN(REC.SITUACAO)
           WHEN 0 THEN 3  -- Aguardando conferência
           WHEN 1 THEN 4  -- Em processo conferência
           WHEN 2 THEN
             CASE MIN(REC.STATUSCONF)
               WHEN 2 THEN 5   -- Prob/Erro confirmação nota
               WHEN 3 THEN 6   -- Aguardando recontagem
               ELSE 12         -- Conferência com divergência
             END
           WHEN 3 THEN
             CASE
               WHEN USACONFPARCIAL = 'S' AND CONFFINAL = 'N' THEN 13  -- Parcialmente conferido
               ELSE 14  -- Aguardando armazenagem
             END
           WHEN 4 THEN 15  -- Enviado para armazenagem
           WHEN 5 THEN
             CASE
               WHEN (USACONFPARCIAL = 'S' AND CONFFINAL = 'N')
                 OR EXISTS(SELECT 1 FROM TGWEST EST
                           WHERE EST.CODEND = REC.CODENDDOCA
                             AND (EST.ENTRPENDVOLPAD + EST.ESTOQUEVOLPAD) > 0)
               THEN 18  -- Armazenamento parcial
               ELSE 19  -- Armazenado
             END
           WHEN 6 THEN 16  -- Concluído
         END, -1) AS COD_SITUACAO
FROM TGWREC REC
INNER JOIN TGWRXN RXN ON (RXN.NURECEBIMENTO = REC.NURECEBIMENTO)
WHERE REC.NURECEBIMENTO = (
  SELECT MAX(NURECEBIMENTO)
  FROM TGWRXN R1
  WHERE R1.NUNOTA = RXN.NUNOTA
)
GROUP BY RXN.NUNOTA, REC.USACONFPARCIAL, REC.CONFFINAL, REC.CODENDDOCA
```

---

## Estatísticas Reais (últimos 30 dias)

| Status | Descrição | Volume |
|--------|-----------|--------|
| 16 | Concluído | Maioria |
| 15 | Enviado para armazenagem | Vários |
| 14 | Aguardando armazenagem | Alguns |
| 3 | Aguardando conferência | ~20 pedidos |
| 5 | Prob/Erro confirmação nota | Poucos |
| 6 | Aguardando recontagem | Poucos |
| 12 | Conferência com divergência | Poucos |
| 19 | Armazenado | Poucos |
| null | Sem registro WMS | Muitos (não passaram pelo WMS) |

---

## Validação

| Campo | Valor |
|-------|-------|
| Pedido teste | 1176397 |
| COD_SITUACAO | 3 |
| Descrição esperada | Aguardando conferência |
| Descrição na tela | Aguardando conferência |

---

## Observação Importante

Muitos pedidos têm `null` no WMS = **não passaram pelo controle de recebimento**. Isso é normal para operações que não usam WMS.

---

## Histórico

| Data | Alteração | Responsável |
|------|-----------|-------------|
| Jan/2026 | Adicionados curls API, estatísticas, 22 status | Ítalo |
| Jan/2026 | Mapeamento inicial | Ítalo |
