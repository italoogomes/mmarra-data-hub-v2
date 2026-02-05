# 🔌 API Sankhya - Documentação Completa

**Versão:** 2.0.0
**Atualizado:** 2026-02-05
**Status:** ✅ Operacional

---

## 📋 Visão Geral

A API Sankhya permite executar queries SQL diretamente no banco Oracle do ERP.

| Item | Valor |
|------|-------|
| **Base URL** | `https://api.sankhya.com.br` |
| **Autenticação** | OAuth2 (client_credentials) |
| **Banco** | Oracle |
| **Timeout recomendado** | 60 segundos |

---

## 🔐 Autenticação

### Endpoint
```
POST https://api.sankhya.com.br/authenticate
```

### Headers
```
Content-Type: application/x-www-form-urlencoded
X-Token: {SANKHYA_X_TOKEN}
```

### Body
```
client_id={SANKHYA_CLIENT_ID}
client_secret={SANKHYA_CLIENT_SECRET}
grant_type=client_credentials
```

### Resposta de Sucesso (200)
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### Exemplo Python
```python
import os
import requests
from dotenv import load_dotenv

load_dotenv('mcp_sankhya/.env')

def autenticar():
    """Autentica na API Sankhya e retorna o access_token."""
    response = requests.post(
        "https://api.sankhya.com.br/authenticate",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Token": os.getenv('SANKHYA_X_TOKEN')
        },
        data={
            "client_id": os.getenv('SANKHYA_CLIENT_ID'),
            "client_secret": os.getenv('SANKHYA_CLIENT_SECRET'),
            "grant_type": "client_credentials"
        },
        timeout=30
    )
    
    if response.status_code != 200:
        raise Exception(f"Erro autenticação: {response.status_code}")
    
    return response.json()["access_token"]
```

---

## 📝 Executar Query SQL

### Endpoint
```
POST https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery&outputType=json
```

### Headers
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

### Body
```json
{
  "requestBody": {
    "sql": "SELECT * FROM TGFCAB WHERE ROWNUM <= 10"
  }
}
```

### Resposta de Sucesso
```json
{
  "status": "1",
  "statusMessage": "OK",
  "responseBody": {
    "fieldsMetadata": [
      {"name": "NUNOTA", "description": "Nr. Único"},
      {"name": "NUMNOTA", "description": "Nr. Nota"}
    ],
    "rows": [
      ["12345", "1001"],
      ["12346", "1002"]
    ]
  }
}
```

### Exemplo Python
```python
def executar_query(access_token, sql):
    """Executa uma query SQL no Sankhya."""
    response = requests.post(
        "https://api.sankhya.com.br/gateway/v1/mge/service.sbr"
        "?serviceName=DbExplorerSP.executeQuery&outputType=json",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json={"requestBody": {"sql": sql}},
        timeout=60
    )
    
    if response.status_code != 200:
        raise Exception(f"Erro HTTP: {response.status_code}")
    
    result = response.json()
    
    if result.get("status") != "1":
        raise Exception(f"Erro Sankhya: {result.get('statusMessage')}")
    
    return result["responseBody"]
```

---

## ⚠️ Erros Comuns e Soluções

### HTTP 401 - Não Autorizado

| Causa | Solução |
|-------|---------|
| Token expirado | Reautenticar (tokens duram 1 hora) |
| X-Token inválido | Verificar variável `SANKHYA_X_TOKEN` |
| Client ID/Secret errado | Verificar credenciais no `.env` |

### HTTP 500 - Erro Interno

| Causa | Solução |
|-------|---------|
| SQL inválido | Verificar sintaxe Oracle |
| Tabela não existe | Verificar nome (case sensitive) |
| Timeout | Adicionar `ROWNUM` ou filtros |

### Status "0" na Resposta

| statusMessage | Causa | Solução |
|---------------|-------|---------|
| `ORA-00942: table or view does not exist` | Tabela não existe | Verificar nome |
| `ORA-00904: invalid identifier` | Coluna não existe | Verificar coluna |
| `ORA-01722: invalid number` | Tipo inválido | Verificar tipos |
| `ORA-00936: missing expression` | SQL incompleto | Verificar sintaxe |

