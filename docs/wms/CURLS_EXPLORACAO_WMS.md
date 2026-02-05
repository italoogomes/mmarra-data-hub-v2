# 🔍 cURLs de Exploração - Estoque e WMS

**Data**: 2026-01-30
**Como usar**: Copie cada cURL e execute no Postman

---

## ⚙️ Configuração Inicial

### 1. Obter Token (Se Expirou)

```bash
curl --request POST \
  --url https://api.sankhya.com.br/gateway/v1/authenticate \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --header 'X-Token: dca9f07d-bf0f-426c-b537-0e5b0ff1123d' \
  --data client_id=09ef3473-cb85-41d4-b6d4-473c15d39292 \
  --data client_secret=7phfkche8hWHpWYBNWbEgf4xY4mPixp0 \
  --data grant_type=client_credentials
```

**Guarde o `access_token` retornado!**

---

## 📊 PARTE 1: Explorar Estrutura (Metadados)

### Query 1: Listar Tabelas WMS ⭐ PRIORIDADE 1

**Endpoint**: POST `/query` ou `/mge/service.sbr?serviceName=CRUDServiceProvider.loadRecords`

```bash
curl --request POST \
  --url 'https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=CRUDServiceProvider.loadRecords&outputType=json' \
  --header 'Authorization: Bearer SEU_ACCESS_TOKEN_AQUI' \
  --header 'Content-Type: application/json' \
  --data '{
  "serviceName": "DbExplorerSP.getObjects",
  "requestBody": {
    "objects": {
      "type": "TABLE",
      "filter": "TGW%"
    }
  }
}'
```

**AJUSTAR**: Dependendo da versão da API, pode ser necessário usar endpoint diferente.

**Alternativa - Query SQL Customizada:**
```bash
curl --request POST \
  --url 'https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery&outputType=json' \
  --header 'Authorization: Bearer SEU_ACCESS_TOKEN_AQUI' \
  --header 'Content-Type: application/json' \
  --data '{
  "serviceName": "DbExplorerSP.executeQuery",
  "requestBody": {
    "sql": "SELECT TABLE_NAME, NUM_ROWS FROM ALL_TABLES WHERE TABLE_NAME LIKE '\''TGW%'\'' OR TABLE_NAME LIKE '\''TCS%'\'' OR TABLE_NAME LIKE '\''%WMS%'\'' ORDER BY TABLE_NAME"
  }
}'
```

---

### Query 2: Estrutura de TGFEST

```bash
curl --request POST \
  --url 'https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery&outputType=json' \
  --header 'Authorization: Bearer SEU_ACCESS_TOKEN_AQUI' \
  --header 'Content-Type: application/json' \
  --data '{
  "serviceName": "DbExplorerSP.executeQuery",
  "requestBody": {
    "sql": "SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE FROM ALL_TAB_COLUMNS WHERE TABLE_NAME = '\''TGFEST'\'' ORDER BY COLUMN_ID"
  }
}'
```

---

### Query 3: Estrutura de TGFRES

```bash
curl --request POST \
  --url 'https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery&outputType=json' \
  --header 'Authorization: Bearer SEU_ACCESS_TOKEN_AQUI' \
  --header 'Content-Type: application/json' \
  --data '{
  "serviceName": "DbExplorerSP.executeQuery",
  "requestBody": {
    "sql": "SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE FROM ALL_TAB_COLUMNS WHERE TABLE_NAME = '\''TGFRES'\'' ORDER BY COLUMN_ID"
  }
}'
```

---

## 📦 PARTE 2: Consultar Dados de Estoque

### Query 4: Estoque do Produto 137216 (TGFEST)

```bash
curl --request POST \
  --url 'https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery&outputType=json' \
  --header 'Authorization: Bearer SEU_ACCESS_TOKEN_AQUI' \
  --header 'Content-Type: application/json' \
  --data '{
  "serviceName": "DbExplorerSP.executeQuery",
  "requestBody": {
    "sql": "SELECT CODPROD, CODEMP, CODLOCAL, ESTOQUE, RESERVADO, (ESTOQUE - NVL(RESERVADO, 0)) AS DISPONIVEL FROM TGFEST WHERE CODPROD = 137216"
  }
}'
```

---

### Query 5: Reservas do Produto 137216 (TGFRES)

```bash
curl --request POST \
  --url 'https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery&outputType=json' \
  --header 'Authorization: Bearer SEU_ACCESS_TOKEN_AQUI' \
  --header 'Content-Type: application/json' \
  --data '{
  "serviceName": "DbExplorerSP.executeQuery",
  "requestBody": {
    "sql": "SELECT * FROM TGFRES WHERE CODPROD = 137216 AND ROWNUM <= 10"
  }
}'
```

---

### Query 6: Buscar Tabelas com "SALDO" ou "ENDEREÇO"

