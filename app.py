#!/usr/bin/env python3
"""
Flask Backend Server para Bedrock MCP Agent conversacional con integración AWS Glue
Servidor web que mantiene contexto conversacional entre el frontend y AWS Bedrock + Glue Catalog
"""

from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
from bedrock_mcp_agent import BedrockMCPAgent
from glue_mcp_server import GlueCatalogMCP, integrate_glue_mcp_with_bedrock
import os
import json
import logging
import uuid
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
app.secret_key = os.getenv('SECRET_KEY', 'bedrock-mcp-secret-key-conversational')
CORS(app, supports_credentials=True)  # Habilitar CORS con soporte para sesiones

# Configuración
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
FIXED_MODEL_ID = 'anthropic.claude-3-sonnet-20240229-v1:0'  # Modelo fijo

# Diccionario para mantener agentes por sesión
session_agents = {}
glue_mcp = None

# Inicializar Glue MCP (compartido entre todas las sesiones)
try:
    glue_mcp = GlueCatalogMCP()
    logger.info(f"✅ Glue MCP Server inicializado en región: {AWS_REGION}")
except Exception as e:
    logger.error(f"❌ Error inicializando Glue MCP: {e}")

def get_session_agent():
    """
    Obtiene o crea un agente para la sesión actual
    """
    # Crear ID de sesión si no existe
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        logger.info(f"🆔 Nueva sesión creada: {session['session_id'][:8]}...")
    
    session_id = session['session_id']
    
    # Crear agente si no existe para esta sesión
    if session_id not in session_agents:
        try:
            agent = BedrockMCPAgent(region_name=AWS_REGION)
            if glue_mcp:
                integrate_glue_mcp_with_bedrock(agent)
            session_agents[session_id] = agent
            logger.info(f"✅ Nuevo agente conversacional creado para sesión: {session_id[:8]}...")
        except Exception as e:
            logger.error(f"❌ Error creando agente para sesión {session_id[:8]}: {e}")
            return None
    
    return session_agents.get(session_id)

@app.route('/')
def index():
    """Página principal - servir el frontend"""
    return send_from_directory('.', 'frontend.html')

