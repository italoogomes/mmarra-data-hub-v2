"""
Servidor HTTP simples para compartilhar relatorios via Ngrok
"""

import http.server
import socketserver
import os
from pathlib import Path

# Configuracoes
PORT = 8000
DIRETORIO = Path(__file__).parent

print("=" * 80)
print("SERVIDOR DE RELATORIOS - MMarra Data Hub")
print("=" * 80)
print(f"\nDiretorio: {DIRETORIO}")
print(f"Porta: {PORT}")

# Mudar para o diretorio do projeto
os.chdir(DIRETORIO)

# Handler customizado
class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Adicionar headers para UTF-8
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        super().end_headers()

    def do_GET(self):
        # Se acessar a raiz, mostrar lista de relatorios
        if self.path == '/':
            self.path = '/index.html'

            # Criar pagina index com lista de relatorios
            html_files = [f for f in os.listdir('.') if f.endswith('.html')]

            html = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MMarra Data Hub - Relatorios</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px 20px;
            min-height: 100vh;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
        }

        h1 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 2.5em;
        }

        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }

        .relatorio-lista {
            list-style: none;
        }

        .relatorio-item {
            background: #f8f9fa;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 10px;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .relatorio-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }

        .relatorio-item a {
            color: #667eea;
            text-decoration: none;
            font-size: 1.2em;
            font-weight: 600;
            display: block;
        }

        .relatorio-item a:hover {
            color: #764ba2;
        }

        .footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }

        .empty {
            text-align: center;
            padding: 40px;
            color: #999;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>MMarra Data Hub</h1>
        <p class="subtitle">Relatorios de Divergencias de Estoque</p>

        <ul class="relatorio-lista">
"""

            if html_files:
                for html_file in sorted(html_files):
                    # Pular o proprio index.html
                    if html_file == 'index.html':
                        continue

                    # Nome amigavel
                    nome = html_file.replace('_', ' ').replace('.html', '').title()

                    html += f"""
            <li class="relatorio-item">
                <a href="/{html_file}">{nome}</a>
            </li>
"""
            else:
                html += """
            <li class="empty">
                Nenhum relatorio disponivel ainda.
            </li>
"""

            html += """
        </ul>

        <div class="footer">
            <p>MMarra Data Hub v0.5.0</p>
            <p>Gerado automaticamente via API Sankhya</p>
        </div>
    </div>
</body>
</html>
"""

            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
            return

        # Servir outros arquivos normalmente
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

# Criar servidor
with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
    print("\n" + "=" * 80)
    print("SERVIDOR INICIADO!")
    print("=" * 80)
    print(f"\nAcesse localmente:")
    print(f"  http://localhost:{PORT}")
    print("\nPara compartilhar via Ngrok:")
    print(f"  1. Abra outro terminal")
    print(f"  2. Execute: ngrok http {PORT}")
    print(f"  3. Copie a URL publica gerada pelo Ngrok")
    print(f"  4. Envie a URL para seu chefe")
    print("\n[CTRL+C para parar o servidor]")
    print("=" * 80)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServidor encerrado.")
