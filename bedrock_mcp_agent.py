#!/usr/bin/env python3
"""
AWS Bedrock MCP Agent
Un agente que integra AWS Bedrock con Model Context Protocol (MCP)
"""

import json
import boto3
from typing import Dict, Any, List, Optional
import logging


class BedrockMCPAgent:
    """
    Agente que integra AWS Bedrock con Model Context Protocol
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
    
    def invoke_model(self, 
                    model_id: str, 
                    prompt: str, 
                    max_tokens: int = 1000,
                    temperature: float = 0.7) -> Dict[str, Any]:
        """
        Invoca un modelo de Bedrock
        
        Args:
            model_id: ID del modelo de Bedrock
            prompt: Prompt para el modelo
            max_tokens: Máximo número de tokens
            temperature: Temperatura para la generación
            
        Returns:
            Respuesta del modelo
        """
        try:
            # Preparar el cuerpo de la solicitud según el modelo
            if 'claude' in model_id.lower():
                body = {
                    "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                    "max_tokens_to_sample": max_tokens,
                    "temperature": temperature,
                    "top_p": 1,
                }
            elif 'titan' in model_id.lower():
                body = {
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": max_tokens,
                        "temperature": temperature,
                        "topP": 1
                    }
                }
            else:
                # Formato genérico
                body = {
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
            
            response = self.bedrock_client.invoke_model(
                body=json.dumps(body),
                modelId=model_id,
                accept='application/json',
                contentType='application/json'
            )
            
            response_body = json.loads(response.get('body').read())
            self.logger.info(f"Modelo {model_id} invocado exitosamente")
            
            return response_body
            
        except Exception as e:
            self.logger.error(f"Error invocando modelo {model_id}: {str(e)}")
            raise
    
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
            
            self.logger.info(f"Se encontraron {len(models)} modelos disponibles")
            return models
            
        except Exception as e:
            self.logger.error(f"Error listando modelos: {str(e)}")
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
        # Extraer el texto generado según el modelo
        if 'claude' in model_id.lower():
            generated_text = bedrock_response.get('completion', '')
        elif 'titan' in model_id.lower():
            results = bedrock_response.get('results', [])
            generated_text = results[0].get('outputText', '') if results else ''
        else:
            # Formato genérico
            generated_text = bedrock_response.get('generated_text', 
                                                bedrock_response.get('completion', ''))
        
        mcp_response = {
            "version": "1.0",
            "model": model_id,
            "response": {
                "text": generated_text,
                "metadata": {
                    "model_id": model_id,
                    "region": self.region_name,
                    "timestamp": bedrock_response.get('ResponseMetadata', {}).get('HTTPHeaders', {}).get('date', ''),
                    "request_id": bedrock_response.get('ResponseMetadata', {}).get('RequestId', '')
                }
            }
        }
        
        return mcp_response


def main():
    """Función principal de demostración"""
    try:
        # Inicializar el agente
        agent = BedrockMCPAgent()
        
        # Listar modelos disponibles
        print("Modelos disponibles:")
        models = agent.list_available_models()
        for model in models[:5]:  # Mostrar solo los primeros 5
            print(f"- {model.get('modelId', 'N/A')}: {model.get('modelName', 'N/A')}")
        
        # Ejemplo de invocación (comentado para evitar errores si no hay credenciales)
        # model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        # response = agent.invoke_model(model_id, "¿Qué es AWS Bedrock?")
        # mcp_response = agent.format_mcp_response(response, model_id)
        # print(json.dumps(mcp_response, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Error en la demostración: {e}")


if __name__ == "__main__":
    main()
