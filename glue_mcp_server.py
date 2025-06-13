#!/usr/bin/env python3
"""
MCP Server para AWS Glue Catalog integrado con Bedrock MCP Agent
Proporciona herramientas para consultar el catálogo de datos de AWS Glue
"""

import json
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Any, Dict, List, Optional
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

try:
    from mcp.server.fastmcp import FastMCP
    mcp_available = True
except ImportError:
    print("⚠️  Módulo MCP no disponible. Instala con: pip install mcp")
    mcp_available = False

class GlueCatalogMCP:
    """
    Clase principal para el servidor MCP de AWS Glue Catalog
    """
    
    def __init__(self):
        self.aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        self.mcp = FastMCP("AWS Glue Catalog Server") if mcp_available else None
        self._setup_tools()
    
    def get_glue_client(self):
        """
        Crea y retorna un cliente de AWS Glue con las credenciales configuradas.
        """
        try:
            # Usar credenciales desde variables de entorno o AWS CLI
            client = boto3.client('glue', region_name=self.aws_region)
            return client
        except Exception as e:
            print(f"❌ Error creando cliente de Glue: {e}")
            return None
    
    def _setup_tools(self):
        """Configura las herramientas MCP"""
        if not self.mcp:
            return
            
        @self.mcp.tool()
        def list_glue_databases():
            """
            Lista todas las bases de datos en el catálogo de AWS Glue.
            """
            return self.list_databases()
        
        @self.mcp.tool()
        def get_database_details(database_name: str):
            """
            Obtiene los detalles de una base de datos específica en el catálogo de Glue.
            
            Args:
                database_name: Nombre de la base de datos
            """
            return self.get_database_info(database_name)
        
        @self.mcp.tool()
        def list_tables_in_database(database_name: str):
            """
            Lista todas las tablas en una base de datos específica del catálogo de Glue.
            
            Args:
                database_name: Nombre de la base de datos
            """
            return self.list_tables(database_name)
        
        @self.mcp.tool()
        def get_table_details(database_name: str, table_name: str):
            """
            Obtiene los detalles completos de una tabla específica.
            
            Args:
                database_name: Nombre de la base de datos
                table_name: Nombre de la tabla
            """
            return self.get_table_info(database_name, table_name)
        
        @self.mcp.tool()
        def search_tables_by_name(search_term: str):
            """
            Busca tablas en todas las bases de datos que contengan el término de búsqueda.
            
            Args:
                search_term: Término a buscar en los nombres de las tablas
            """
            return self.search_tables(search_term)
        
        @self.mcp.tool()
        def get_glue_catalog_stats():
            """
            Obtiene estadísticas generales del catálogo de Glue.
            """
            return self.get_catalog_statistics()
    
    def list_databases(self) -> str:
        """Lista todas las bases de datos en el catálogo de AWS Glue"""
        try:
            glue_client = self.get_glue_client()
            if not glue_client:
                return json.dumps({
                    "error": "No se pudo crear el cliente de AWS Glue. Verifica las credenciales.",
                    "status": "failed"
                }, indent=2)

            response = glue_client.get_databases()
            
            databases = []
            for db in response.get('DatabaseList', []):
                databases.append({
                    "name": db.get('Name', ''),
                    "description": db.get('Description', 'Sin descripción'),
                    "location_uri": db.get('LocationUri', ''),
                    "create_time": str(db.get('CreateTime', '')),
                    "parameters": db.get('Parameters', {})
                })
            
            return json.dumps({
                "status": "success",
                "region": self.aws_region,
                "total_databases": len(databases),
                "databases": databases
            }, indent=2, default=str)
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            return json.dumps({
                "error": f"Error de AWS Glue [{error_code}]: {error_message}",
                "status": "failed"
            }, indent=2)
        
        except NoCredentialsError:
            return json.dumps({
                "error": "Credenciales de AWS no encontradas o inválidas",
                "status": "failed"
            }, indent=2)
        
        except Exception as e:
            return json.dumps({
                "error": f"Error inesperado: {str(e)}",
                "status": "failed"
            }, indent=2)
    
    def get_database_info(self, database_name: str) -> str:
        """Obtiene información detallada de una base de datos"""
        try:
            glue_client = self.get_glue_client()
            if not glue_client:
                return json.dumps({
                    "error": "No se pudo crear el cliente de AWS Glue.",
                    "status": "failed"
                }, indent=2)

            response = glue_client.get_database(Name=database_name)
            
            db = response.get('Database', {})
            database_info = {
                "name": db.get('Name', ''),
                "description": db.get('Description', 'Sin descripción'),
                "location_uri": db.get('LocationUri', ''),
                "create_time": str(db.get('CreateTime', '')),
                "parameters": db.get('Parameters', {}),
                "catalog_id": db.get('CatalogId', '')
            }
            
            return json.dumps({
                "status": "success",
                "database": database_info
            }, indent=2, default=str)
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            return json.dumps({
                "error": f"Error de AWS Glue [{error_code}]: {error_message}",
                "status": "failed"
            }, indent=2)
        
        except Exception as e:
            return json.dumps({
                "error": f"Error inesperado: {str(e)}",
                "status": "failed"
            }, indent=2)
    
    def list_tables(self, database_name: str) -> str:
        """Lista todas las tablas en una base de datos específica"""
        try:
            glue_client = self.get_glue_client()
            if not glue_client:
                return json.dumps({
                    "error": "No se pudo crear el cliente de AWS Glue.",
                    "status": "failed"
                }, indent=2)

            # Usar paginación para obtener todas las tablas
            paginator = glue_client.get_paginator('get_tables')
            page_iterator = paginator.paginate(DatabaseName=database_name)
            
            tables = []
            for page in page_iterator:
                for table in page.get('TableList', []):
                    tables.append({
                        "name": table.get('Name', ''),
                        "database_name": table.get('DatabaseName', ''),
                        "owner": table.get('Owner', ''),
                        "create_time": str(table.get('CreateTime', '')),
                        "update_time": str(table.get('UpdateTime', '')),
                        "table_type": table.get('TableType', ''),
                        "storage_descriptor": {
                            "location": table.get('StorageDescriptor', {}).get('Location', ''),
                            "input_format": table.get('StorageDescriptor', {}).get('InputFormat', ''),
                            "output_format": table.get('StorageDescriptor', {}).get('OutputFormat', ''),
                            "serde_info": table.get('StorageDescriptor', {}).get('SerdeInfo', {})
                        },
                        "parameters": table.get('Parameters', {}),
                        "partition_keys": [
                            {
                                "name": key.get('Name', ''),
                                "type": key.get('Type', ''),
                                "comment": key.get('Comment', '')
                            }
                            for key in table.get('PartitionKeys', [])
                        ]
                    })
            
            return json.dumps({
                "status": "success",
                "database_name": database_name,
                "total_tables": len(tables),
                "tables": tables
            }, indent=2, default=str)
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            return json.dumps({
                "error": f"Error de AWS Glue [{error_code}]: {error_message}",
                "status": "failed"
            }, indent=2)
        
        except Exception as e:
            return json.dumps({
                "error": f"Error inesperado: {str(e)}",
                "status": "failed"
            }, indent=2)
    
    def get_table_info(self, database_name: str, table_name: str) -> str:
        """Obtiene información detallada de una tabla específica"""
        try:
            glue_client = self.get_glue_client()
            if not glue_client:
                return json.dumps({
                    "error": "No se pudo crear el cliente de AWS Glue.",
                    "status": "failed"
                }, indent=2)

            response = glue_client.get_table(DatabaseName=database_name, Name=table_name)
            
            table = response.get('Table', {})
            storage_desc = table.get('StorageDescriptor', {})
            
            # Obtener información de las columnas
            columns = []
            for col in storage_desc.get('Columns', []):
                columns.append({
                    "name": col.get('Name', ''),
                    "type": col.get('Type', ''),
                    "comment": col.get('Comment', '')
                })
            
            table_details = {
                "name": table.get('Name', ''),
                "database_name": table.get('DatabaseName', ''),
                "owner": table.get('Owner', ''),
                "create_time": str(table.get('CreateTime', '')),
                "update_time": str(table.get('UpdateTime', '')),
                "last_access_time": str(table.get('LastAccessTime', '')),
                "table_type": table.get('TableType', ''),
                "storage_descriptor": {
                    "columns": columns,
                    "location": storage_desc.get('Location', ''),
                    "input_format": storage_desc.get('InputFormat', ''),
                    "output_format": storage_desc.get('OutputFormat', ''),
                    "compressed": storage_desc.get('Compressed', False),
                    "number_of_buckets": storage_desc.get('NumberOfBuckets', 0),
                    "serde_info": storage_desc.get('SerdeInfo', {}),
                    "bucket_columns": storage_desc.get('BucketColumns', []),
                    "sort_columns": storage_desc.get('SortColumns', [])
                },
                "partition_keys": [
                    {
                        "name": key.get('Name', ''),
                        "type": key.get('Type', ''),
                        "comment": key.get('Comment', '')
                    }
                    for key in table.get('PartitionKeys', [])
                ],
                "parameters": table.get('Parameters', {}),
                "retention": table.get('Retention', 0)
            }
            
            return json.dumps({
                "status": "success",
                "table": table_details
            }, indent=2, default=str)
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            return json.dumps({
                "error": f"Error de AWS Glue [{error_code}]: {error_message}",
                "status": "failed"
            }, indent=2)
        
        except Exception as e:
            return json.dumps({
                "error": f"Error inesperado: {str(e)}",
                "status": "failed"
            }, indent=2)
    
    def search_tables(self, search_term: str) -> str:
        """Busca tablas por nombre en todas las bases de datos"""
        try:
            glue_client = self.get_glue_client()
            if not glue_client:
                return json.dumps({
                    "error": "No se pudo crear el cliente de AWS Glue.",
                    "status": "failed"
                }, indent=2)

            # Primero obtener todas las bases de datos
            db_response = glue_client.get_databases()
            databases = [db['Name'] for db in db_response.get('DatabaseList', [])]
            
            found_tables = []
            
            # Buscar en cada base de datos
            for db_name in databases:
                try:
                    paginator = glue_client.get_paginator('get_tables')
                    page_iterator = paginator.paginate(DatabaseName=db_name)
                    
                    for page in page_iterator:
                        for table in page.get('TableList', []):
                            table_name = table.get('Name', '')
                            if search_term.lower() in table_name.lower():
                                found_tables.append({
                                    "database_name": db_name,
                                    "table_name": table_name,
                                    "table_type": table.get('TableType', ''),
                                    "create_time": str(table.get('CreateTime', '')),
                                    "location": table.get('StorageDescriptor', {}).get('Location', '')
                                })
                except ClientError:
                    # Si no se puede acceder a una base de datos, continuar
                    continue
            
            return json.dumps({
                "status": "success",
                "search_term": search_term,
                "total_found": len(found_tables),
                "tables": found_tables
            }, indent=2, default=str)
            
        except Exception as e:
            return json.dumps({
                "error": f"Error inesperado: {str(e)}",
                "status": "failed"
            }, indent=2)
    
    def get_catalog_statistics(self) -> str:
        """Obtiene estadísticas generales del catálogo de Glue"""
        try:
            glue_client = self.get_glue_client()
            if not glue_client:
                return json.dumps({
                    "error": "No se pudo crear el cliente de AWS Glue.",
                    "status": "failed"
                }, indent=2)

            # Obtener bases de datos
            db_response = glue_client.get_databases()
            databases = db_response.get('DatabaseList', [])
            
            total_tables = 0
            database_stats = []
            
            # Contar tablas por base de datos
            for db in databases:
                db_name = db['Name']
                try:
                    table_response = glue_client.get_tables(DatabaseName=db_name)
                    table_count = len(table_response.get('TableList', []))
                    total_tables += table_count
                    
                    database_stats.append({
                        "database_name": db_name,
                        "table_count": table_count,
                        "description": db.get('Description', 'Sin descripción')
                    })
                except ClientError:
                    database_stats.append({
                        "database_name": db_name,
                        "table_count": "Error al acceder",
                        "description": db.get('Description', 'Sin descripción')
                    })
            
            return json.dumps({
                "status": "success",
                "region": self.aws_region,
                "catalog_stats": {
                    "total_databases": len(databases),
                    "total_tables": total_tables,
                    "database_breakdown": database_stats
                }
            }, indent=2, default=str)
            
        except Exception as e:
            return json.dumps({
                "error": f"Error inesperado: {str(e)}",
                "status": "failed"
            }, indent=2)
    
    def run_server(self):
        """Ejecuta el servidor MCP"""
        if not self.mcp:
            print("❌ Servidor MCP no disponible. Instala el módulo MCP.")
            return
            
        print("🚀 Iniciando MCP Server para AWS Glue Catalog...")
        print(f"🌍 Región configurada: {self.aws_region}")
        self.mcp.run()


# Integración con el agente principal
def integrate_glue_mcp_with_bedrock(bedrock_agent):
    """
    Integra las funcionalidades de Glue MCP con el agente de Bedrock
    """
    glue_mcp = GlueCatalogMCP()
    
    # Añadir métodos de Glue al agente de Bedrock
    bedrock_agent.glue_list_databases = glue_mcp.list_databases
    bedrock_agent.glue_get_database_info = glue_mcp.get_database_info
    bedrock_agent.glue_list_tables = glue_mcp.list_tables
    bedrock_agent.glue_get_table_info = glue_mcp.get_table_info
    bedrock_agent.glue_search_tables = glue_mcp.search_tables
    bedrock_agent.glue_get_catalog_stats = glue_mcp.get_catalog_statistics
    
    return glue_mcp


def main():
    """Función principal para ejecutar el servidor MCP standalone"""
    print("🧠 AWS Glue Catalog MCP Server")
    print("=" * 40)
    
    if not mcp_available:
        print("❌ Para usar el servidor MCP, instala:")
        print("   pip install mcp")
        return
    
    glue_mcp = GlueCatalogMCP()
    
    # Ejecutar servidor MCP
    glue_mcp.run_server()


if __name__ == "__main__":
    main()
