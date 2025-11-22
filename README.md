# DynamoDB MCP Server

A Model Context Protocol (MCP) server for AWS DynamoDB operations using FastMCP.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
set AWS_ACCESS_KEY_ID=your_access_key
set AWS_SECRET_ACCESS_KEY=your_secret_key
set AWS_REGION=your_region
```

## Example Usage

### Create Table
```python
create_table(
    tableName="users",
    partitionKey="userId", 
    partitionKeyType="S",
    sortKey="timestamp",
    sortKeyType="N",
    readCapacity=5,
    writeCapacity=5
)
```

### Put Item
```python
put_item(
    tableName="users",
    item={"userId": "123", "name": "John", "age": 30}
)
```

### Query Table
```python
query_table(
    tableName="users",
    keyConditionExpression="userId = :uid",
    expressionAttributeValues={":uid": "123"}
)
```

## Run Server

```bash
python server.py
```

## Available Tools

### Table Management
- `list_tables(limit, exclusiveStartTableName)` - List all DynamoDB tables
- `describe_table(tableName)` - Get detailed table information
- `create_table(tableName, partitionKey, partitionKeyType, sortKey, sortKeyType, readCapacity, writeCapacity)` - Create table
- `update_capacity(tableName, readCapacity, writeCapacity)` - Update table capacity

### Item Operations
- `put_item(tableName, item)` - Insert/replace item
- `get_item(tableName, key)` - Retrieve item by key
- `update_item(tableName, key, updateExpression, expressionAttributeNames, expressionAttributeValues, conditionExpression, returnValues)` - Update item

### Query & Scan
- `scan_table(tableName, filterExpression, expressionAttributeValues, expressionAttributeNames, limit)` - Scan table
- `query_table(tableName, keyConditionExpression, expressionAttributeValues, expressionAttributeNames, filterExpression, limit)` - Query table

### Index Management
- `create_gsi(tableName, indexName, partitionKey, partitionKeyType, sortKey, sortKeyType, projectionType, nonKeyAttributes, readCapacity, writeCapacity)` - Create Global Secondary Index
- `update_gsi(tableName, indexName, readCapacity, writeCapacity)` - Update GSI capacity
- `create_lsi(tableName, indexName, partitionKey, partitionKeyType, sortKey, sortKeyType, projectionType, nonKeyAttributes)` - Create Local Secondary Index (table creation only)