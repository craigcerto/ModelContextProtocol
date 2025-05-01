# Model Context Protocol (MCP) Implementation

This README provides a comprehensive overview of implementing the Model Context Protocol in a client application that integrates with a centralized AI platform.

## Overview

The Model Context Protocol (MCP) allows applications to communicate with a centralized AI platform while maintaining application-specific context and enabling secure tool calling between systems. This implementation enables you to:

1. Create and manage AI contexts for user sessions
2. Invoke AI models with proper context
3. Implement and expose application-specific tools for AI use
4. Handle bidirectional communication between your application and the central platform

## Architecture

```
┌───────────────────────┐     ┌───────────────────────┐
│                       │     │                       │
│   Your Application    │     │   Central AI Platform │
│                       │     │                       │
└───────────┬───────────┘     └───────────┬───────────┘
            │                             │
            │ 1. Create Context           │
            ├─────────────────────────────►
            │                             │
            │ 2. Invoke Model w/ Context  │
            ├─────────────────────────────►
            │                             │
            │ 3. Tool Calls               │
            │◄─────────────────────────────┤
            │                             │
            │ 4. Tool Results             │
            ├─────────────────────────────►
            │                             │
            │ 5. Final Response           │
            │◄─────────────────────────────┤
            │                             │
```

## Core Components

### CentralAIClient

The client SDK for communicating with the central AI platform. Key functionalities include:

- Creating and managing AI contexts
- Invoking AI models with proper context
- Registering application tools with the central platform
- Processing tool calls from the central platform

```python
class CentralAIClient:
    def __init__(self, central_api_url: str, app_id: str, api_key: str, app_callback_url: str):
        # Initialize client with connection details
        
    async def create_context(self, metadata: Dict[str, Any] = None) -> str:
        # Create a new context in the central platform
        
    async def invoke_model(self, prompt: str, context_id: str, 
                          system_prompt: str = None, 
                          model_options: Dict[str, Any] = None) -> Dict[str, Any]:
        # Invoke the model through the central platform
        
    async def _process_tool_calls(self, model_response: Dict[str, Any], context_id: str) -> Dict[str, Any]:
        # Process tool calls in the model response
        
    def register_tool(self, name: str, description: str, 
                     parameters_schema: Dict[str, Any], 
                     handler: Callable):
        # Register a local tool with the central platform
```

### AppContextManager

Manages application-specific contexts and their integration with the central platform:

- Creating user sessions with appropriate context
- Tracking local context data
- Executing AI queries with proper context

```python
class AppContextManager:
    def __init__(self, ai_client: CentralAIClient):
        # Initialize with AI client
        
    async def create_user_session(self, user_id: str, user_permissions: List[str]) -> str:
        # Create a new AI context for a user session
        
    def update_local_context(self, context_id: str, key: str, value: Any) -> None:
        # Update local context data
        
    def get_local_context(self, context_id: str) -> Dict[str, Any]:
        # Get local context data
        
    async def execute_ai_query(self, context_id: str, user_query: str) -> Dict[str, Any]:
        # Execute an AI query with proper context
```

### Tool Implementation

Tools are registered with the central platform but executed in your application:

```python
# Example tool: Inventory Search
async def search_inventory(parameters: Dict[str, Any], context_id: str) -> Dict[str, Any]:
    """Tool to search inventory database"""
    query = parameters.get("query", "")
    category = parameters.get("category", None)
    limit = parameters.get("limit", 10)
    
    # Your actual database query logic here
    
    return {
        "results": results,
        "total_count": len(results),
        "query": query
    }

# Register the tool with the client
ai_client.register_tool(
    name="search_inventory",
    description="Search the inventory database for products",
    parameters_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query string"
            },
            # Other parameters...
        },
        "required": ["query"]
    },
    handler=search_inventory
)
```

### API Endpoints

Your application should expose several endpoints for interaction with the central platform:

- `/api/chat` - Main endpoint for user queries
- `/tools/{tool_name}` - Endpoints for tool execution
- `/context/update` - Endpoint for context updates from central platform
- `/context/end` - Endpoint for context termination

## Implementation Steps

1. **Initialize the Client SDK**
   ```python
   ai_client = CentralAIClient(
       central_api_url="https://ai-central-platform.example.com",
       app_id="inventory_management_app",
       api_key="your_api_key_here",
       app_callback_url="https://your-inventory-app.example.com/api"
   )
   ```

2. **Create the Context Manager**
   ```python
   context_manager = AppContextManager(ai_client)
   ```

3. **Implement and Register Tools**
   ```python
   # Implement tool functions
   async def search_inventory(parameters, context_id):
       # Tool implementation...
       
   # Register tools with the client
   ai_client.register_tool("search_inventory", "Search inventory", schema, search_inventory)
   ```

4. **Implement API Endpoints**
   ```python
   @app.post("/api/chat")
   async def chat_endpoint(request: Dict[str, Any]):
       # Implementation...
   
   @app.post("/tools/{tool_name}")
   async def tool_endpoint(tool_name: str, request: ToolRequest):
       # Implementation...
   ```

5. **Verify Connectivity**
   ```python
   if await ai_client.verify_callbacks():
       print("Successfully connected to central platform")
   else:
       print("Failed to verify callbacks")
   ```

## Best Practices

1. **Context Management**
   - Include relevant user information in contexts
   - Store minimal sensitive information
   - Implement proper context cleanup

2. **Tool Implementation**
   - Define precise parameter schemas
   - Implement proper error handling
   - Follow principle of least privilege

3. **Security Considerations**
   - Validate all incoming requests
   - Use HTTPS for all communications
   - Implement proper authentication

4. **Performance Optimization**
   - Cache frequently used tool results
   - Implement request throttling
   - Monitor resource usage

## Example Usage Flow

1. User starts a session in your application
2. Application creates an AI context with the central platform
3. User submits a query
4. Application sends query to central platform with context
5. Central platform processes query, possibly making tool calls
6. Application receives and processes tool calls
7. Central platform completes the response
8. Application displays response to user

## Error Handling

Implement proper error handling for various scenarios:

```python
try:
    result = await ai_client.invoke_model(prompt, context_id)
except ConnectionError:
    # Handle connection issues
except AuthenticationError:
    # Handle authentication issues
except ToolExecutionError:
    # Handle tool execution errors
```

## Monitoring and Logging

Implement comprehensive logging:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_client")

# Log important events
logger.info(f"Created context: {context_id}")
logger.info(f"Invoking model with context: {context_id}")
logger.info(f"Received tool call: {tool_name}")
```

## Conclusion

This Model Context Protocol implementation enables your application to securely interact with a centralized AI platform while maintaining application-specific context and enabling powerful tool functionality. By following this implementation, you can integrate sophisticated AI capabilities into your application while keeping sensitive data and business logic within your control.
