# 🧠 Bedrock MCP Agent

**Agente de AWS Bedrock integrado con Model Context Protocol (MCP)**

Una aplicación completa que permite interactuar con los modelos de lenguaje de AWS Bedrock a través de una interfaz web moderna y un backend Python robusto.

![Bedrock MCP Agent](https://img.shields.io/badge/AWS-Bedrock-orange?style=flat-square&logo=amazon-aws)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)
![React](https://img.shields.io/badge/React-18-blue?style=flat-square&logo=react)
![Flask](https://img.shields.io/badge/Flask-2.3+-green?style=flat-square&logo=flask)

## 🚀 Características

- **🐍 Backend Python** con integración completa a AWS Bedrock
- **⚛️ Frontend React** moderno y responsivo
- **🤖 Soporte múltiples modelos**: Claude 3, Titan, Llama 2, y más
- **📡 Protocolo MCP** para formateo estandarizado de respuestas
- **⚙️ Configuración flexible** de parámetros (temperatura, tokens, región)
- **💬 Interfaz de chat interactiva** con historial de conversaciones
- **🔄 Scripts de inicio automatizados** para Windows, Linux y macOS
- **📊 Monitoreo en tiempo real** del estado del servidor
- **🛡️ Manejo robusto de errores** y logging completo

## 📁 Estructura del Proyecto

```
bedrock-mcp-agent/
├── 📄 README.md                 # Documentación del proyecto
├── 🐍 bedrock_mcp_agent.py     # Agente principal de Python
├── 🌐 app.py                   # Servidor Flask backend
├── 🎨 frontend.html            # Interfaz web React
├── 📦 requirements.txt         # Dependencias de Python
├── ⚙️ .env.example             # Plantilla de variables de entorno
├── 🚫 .gitignore               # Archivos excluidos de Git
├── 🚀 start.sh                 # Script de inicio para Linux/macOS
└── 🚀 start.bat                # Script de inicio para Windows
```

## 📋 Requisitos Previos

### AWS
- ✅ Cuenta de AWS activa
- ✅ Acceso habilitado a AWS Bedrock
- ✅ Credenciales AWS configuradas (IAM user o role)
- ✅ Permisos para `bedrock:InvokeModel` y `bedrock:ListFoundationModels`

### Software
- ✅ Python 3.8 o superior
- ✅ pip (gestor de paquetes de Python)
- ✅ Navegador web moderno

## ⚡ Inicio Rápido

### Método 1: Scripts Automatizados (Recomendado)

**Para Linux/macOS:**
```bash
git clone https://github.com/harold-moncaleano/bedrock-mcp-agent.git
cd bedrock-mcp-agent
chmod +x start.sh
./start.sh
```

**Para Windows:**
```cmd
git clone https://github.com/harold-moncaleano/bedrock-mcp-agent.git
cd bedrock-mcp-agent
start.bat
```

Los scripts automatizados se encargan de:
- ✅ Verificar Python y pip
- ✅ Crear el entorno virtual
- ✅ Instalar dependencias automáticamente
- ✅ Configurar variables de entorno
- ✅ Ofrecer opciones de ejecución interactivas

### Método 2: Instalación Manual

#### 1. Clonar el repositorio
```bash
git clone https://github.com/harold-moncaleano/bedrock-mcp-agent.git
cd bedrock-mcp-agent
```

#### 2. Crear entorno virtual
```bash
python -m venv venv

# Activar entorno virtual
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

#### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

#### 4. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus credenciales AWS
```

## ⚙️ Configuración AWS

### Opción 1: Variables de entorno (.env)
```bash
# Editar archivo .env
AWS_ACCESS_KEY_ID=tu_access_key_id
AWS_SECRET_ACCESS_KEY=tu_secret_access_key
AWS_DEFAULT_REGION=us-east-1
```

### Opción 2: AWS CLI
```bash
aws configure
```

### Opción 3: IAM Role (EC2)
Si ejecutas en EC2, el agente usará automáticamente el IAM role de la instancia.

### Habilitar modelos en AWS Bedrock

1. Ve a la **consola AWS Bedrock**
2. Navega a **"Model access"**
3. Solicita acceso a los modelos:
   - ✅ Anthropic Claude 3 Sonnet
   - ✅ Anthropic Claude 3 Haiku  
   - ✅ Amazon Titan Text Premier
   - ✅ Meta Llama 2 70B Chat

## 🚀 Ejecución

### Aplicación Web Completa

```bash
# Ejecutar servidor Flask
python app.py

# Abrir en navegador
# http://localhost:5000
```

El servidor Flask:
- 🌐 Sirve el frontend en la ruta principal `/`
- 📡 Expone API REST en `/api/*`
- 🔍 Incluye endpoint de salud en `/health`
- 📊 Proporciona configuración en `/api/config`

### Solo Backend (Línea de comandos)

```bash
# Ejecutar agente directamente
python bedrock_mcp_agent.py
```

## 🌐 API Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Interfaz web principal |
| `/health` | GET | Estado del servidor y agente |
| `/api/models` | GET | Lista de modelos disponibles |
| `/api/chat` | POST | Enviar mensaje a modelo |
| `/api/config` | GET | Configuración del servidor |

### Ejemplo de uso de API

```javascript
// Enviar mensaje
const response = await fetch('http://localhost:5000/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    model_id: 'anthropic.claude-3-sonnet-20240229-v1:0',
    prompt: '¿Qué es AWS Bedrock?',
    temperature: 0.7,
    max_tokens: 1000
  })
});
```

## 🎛️ Configuración Avanzada

### Variables de entorno disponibles

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `AWS_ACCESS_KEY_ID` | ID de clave de acceso AWS | - |
| `AWS_SECRET_ACCESS_KEY` | Clave secreta AWS | - |
| `AWS_DEFAULT_REGION` | Región AWS | `us-east-1` |
| `FLASK_HOST` | Host del servidor Flask | `0.0.0.0` |
| `FLASK_PORT` | Puerto del servidor Flask | `5000` |
| `FLASK_DEBUG` | Modo debug | `True` |
| `SECRET_KEY` | Clave secreta Flask | `bedrock-mcp-*` |

### Modelos soportados

| Modelo | ID | Proveedor | Descripción |
|--------|----|-----------| ------------|
| Claude 3 Sonnet | `anthropic.claude-3-sonnet-20240229-v1:0` | Anthropic | Balanceado para tareas complejas |
| Claude 3 Haiku | `anthropic.claude-3-haiku-20240307-v1:0` | Anthropic | Rápido y eficiente |
| Titan Text Premier | `amazon.titan-text-premier-v1:0` | Amazon | Modelo avanzado de Amazon |
| Titan Text Express | `amazon.titan-text-express-v1` | Amazon | Modelo rápido de Amazon |
| Llama 2 70B Chat | `meta.llama2-70b-chat-v1` | Meta | Conversacional de Meta |

## 🎯 Funcionalidades de la Interfaz

### Panel de Configuración
- 🔧 **Selector de modelos** dinámico desde AWS
- 🌡️ **Control de temperatura** (0-1) con slider
- 🔢 **Configuración de tokens máximos** (1-4000)
- 🌍 **Selector de región AWS**

### Chat Interactivo
- 💬 **Historial de conversaciones** persistente
- ⏱️ **Indicadores de estado** y tiempo de procesamiento
- 📊 **Metadata detallada** (tokens, tiempo, ID de request)
- 🔄 **Indicador de estado del servidor** en tiempo real

### Controles Adicionales
- 🗑️ **Limpiar chat** con un clic
- 🔄 **Recargar configuración** y modelos
- 📱 **Diseño responsivo** para móviles
- ⚙️ **Panel de configuración** colapsible

## 🐛 Solución de Problemas

### Error: "Resource not accessible by personal access token"
```bash
# Verificar credenciales AWS
aws configure list
# o revisar archivo .env
```

### Error: "Access denied to model"
1. Ve a AWS Bedrock Console → Model access
2. Solicita acceso al modelo específico
3. Espera aprobación (puede tomar minutos)

### Error: "Region not supported"
- Usa regiones soportadas: `us-east-1`, `us-west-2`, `eu-west-1`, `ap-southeast-1`

### Frontend no conecta con Backend
```bash
# Verificar que el servidor esté ejecutándose
curl http://localhost:5000/health

# Revisar logs del servidor
python app.py
```

### Problemas con dependencias
```bash
# Reinstalar dependencias
pip install --upgrade -r requirements.txt

# Limpiar caché
pip cache purge
```

## 🔐 Seguridad

### Mejores Prácticas
- ⚠️ **Nunca** commitees credenciales AWS en el código
- ✅ Usa variables de entorno o AWS IAM roles
- ✅ Implementa autenticación en producción
- ✅ Limita permisos IAM al mínimo necesario
- ✅ Usa HTTPS en producción

### Permisos IAM mínimos
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:ListFoundationModels"
      ],
      "Resource": "*"
    }
  ]
}
```

## 📊 Monitoreo y Logs

### Logs del servidor
```bash
# Los logs aparecen automáticamente en consola
python app.py

