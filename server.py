import os
import json
from typing import Dict, Any, List, Optional
import boto3
from botocore.exceptions import ClientError
from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

# Initialize MCP server
mcp = FastMCP("DynamoDB MCP Server")

# Define middleware
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

# Initialize DynamoDB client
def get_dynamodb_client():
    return boto3.client(
        'dynamodb',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION')
    )

def serialize_dynamodb_item(item):
    """Convert Python dict to DynamoDB format"""
    if isinstance(item, dict):
        return {k: serialize_dynamodb_value(v) for k, v in item.items()}
    return item

def serialize_dynamodb_value(value):
    """Convert Python value to DynamoDB attribute value"""
    if isinstance(value, str):
        return {'S': value}
    elif isinstance(value, (int, float)):
        return {'N': str(value)}
    elif isinstance(value, bool):
        return {'BOOL': value}
    elif isinstance(value, list):
        return {'L': [serialize_dynamodb_value(v) for v in value]}
    elif isinstance(value, dict):
        return {'M': {k: serialize_dynamodb_value(v) for k, v in value.items()}}
    elif value is None:
        return {'NULL': True}
    return {'S': str(value)}

@mcp.tool()
def list_tables(limit: Optional[int] = None, exclusiveStartTableName: Optional[str] = None) -> Dict[str, Any]:
    """Lists all DynamoDB tables in the account"""
    try:
        client = get_dynamodb_client()
        params = {}
        if limit:
            params['Limit'] = limit
        if exclusiveStartTableName:
            params['ExclusiveStartTableName'] = exclusiveStartTableName
        
        response = client.list_tables(**params)
        return {
            "TableNames": response['TableNames'],
            "LastEvaluatedTableName": response.get('LastEvaluatedTableName')
        }
    except ClientError as e:
        return {"error": str(e)}

@mcp.tool()
def describe_table(tableName: str) -> Dict[str, Any]:
    """Gets detailed information about a DynamoDB table"""
    try:
        client = get_dynamodb_client()
        response = client.describe_table(TableName=tableName)
        return response['Table']
    except ClientError as e:
        return {"error": str(e)}

@mcp.tool()
def create_table(tableName: str, partitionKey: str, partitionKeyType: str, 
                sortKey: Optional[str] = None, sortKeyType: Optional[str] = None,
                readCapacity: int = 5, writeCapacity: int = 5) -> Dict[str, Any]:
    """Creates a new DynamoDB table with specified configuration"""
    try:
        client = get_dynamodb_client()
        
        # Build key schema
        key_schema = [{'AttributeName': partitionKey, 'KeyType': 'HASH'}]
        attribute_definitions = [{'AttributeName': partitionKey, 'AttributeType': partitionKeyType}]
        
        if sortKey:
            key_schema.append({'AttributeName': sortKey, 'KeyType': 'RANGE'})
            attribute_definitions.append({'AttributeName': sortKey, 'AttributeType': sortKeyType})
        
        params = {
            'TableName': tableName,
            'KeySchema': key_schema,
            'AttributeDefinitions': attribute_definitions,
            'BillingMode': 'PROVISIONED',
            'ProvisionedThroughput': {
                'ReadCapacityUnits': readCapacity,
                'WriteCapacityUnits': writeCapacity
            }
        }
        
        response = client.create_table(**params)
        return {"status": "creating", "tableArn": response['TableDescription']['TableArn']}
    except ClientError as e:
        return {"error": str(e)}

@mcp.tool()
def update_capacity(tableName: str, readCapacity: int, writeCapacity: int) -> Dict[str, Any]:
    """Updates the provisioned capacity of a table"""
    try:
        client = get_dynamodb_client()
        response = client.update_table(
            TableName=tableName,
            ProvisionedThroughput={
                'ReadCapacityUnits': readCapacity,
                'WriteCapacityUnits': writeCapacity
            }
        )
        return {"status": "updating", "tableArn": response['TableDescription']['TableArn']}
    except ClientError as e:
        return {"error": str(e)}

@mcp.tool()
def put_item(tableName: str, item: Dict[str, Any]) -> Dict[str, Any]:
    """Inserts or replaces an item in a table"""
    try:
        client = get_dynamodb_client()
        dynamodb_item = serialize_dynamodb_item(item)
        response = client.put_item(
            TableName=tableName,
            Item=dynamodb_item
        )
        return {"status": "success"}
    except ClientError as e:
        return {"error": str(e)}

