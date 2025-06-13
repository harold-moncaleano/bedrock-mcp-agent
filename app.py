#!/usr/bin/env python3
"""
Flask Backend Server para Bedrock MCP Agent con integración AWS Glue
Servidor web que conecta el frontend React con el agente de AWS Bedrock y Glue Catalog
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from bedrock_mcp_agent import BedrockMCPAgent
from glue_mcp_server import GlueCatalogMCP, integrate_glue_mcp_with_bedrock
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

# Inicializar agentes
agent = None
glue_mcp = None

try:
    agent = BedrockMCPAgent(region_name=AWS_REGION)
    glue_mcp = GlueCatalogMCP()
    # Integrar Glue MCP con Bedrock Agent
    integrate_glue_mcp_with_bedrock(agent)
    logger.info(f"✅ Agente Bedrock MCP inicializado en región: {AWS_REGION}")
    logger.info(f"✅ Glue MCP Server integrado")
    logger.info(f"🤖 Usando modelo fijo: {FIXED_MODEL_ID}")
except Exception as e:
    logger.error(f"❌ Error inicializando agentes: {e}")
    logger.warning("⚠️  Verifica tus credenciales AWS y acceso a Bedrock/Glue")

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
        "bedrock_agent_status": "initialized" if agent else "error",
        "glue_mcp_status": "initialized" if glue_mcp else "error",
        "region": AWS_REGION,
        "model_id": FIXED_MODEL_ID,
        "integrations": ["bedrock", "glue-catalog"]
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
        
        # Detectar si es una consulta relacionada con Glue
        glue_keywords = ['glue', 'database', 'table', 'catalog', 'schema', 'datos', 'metadatos']
        is_glue_query = any(keyword in prompt.lower() for keyword in glue_keywords)
        
        if is_glue_query and glue_mcp:
            # Procesar consulta de Glue junto con Bedrock
            response_text = process_glue_enhanced_query(prompt, temperature, max_tokens)
        else:
            # Procesar consulta normal de Bedrock
            bedrock_response = agent.invoke_model(
                model_id=FIXED_MODEL_ID,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Formatear respuesta según protocolo MCP
            mcp_response = agent.format_mcp_response(bedrock_response, FIXED_MODEL_ID)
            response_text = mcp_response.get('response', {}).get('text', '')
        
        end_time = datetime.now()
        processing_time = int((end_time - start_time).total_seconds() * 1000)
        
        logger.info(f"✅ Respuesta generada en {processing_time}ms")
        
        return jsonify({
            "success": True,
            "response": response_text,
            "model_id": FIXED_MODEL_ID,
            "metadata": {
                "processing_time_ms": processing_time,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "timestamp": datetime.now().isoformat(),
                "glue_enhanced": is_glue_query and glue_mcp is not None
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error en chat: {e}")
        return jsonify({
            "success": False,
            "error": f"Error procesando solicitud: {str(e)}"
        }), 500

def process_glue_enhanced_query(prompt: str, temperature: float, max_tokens: int) -> str:
    """
    Procesa una consulta que puede beneficiarse de datos de Glue Catalog
    """
    try:
        # Obtener contexto de Glue si es relevante
        glue_context = ""
        
        # Palabras clave específicas para diferentes consultas de Glue
        if any(word in prompt.lower() for word in ['listar', 'list', 'mostrar', 'bases de datos', 'databases']):
            logger.info("🔍 Obteniendo lista de bases de datos de Glue...")
            glue_context = agent.glue_list_databases()
        elif any(word in prompt.lower() for word in ['tabla', 'table', 'schema', 'columna']):
            # Buscar si se menciona una tabla específica
            words = prompt.lower().split()
            for i, word in enumerate(words):
                if word in ['tabla', 'table'] and i + 1 < len(words):
                    table_name = words[i + 1]
                    logger.info(f"🔍 Buscando tabla: {table_name}")
                    glue_context = agent.glue_search_tables(table_name)
                    break
        elif any(word in prompt.lower() for word in ['estadísticas', 'stats', 'resumen', 'overview']):
            logger.info("🔍 Obteniendo estadísticas del catálogo...")
            glue_context = agent.glue_get_catalog_stats()
        
        # Construir prompt enriquecido con contexto de Glue
        if glue_context and glue_context != "":
            enhanced_prompt = f"""
Contexto del Catálogo de Datos AWS Glue:
{glue_context}

Pregunta del usuario: {prompt}

