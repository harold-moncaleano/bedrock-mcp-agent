#!/bin/bash

# Script de inicio para Bedrock MCP Agent
# Este script automatiza la configuración y ejecución del proyecto

echo "🚀 Iniciando Bedrock MCP Agent..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes coloreados
print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 no está instalado. Por favor instala Python 3.8 o superior."
    exit 1
fi

print_success "Python 3 encontrado: $(python3 --version)"

# Verificar si pip está instalado
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 no está instalado. Por favor instala pip."
    exit 1
fi

print_success "pip3 encontrado: $(pip3 --version)"

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    print_status "Creando entorno virtual..."
    python3 -m venv venv
    print_success "Entorno virtual creado"
else
    print_success "Entorno virtual ya existe"
fi

# Activar entorno virtual
print_status "Activando entorno virtual..."
source venv/bin/activate

# Actualizar pip
print_status "Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias
print_status "Instalando dependencias..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_success "Dependencias instaladas"
else
    print_error "Archivo requirements.txt no encontrado"
    exit 1
fi

# Verificar archivo .env
if [ ! -f ".env" ]; then
    print_warning "Archivo .env no encontrado"
    if [ -f ".env.example" ]; then
        print_status "Copiando .env.example a .env..."
        cp .env.example .env
        print_warning "Por favor edita el archivo .env con tus credenciales AWS antes de continuar"
        print_status "Abre .env en tu editor favorito y configura:"
        echo "  - AWS_ACCESS_KEY_ID"
        echo "  - AWS_SECRET_ACCESS_KEY"
        echo "  - AWS_DEFAULT_REGION"
        read -p "Presiona Enter cuando hayas configurado el archivo .env..."
    else
        print_error "Archivo .env.example no encontrado"
        exit 1
    fi
else
    print_success "Archivo .env encontrado"
fi

# Verificar credenciales AWS
print_status "Verificando configuración AWS..."
if [ -z "$AWS_ACCESS_KEY_ID" ] && [ -z "$AWS_PROFILE" ]; then
    source .env
    if [ -z "$AWS_ACCESS_KEY_ID" ] && [ -z "$AWS_PROFILE" ]; then
        print_warning "No se encontraron credenciales AWS configuradas"
        print_status "Asegúrate de tener configurado uno de estos métodos:"
        echo "  1. Variables de entorno (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)"
        echo "  2. Archivo ~/.aws/credentials"
        echo "  3. IAM Role (si ejecutas en EC2)"
        echo "  4. AWS_PROFILE en archivo .env"
    fi
fi

# Función para mostrar opciones de ejecución
show_menu() {
    echo ""
    print_status "Selecciona cómo ejecutar el proyecto:"
    echo "1. Solo Backend (línea de comandos)"
    echo "2. Servidor web completo (Flask + Frontend)"
    echo "3. Verificar configuración"
    echo "4. Salir"
    echo ""
}

# Función para ejecutar solo backend
run_backend_only() {
    print_status "Ejecutando solo el backend..."
    python3 bedrock_mcp_agent.py
}

# Función para ejecutar servidor web completo
run_web_server() {
    print_status "Iniciando servidor web..."
    print_success "Servidor iniciado en http://localhost:5000"
    print_status "Para detener el servidor, presiona Ctrl+C"
    python3 app.py
}

# Función para verificar configuración
verify_config() {
    print_status "Verificando configuración..."
    python3 -c "
import sys
sys.path.append('.')
try:
    from bedrock_mcp_agent import BedrockMCPAgent
    agent = BedrockMCPAgent()
    print('✅ Agente Bedrock inicializado correctamente')
    models = agent.list_available_models()
    print(f'✅ Se encontraron {len(models)} modelos disponibles')
    for model in models[:3]:
        print(f'   - {model.get(\"modelId\", \"N/A\")}')
    if len(models) > 3:
        print(f'   ... y {len(models) - 3} más')
except Exception as e:
    print(f'❌ Error: {e}')
    print('⚠️  Verifica tus credenciales AWS y acceso a Bedrock')
"
}

# Menú principal
while true; do
    show_menu
    read -p "Selecciona una opción (1-4): " choice
    
    case $choice in
        1)
            run_backend_only
            ;;
        2)
            run_web_server
            ;;
        3)
            verify_config
            ;;
        4)
            print_success "¡Hasta luego!"
            break
            ;;
        *)
            print_error "Opción inválida. Por favor selecciona 1-4."
            ;;
    esac
    
    echo ""
    read -p "Presiona Enter para continuar..."
done

# Desactivar entorno virtual
deactivate