```bash
curl --request POST \
  --url 'https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery&outputType=json' \
  --header 'Authorization: Bearer SEU_ACCESS_TOKEN_AQUI' \
  --header 'Content-Type: application/json' \
  --data '{
  "serviceName": "DbExplorerSP.executeQuery",
  "requestBody": {
    "sql": "SELECT DISTINCT TABLE_NAME, COLUMN_NAME FROM ALL_TAB_COLUMNS WHERE (COLUMN_NAME LIKE '\''%SALDO%'\'' OR COLUMN_NAME LIKE '\''%END%'\'') AND TABLE_NAME LIKE '\''TG%'\'' ORDER BY TABLE_NAME"
  }
}'
```

---

### Query 7: Verificar Quais Tabelas Existem

```bash
curl --request POST \
  --url 'https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery&outputType=json' \
  --header 'Authorization: Bearer SEU_ACCESS_TOKEN_AQUI' \
  --header 'Content-Type: application/json' \
  --data '{
  "serviceName": "DbExplorerSP.executeQuery",
  "requestBody": {
    "sql": "SELECT '\''TGFEST'\'' AS TABELA, CASE WHEN COUNT(*) > 0 THEN '\''Existe'\'' ELSE '\''Não existe'\'' END AS STATUS FROM ALL_TABLES WHERE TABLE_NAME = '\''TGFEST'\'' UNION ALL SELECT '\''TGFRES'\'', CASE WHEN COUNT(*) > 0 THEN '\''Existe'\'' ELSE '\''Não existe'\'' END FROM ALL_TABLES WHERE TABLE_NAME = '\''TGFRES'\'' UNION ALL SELECT '\''TGFSAL'\'', CASE WHEN COUNT(*) > 0 THEN '\''Existe'\'' ELSE '\''Não existe'\'' END FROM ALL_TABLES WHERE TABLE_NAME = '\''TGFSAL'\''"
  }
}'
```

---

## ⚠️ IMPORTANTE: API Sankhya pode não permitir queries SQL diretas

Se as queries acima **NÃO funcionarem**, a API Sankhya pode bloquear acesso direto ao banco.

### Alternativa: Endpoints Padrão de Entidades

**Consultar Estoque via Endpoint:**
```bash
curl --request GET \
  --url 'https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=CRUDServiceProvider.loadRecords&outputType=json' \
  --header 'Authorization: Bearer SEU_ACCESS_TOKEN_AQUI' \
  --header 'Content-Type: application/json' \
  --data '{
  "serviceName": "CRUDServiceProvider.loadRecords",
  "requestBody": {
    "dataSet": {
      "rootEntity": "Estoque",
      "includePresentationFields": "S",
      "dataRow": {
        "localFields": {
          "CODPROD": { "$": 137216 }
        }
      }
    }
  }
}'
```

---

## 🔧 Como Testar no Postman

### Passo 1: Importar cURL
1. Abra Postman
2. Clique em "Import"
3. Cole o cURL completo
4. Clique em "Import"

### Passo 2: Substituir Token
- Substitua `SEU_ACCESS_TOKEN_AQUI` pelo token obtido na autenticação

### Passo 3: Executar
- Clique em "Send"
- Copie o resultado JSON

### Passo 4: Me Enviar
```
Query X executada:

{
  "resultado": [...],
  "status": "sucesso"
}
```

---

## 📋 Ordem Sugerida de Execução

1. ✅ **Autenticação** (obter token)
2. ⭐ **Query 1** (listar tabelas WMS) - PRIMEIRO!
3. 📊 **Query 4** (estoque produto 137216)
4. 📊 **Query 2** (estrutura TGFEST)
5. 📊 **Query 3** (estrutura TGFRES)
6. 📊 **Query 5** (reservas produto 137216)
7. 🔍 **Query 6** (buscar tabelas com SALDO/END)

---

## ❓ Se der erro "serviceName não encontrado"

Tente esta estrutura alternativa (API mais antiga):

```bash
curl --request POST \
  --url 'https://api.sankhya.com.br/gateway/v1/mge/service.sbr' \
  --header 'Authorization: Bearer SEU_ACCESS_TOKEN_AQUI' \
  --header 'Content-Type: application/json' \
  --data '{
  "serviceName": "MobileDisponibilidadeSP.consultarDisponibilidade",
  "requestBody": {
    "produtos": {
      "produto": [
        {
          "CODPROD": 137216
        }
      ]
    }
  }
}'
```

---

## 💡 Dica: Ver Documentação da API

Se as queries SQL não funcionarem, consulte:
- https://developer.sankhya.com.br/reference
- Procure por "service" ou "query" na documentação
- Veja exemplos de como consultar entidades

---

## 📞 Como Me Enviar os Resultados

**Formato:**
```
=== Query X: [NOME] ===
Status: 200 OK / 400 Error

Response:
{
  "dados": [...]
}

Observações:
- [algo que notou]
```

Ou simplesmente cole o JSON retornado! 👍

---

**Última atualização**: 2026-01-30
