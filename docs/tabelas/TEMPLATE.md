# NOME_TABELA - Descrição Curta

**Módulo**: Compras / Vendas / Estoque / Financeiro / Cadastro
**Tipo**: Transacional / Cadastro / View
**Criado em**: YYYY-MM-DD
**Última atualização**: YYYY-MM-DD

---

## 📋 Descrição

Breve descrição do propósito desta tabela no sistema.

**Exemplo de uso:**
- Caso de uso 1
- Caso de uso 2

---

## 📊 Estrutura (Colunas)

| Campo | Tipo | Nulo | PK/FK | Descrição | Exemplo |
|-------|------|------|-------|-----------|---------|
| CAMPO1 | NUMBER(10) | NOT NULL | PK | Descrição do campo | 12345 |
| CAMPO2 | VARCHAR2(60) | NULL | FK → TABELA | Descrição | "Valor exemplo" |
| CAMPO3 | DATE | NOT NULL | - | Data de criação | 2026-01-27 |
| CAMPO4 | NUMBER(15,2) | NULL | - | Valor monetário | 1500.50 |

### Campos Obrigatórios
- `CAMPO1` - Por que é obrigatório
- `CAMPO3` - Por que é obrigatório

### Campos Opcionais
- `CAMPO2` - Quando usar
- `CAMPO4` - Quando usar

---

## 🔗 Relacionamentos

### Tabelas Pai (Foreign Keys)

| FK Local | → | Tabela Pai | Campo | Descrição |
|----------|---|------------|-------|-----------|
| `CAMPO2` | → | `TABELA_PAI` | `ID` | Relacionamento com... |

### Tabelas Filhas (Reversed)

| Tabela Filha | Campo | ← | FK Local | Descrição |
|--------------|-------|---|----------|-----------|
| `TABELA_FILHA` | `CAMPO_FK` | ← | `CAMPO1` | Itens deste registro |

### Diagrama de Relacionamento

```
TABELA_PAI
    ↓
ESTA_TABELA
    ↓
TABELA_FILHA
```

---

## 🔍 Índices

| Nome do Índice | Colunas | Tipo | Uso |
|----------------|---------|------|-----|
| PK_TABELA | CAMPO1 | PRIMARY KEY | Chave primária |
| IDX_TABELA_01 | CAMPO2, CAMPO3 | NON-UNIQUE | Busca por... |

---

## 📋 Queries Comuns

### 1. Listar registros ativos
```sql
SELECT *
FROM NOME_TABELA
WHERE ATIVO = 'S'
ORDER BY CAMPO1 DESC;
```

### 2. Join com tabelas relacionadas
```sql
SELECT
    t.*,
    p.CAMPO AS CAMPO_PAI
FROM NOME_TABELA t
INNER JOIN TABELA_PAI p ON t.CAMPO2 = p.ID
WHERE t.DATA >= SYSDATE - 30
ORDER BY t.CAMPO1;
```

### 3. Agregação por período
```sql
SELECT
    TRUNC(CAMPO3, 'MM') AS MES,
    COUNT(*) AS QTD,
    SUM(CAMPO4) AS TOTAL
FROM NOME_TABELA
WHERE CAMPO3 >= ADD_MONTHS(SYSDATE, -12)
GROUP BY TRUNC(CAMPO3, 'MM')
ORDER BY MES DESC;
```

### 4. Filtrar por status/situação
```sql
SELECT *
FROM NOME_TABELA
WHERE STATUS IN ('A', 'P', 'C')
  AND CAMPO3 BETWEEN :data_inicio AND :data_fim;
```

---

## 🔧 Campos Customizados (AD_*)

| Campo | Tipo | Descrição | Uso no Negócio |
|-------|------|-----------|----------------|
| AD_CAMPO1 | VARCHAR2(100) | Descrição | Para que serve |
| AD_CAMPO2 | NUMBER | Descrição | Para que serve |