Por favor, responde la pregunta del usuario utilizando la información del catálogo de Glue proporcionada arriba cuando sea relevante.
"""
            logger.info("🔧 Usando contexto enriquecido de Glue")
        else:
            enhanced_prompt = prompt
        
        # Invocar Bedrock con el prompt enriquecido
        bedrock_response = agent.invoke_model(
            model_id=FIXED_MODEL_ID,
            prompt=enhanced_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Formatear respuesta
        mcp_response = agent.format_mcp_response(bedrock_response, FIXED_MODEL_ID)
        return mcp_response.get('response', {}).get('text', '')
        
    except Exception as e:
        logger.error(f"Error en consulta enriquecida con Glue: {e}")
        # Fallback a consulta normal
        bedrock_response = agent.invoke_model(
            model_id=FIXED_MODEL_ID,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        mcp_response = agent.format_mcp_response(bedrock_response, FIXED_MODEL_ID)
        return mcp_response.get('response', {}).get('text', '')

@app.route('/api/glue/databases', methods=['GET'])
def get_glue_databases():
    """Endpoint para obtener bases de datos de Glue"""
    try:
        if not glue_mcp:
            return jsonify({
                "success": False,
                "error": "Glue MCP no inicializado"
            }), 500
        
        result = glue_mcp.list_databases()
        return jsonify({
            "success": True,
            "data": json.loads(result)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo bases de datos de Glue: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/glue/tables/<database_name>', methods=['GET'])
def get_glue_tables(database_name):
    """Endpoint para obtener tablas de una base de datos de Glue"""
    try:
        if not glue_mcp:
            return jsonify({
                "success": False,
                "error": "Glue MCP no inicializado"
            }), 500
        
        result = glue_mcp.list_tables(database_name)
        return jsonify({
            "success": True,
            "data": json.loads(result)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo tablas de Glue: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/glue/search', methods=['GET'])
def search_glue_tables():
    """Endpoint para buscar tablas en Glue"""
    try:
        if not glue_mcp:
            return jsonify({
                "success": False,
                "error": "Glue MCP no inicializado"
            }), 500
        
        search_term = request.args.get('q', '')
        if not search_term:
            return jsonify({
                "success": False,
                "error": "Parámetro de búsqueda 'q' requerido"
            }), 400
        
        result = glue_mcp.search_tables(search_term)
        return jsonify({
            "success": True,
            "data": json.loads(result)
        })
        
    except Exception as e:
        logger.error(f"Error buscando tablas en Glue: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/glue/stats', methods=['GET'])
def get_glue_stats():
    """Endpoint para obtener estadísticas del catálogo de Glue"""
    try:
        if not glue_mcp:
            return jsonify({
                "success": False,
                "error": "Glue MCP no inicializado"
            }), 500
        
        result = glue_mcp.get_catalog_statistics()
        return jsonify({
            "success": True,
            "data": json.loads(result)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de Glue: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/glue/table/<database_name>/<table_name>', methods=['GET'])
def get_glue_table_details(database_name, table_name):
    """Endpoint para obtener detalles de una tabla específica"""
    try:
        if not glue_mcp:
            return jsonify({
                "success": False,
                "error": "Glue MCP no inicializado"
            }), 500
        
        result = glue_mcp.get_table_info(database_name, table_name)
        return jsonify({
            "success": True,
            "data": json.loads(result)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo detalles de tabla: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/config', methods=['GET'])
def get_config():
    """Obtener configuración actual del servidor"""
    return jsonify({
        "model_id": FIXED_MODEL_ID,
        "region": AWS_REGION,
        "bedrock_agent_initialized": agent is not None,
        "glue_mcp_initialized": glue_mcp is not None,
        "max_tokens_limit": 4000,
        "temperature_range": [0, 1],
        "default_temperature": 0.7,
        "default_max_tokens": 1000,
        "features": {
            "bedrock_chat": True,
            "glue_catalog": glue_mcp is not None,
            "enhanced_queries": glue_mcp is not None
        }
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
    
    print("🚀 Iniciando Bedrock MCP Agent con integración Glue...")
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
    
    if not glue_mcp:
        print("⚠️  ADVERTENCIA: Glue MCP no inicializado")
        print("🔧 Verifica acceso a AWS Glue")
    else:
        print("✅ Glue MCP integrado")
        print("🔍 Funcionalidades disponibles:")
        print("   - Chat con contexto de catálogo de datos")
        print("   - Consultas enriquecidas sobre bases de datos y tablas")
        print("   - API endpoints para Glue Catalog")
    
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
