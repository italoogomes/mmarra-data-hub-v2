@echo off
REM =====================================================
REM Script de Instalacao Rapida - Servidor MCP Sankhya
REM =====================================================

echo.
echo ========================================================
echo   Instalacao do Servidor MCP Sankhya
echo ========================================================
echo.

REM Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado!
    echo Por favor, instale Python 3.11+ e tente novamente.
    pause
    exit /b 1
)

echo [1/4] Python encontrado!
echo.

REM Instalar dependencias
echo [2/4] Instalando dependencias...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao instalar dependencias!
    pause
    exit /b 1
)
echo.

REM Copiar .env
if not exist .env (
    echo [3/4] Criando arquivo .env...
    copy .env.example .env
    echo.
    echo [INFO] Arquivo .env criado com credenciais padrao.
) else (
    echo [3/4] Arquivo .env ja existe.
)
echo.

REM Mostrar configuracao MCP
echo [4/4] Configuracao do Claude Code:
echo.
echo Adicione isto ao arquivo claude_desktop_config.json:
echo.
echo {
echo   "mcpServers": {
echo     "sankhya": {
echo       "command": "python",
echo       "args": ["%cd%\server.py"],
echo       "env": {
echo         "SANKHYA_CLIENT_ID": "09ef3473-cb85-41d4-b6d4-473c15d39292",
echo         "SANKHYA_CLIENT_SECRET": "7phfkche8hWHpWYBNWbEgf4xY4mPixp0",
echo         "SANKHYA_X_TOKEN": "dca9f07d-bf0f-426c-b537-0e5b0ff1123d"
echo       }
echo     }
echo   }
echo }
echo.
echo Localizacao: %%APPDATA%%\Claude\claude_desktop_config.json
echo.
echo ========================================================
echo   Instalacao Concluida!
echo ========================================================
echo.
echo Proximos passos:
echo 1. Adicione a configuracao acima ao claude_desktop_config.json
echo 2. Reinicie o Claude Code
echo 3. Teste com: "Claude, execute a query de divergencias"
echo.
pause
