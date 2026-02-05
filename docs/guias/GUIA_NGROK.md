# 🌐 Guia: Compartilhar Relatórios via Ngrok

**Objetivo**: Enviar links dos relatórios HTML para seu chefe via Ngrok

---

## 📋 Passo a Passo

### 1️⃣ Instalar o Ngrok (Primeira Vez)

1. **Baixar o Ngrok**:
   - Acesse: https://ngrok.com/download
   - Baixe a versão para Windows
   - Extraia o arquivo `ngrok.exe`

2. **Criar conta (grátis)**:
   - Acesse: https://dashboard.ngrok.com/signup
   - Crie uma conta gratuita
   - Copie seu **authtoken**

3. **Configurar o authtoken**:
   ```bash
   ngrok config add-authtoken SEU_TOKEN_AQUI
   ```

---

### 2️⃣ Iniciar o Servidor de Relatórios

**Terminal 1** (deixe aberto):
```bash
python servidor_relatorios.py
```

**Resultado**:
```
================================================================================
SERVIDOR INICIADO!
================================================================================

Acesse localmente:
  http://localhost:8000

Para compartilhar via Ngrok:
  1. Abra outro terminal
  2. Execute: ngrok http 8000
  3. Copie a URL publica gerada pelo Ngrok
  4. Envie a URL para seu chefe

[CTRL+C para parar o servidor]
================================================================================
```

---

### 3️⃣ Iniciar o Ngrok

**Terminal 2** (novo terminal):
```bash
ngrok http 8000
```

**Resultado**:
```
ngrok

Session Status                online
Account                       seu-email@example.com
Version                       3.x.x
Region                        United States (us)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok-free.app -> http://localhost:8000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

---

### 4️⃣ Compartilhar o Link

1. **Copie a URL pública**:
   ```
   https://abc123.ngrok-free.app
   ```

2. **Envie para seu chefe**:
   - WhatsApp
   - Email
   - Teams
   - Qualquer canal

3. **Seu chefe vai ver**:
   - Página inicial com lista de relatórios
   - Pode clicar em qualquer relatório
   - HTML interativo completo

---

## 📊 Relatórios Disponíveis

Os seguintes arquivos HTML serão compartilhados:

- `relatorio_consolidado_produtos.html` - **PRINCIPAL** (686 produtos)
- `relatorio_divergencias_v3.html` - Query V3 (5.000 notas)
- Outros relatórios que você gerar

---

## ⚠️ Observações Importantes

### Limitações do Plano Gratuito Ngrok:

- ✅ **Funciona perfeitamente** para compartilhar relatórios
- ✅ URL pública válida por algumas horas
- ⚠️ **URL muda** toda vez que reinicia o Ngrok
- ⚠️ Limite de 40 conexões/minuto (suficiente para relatórios)
- ⚠️ Aparece aviso do Ngrok antes de acessar (clique em "Visit Site")

### Segurança:

- 🔒 Conexão HTTPS segura
- 🔒 URL aleatória difícil de adivinhar
- ⚠️ **Não compartilhe o link publicamente** (apenas com pessoas autorizadas)
- ⚠️ **Feche o servidor** quando terminar (CTRL+C nos dois terminais)

---

## 🚀 Uso Rápido (Depois da Primeira Vez)

```bash
# Terminal 1: Servidor
python servidor_relatorios.py

# Terminal 2: Ngrok
ngrok http 8000
```

**Copie a URL pública e envie!** 🎉

---

## 🔧 Troubleshooting

### Erro: "command not found: ngrok"

**Solução Windows**:
1. Mova `ngrok.exe` para uma pasta (ex: `C:\ngrok`)
2. Adicione ao PATH ou use o caminho completo:
   ```bash
   C:\ngrok\ngrok http 8000
   ```

### Erro: "bind: address already in use"

**Solução**: Porta 8000 já está em uso
```bash
# Mude a porta no servidor_relatorios.py (linha PORT = 8000)
# Exemplo: PORT = 8001
# Depois execute:
python servidor_relatorios.py
ngrok http 8001
```

### Erro: "authtoken is not configured"

**Solução**:
```bash
ngrok config add-authtoken SEU_TOKEN_AQUI
```

---

## 🎯 Exemplo de Uso Completo

```bash
# Passo 1: Gerar relatório
python executar_relatorio_consolidado.py
python gerar_html_consolidado.py

# Passo 2: Iniciar servidor (Terminal 1)
python servidor_relatorios.py

# Passo 3: Iniciar Ngrok (Terminal 2)
ngrok http 8000

# Passo 4: Enviar link para o chefe
# Exemplo: https://abc123.ngrok-free.app
```

---

## 📱 Alternativas ao Ngrok

Se não quiser usar Ngrok, outras opções:

1. **Email**: Anexar o HTML diretamente
2. **OneDrive/Google Drive**: Upload do HTML e compartilhar link
3. **SharePoint**: Upload e compartilhar
4. **Teams**: Enviar arquivo diretamente

**Vantagem do Ngrok**: Relatórios ficam sempre atualizados em tempo real!

---

## 💡 Dicas

- ✅ Mantenha os terminais abertos enquanto seu chefe estiver visualizando
- ✅ Gere novos relatórios e atualize sem mudar o link
- ✅ Use CTRL+C para parar tudo quando terminar
- ✅ Salve a URL do Ngrok se for usar por algumas horas

---

**Última atualização:** 2026-02-02
**Versão:** v0.5.0
