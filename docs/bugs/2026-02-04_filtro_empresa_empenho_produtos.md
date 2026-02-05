# Bug Report - Filtro de Empresa na Tela Empenho de Produtos

**Data:** 2026-02-04
**Tela:** Empenho de Produtos
**Severidade:** Media
**Status:** Aberto

---

## Resumo

O filtro de **Empresa** na tela "Empenho de Produtos" funciona corretamente para o grid **"Itens de compra"**, mas **NAO funciona** para o grid **"Itens de pedido de venda"**.

---

## Comportamento Esperado

Ao selecionar uma empresa no filtro lateral (ex: Empresa = 1), ambos os grids devem mostrar apenas registros daquela empresa:
- Grid "Itens de compra" - Filtrado por empresa ✅
- Grid "Itens de pedido de venda" - Filtrado por empresa ✅

## Comportamento Atual

- Grid "Itens de compra" - Filtrado por empresa ✅ **FUNCIONA**
- Grid "Itens de pedido de venda" - **NAO FILTRA** por empresa ❌

---

## Evidencia Tecnica

### Query de Compras (FUNCIONA)

Servico: `EmpenhoProdutoSP.buscaPossiveisProdutosParaEmpenho`

```sql
SELECT ...
FROM TGFITE ITE
INNER JOIN TGFCAB CAB1 ON ITE.NUNOTA = CAB1.NUNOTA
...
WHERE ...
  AND CAB1.CODEMP = ?   -- <<< FILTRO DE EMPRESA PRESENTE
```

**Parametro 13 = 1** (codigo da empresa)

### Query de Vendas (NAO FUNCIONA)

Servico: `EmpenhoProdutoSP.buscaPossiveisEmpenhoProdVenda`

```sql
SELECT ...
FROM TGFITE ITE
INNER JOIN TGFCAB CAB ON ITE.NUNOTA = CAB.NUNOTA
...
WHERE ...
  -- <<< FILTRO CODEMP AUSENTE!
```

**Observacao:** A query de vendas NAO possui clausula `AND CAB.CODEMP = ?`

---

## Causa Raiz

A tabela `TGWEMPE` (empenhos) **nao possui** o campo `CODEMP` diretamente.

Para filtrar por empresa, e necessario fazer JOIN com `TGFCAB`:

```sql
TGWEMPE EMPE
INNER JOIN TGFCAB CAB ON EMPE.NUNOTA = CAB.NUNOTA
WHERE CAB.CODEMP = ?
```

A query de **compras** faz esse JOIN corretamente.
A query de **vendas** **NAO FAZ** esse JOIN.

---

## Estrutura das Tabelas Envolvidas

### TGWEMPE (Empenhos)
| Coluna | Tipo | Descricao |
|--------|------|-----------|
| NUNOTA | NUMBER | Numero unico da nota (PK) |
| CODPROD | NUMBER | Codigo do produto (PK) |
| CONTROLE | VARCHAR2 | Controle (PK) |
| NUNOTAPEDVEN | NUMBER | Numero do pedido de venda |
| QTDEMPENHO | FLOAT | Quantidade empenhada |
| **CODEMP** | **NAO EXISTE** | - |

### TGFCAB (Cabecalho Nota)
| Coluna | Tipo | Descricao |
|--------|------|-----------|
| NUNOTA | NUMBER | Numero unico (PK) |
| **CODEMP** | NUMBER | Codigo da empresa |

---

## Correcao Sugerida

Adicionar o filtro `CAB.CODEMP = ?` na query `buscaPossiveisEmpenhoProdVenda`, similar ao que ja existe em `buscaPossiveisProdutosParaEmpenho`.

**Antes (query de vendas):**
```sql
SELECT ...
FROM TGFITE ITE
INNER JOIN TGFCAB CAB ON ITE.NUNOTA = CAB.NUNOTA
WHERE ...
```

**Depois (correcao):**
```sql
SELECT ...
FROM TGFITE ITE
INNER JOIN TGFCAB CAB ON ITE.NUNOTA = CAB.NUNOTA
WHERE ...
  AND CAB.CODEMP = ?   -- <<< ADICIONAR ESTE FILTRO
```

---

## Impacto no Cliente

1. **Performance:** Sem o filtro, a query retorna registros de TODAS as empresas, causando lentidao
2. **Usabilidade:** Usuario precisa criar filtro personalizado como workaround
3. **Consistencia:** Grid de compras filtra corretamente, grid de vendas nao

---

## Workaround Temporario

Ate a correcao ser aplicada, o usuario pode criar um filtro personalizado na tela:

1. Clicar em "Filtro venda"
2. Adicionar condicao: `Item Nota/Pedido >> Empresa >> Cod. Empresa = 1`
3. Salvar o filtro

**Limitacao:** O filtro e fixo (ex: sempre empresa 1), nao dinamico.

---

## Anexos

- Log do Monitor de Consultas mostrando as queries
- Screenshots da tela com o problema
- Scripts de investigacao (se necessario)

---

## Informacoes do Ambiente

- **Versao Sankhya:** (informar versao)
- **Modulo:** WMS
- **Tela:** br.com.sankhya.wms.view.EmpenhoProduto
- **Base de Dados:** Oracle

---

**Reportado por:** MMarra Distribuidora
**Contato:** (informar email/telefone)
