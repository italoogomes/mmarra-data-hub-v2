# 🚀 Guia Rápido - Servidor MCP Sankhya

## ⚡ Instalação em 3 Passos

### 1. Instalar Dependências

Abra o terminal na pasta do projeto e execute:

```bash
cd mcp_sankhya
python -m pip install -r requirements.txt
```

**OU** use o instalador automático (Windows):

```bash
cd mcp_sankhya
install.bat
```

### 2. Configurar Claude Code

Abra o arquivo de configuração do Claude:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Se o arquivo não existir, crie-o com este conteúdo:

```json
{
  "mcpServers": {
    "sankhya": {
      "command": "python",
      "args": ["c:\\Users\\Ítalo Gomes\\Documents\\mmarra-data-hub\\mcp_sankhya\\server.py"],
      "env": {
        "SANKHYA_CLIENT_ID": "09ef3473-cb85-41d4-b6d4-473c15d39292",
        "SANKHYA_CLIENT_SECRET": "7phfkche8hWHpWYBNWbEgf4xY4mPixp0",
        "SANKHYA_X_TOKEN": "dca9f07d-bf0f-426c-b537-0e5b0ff1123d"
      }
    }
  }
}
```

⚠️ **IMPORTANTE**: Ajuste o caminho em `args` se sua pasta do projeto estiver em outro local!

### 3. Reiniciar Claude Code

Feche completamente o Claude Code e abra novamente.

---

## 💡 Exemplos de Uso

### 🔍 Executar Query de Divergências

```
Você: Claude, execute a query de divergências para a empresa 7

Claude: ✅ Query de Divergências V3 executada com sucesso!

📊 ESTATÍSTICAS:
   • Total de registros: 47
   • Produtos únicos: 23
   • Notas únicas: 15
   • Divergência total: 8.234 unidades
   • Maior divergência: 5.894 unidades

🔝 TOP 5 DIVERGÊNCIAS:
1. Produto 263340 (PRODUTO EXEMPLO A): 5.894 un
2. Produto 261302 (PRODUTO EXEMPLO B): 1.240 un
...

💾 JSON completo salvo em: resultado_query_divergencias.json
💡 Use 'gerar_relatorio_divergencias' para criar o HTML interativo!
```

### 📊 Analisar Produto Específico

```
Você: Claude, analise o produto 261302 da empresa 7

Claude: ✅ Análise Detalhada - Produto 261302 (Empresa 7)

📊 CAMADAS DE DISPONIBILIDADE:

1️⃣ ESTOQUE BRUTO (TGFEST):
   └─ 316 unidades

2️⃣ RESERVADO:
   └─ 260 unidades

3️⃣ BLOQUEADO WMS:
   └─ 213 unidades

4️⃣ DISPONÍVEL COMERCIAL (ERP):
   └─ -157 unidades
   └─ (ESTOQUE - RESERVADO - WMSBLOQUEADO)

5️⃣ SALDO FÍSICO WMS:
   └─ 43 unidades

⚠️ DIVERGÊNCIA ENCONTRADA:
   └─ 200 unidades (ERP > WMS)
```

### 🔧 Query SQL Customizada

```
Você: Claude, execute esta query SQL:

SELECT CODPROD, DESCRPROD, REFERENCIA
FROM TGFPRO
WHERE CODPROD IN (137216, 261302, 263340)

Claude: ✅ Query executada com sucesso!

📊 Total de registros: 3

📋 Dados:
[
  [137216, "PRODUTO A", "REF-001"],
  [261302, "PRODUTO B", "REF-002"],
  [263340, "PRODUTO C", "REF-003"]
]
```

### 📄 Gerar Relatório HTML Automaticamente

```
Você: Claude, execute a query de divergências e depois gere o relatório HTML

Claude: [executa query via MCP]
        ✅ 47 divergências encontradas!

        [gera HTML automaticamente]
        ✅ Relatório HTML gerado: relatorio_divergencias_completo.html

        🌐 Abra o arquivo no navegador para visualizar!
```

### 📋 Listar Queries Disponíveis

```
Você: Claude, quais queries SQL estão disponíveis?

Claude: 📋 QUERIES DISPONÍVEIS:

📄 query_divergencias_v3_definitiva.sql
📄 query_analise_detalhada_produto.sql
📄 query_divergencias_corrigida.sql

💡 Use 'executar_query_sql' com o conteúdo do arquivo
```

---

## 🎯 Comandos Úteis

| O que você quer | Comando para o Claude |
|-----------------|----------------------|
| Ver todas as divergências | "Execute a query de divergências" |
| Analisar um produto | "Analise o produto XXXXX da empresa 7" |
| Query customizada | "Execute esta query: [SQL]" |
| Gerar relatório HTML | "Gere o relatório de divergências" |
| Listar queries | "Quais queries estão disponíveis?" |

---

## ✅ Vantagens do MCP

### Antes (Sem MCP):
1. Abrir Postman
2. Copiar query SQL
3. Executar no Postman
4. Copiar JSON do resultado
5. Colar no terminal Python
6. Executar script de geração
7. Abrir HTML no navegador

### Agora (Com MCP):
1. "Claude, execute a query de divergências e gere o relatório"
2. ✅ Pronto!

---

## 🔧 Troubleshooting

### ❌ Erro: "MCP server not found"

**Solução:**
1. Verifique se o caminho em `claude_desktop_config.json` está correto
2. Reinicie o Claude Code
3. Verifique logs em `%APPDATA%\Claude\logs\`

### ❌ Erro: "Credenciais Sankhya não configuradas"

**Solução:**
1. Verifique se as credenciais estão no `claude_desktop_config.json`
2. Certifique-se de que não há espaços extras
3. Reinicie o Claude Code

### ❌ Erro: "Connection timeout"

**Solução:**
- Query pode estar demorando muito
- Tente filtrar por período menor
- Verifique conexão com internet

### ❌ MCP não aparece no Claude Code

**Solução:**
1. Feche COMPLETAMENTE o Claude Code (Ctrl+Q)
2. Verifique se o arquivo de config existe
3. Valide o JSON em https://jsonlint.com/
4. Abra o Claude Code novamente

---

## 📚 Recursos

- [README do MCP Sankhya](mcp_sankhya/README.md) - Documentação completa
- [Servidor MCP](mcp_sankhya/server.py) - Código fonte
- [PROGRESSO_SESSAO.md](PROGRESSO_SESSAO.md) - Histórico do projeto

---

## 🎉 Pronto!

Agora você pode executar queries SQL e gerar relatórios diretamente na conversa com o Claude, sem precisar sair do VS Code!

**Teste agora:**
```
Claude, execute a query de divergências e me mostre os resultados!
```

---

**Versão:** 1.0.0
**Data:** 2026-02-01
**Projeto:** MMarra Data Hub
