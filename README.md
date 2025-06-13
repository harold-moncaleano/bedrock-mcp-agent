# 🧠 Bedrock MCP Agent

**Agente de AWS Bedrock integrado con Model Context Protocol (MCP)**

Una aplicación completa que permite interactuar con los modelos de lenguaje de AWS Bedrock a través de una interfaz web moderna y un backend Python robusto.

## 🚀 Características

- **Backend Python** con integración completa a AWS Bedrock
- **Frontend React** moderno y responsivo
- **Soporte múltiples modelos**: Claude 3, Titan, Llama 2, y más
- **Protocolo MCP** para formateo estandarizado de respuestas
- **Configuración flexible** de parámetros (temperatura, tokens, región)
- **Interfaz de chat interactiva** con historial de conversaciones

## 📋 Requisitos Previos

### AWS
- Cuenta de AWS activa
- Acceso habilitado a AWS Bedrock
- Credenciales AWS configuradas (IAM user o role)
- Permisos para `bedrock:InvokeModel` y `bedrock:ListFoundationModels`

### Software
- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Navegador web moderno

## 🛠️ Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/harold-moncaleano/bedrock-mcp-agent.git
cd bedrock-mcp-agent
```

### 2. Crear entorno virtual (recomendado)
```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate
```

### 3. Instalar dependencias Python
```bash
pip install boto3 flask flask-cors python-dotenv
```

## ⚙️ Configuración

### 1. Configurar credenciales AWS

**Opción A: Variables de entorno**
```bash
export AWS_ACCESS_KEY_ID=tu_access_key
export AWS_SECRET_ACCESS_KEY=tu_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

**Opción B: Archivo ~/.aws/credentials**
```ini
[default]
aws_access_key_id = tu_access_key
aws_secret_access_key = tu_secret_key
region = us-east-1
```

**Opción C: IAM Role (si ejecutas en EC2)**
El agente utilizará automáticamente el role de la instancia EC2.

### 2. Habilitar modelos en AWS Bedrock

1. Ve a la consola de AWS Bedrock
2. Navega a "Model access" en el panel izquierdo
3. Solicita acceso a los modelos que desees usar:
   - Anthropic Claude 3 Sonnet
   - Anthropic Claude 3 Haiku  
   - Amazon Titan Text Premier
   - Meta Llama 2 70B Chat

## 🚀 Ejecución

### Método 1: Solo Backend (Línea de comandos)

```bash
# Ejecutar el agente directamente
python bedrock_mcp_agent.py
```

Este método:
- Lista los modelos disponibles
- Muestra ejemplos de uso
- Ideal para pruebas rápidas

### Método 2: Frontend + Backend (Aplicación Web Completa)

**Paso 1: Crear servidor backend (Flask)**

Crea un archivo `app.py`:

```python
from flask import Flask, request, jsonify
from flask_cors import CORS
from bedrock_mcp_agent import BedrockMCPAgent
import json

app = Flask(__name__)
CORS(app)  # Permitir requests desde el frontend

# Inicializar el agente
agent = BedrockMCPAgent()

@app.route('/api/models', methods=['GET'])
def get_models():
    try:
        models = agent.list_available_models()
        return jsonify({"success": True, "models": models})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        model_id = data.get('model_id')
        prompt = data.get('prompt')
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 1000)
        
        # Invocar el modelo
        bedrock_response = agent.invoke_model(
            model_id=model_id,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Formatear respuesta MCP
        mcp_response = agent.format_mcp_response(bedrock_response, model_id)
        
        return jsonify({"success": True, "response": mcp_response})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

**Paso 2: Ejecutar el servidor backend**
```bash
python app.py
```

**Paso 3: Abrir el frontend**
Abre `frontend.html` en tu navegador web o sírvelo desde un servidor web:

```bash
# Opción 1: Abrir directamente
open frontend.html  # macOS
start frontend.html # Windows
xdg-open frontend.html # Linux

# Opción 2: Servidor web simple
python -m http.server 8080
# Luego ve a http://localhost:8080/frontend.html
```

## 🔧 Uso

### Interfaz Web
1. Selecciona el modelo de Bedrock que deseas usar
2. Ajusta los parámetros (temperatura, tokens máximos, región)
3. Escribe tu mensaje en el chat
4. Presiona Enter o haz clic en enviar
5. Ve la respuesta del modelo con metadata incluida

### API Endpoints

**GET /api/models**
- Obtiene la lista de modelos disponibles

**POST /api/chat**
```json
{
  "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
  "prompt": "¿Qué es AWS Bedrock?",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

## 📁 Estructura del Proyecto

```
bedrock-mcp-agent/
├── README.md                 # Documentación del proyecto
├── bedrock_mcp_agent.py     # Agente principal de Python
├── frontend.html            # Interfaz web React
├── app.py                   # Servidor Flask (crear manualmente)
└── requirements.txt         # Dependencias (crear manualmente)
```

## 🐛 Solución de Problemas

### Error: "Resource not accessible by personal access token"
- Verifica que tus credenciales AWS estén configuradas correctamente
- Asegúrate de tener permisos para Bedrock

### Error: "Access denied to model"
- Ve a la consola AWS Bedrock → Model access
- Solicita acceso al modelo específico
- Puede tomar algunos minutos en ser aprobado

### Error: "Region not supported"
- Verifica que AWS Bedrock esté disponible en tu región
- Regiones soportadas: us-east-1, us-west-2, eu-west-1, ap-southeast-1

### Frontend no conecta con Backend
- Asegúrate de que el servidor Flask esté ejecutándose en puerto 5000
- Verifica que CORS esté habilitado
- Revisa la consola del navegador para errores

## 🔐 Seguridad

- **Nunca** commits credenciales AWS en el código
- Usa variables de entorno o AWS IAM roles
- Implementa autenticación en producción
- Limita permisos IAM al mínimo necesario

## 📚 Recursos Adicionales

- [Documentación AWS Bedrock](https://docs.aws.amazon.com/bedrock/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)

## 🤝 Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ve el archivo `LICENSE` para más detalles.

## 👨‍💻 Autor

**Harold Moncaleano**
- GitHub: [@harold-moncaleano](https://github.com/harold-moncaleano)
- Email: harold.moncaleano@nuvu.cc

---

⭐ **¡Si este proyecto te resulta útil, dale una estrella!** ⭐