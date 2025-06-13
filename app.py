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
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'bedrock-mcp-secret-key')
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')

# Inicializar el agente Bedrock MCP
try:
    agent = BedrockMCPAgent(region_name=AWS_REGION)
    logger.info(f"Agente Bedrock MCP inicializado en región: {AWS_REGION}")
except Exception as e:
    logger.error(f"Error inicializando agente Bedrock: {e}")
    agent = None

# Modelos soportados con metadata
SUPPORTED_MODELS = {
    "anthropic.claude-3-sonnet-20240229-v1:0": {
        "name": "Claude 3 Sonnet",
        "provider": "Anthropic",
        "description": "Modelo balanceado para tareas complejas"
    },
    "anthropic.claude-3-haiku-20240307-v1:0": {
        "name": "Claude 3 Haiku",
        "provider": "Anthropic", 
        "description": "Modelo rápido y eficiente"
    },
    "amazon.titan-text-premier-v1:0": {
        "name": "Titan Text Premier",
        "provider": "Amazon",
        "description": "Modelo de texto avanzado de Amazon"
    },
    "amazon.titan-text-express-v1": {
        "name": "Titan Text Express",
        "provider": "Amazon",
        "description": "Modelo de texto rápido de Amazon"
    },
    "meta.llama2-70b-chat-v1": {
        "name": "Llama 2 70B Chat",
        "provider": "Meta",
        "description": "Modelo conversacional de Meta"
    }
}

@app.route('/')
def index():
    """Página principal - servir el frontend"""
    return send_from_directory('.', 'frontend.html')

@app.route('/health')
def health_check():
    """Endpoint de health check"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_status": "initialized" if agent else "error",
        "region": AWS_REGION
    })

@app.route('/api/models', methods=['GET'])
def get_models():
    """Obtener lista de modelos disponibles"""
    try:
        if not agent:
            return jsonify({
                "success": False, 
                "error": "Agente Bedrock no inicializado"
            }), 500
        
        # Intentar obtener modelos desde AWS
        try:
            aws_models = agent.list_available_models()
            available_models = []
            
            for model in aws_models:
                model_id = model.get('modelId', '')
                if model_id in SUPPORTED_MODELS:
                    model_info = SUPPORTED_MODELS[model_id].copy()
                    model_info['id'] = model_id
                    model_info['status'] = 'available'
                    available_models.append(model_info)
            
            logger.info(f"Se encontraron {len(available_models)} modelos disponibles")
            
        except Exception as e:
            logger.warning(f"No se pudieron obtener modelos de AWS: {e}")
            # Devolver modelos por defecto
            available_models = []
            for model_id, info in SUPPORTED_MODELS.items():
                model_info = info.copy()
                model_info['id'] = model_id
                model_info['status'] = 'unknown'
                available_models.append(model_info)
        
        return jsonify({
            "success": True,
            "models": available_models,
            "region": AWS_REGION
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo modelos: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint principal para chat con modelos de Bedrock"""
    try:
        if not agent:
            return jsonify({
                "success": False,
                "error": "Agente Bedrock no inicializado"
            }), 500
        
        # Validar datos de entrada
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "No se recibieron datos JSON"
            }), 400
        
        model_id = data.get('model_id')
        prompt = data.get('prompt')
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 1000)
        
        # Validaciones
        if not model_id:
            return jsonify({
                "success": False,
                "error": "model_id es requerido"
            }), 400
            
        if not prompt:
            return jsonify({
                "success": False,
                "error": "prompt es requerido"
            }), 400
        
        if not isinstance(temperature, (int, float)) or not (0 <= temperature <= 1):
            return jsonify({
                "success": False,
                "error": "temperature debe estar entre 0 y 1"
            }), 400
            
        if not isinstance(max_tokens, int) or not (1 <= max_tokens <= 4000):
            return jsonify({
                "success": False,
                "error": "max_tokens debe estar entre 1 y 4000"
            }), 400
        
        logger.info(f"Procesando chat con modelo: {model_id}")
        start_time = datetime.now()
        
        # Invocar el modelo de Bedrock
        bedrock_response = agent.invoke_model(
            model_id=model_id,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        end_time = datetime.now()
        processing_time = int((end_time - start_time).total_seconds() * 1000)
        
        # Formatear respuesta según protocolo MCP
        mcp_response = agent.format_mcp_response(bedrock_response, model_id)
        
        # Añadir metadata adicional
        mcp_response['response']['metadata']['processing_time_ms'] = processing_time
        mcp_response['response']['metadata']['estimated_tokens'] = len(prompt.split()) + len(mcp_response['response']['text'].split())
        
        logger.info(f"Chat procesado exitosamente en {processing_time}ms")
        
        return jsonify({
            "success": True,
            "response": mcp_response,
            "processing_time": processing_time
        })
        
    except Exception as e:
        logger.error(f"Error en chat: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """Obtener configuración actual del servidor"""
    return jsonify({
        "region": AWS_REGION,
        "supported_models": list(SUPPORTED_MODELS.keys()),
        "agent_initialized": agent is not None,
        "max_tokens_limit": 4000,
        "temperature_range": [0, 1]
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
    
    logger.info(f"Iniciando servidor Flask en {host}:{port}")
    logger.info(f"Modo debug: {debug}")
    logger.info(f"Región AWS: {AWS_REGION}")
    
    if not agent:
        logger.warning("⚠️  Agente Bedrock no inicializado - revisa credenciales AWS")
    else:
        logger.info("✅ Agente Bedrock inicializado correctamente")
    
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
    except Exception as e:
        logger.error(f"Error iniciando servidor: {e}")
