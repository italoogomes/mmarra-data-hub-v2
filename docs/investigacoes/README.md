# 📚 Investigações - MMarra Data Hub

**Atualizado:** 2026-02-05
**Total de scripts:** 25

> Esta pasta documenta todas as investigações realizadas no Sankhya ERP.
> A IA deve consultar aqui para aprender com descobertas anteriores.

---

## 📊 Estatísticas Globais

### Pedidos/Notas Investigados (NUNOTA)

Total: **9** pedidos únicos já analisados.

| NUNOTA | Contexto |
|--------|----------|
| 1167528 | Investigado em scripts anteriores |
| 1169047 | Investigado em scripts anteriores |
| 1183490 | Investigado em scripts anteriores |
| 1191930 | Investigado em scripts anteriores |
| 1191931 | Investigado em scripts anteriores |
| 1192177 | Investigado em scripts anteriores |
| 1192208 | Investigado em scripts anteriores |
| 1192265 | Investigado em scripts anteriores |
| 1193546 | Investigado em scripts anteriores |

### Produtos Investigados (CODPROD)

Total: **2** produtos analisados.

| CODPROD | Contexto |
|---------|----------|
| 101357 | Investigado em scripts anteriores |
| 406700 | Investigado em scripts anteriores |

---

## 📊 Tabelas Mais Utilizadas nas Investigações

| Tabela | Frequência | Módulo |
|--------|------------|--------|
| TGFCAB | 47x | Comercial |
| TGWEMPE | 38x | WMS |
| TGFITC | 23x | Cotação |
| TGFPAR | 21x | Parceiros |
| TGFPRO | 19x | Produtos |
| TGFITE | 18x | Comercial |
| TGFCOT | 15x | Cotação |
| TGWREC | 10x | WMS |
| TGFTOP | 9x | Operações |
| TSIUSU | 8x | Sistema |
| TGFTAB | 6x | - |
| TGFEXC | 5x | - |
| TGFNTA | 4x | - |
| AD_RECEBCANH | 3x | Customizado |
| ENTRE | 3x | - |
| COM | 2x | - |
| TDDDOM | 2x | - |
| TDDCAM | 2x | - |
| TGWSOL | 2x | - |
| TDDTAB | 2x | - |
| TSIINS | 2x | - |
| TGFITC_DLT | 2x | - |
| TSIEMP | 1x | - |
| CORRETO | 1x | - |
| SOLUCAO | 1x | - |

---

## 📁 Lista de Investigações

| Script | Objetivo |
|--------|----------|
| **Canhoto** | Investiga tabelas relacionadas a Recebimento de Canhoto |
| **Caso Rima** | CASO RIMA - Investigacao completa |
| **Contexto Status** | Investiga o contexto de uso dos status para entender significado |
| **Cotacao 131** | Investigar COTAÇÃO 131 - Qual pedido de compra está vinculado? |
| **Cotacao Pedido** | Investiga como a cotacao esta vinculada ao pedido de venda 1191930 |
| **Cotacao Pedido V2** | Investiga como a cotacao esta vinculada ao pedido de venda 1191930 - V2 |
| **Cotacao Pedido V3** | Investiga a desconexao entre cotacao e empenho do pedido 1191930 - V3 |
| **Divergencia Pedido** | Investigar divergência entre NUM_UNICO no CSV (1167205) vs tela (1167528) |
| **Empenho Parcial** | Investigar empenho parcial - Pedido 1181756 |
| **Empenho Travado** | Investigar empenho travado - pedido 1183490 |
| **Historico Cotacao** | Investiga se existe historico/log de cotacoes no Sankhya |
| **Pedido** | Investiga um pedido especifico para verificar status de faturamento |
| **Pedido 1192177** | Investigação do pedido 1192177 - Por que não aparece cotação? |
| **Pedido Simples** | Investigação simples do pedido 1192177 |
| **Query Precos** | Investiga as tabelas da query de precos/excecoes |
| **Query Precos2** | Investiga as tabelas da query de precos/excecoes - v2 |
| **Situacao Wms** | Investiga códigos de situação do WMS e cruza com canhotos |
| **Status Cotacao** | Investiga os status de cotacao no Sankhya |
| **Tabelas Auxiliares** | Investiga tabelas auxiliares de cotacao: TGFITC_COT, TGFITC_DLT, AD_COTACOESDEIT |
| **Tela Empenho** | Investigar a estrutura da tela Empenho de Produtos |
| **View Empenho** | Investigar Views de empenho e a estrutura da query |
| **Vinculo Cotacao Compra** | Investigar como vincular cotação ao pedido de compra no Sankhya |
| **Wms Entrada** | Investiga tabelas WMS para status de entrada, conferência e armazenagem |
| **Wms Pedido** | Investiga o status WMS detalhado de um pedido específico |
| **Xml Compra** | Investiga campos de XML/NFe na TGFCAB para compras vinculadas ao empenho |

---

## 🎯 Como a IA Deve Usar Este Conhecimento

1. **Antes de investigar um pedido**: Verificar se NUNOTA já foi analisado
2. **Ao explorar tabelas**: Consultar quais já foram mapeadas
3. **Ao encontrar problemas**: Verificar se já existe bug documentado em 
4. **Ao criar queries**: Usar as tabelas mais frequentes como referência

---

## 📝 Padrão para Novas Investigações

Ao fazer uma nova investigação, documentar em arquivo separado:



Conteúdo mínimo:
- Objetivo
- Pedidos/Produtos analisados
- Tabelas consultadas
- Queries que funcionaram
- Descobertas
- Conclusão

---

## 🔗 Documentação Relacionada

- [Mapeamento de Tabelas](../de-para/sankhya/)
- [Status WMS](../de-para/sankhya/wms.md)
- [Bugs Conhecidos](../bugs/)
- [API Sankhya](../api/sankhya.md)

---

*Gerado automaticamente. Revisar e completar manualmente.*
