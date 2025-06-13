#!/usr/bin/env python3
"""
AWS Bedrock MCP Agent con soporte conversacional
Un agente que integra AWS Bedrock con Model Context Protocol (MCP) manteniendo contexto
"""

import json
import boto3
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime


class BedrockMCPAgent:
    """
    Agente que integra AWS Bedrock con Model Context Protocol manteniendo contexto conversacional
    """
    
    def __init__(self, region_name: str = 'us-east-1'):
        """
        Inicializa el agente Bedrock MCP
        
        Args:
            region_name: Región de AWS donde se ejecutará Bedrock
        """
        self.region_name = region_name
        self.bedrock_client = boto3.client(
            service_name='bedrock-runtime',
            region_name=region_name
        )
        self.logger = self._setup_logger()
        
        # Contexto conversacional
        self.conversation_history = []
        self.system_prompt = """Eres un asistente inteligente especializado en datos y análisis. Tienes acceso al catálogo de AWS Glue y puedes ayudar con consultas sobre bases de datos, tablas, esquemas y análisis de datos. 

Mantén un tono profesional pero amigable. Cuando te proporcionen información del catálogo de Glue, úsala para dar respuestas precisas y útiles. Si no tienes información específica sobre algo, dilo claramente.

Recuerda el contexto de nuestra conversación anterior para dar respuestas coherentes y útiles."""
        
    def _setup_logger(self) -> logging.Logger:
        """Configura el logger para el agente"""
        logger = logging.getLogger('bedrock-mcp-agent')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def add_message_to_history(self, role: str, content: str):
        """
        Añade un mensaje al historial conversacional
        
        Args:
            role: 'user' o 'assistant'
            content: Contenido del mensaje
        """
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Mantener solo los últimos 20 mensajes para no exceder límites
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def clear_conversation(self):
        """Limpia el historial conversacional"""
        self.conversation_history = []
        self.logger.info("🧹 Historial conversacional limpiado")
    
    def get_conversation_context(self) -> str:
        """
        Obtiene el contexto conversacional formateado
        
        Returns:
            String con el historial de la conversación
        """
        if not self.conversation_history:
            return ""
        
        context = "\nContexto de la conversación anterior:\n"
        for msg in self.conversation_history[-10:]:  # Últimos 10 mensajes
            role_label = "Usuario" if msg["role"] == "user" else "Asistente"
            context += f"{role_label}: {msg['content']}\n"
        
        return context
    
    def invoke_conversational_model(self, 
                                  model_id: str, 
                                  user_message: str, 
                                  glue_context: str = "",
                                  max_tokens: int = 1000,
                                  temperature: float = 0.7) -> Dict[str, Any]:
        """
        Invoca un modelo de Bedrock manteniendo contexto conversacional
        
        Args:
            model_id: ID del modelo de Bedrock
            user_message: Mensaje del usuario
            glue_context: Contexto adicional de Glue (opcional)
            max_tokens: Máximo número de tokens
            temperature: Temperatura para la generación
            
        Returns:
            Respuesta del modelo
        """
        try:
            # Construir prompt completo con contexto
            conversation_context = self.get_conversation_context()
            
            # Construir el prompt con toda la información
            full_prompt = self.system_prompt
            
            if glue_context:
                full_prompt += f"\n\nInformación del catálogo de datos AWS Glue:\n{glue_context}"
            
            if conversation_context:
                full_prompt += conversation_context
            
            full_prompt += f"\n\nUsuario: {user_message}\nAsistente:"
            
            # Preparar el cuerpo de la solicitud según el modelo
            if 'claude-3' in model_id.lower():
                # Claude 3 - Formato de mensajes
                messages = [
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ]
                
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": messages
                }
            elif 'claude' in model_id.lower():
                # Claude 2 y versiones anteriores
                body = {
                    "prompt": f"\n\nHuman: {full_prompt}\n\nAssistant:",
                    "max_tokens_to_sample": max_tokens,
                    "temperature": temperature,
                    "top_p": 1,
                }
            elif 'titan' in model_id.lower():
                body = {
                    "inputText": full_prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": max_tokens,
                        "temperature": temperature,
                        "topP": 1
                    }
                }
            else:
                # Formato genérico
                body = {
                    "prompt": full_prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
            
            self.logger.info(f"🚀 Invocando modelo conversacional: {model_id}")
            
            response = self.bedrock_client.invoke_model(
                body=json.dumps(body),
                modelId=model_id,
                accept='application/json',
                contentType='application/json'
            )
            
            response_body = json.loads(response.get('body').read())
            
            # Extraer la respuesta del modelo
            assistant_response = self._extract_response_text(response_body, model_id)
            
            # Añadir mensajes al historial
            self.add_message_to_history("user", user_message)
            self.add_message_to_history("assistant", assistant_response)
            
            self.logger.info(f"✅ Respuesta conversacional generada exitosamente")
            
            return response_body
            
        except Exception as e:
            self.logger.error(f"❌ Error en modelo conversacional {model_id}: {str(e)}")
            raise
    
    def _extract_response_text(self, bedrock_response: Dict[str, Any], model_id: str) -> str:
        """
        Extrae el texto de respuesta según el tipo de modelo
        
        Args:
            bedrock_response: Respuesta de Bedrock
            model_id: ID del modelo usado
            
        Returns:
            Texto de la respuesta
        """
        if 'claude-3' in model_id.lower():
            # Claude 3 usa formato de mensajes
            content = bedrock_response.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
        elif 'claude' in model_id.lower():
            # Claude 2 y anteriores
            return bedrock_response.get('completion', '')
        elif 'titan' in model_id.lower():
            results = bedrock_response.get('results', [])
            return results[0].get('outputText', '') if results else ''
        else:
            # Formato genérico
            return bedrock_response.get('generated_text', 
                                     bedrock_response.get('completion', ''))
        return ''
    
    def invoke_model(self, 
                    model_id: str, 
                    prompt: str, 
                    max_tokens: int = 1000,
                    temperature: float = 0.7) -> Dict[str, Any]:
        """
        Método legacy para compatibilidad - redirige a conversacional
        """
        return self.invoke_conversational_model(
            model_id=model_id,
            user_message=prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """
        Lista los modelos disponibles en Bedrock
        
        Returns:
            Lista de modelos disponibles
        """
        try:
            bedrock_client = boto3.client(
                service_name='bedrock',
                region_name=self.region_name
            )
            
            response = bedrock_client.list_foundation_models()
            models = response.get('modelSummaries', [])
            
            self.logger.info(f"📋 Se encontraron {len(models)} modelos disponibles")
            return models
            
        except Exception as e:
            self.logger.error(f"❌ Error listando modelos: {str(e)}")
            raise
    
    def format_mcp_response(self, 
                           bedrock_response: Dict[str, Any], 
                           model_id: str) -> Dict[str, Any]:
        """
        Formatea la respuesta de Bedrock para el protocolo MCP
        
        Args:
            bedrock_response: Respuesta de Bedrock
            model_id: ID del modelo usado
            
        Returns:
            Respuesta formateada para MCP
        """
        # Extraer el texto generado
        generated_text = self._extract_response_text(bedrock_response, model_id)
        
        mcp_response = {
            "version": "1.0",
            "model": model_id,
            "response": {
                "text": generated_text,
                "metadata": {
                    "model_id": model_id,
                    "region": self.region_name,
                    "usage": bedrock_response.get('usage', {}),
                    "conversation_length": len(self.conversation_history),
                    "has_context": len(self.conversation_history) > 0
                }
            }
        }
        
        return mcp_response
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen del estado conversacional
        
        Returns:
            Información sobre la conversación actual
        """
        return {
            "total_messages": len(self.conversation_history),
            "conversation_active": len(self.conversation_history) > 0,
            "last_message_time": self.conversation_history[-1]["timestamp"] if self.conversation_history else None,
            "messages_preview": [
                {
                    "role": msg["role"],
                    "content": msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"],
                    "timestamp": msg["timestamp"]
                }
                for msg in self.conversation_history[-3:]  # Últimos 3 mensajes
            ]
        }


def main():
    """Función principal de demostración"""
    try:
        print("🧠 Bedrock MCP Agent Conversacional - Demo")
        print("=" * 50)
        
        # Inicializar el agente
        agent = BedrockMCPAgent()
        print("✅ Agente conversacional inicializado")
        
        # Ejemplo de conversación
        print("\n💬 Ejemplo de conversación:")
        model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        
        # Primera pregunta
        print("\n👤 Usuario: ¿Qué es AWS Bedrock?")
        print("🤖 Asistente: [Simularía respuesta sobre Bedrock]")
        
        # Segunda pregunta con contexto
        print("\n👤 Usuario: ¿Y cómo se integra con Glue?")
        print("🤖 Asistente: [Respondería considerando el contexto anterior]")
        
        # Mostrar estado conversacional
        summary = agent.get_conversation_summary()
        print(f"\n📊 Estado conversacional: {summary['total_messages']} mensajes")
        
        print("✅ Demo completada")
        
    except Exception as e:
        print(f"❌ Error en la demostración: {e}")


if __name__ == "__main__":
    main()