---

## 🚀 Boas Práticas

### 1. SEMPRE usar ROWNUM para limitar resultados
```sql
-- ❌ RUIM (pode travar ou timeout)
SELECT * FROM TGFCAB

-- ✅ BOM
SELECT * FROM TGFCAB WHERE ROWNUM <= 1000
```

### 2. Filtrar por empresa quando possível
```sql
-- Empresa 6 é a principal da MMarra
SELECT * FROM TGFCAB 
WHERE CODEMP = 6 
  AND ROWNUM <= 100
```

### 3. Usar filtro de data para queries grandes
```sql
-- Últimos 30 dias
SELECT * FROM TGFCAB 
WHERE DTNEG >= TRUNC(SYSDATE) - 30
  AND ROWNUM <= 1000
```

### 4. Tratar campos nulos
```sql
-- Usar NVL para valores default
SELECT 
    NUNOTA,
    NVL(CODVEND, 0) AS CODVEND,
    NVL(VLRNOTA, 0) AS VLRNOTA
FROM TGFCAB
```

---

## 📊 Serviços Disponíveis

| Serviço | Descrição | Uso |
|---------|-----------|-----|
| `DbExplorerSP.executeQuery` | Executa SQL SELECT | ✅ Principal |
| `CRUDServiceProvider.loadRecords` | Busca registros CRUD | Alternativo |
| `CRUDServiceProvider.saveRecord` | Salva registro | Updates |

---

## 🔗 Variáveis de Ambiente

```bash
# Arquivo: mcp_sankhya/.env

SANKHYA_CLIENT_ID=seu_client_id_aqui
SANKHYA_CLIENT_SECRET=seu_client_secret_aqui
SANKHYA_X_TOKEN=seu_x_token_aqui
```

---

## 📝 Queries de Exemplo

### Vendas dos últimos 30 dias
```sql
SELECT 
    c.NUNOTA, c.NUMNOTA, c.DTNEG,
    c.CODPARC, p.NOMEPARC AS CLIENTE,
    c.VLRNOTA
FROM TGFCAB c
JOIN TGFPAR p ON p.CODPARC = c.CODPARC
WHERE c.TIPMOV = 'V'
  AND c.DTNEG >= TRUNC(SYSDATE) - 30
  AND ROWNUM <= 1000
ORDER BY c.DTNEG DESC
```

### Estoque atual
```sql
SELECT 
    e.CODPROD, p.DESCRPROD,
    e.ESTOQUE, e.RESERVADO,
    (e.ESTOQUE - NVL(e.RESERVADO, 0)) AS DISPONIVEL
FROM TGFEST e
JOIN TGFPRO p ON p.CODPROD = e.CODPROD
WHERE e.CODEMP = 6 AND e.ESTOQUE > 0
ORDER BY e.ESTOQUE DESC
```

### Pedidos de compra pendentes
```sql
SELECT 
    c.NUNOTA, c.NUMNOTA, c.DTNEG,
    p.NOMEPARC AS FORNECEDOR,
    c.VLRNOTA, c.PENDENTE
FROM TGFCAB c
JOIN TGFPAR p ON p.CODPARC = c.CODPARC
WHERE c.TIPMOV = 'C' AND c.PENDENTE = 'S'
  AND ROWNUM <= 500
ORDER BY c.DTNEG DESC
```

---

## 🔍 Descobrir Estrutura de Tabelas

### Listar colunas de uma tabela
```sql
SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE
FROM ALL_TAB_COLUMNS
WHERE TABLE_NAME = 'TGFCAB'
ORDER BY COLUMN_ID
```

### Listar tabelas por prefixo
```sql
SELECT TABLE_NAME
FROM ALL_TABLES
WHERE TABLE_NAME LIKE 'TGF%'
ORDER BY TABLE_NAME
```

---

## 📚 Referências

- [Developer Sankhya](https://developer.sankhya.com.br)
- [Community Sankhya](https://community.sankhya.com.br)

---

*Última atualização: 2026-02-05*
