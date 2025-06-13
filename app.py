#!/usr/bin/env python3
"""
Flask Backend Server para Bedrock MCP Agent
Servidor web que conecta el frontend React con el agente de AWS Bedrock
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from bedrock_mcp_agent import BedrockMCPAgent
import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__)
CORS(app)  # Habilitar CORS para requests del frontend

# Configuración
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
FIXED_MODEL_ID = 'anthropic.claude-3-sonnet-20240229-v1:0'  # Modelo fijo

# Inicializar el agente Bedrock MCP
agent = None
try:
    agent = BedrockMCPAgent(region_name=AWS_REGION)
    logger.info(f"✅ Agente Bedrock MCP inicializado en región: {AWS_REGION}")
    logger.info(f"🤖 Usando modelo fijo: {FIXED_MODEL_ID}")
except Exception as e:
    logger.error(f"❌ Error inicializando agente Bedrock: {e}")
    logger.warning("⚠️  Verifica tus credenciales AWS y acceso a Bedrock")

@app.route('/')
def index():
    """Página principal - servir el frontend"""
    return send_from_directory('.', 'frontend.html')

@app.route('/health')
def health_check():
    """Endpoint de health check"""
    return jsonify({
        "status": "healthy" if agent else "error",
        "timestamp": datetime.now().isoformat(),
        "agent_status": "initialized" if agent else "error",
        "region": AWS_REGION,
        "model_id": FIXED_MODEL_ID
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint principal para chat con modelos de Bedrock"""
    try:
        if not agent:
            return jsonify({
                "success": False,
                "error": "Agente Bedrock no inicializado. Verifica credenciales AWS."
            }), 500
        
        # Validar datos de entrada
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "No se recibieron datos JSON"
            }), 400
        
        prompt = data.get('prompt', '').strip()
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 1000)
        
        # Validaciones
        if not prompt:
            return jsonify({
                "success": False,
                "error": "El prompt es requerido"
            }), 400
        
        if not isinstance(temperature, (int, float)) or not (0 <= temperature <= 1):
            temperature = 0.7
            
        if not isinstance(max_tokens, int) or not (1 <= max_tokens <= 4000):
            max_tokens = 1000
        
        logger.info(f"📨 Procesando mensaje: {prompt[:50]}...")
        start_time = datetime.now()
        
        # Invocar el modelo de Bedrock con ID fijo
        bedrock_response = agent.invoke_model(
            model_id=FIXED_MODEL_ID,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        end_time = datetime.now()
        processing_time = int((end_time - start_time).total_seconds() * 1000)
        
        # Formatear respuesta según protocolo MCP
        mcp_response = agent.format_mcp_response(bedrock_response, FIXED_MODEL_ID)
        
        # Extraer texto de respuesta
        response_text = mcp_response.get('response', {}).get('text', '')
        
        logger.info(f"✅ Respuesta generada en {processing_time}ms")
        
        return jsonify({
            "success": True,
            "response": response_text,
            "model_id": FIXED_MODEL_ID,
            "metadata": {
                "processing_time_ms": processing_time,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "timestamp": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error en chat: {e}")
        return jsonify({
            "success": False,
            "error": f"Error procesando solicitud: {str(e)}"
        }), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """Obtener configuración actual del servidor"""
    return jsonify({
        "model_id": FIXED_MODEL_ID,
        "region": AWS_REGION,
        "agent_initialized": agent is not None,
        "max_tokens_limit": 4000,
        "temperature_range": [0, 1],
        "default_temperature": 0.7,
        "default_max_tokens": 1000
    })

@app.errorhandler(404)
def not_found(error):
    """Manejador de error 404"""
    return jsonify({
        "success": False,
        "error": "Endpoint no encontrado"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Manejador de error 500"""
    logger.error(f"Error interno del servidor: {error}")
    return jsonify({
        "success": False,
        "error": "Error interno del servidor"
    }), 500

if __name__ == '__main__':
    # Configuración del servidor
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    print("🚀 Iniciando Bedrock MCP Agent...")
    print(f"🌐 Servidor: http://{host}:{port}")
    print(f"🔧 Debug: {debug}")
    print(f"🌍 Región AWS: {AWS_REGION}")
    print(f"🤖 Modelo: {FIXED_MODEL_ID}")
    
    if not agent:
        print("⚠️  ADVERTENCIA: Agente Bedrock no inicializado")
        print("🔧 Verifica tus credenciales AWS:")
        print("   1. Archivo .env con AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY")
        print("   2. O AWS CLI configurado: aws configure")
        print("   3. O IAM Role si ejecutas en EC2")
        print("   4. Acceso habilitado en AWS Bedrock Console")
    else:
        print("✅ Agente Bedrock listo")
    
    print("-" * 50)
    
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
    except Exception as e:
        logger.error(f"❌ Error iniciando servidor: {e}")