### Como descobrir campos AD_*
```sql
SELECT COLUMN_NAME, DATA_TYPE
FROM ALL_TAB_COLUMNS
WHERE TABLE_NAME = 'NOME_TABELA'
  AND COLUMN_NAME LIKE 'AD_%'
ORDER BY COLUMN_NAME;
```

---

## 💡 Regras de Negócio

### Regra 1: Título da Regra
**Descrição**: Explicação detalhada da regra

**Exemplo:**
```sql
-- Se CAMPO1 > 1000, então CAMPO2 deve ser preenchido
WHERE (CAMPO1 <= 1000 OR CAMPO2 IS NOT NULL)
```

### Regra 2: Validação de Status
**Descrição**: Estados válidos e transições permitidas

**Estados:**
- A = Ativo
- P = Pendente
- C = Cancelado

**Transições:**
```
P → A (aprovação)
P → C (cancelamento)
A → C (cancelamento)
```

---

## 🎯 Para o LLM Saber

### Esta tabela é usada para:
- [ ] Listar registros por período
- [ ] Calcular totais/agregações
- [ ] Filtrar por status/situação
- [ ] Join com outras tabelas
- [ ] Auditoria (criado/modificado)

### Campos-chave para filtros:
- `CAMPO3` (DATA) - Filtrar por período
- `STATUS` - Filtrar por situação
- `CAMPO2` - Filtrar por relacionamento

### Campos-chave para agregação:
- `CAMPO4` (VALOR) - Somar valores
- `CAMPO1` (ID) - Contar registros
- `CAMPO3` (DATA) - Agrupar por período

### Exemplos de perguntas que a LLM pode responder:

**1. Quantos registros há nesta tabela?**
```sql
SELECT COUNT(*) FROM NOME_TABELA;
```

**2. Qual o total por período?**
```sql
SELECT
    TRUNC(CAMPO3, 'MM') AS MES,
    SUM(CAMPO4) AS TOTAL
FROM NOME_TABELA
GROUP BY TRUNC(CAMPO3, 'MM');
```

**3. Quais registros estão pendentes?**
```sql
SELECT * FROM NOME_TABELA WHERE STATUS = 'P';
```

**4. Top 10 por valor**
```sql
SELECT * FROM NOME_TABELA
ORDER BY CAMPO4 DESC
FETCH FIRST 10 ROWS ONLY;
```

---

## 📊 Estatísticas

**Última análise**: YYYY-MM-DD

| Métrica | Valor | Observação |
|---------|-------|------------|
| Total de registros | 1.234.567 | - |
| Registros ativos | 950.000 | 77% |
| Tamanho médio linha | 250 bytes | - |
| Espaço usado | 300 MB | - |
| Crescimento mensal | 50.000 | Aproximado |

### Como atualizar estatísticas:
```sql
EXEC DBMS_STATS.GATHER_TABLE_STATS('SANKHYA', 'NOME_TABELA');
```

---

## 🔐 Segurança e RLS

### Filtros de Row Level Security

**Por empresa/filial:**
```sql
WHERE CODEMP IN (SELECT CODEMP FROM USUARIO_FILIAIS WHERE CODUSU = :usuario)
```

**Por comprador:**
```sql
WHERE CODCOMPRADOR = :cod_comprador
```

**Por região:**
```sql
WHERE CODEMP IN (SELECT CODEMP FROM FILIAIS_REGIAO WHERE CODREGIAO = :regiao)
```

---

## 📝 Notas e Observações

### Importante:
- Nota importante 1
- Nota importante 2

### Limitações:
- Limitação conhecida 1
- Limitação conhecida 2

### Dicas:
- Dica de uso 1
- Dica de uso 2

---

## 🔄 Histórico de Alterações

| Data | Alteração | Responsável |
|------|-----------|-------------|
| 2026-01-30 | Criação inicial | Ítalo |
| YYYY-MM-DD | Adicionado campo X | Nome |

---

## 📚 Referências

- [Documentação Sankhya](link)
- [Postman Collection](../../postman/)
- [Queries relacionadas](../QUERIES_EXPLORACAO.sql)

---

**Template versão:** 1.0
**Criado em:** 2026-01-30
