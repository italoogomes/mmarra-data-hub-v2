# ⚠️ Erros Comuns - MMarra Data Hub

**Atualizado:** 2026-02-05

> Esta página documenta erros comuns e suas soluções.
> A IA deve consultar aqui ao encontrar problemas.

---

## 🔴 Erros de API Sankhya

### HTTP 401 - Não Autorizado

**Sintoma:**
```json
{"error": "unauthorized", "status": 401}
```

**Causas e Soluções:**

| Causa | Solução |
|-------|---------|
| Token expirado | Reautenticar (tokens duram 1 hora) |
| X-Token inválido | Verificar `SANKHYA_X_TOKEN` no `.env` |
| Credenciais erradas | Verificar `CLIENT_ID` e `CLIENT_SECRET` |

**Código de verificação:**
```python
# Testar autenticação
token = autenticar()
print(f"Token obtido: {token[:20]}...")
```

---

### HTTP 500 - Erro Interno

**Sintoma:**
```json
{"status": "0", "statusMessage": "ORA-xxxxx: ..."}
```

**Causas comuns:**

| Erro Oracle | Causa | Solução |
|-------------|-------|---------|
| ORA-00942 | Tabela não existe | Verificar nome da tabela |
| ORA-00904 | Coluna não existe | Verificar nome da coluna |
| ORA-01722 | Tipo inválido | Verificar conversão de tipos |
| ORA-00936 | Expressão faltando | Verificar sintaxe SQL |
| ORA-01555 | Snapshot too old | Query muito longa, usar ROWNUM |

---

### Timeout

**Sintoma:**
```
requests.exceptions.ReadTimeout: Read timed out
```

**Soluções:**
1. Adicionar `ROWNUM <= 1000` na query
2. Aumentar timeout para 60 segundos
3. Adicionar filtros (CODEMP, DTNEG)
4. Dividir em queries menores

---

## 🟡 Erros de Dados

### Campos NULL inesperados

**Problema:** Campos retornando NULL quando deveria ter valor.

**Solução:** Usar NVL para valores default:
```sql
SELECT 
    NVL(CODVEND, 0) AS CODVEND,
    NVL(VLRNOTA, 0) AS VLRNOTA
FROM TGFCAB
```

---

### Encoding incorreto

**Problema:** Caracteres estranhos em nomes.

**Solução:** Garantir UTF-8:
```python
conteudo = response.text.encode('latin1').decode('utf-8')
```

---

### Datas em formato errado

**Problema:** Datas Oracle vs Python.

**Solução:**
```python
from datetime import datetime

# Oracle para Python
data_oracle = "2026-02-05 10:30:00"
data_python = datetime.strptime(data_oracle, "%Y-%m-%d %H:%M:%S")
```

---

## 🟢 Erros de Configuração

### Arquivo .env não encontrado

**Sintoma:**
```
FileNotFoundError: .env
```

**Solução:**
```bash
cp .env.example .env
# Editar .env com credenciais
```

---

### Módulo não encontrado

**Sintoma:**
```
ModuleNotFoundError: No module named 'xxx'
```

**Solução:**
```bash
pip install -r requirements.txt
```

---

## 📊 Erros Específicos do Negócio

### Empenho não encontrado

**Contexto:** Tabela TGWEMPE não retorna dados.

**Verificar:**
1. O pedido existe em TGFCAB?
2. O pedido tem itens em TGFITE?
3. Foi gerado empenho (processo WMS)?

**Query de diagnóstico:**
```sql
SELECT 
    'TGFCAB' AS TABELA, COUNT(*) AS QTD
FROM TGFCAB WHERE NUNOTA = :nunota
UNION ALL
SELECT 'TGFITE', COUNT(*) FROM TGFITE WHERE NUNOTA = :nunota
UNION ALL
SELECT 'TGWEMPE', COUNT(*) FROM TGWEMPE WHERE NUNOTA = :nunota
```

---

### Status WMS inconsistente

**Contexto:** Status na tela diferente do banco.

**Explicação:** O campo SITUACAOWMS é calculado, não físico.

**Solução:** Consultar view VGWRECSITCAB:
```sql
SELECT NUNOTA, COD_SITUACAO 
FROM VGWRECSITCAB 
WHERE NUNOTA = :nunota
```

Ver detalhes em `docs/de-para/sankhya/wms.md`.

---

## 🔧 Como Reportar Novos Erros

1. Criar arquivo em `docs/bugs/YYYY-MM-DD_descricao.md`
2. Incluir:
   - Sintoma
   - Query/código que causou
   - Mensagem de erro completa
   - Solução encontrada (se houver)

---

*Última atualização: 2026-02-05*
