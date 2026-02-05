# 📊 Relatório HTML de Divergências - Guia de Uso

**Versão:** 2.0
**Data:** 2026-01-30
**Status:** ✅ Query corrigida (sem duplicatas)

---

## 🎯 O que é isso?

Um relatório HTML interativo e bonito para visualizar divergências de estoque entre WMS e TGFEST, sem precisar do Excel!

---

## 🚀 Como Usar - Método Rápido

### Opção 1: Visualizar com Dados de Exemplo

1. Abra o arquivo **`relatorio_divergencias.html`** no navegador
2. Você verá 2 produtos de exemplo (263340 e 137216)
3. É só para demonstrar como fica o layout

---

### Opção 2: Atualizar com Dados Reais (Recomendado)

#### Passo 1: Executar a Query no Postman

1. Abra o arquivo **`curl_divergencias_corrigida.txt`**
2. Copie o cURL completo
3. Cole no Postman
4. Substitua `{SEU_TOKEN}` pelo seu Bearer token do Sankhya
5. Execute a requisição

#### Passo 2: Salvar o Resultado

1. Copie o **JSON completo** da resposta do Postman
2. Salve em um arquivo chamado **`resultado_query.json`** nesta pasta

#### Passo 3: Converter para HTML

**Opção A - Usando Python (Automático):**
```bash
python converter_json_para_html.py
```

O script vai:
- ✅ Ler o `resultado_query.json`
- ✅ Converter os dados
- ✅ Gerar `relatorio_divergencias_atualizado.html`
- ✅ Mostrar estatísticas (total de produtos, divergências, etc.)

**Opção B - Manual (Se não tiver Python):**
1. Abra `relatorio_divergencias.html` em um editor de texto
2. Localize a linha `let tableData = [`
3. Substitua o array pelos seus dados (seguindo o formato do exemplo)
4. Salve e abra no navegador

#### Passo 4: Visualizar

1. Abra o arquivo **`relatorio_divergencias_atualizado.html`** no navegador
2. Pronto! 🎉

---

## ✨ Funcionalidades do Relatório

### 📊 Dashboard Interativo
- **Total de Produtos** com divergência
- **Total de Notas** pendentes
- **Maior Divergência** individual
- **Divergência Total** acumulada

### 🔍 Busca em Tempo Real
- Digite qualquer coisa na caixa de busca
- Filtra produtos, descrição, notas, TOPs, etc.
- Resultados instantâneos

### 🔄 Ordenação de Colunas
- Clique em qualquer cabeçalho para ordenar
- Clique novamente para inverter a ordem
- Indicadores visuais (↑ ↓)

### 📥 Exportar Dados
- Botão "Exportar CSV" gera arquivo .csv
- Mantém filtros aplicados na busca
- Nome automático com data

### 🖨️ Impressão
- Botão "Imprimir" para gerar PDF
- Layout otimizado para papel
- Mantém cores e formatação

### 🎨 Visual Profissional
- ✅ Design moderno com gradientes
- ✅ Cores indicativas (vermelho = alta divergência)
- ✅ Badges coloridos para status
- ✅ Hover effects e animações
- ✅ Responsivo (funciona em mobile)

---

## 📁 Arquivos Criados

| Arquivo | Descrição |
|---------|-----------|
| `relatorio_divergencias.html` | Relatório HTML interativo (com dados de exemplo) |
| `converter_json_para_html.py` | Script Python para automatizar conversão |
| `curl_divergencias_corrigida.txt` | cURL pronto para Postman com query corrigida |
| `query_divergencias_corrigida.sql` | Query SQL comentada e documentada |
| `README_RELATORIO.md` | Este arquivo (guia de uso) |

---

## 🎨 Capturas de Tela (Como Fica)

### Dashboard com KPIs
```
┌─────────────────────────────────────────────────────────────┐
│  Total de Produtos    Total de Notas    Maior Divergência  │
│        145                  287                5894         │
│  com divergência     itens pendentes        unidades       │
└─────────────────────────────────────────────────────────────┘
```

### Tabela Interativa
```
┌──────────────────────────────────────────────────────────────┐
│ Código │ Produto                    │ Divergência  │ Status │
├────────┼────────────────────────────┼──────────────┼────────┤
│ 263340 │ DIPOSITIVO INDICADOR...   │ 5894 🔴     │   P    │
│ 137216 │ PARAFUSO SEXTAVADO...      │   72 🟡     │   P    │
└──────────────────────────────────────────────────────────────┘
```

---

## 🐛 Problemas Comuns

### "Nenhum registro encontrado"
- ✅ Execute a query corrigida no Postman primeiro
- ✅ Verifique se salvou o JSON corretamente
- ✅ Confirme que o JSON tem a estrutura esperada

### Python não está instalado
- ✅ Baixe em: https://www.python.org/downloads/
- ✅ OU faça a atualização manual (Opção B)

### JSON inválido
- ✅ Copie o response completo do Postman
- ✅ Não copie apenas parte do JSON
- ✅ Mantenha toda a estrutura `{ "responseBody": {...} }`

---

## 📞 Próximos Passos

Após visualizar o relatório, você pode:

1. **Identificar produtos problemáticos**
   - Quais têm maior divergência?
   - Quais TOPs são mais afetadas?

2. **Investigar causas**
   - Por que notas estão PENDENTES?
   - Há job de sincronização travado?
   - Configuração de TOP incorreta?

3. **Tomar ação**
   - Corrigir configuração de TOPs
   - Processar notas pendentes
   - Acertar estoques manualmente (último caso)

---

## 📝 Observações Importantes

⚠️ **Sobre Duplicatas:**
- A query corrigida (`query_divergencias_corrigida.sql`) já elimina duplicatas
- Se ainda ver dados repetidos, verifique se está usando a query antiga

⚠️ **Sobre Performance:**
- Com muitos registros (>1000), a busca pode ficar lenta no navegador
- Considere filtrar por período na query SQL
- Ou exportar para CSV e analisar em partes

⚠️ **Sobre Atualização:**
- O HTML é estático (não se atualiza sozinho)
- Execute a query novamente quando precisar dados frescos
- Rode o script Python para atualizar o relatório

---

## 🎯 Checklist de Uso

- [ ] Executei a query corrigida no Postman
- [ ] Salvei o JSON em `resultado_query.json`
- [ ] Rodei o script Python (ou atualizei manualmente)
- [ ] Abri o HTML no navegador
- [ ] Dados carregaram corretamente
- [ ] Dashboard mostra estatísticas reais
- [ ] Busca está funcionando
- [ ] Ordenação funciona

---

**🎉 Pronto! Agora você tem um relatório profissional sem precisar de Excel!**

**Dúvidas?** Consulte a documentação completa em [docs/de-para/sankhya/estoque.md](docs/de-para/sankhya/estoque.md)
