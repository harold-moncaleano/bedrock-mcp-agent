@echo off
REM Script de inicio para Bedrock MCP Agent en Windows
REM Este script automatiza la configuración y ejecución del proyecto

echo 🚀 Iniciando Bedrock MCP Agent...

REM Verificar si Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python no está instalado. Por favor instala Python 3.8 o superior.
    pause
    exit /b 1
)

echo ✅ Python encontrado
python --version

REM Verificar si pip está instalado
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip no está instalado. Por favor instala pip.
    pause
    exit /b 1
)

echo ✅ pip encontrado
pip --version

REM Crear entorno virtual si no existe
if not exist "venv" (
    echo ℹ️  Creando entorno virtual...
    python -m venv venv
    echo ✅ Entorno virtual creado
) else (
    echo ✅ Entorno virtual ya existe
)

REM Activar entorno virtual
echo ℹ️  Activando entorno virtual...
call venv\Scripts\activate.bat

REM Actualizar pip
echo ℹ️  Actualizando pip...
python -m pip install --upgrade pip

REM Instalar dependencias
echo ℹ️  Instalando dependencias...
if exist "requirements.txt" (
    pip install -r requirements.txt
    echo ✅ Dependencias instaladas
) else (
    echo ❌ Archivo requirements.txt no encontrado
    pause
    exit /b 1
)

REM Verificar archivo .env
if not exist ".env" (
    echo ⚠️  Archivo .env no encontrado
    if exist ".env.example" (
        echo ℹ️  Copiando .env.example a .env...
        copy .env.example .env
        echo ⚠️  Por favor edita el archivo .env con tus credenciales AWS antes de continuar
        echo ℹ️  Abre .env en tu editor favorito y configura:
        echo   - AWS_ACCESS_KEY_ID
        echo   - AWS_SECRET_ACCESS_KEY
        echo   - AWS_DEFAULT_REGION
        pause
    ) else (
        echo ❌ Archivo .env.example no encontrado
        pause
        exit /b 1
    )
) else (
    echo ✅ Archivo .env encontrado
)

REM Menú principal
:menu
echo.
echo ℹ️  Selecciona cómo ejecutar el proyecto:
echo 1. Solo Backend (línea de comandos)
echo 2. Servidor web completo (Flask + Frontend)
echo 3. Verificar configuración
echo 4. Salir
echo.
set /p choice=Selecciona una opción (1-4): 

if "%choice%"=="1" goto backend_only
if "%choice%"=="2" goto web_server
if "%choice%"=="3" goto verify_config
if "%choice%"=="4" goto exit
echo ❌ Opción inválida. Por favor selecciona 1-4.
goto menu

:backend_only
echo ℹ️  Ejecutando solo el backend...
python bedrock_mcp_agent.py
pause
goto menu

:web_server
echo ℹ️  Iniciando servidor web...
echo ✅ Servidor iniciado en http://localhost:5000
echo ℹ️  Para detener el servidor, presiona Ctrl+C
python app.py
pause
goto menu

:verify_config
echo ℹ️  Verificando configuración...
python -c "import sys; sys.path.append('.'); from bedrock_mcp_agent import BedrockMCPAgent; agent = BedrockMCPAgent(); print('✅ Agente Bedrock inicializado correctamente'); models = agent.list_available_models(); print(f'✅ Se encontraron {len(models)} modelos disponibles'); [print(f'   - {model.get(\"modelId\", \"N/A\")}') for model in models[:3]]; print(f'   ... y {len(models) - 3} más') if len(models) > 3 else None" 2>nul
if %errorlevel% neq 0 (
    echo ❌ Error verificando configuración
    echo ⚠️  Verifica tus credenciales AWS y acceso a Bedrock
)
pause
goto menu

:exit
echo ✅ ¡Hasta luego!
call venv\Scripts\deactivate.bat
pause
exit /b 0