# Configurar nivel de logging en .env
FLASK_DEBUG=True  # Para logs detallados
```

### Endpoint de salud
```bash
curl http://localhost:5000/health
```

Respuesta ejemplo:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "agent_status": "initialized",
  "region": "us-east-1"
}
```

## 🚢 Despliegue en Producción

### Usando Gunicorn
```bash
# Instalar Gunicorn
pip install gunicorn

# Ejecutar en producción
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker (opcional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

## 🤝 Contribuir

1. **Fork** el repositorio
2. Crea una rama para tu feature: `git checkout -b feature/nueva-funcionalidad`
3. **Commit** tus cambios: `git commit -am 'Añadir nueva funcionalidad'`
4. **Push** a la rama: `git push origin feature/nueva-funcionalidad`
5. Crea un **Pull Request**

### Áreas de contribución
- 🔧 Nuevos modelos de Bedrock
- 🎨 Mejoras en la interfaz
- 📚 Documentación
- 🧪 Tests unitarios
- 🔐 Mejoras de seguridad

## 📚 Recursos Adicionales

- 📖 [Documentación AWS Bedrock](https://docs.aws.amazon.com/bedrock/)
- 🔗 [Model Context Protocol](https://modelcontextprotocol.io/)
- 🤖 [Anthropic Claude API](https://docs.anthropic.com/)
- 🛡️ [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- ⚛️ [React Documentation](https://react.dev/)
- 🐍 [Flask Documentation](https://flask.palletsprojects.com/)

## 📄 Licencia

Este proyecto está bajo la **Licencia MIT**. Ve el archivo `LICENSE` para más detalles.

## 👨‍💻 Autor

**Harold Moncaleano**
- 🐙 GitHub: [@harold-moncaleano](https://github.com/harold-moncaleano)
- 📧 Email: harold.moncaleano@nuvu.cc
- 🌐 Proyecto: [bedrock-mcp-agent](https://github.com/harold-moncaleano/bedrock-mcp-agent)

---

⭐ **¡Si este proyecto te resulta útil, dale una estrella!** ⭐

## 🆘 Soporte

¿Necesitas ayuda? 
- 🐛 Reporta bugs en [Issues](https://github.com/harold-moncaleano/bedrock-mcp-agent/issues)
- 💡 Sugiere features en [Discussions](https://github.com/harold-moncaleano/bedrock-mcp-agent/discussions)
- 📧 Contacto directo: harold.moncaleano@nuvu.cc

## 📈 Roadmap

### Próximas funcionalidades
- [ ] 🔐 Autenticación de usuarios
- [ ] 💾 Persistencia de conversaciones
- [ ] 📁 Carga de archivos y documentos
- [ ] 🎨 Temas personalizables
- [ ] 📊 Dashboard de métricas
- [ ] 🔌 Plugins y extensiones
- [ ] 🌐 Soporte multiidioma
- [ ] 📱 Aplicación móvil nativa

### Integraciones planeadas
- [ ] 🗄️ Base de datos (PostgreSQL/MongoDB)
- [ ] 🔍 Elasticsearch para búsqueda
- [ ] 📊 Grafana para monitoreo
- [ ] 🐳 Docker Compose completo
- [ ] ☸️ Kubernetes deployment
- [ ] 🚀 CI/CD con GitHub Actions