@app.route('/health')
def health_check():
    """Endpoint de health check"""
    agent = get_session_agent()
    return jsonify({
        "status": "healthy" if agent else "error",
        "timestamp": datetime.now().isoformat(),
        "bedrock_agent_status": "initialized" if agent else "error",
        "glue_mcp_status": "initialized" if glue_mcp else "error",
        "region": AWS_REGION,
        "model_id": FIXED_MODEL_ID,
        "integrations": ["bedrock", "glue-catalog"],
        "conversational": True,
        "session_id": session.get('session_id', 'none')[:8] + "..." if session.get('session_id') else 'none'
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint principal para chat conversacional con modelos de Bedrock"""
    try:
        agent = get_session_agent()
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
        
        user_message = data.get('prompt', '').strip()
        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 1000)
        
        # Validaciones
        if not user_message:
            return jsonify({
                "success": False,
                "error": "El mensaje es requerido"
            }), 400
        
        if not isinstance(temperature, (int, float)) or not (0 <= temperature <= 1):
            temperature = 0.7
            
        if not isinstance(max_tokens, int) or not (1 <= max_tokens <= 4000):
            max_tokens = 1000
        
        logger.info(f"📨 Procesando mensaje conversacional: {user_message[:50]}...")
        start_time = datetime.now()
        
        # Detectar si es una consulta relacionada con Glue
        glue_keywords = ['glue', 'database', 'table', 'catalog', 'schema', 'datos', 'metadatos', 'columna', 'bd', 'base de datos']
        is_glue_query = any(keyword in user_message.lower() for keyword in glue_keywords)
        
        glue_context = ""
        if is_glue_query and glue_mcp:
            glue_context = get_glue_context_for_query(user_message, agent)
        
        # Invocar modelo conversacional con contexto
        bedrock_response = agent.invoke_conversational_model(
            model_id=FIXED_MODEL_ID,
            user_message=user_message,
            glue_context=glue_context,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        end_time = datetime.now()
        processing_time = int((end_time - start_time).total_seconds() * 1000)
        
        # Formatear respuesta según protocolo MCP
        mcp_response = agent.format_mcp_response(bedrock_response, FIXED_MODEL_ID)
        response_text = mcp_response.get('response', {}).get('text', '')
        
        # Obtener información conversacional
        conversation_summary = agent.get_conversation_summary()
        
        logger.info(f"✅ Respuesta conversacional generada en {processing_time}ms")
        
        return jsonify({
            "success": True,
            "response": response_text,
            "model_id": FIXED_MODEL_ID,
            "metadata": {
                "processing_time_ms": processing_time,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "timestamp": datetime.now().isoformat(),
                "glue_enhanced": bool(glue_context),
                "conversation_length": conversation_summary["total_messages"],
                "has_context": conversation_summary["conversation_active"],
                "session_id": session.get('session_id', 'unknown')[:8] + "..."
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error en chat conversacional: {e}")
        return jsonify({
            "success": False,
            "error": f"Error procesando solicitud: {str(e)}"
        }), 500

def get_glue_context_for_query(user_message: str, agent) -> str:
    """
    Obtiene contexto relevante de Glue según la consulta del usuario
    """
    try:
        glue_context = ""
        message_lower = user_message.lower()
        
        # Detectar tipo de consulta y obtener contexto apropiado
        if any(word in message_lower for word in ['listar', 'list', 'mostrar', 'todas las', 'bases de datos', 'databases']):
            logger.info("🔍 Obteniendo lista de bases de datos...")
            glue_context = agent.glue_list_databases()
            
        elif any(word in message_lower for word in ['tabla', 'table', 'tablas', 'tables']):
            # Si menciona una base de datos específica
            words = message_lower.split()
            db_name = None
            for i, word in enumerate(words):
                if word in ['database', 'bd', 'base'] and i + 1 < len(words):
                    db_name = words[i + 1].strip('",.')
                    break
            
            if db_name:
                logger.info(f"🔍 Obteniendo tablas de la base de datos: {db_name}")
                glue_context = agent.glue_list_tables(db_name)
            else:
                # Buscar por nombre de tabla mencionada
                for word in words:
                    if len(word) > 3 and word not in ['tabla', 'table', 'datos', 'data']:
                        logger.info(f"🔍 Buscando tabla: {word}")
                        search_result = agent.glue_search_tables(word)
                        if search_result and '"total_found"' in search_result:
                            glue_context = search_result
                            break
                        
        elif any(word in message_lower for word in ['estadísticas', 'stats', 'resumen', 'overview', 'cuántas', 'cuantas']):
            logger.info("🔍 Obteniendo estadísticas del catálogo...")
            glue_context = agent.glue_get_catalog_stats()
            
        elif any(word in message_lower for word in ['buscar', 'search', 'encuentra', 'find']):
            # Extraer término de búsqueda
            search_terms = []
            words = message_lower.split()
            for i, word in enumerate(words):
                if word in ['buscar', 'search', 'encuentra', 'find'] and i + 1 < len(words):
                    search_terms.extend(words[i+1:i+3])  # Siguiente 1-2 palabras
                elif word.startswith('"') and word.endswith('"'):
                    search_terms.append(word.strip('"'))
            
            if search_terms:
                search_term = search_terms[0]
                logger.info(f"🔍 Buscando tablas con término: {search_term}")
                glue_context = agent.glue_search_tables(search_term)
        
        return glue_context
        
    except Exception as e:
        logger.error(f"Error obteniendo contexto de Glue: {e}")
        return ""

@app.route('/api/conversation/clear', methods=['POST'])
def clear_conversation():
    """Endpoint para limpiar el historial conversacional"""
    try:
        agent = get_session_agent()
        if agent:
            agent.clear_conversation()
            logger.info(f"🧹 Conversación limpiada para sesión: {session.get('session_id', 'unknown')[:8]}...")
            return jsonify({
                "success": True,
                "message": "Historial conversacional limpiado"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Agente no disponible"
            }), 500
            
    except Exception as e:
        logger.error(f"Error limpiando conversación: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/conversation/summary', methods=['GET'])
def get_conversation_summary():
    """Endpoint para obtener resumen de la conversación actual"""
    try:
        agent = get_session_agent()
        if agent:
            summary = agent.get_conversation_summary()
            return jsonify({
                "success": True,
                "summary": summary
            })
        else:
            return jsonify({
                "success": False,
                "error": "Agente no disponible"
            }), 500
            
    except Exception as e:
        logger.error(f"Error obteniendo resumen de conversación: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Endpoints de Glue
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

@app.route('/api/config', methods=['GET'])
def get_config():
    """Obtener configuración actual del servidor"""
    agent = get_session_agent()
    conversation_summary = agent.get_conversation_summary() if agent else {}
    
    return jsonify({
        "model_id": FIXED_MODEL_ID,
        "region": AWS_REGION,
        "bedrock_agent_initialized": agent is not None,
        "glue_mcp_initialized": glue_mcp is not None,
        "max_tokens_limit": 4000,
        "temperature_range": [0, 1],
        "default_temperature": 0.7,
        "default_max_tokens": 1000,
        "conversational": True,
        "features": {
            "bedrock_chat": True,
            "glue_catalog": glue_mcp is not None,
            "enhanced_queries": glue_mcp is not None,
            "conversation_memory": True,
            "session_management": True
        },
        "conversation": conversation_summary
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
    
    print("🚀 Iniciando Bedrock MCP Agent CONVERSACIONAL...")
    print(f"🌐 Servidor: http://{host}:{port}")
    print(f"🔧 Debug: {debug}")
    print(f"🌍 Región AWS: {AWS_REGION}")
    print(f"🤖 Modelo: {FIXED_MODEL_ID}")
    print("💬 Modo: CONVERSACIONAL (mantiene contexto)")
    
    if not glue_mcp:
        print("⚠️  ADVERTENCIA: Glue MCP no inicializado")
    else:
        print("✅ Glue MCP integrado")
        
    print("🔍 Funcionalidades conversacionales:")
    print("   - Memoria de conversación por sesión")
    print("   - Contexto automático en todas las respuestas")
    print("   - Integración inteligente con catálogo de datos")
    print("   - Gestión automática de sesiones")
    
    print("-" * 60)
    
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
    except Exception as e:
        logger.error(f"❌ Error iniciando servidor: {e}")
