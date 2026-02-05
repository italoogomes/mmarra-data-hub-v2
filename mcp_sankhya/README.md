# 🔧 Servidor MCP Sankhya

Servidor MCP (Model Context Protocol) que permite ao Claude Code executar queries SQL diretamente na API Sankhya e processar os resultados automaticamente.

## 📋 Funcionalidades

### Tools Disponíveis:

1. **executar_query_sql** - Executa qualquer query SQL customizada
2. **executar_query_divergencias** - Executa a query V3 de divergências (corrigida)
3. **executar_query_analise_produto** - Análise detalhada de um produto específico
4. **gerar_relatorio_divergencias** - Gera relatório HTML interativo
5. **listar_queries_disponiveis** - Lista queries SQL do projeto

## 🚀 Instalação

### 1. Instalar Dependências

```bash
cd mcp_sankhya
pip install -r requirements.txt
```

### 2. Configurar Credenciais

Crie o arquivo `.env` baseado no `.env.example`:

```bash
cp .env.example .env
```

Edite `.env` com suas credenciais Sankhya (já preenchidas com as credenciais do projeto).

### 3. Configurar Claude Code

Adicione ao arquivo de configuração do Claude Code:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Mac/Linux**: `~/.claude/claude_desktop_config.json`

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

### 4. Reiniciar Claude Code

Feche e abra o Claude Code novamente para carregar o servidor MCP.

## 💡 Uso

### Exemplo 1: Executar Query de Divergências

```
Você: Claude, execute a query de divergências para a empresa 7
Claude: [usa MCP] ✅ Query executada! Encontradas 47 divergências...
```

### Exemplo 2: Analisar Produto Específico

```
Você: Claude, analise o produto 261302 da empresa 7
Claude: [usa MCP] ✅ Análise completa:
        - Estoque: 316
        - Reservado: 260
        - Bloqueado: 213
        - Disponível: -157 ⚠️
```

### Exemplo 3: Query SQL Customizada

```
Você: Claude, execute esta query:
      SELECT CODPROD, DESCRPROD FROM TGFPRO WHERE CODPROD = 137216

Claude: [usa MCP] ✅ Resultado:
        CODPROD: 137216
        DESCRPROD: PRODUTO EXEMPLO
```

### Exemplo 4: Gerar Relatório HTML

```
Você: Claude, execute a query de divergências e gere o relatório HTML
Claude: [usa MCP para query] → [usa MCP para HTML] ✅ Relatório gerado!
```

## 🔧 Estrutura do Servidor

```
mcp_sankhya/
├── server.py           # Servidor MCP principal
├── requirements.txt    # Dependências Python
├── .env.example        # Exemplo de configuração
├── .env                # Credenciais (NÃO COMMITAR!)
└── README.md           # Esta documentação
```

## 🔐 Segurança

- ⚠️ **NUNCA** commite o arquivo `.env` no git
- ✅ Credenciais são carregadas de variáveis de ambiente
- ✅ Token renovado automaticamente a cada 23 horas
- ✅ Conexões HTTPS com timeout

## 🐛 Troubleshooting

### Erro: "Credenciais Sankhya não configuradas"

Verifique se o arquivo `.env` existe e contém todas as variáveis.

### Erro: "Connection timeout"

Aumente o timeout em `server.py` (padrão: 120s para queries).

### MCP não aparece no Claude Code

1. Verifique se o caminho em `claude_desktop_config.json` está correto
2. Reinicie o Claude Code
3. Verifique logs em: `%APPDATA%\Claude\logs\`

## 📚 Referências

- [MCP SDK Python](https://github.com/anthropics/anthropic-sdk-python)
- [API Sankhya](https://ajuda.sankhya.com.br/hc/pt-br/articles/360038506734)
- [Claude Code Docs](https://docs.anthropic.com/)

## 📞 Suporte

Em caso de problemas, verifique:
1. Credenciais corretas no `.env`
2. Dependências instaladas (`pip list`)
3. Configuração correta em `claude_desktop_config.json`
4. Logs do Claude Code

---

**Versão:** 1.0.0
**Data:** 2026-02-01
**Projeto:** MMarra Data Hub