@mcp.tool()
def get_item(tableName: str, key: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieves an item from a table by its primary key"""
    try:
        client = get_dynamodb_client()
        dynamodb_key = serialize_dynamodb_item(key)
        response = client.get_item(
            TableName=tableName,
            Key=dynamodb_key
        )
        return response.get('Item', {})
    except ClientError as e:
        return {"error": str(e)}

@mcp.tool()
def update_item(tableName: str, key: Dict[str, Any], updateExpression: str,
               expressionAttributeNames: Dict[str, str], expressionAttributeValues: Dict[str, Any],
               conditionExpression: Optional[str] = None, returnValues: str = "ALL_NEW") -> Dict[str, Any]:
    """Updates specific attributes of an item in a table"""
    try:
        client = get_dynamodb_client()
        dynamodb_key = serialize_dynamodb_item(key)
        dynamodb_values = serialize_dynamodb_item(expressionAttributeValues)
        
        params = {
            'TableName': tableName,
            'Key': dynamodb_key,
            'UpdateExpression': updateExpression,
            'ExpressionAttributeNames': expressionAttributeNames,
            'ExpressionAttributeValues': dynamodb_values,
            'ReturnValues': returnValues
        }
        
        if conditionExpression:
            params['ConditionExpression'] = conditionExpression
        
        response = client.update_item(**params)
        return response.get('Attributes', {})
    except ClientError as e:
        return {"error": str(e)}



@mcp.tool()
def scan_table(tableName: str, filterExpression: Optional[str] = None,
              expressionAttributeValues: Optional[Dict[str, Any]] = None,
              expressionAttributeNames: Optional[Dict[str, str]] = None,
              limit: Optional[int] = None) -> Dict[str, Any]:
    """Scans an entire table with optional filters"""
    try:
        client = get_dynamodb_client()
        params = {'TableName': tableName}
        
        if filterExpression:
            params['FilterExpression'] = filterExpression
        if expressionAttributeValues:
            params['ExpressionAttributeValues'] = serialize_dynamodb_item(expressionAttributeValues)
        if expressionAttributeNames:
            params['ExpressionAttributeNames'] = expressionAttributeNames
        if limit:
            params['Limit'] = limit
            
        response = client.scan(**params)
        return {
            "Items": response.get('Items', []),
            "Count": response.get('Count', 0),
            "ScannedCount": response.get('ScannedCount', 0)
        }
    except ClientError as e:
        return {"error": str(e)}

@mcp.tool()
def query_table(tableName: str, keyConditionExpression: str, expressionAttributeValues: Dict[str, Any],
               expressionAttributeNames: Optional[Dict[str, str]] = None,
               filterExpression: Optional[str] = None, limit: Optional[int] = None) -> Dict[str, Any]:
    """Queries a table using key conditions and optional filters"""
    try:
        client = get_dynamodb_client()
        params = {
            'TableName': tableName,
            'KeyConditionExpression': keyConditionExpression,
            'ExpressionAttributeValues': serialize_dynamodb_item(expressionAttributeValues)
        }
        
        if expressionAttributeNames:
            params['ExpressionAttributeNames'] = expressionAttributeNames
        if filterExpression:
            params['FilterExpression'] = filterExpression
        if limit:
            params['Limit'] = limit
            
        response = client.query(**params)
        return {
            "Items": response.get('Items', []),
            "Count": response.get('Count', 0)
        }
    except ClientError as e:
        return {"error": str(e)}

@mcp.tool()
def create_gsi(tableName: str, indexName: str, partitionKey: str, partitionKeyType: str,
              sortKey: Optional[str] = None, sortKeyType: Optional[str] = None,
              projectionType: str = "ALL", nonKeyAttributes: Optional[List[str]] = None,
              readCapacity: int = 5, writeCapacity: int = 5) -> Dict[str, Any]:
    """Creates a global secondary index on a table"""
    try:
        client = get_dynamodb_client()
        
        # Build GSI key schema
        key_schema = [{'AttributeName': partitionKey, 'KeyType': 'HASH'}]
        attribute_definitions = [{'AttributeName': partitionKey, 'AttributeType': partitionKeyType}]
        
        if sortKey:
            key_schema.append({'AttributeName': sortKey, 'KeyType': 'RANGE'})
            attribute_definitions.append({'AttributeName': sortKey, 'AttributeType': sortKeyType})
        
        # Build projection
        projection = {'ProjectionType': projectionType}
        if projectionType == 'INCLUDE' and nonKeyAttributes:
            projection['NonKeyAttributes'] = nonKeyAttributes
        
        gsi_spec = {
            'IndexName': indexName,
            'KeySchema': key_schema,
            'Projection': projection,
            'ProvisionedThroughput': {
                'ReadCapacityUnits': readCapacity,
                'WriteCapacityUnits': writeCapacity
            }
        }
        
        response = client.update_table(
            TableName=tableName,
            AttributeDefinitions=attribute_definitions,
            GlobalSecondaryIndexUpdates=[{'Create': gsi_spec}]
        )
        return {"status": "creating", "indexName": indexName}
    except ClientError as e:
        return {"error": str(e)}

@mcp.tool()
def update_gsi(tableName: str, indexName: str, readCapacity: int, writeCapacity: int) -> Dict[str, Any]:
    """Updates the provisioned capacity of a global secondary index"""
    try:
        client = get_dynamodb_client()
        response = client.update_table(
            TableName=tableName,
            GlobalSecondaryIndexUpdates=[{
                'Update': {
                    'IndexName': indexName,
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': readCapacity,
                        'WriteCapacityUnits': writeCapacity
                    }
                }
            }]
        )
        return {"status": "updating", "indexName": indexName}
    except ClientError as e:
        return {"error": str(e)}

@mcp.tool()
def create_lsi(tableName: str, indexName: str, partitionKey: str, partitionKeyType: str,
              sortKey: str, sortKeyType: str, projectionType: str = "ALL",
              nonKeyAttributes: Optional[List[str]] = None, readCapacity: int = 5, writeCapacity: int = 5) -> Dict[str, Any]:
    """Creates a local secondary index on a table (must be done during table creation)"""
    try:
        # Note: LSI can only be created during table creation, not after
        return {"error": "Local Secondary Indexes can only be created during table creation. Use create_table with LSI specification."}
    except Exception as e:
        return {"error": str(e)}

# Web interface for browser access
@mcp.custom_route("/", methods=["GET"])
async def web_interface(request):
    from starlette.responses import HTMLResponse
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>DynamoDB MCP Server</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; }
        button { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        #output { background: #f9f9f9; padding: 15px; margin: 15px 0; border-radius: 5px; white-space: pre-wrap; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 DynamoDB MCP Server</h1>
        <p>Your MCP server is running!</p>
        
        <h2>🔗 Endpoints</h2>
        <ul>
            <li><strong>MCP Protocol:</strong> POST /mcp</li>
            <li><strong>Health Check:</strong> <a href="/health">GET /health</a></li>
        </ul>
        
        <h2>🧪 Test Interface</h2>
        <button onclick="testConnection()">Test Connection</button>
        <button onclick="listTables()">List Tables</button>
        <div id="output"></div>
    </div>
    
    <script>
        let sessionId = null;
        
        async function mcpCall(method, params = {}) {
            const headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/event-stream',
                'mcp-protocol-version': '2024-11-05'
            };
            
            if (sessionId) {
                headers['mcp-session-id'] = sessionId;
            }
            
            const response = await fetch('/mcp', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    id: 1,
                    method: method,
                    params: params
                })
            });
            
            const newSessionId = response.headers.get('mcp-session-id');
            if (newSessionId) {
                sessionId = newSessionId;
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType === 'text/event-stream') {
                const text = await response.text();
                const lines = text.split('\\n');
                let data = '';
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        data += line.substring(6);
                    }
                }
                return JSON.parse(data);
            } else {
                return await response.json();
            }
        }
        
        async function testConnection() {
            document.getElementById('output').textContent = 'Testing connection...';
            try {
                const result = await mcpCall('initialize', {
                    protocolVersion: '2024-11-05',
                    capabilities: {},
                    clientInfo: { name: 'web-client', version: '1.0.0' }
                });
                document.getElementById('output').textContent = 'Connection successful!\\nSession ID: ' + sessionId;
            } catch (error) {
                document.getElementById('output').textContent = 'Error: ' + error.message;
            }
        }
        
        async function listTables() {
            if (!sessionId) await testConnection();
            document.getElementById('output').textContent = 'Listing tables...';
            try {
                const result = await mcpCall('tools/call', {
                    name: 'list_tables',
                    arguments: {}
                });
                document.getElementById('output').textContent = JSON.stringify(result, null, 2);
            } catch (error) {
                document.getElementById('output').textContent = 'Error: ' + error.message;
            }
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

# Health check endpoint
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    from starlette.responses import JSONResponse
    return JSONResponse({"status": "healthy", "service": "dynamodb-mcp-server"})

if __name__ == "__main__":
    print("🚀 DynamoDB MCP Server starting...")
    print("📍 Web Interface: http://localhost:8000")
    print("📍 MCP Endpoint: http://localhost:8000/mcp")
    print("🏥 Health Check: http://localhost:8000/health")
    mcp.run(transport="http", host="0.0.0.0", port=8000)