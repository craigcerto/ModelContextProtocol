# Model Context Protocol (MCP) Implementation

This README provides a comprehensive overview of implementing the Model Context Protocol in an enterprise AI architecture with a central AI platform and distributed applications.

## Architecture Overview

The Model Context Protocol (MCP) enables seamless communication between:
1. A **Central AI Platform** that manages model invocations (e.g., Claude 3.5 Sonnet via AWS Bedrock)
2. **Application Services** that integrate AI capabilities while maintaining control of their data and business logic

```
┌─────────────────┐     ┌─────────────────────┐
│                 │     │                     │
│  Applications   │◄────┤  Central AI Platform│
│                 │     │                     │
└────────┬────────┘     └─────────────────────┘
         │                         ▲
         │                         │
         │                         │
         ▼                         │
┌─────────────────┐      ┌────────┴────────┐
│                 │      │                 │
│  Local Tools    │      │    AI Models    │
│  & Data         │      │    (Bedrock)    │
│                 │      │                 │
└─────────────────┘      └─────────────────┘
```

## Central AI Platform Implementation

The Central AI Platform serves as the hub for all model invocations in your enterprise.

### Core Components

#### 1. Context Registry Service
```python
class ContextRegistry:
    def __init__(self):
        self.contexts = {}
        self.context_metadata = {}
    
    def register_context(self, app_id: str, metadata: Dict[str, Any]) -> str:
        context_id = str(uuid.uuid4())
        self.contexts[context_id] = {
            "app_id": app_id,
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "sessions": []
        }
        self.context_metadata[context_id] = metadata
        return context_id
    
    def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        # Retrieve context and update last_accessed timestamp
        # ...
```

#### 2. Model Invocation Wrapper
```python
class ModelInvoker:
    def __init__(self, context_registry: ContextRegistry):
        self.context_registry = context_registry
        self.bedrock_client = boto3.client('bedrock-runtime')
    
    async def invoke_model_with_context(self, model_params: Dict[str, Any], context_id: str) -> Dict[str, Any]:
        # 1. Retrieve context 
        # 2. Enhance prompt with context
        # 3. Add MCP instructions
        # 4. Invoke model
        # 5. Process response for tool calls
        # ...
```

#### 3. Tool Registry and Execution
```python
class ToolRegistry:
    def __init__(self):
        self.tools = {}
    
    def register_tool(self, app_id: str, tool_id: str, tool_spec: Dict[str, Any], callback_url: str):
        # Store tool metadata and callback info
        # ...
    
    async def invoke_tool(self, app_id: str, tool_id: str, params: Dict[str, Any], context_id: str) -> Any:
        # Make HTTP request to application callback URL
        # ...
```

#### 4. API Endpoints (FastAPI)
```python
@app.post("/api/contexts")
async def create_context(request: ContextRequest):
    # Create and store new context
    # ...

@app.get("/api/contexts/{context_id}")
async def get_context(context_id: str):
    # Retrieve existing context
    # ...

@app.post("/api/models/invoke")
async def invoke_model(request: Dict[str, Any]):
    # Handle model invocation with context
    # ...

@app.post("/api/tools/register")
async def register_tool(request: Dict[str, Any]):
    # Register application tool
    # ...

@app.post("/api/tool-results")
async def process_tool_results(request: Dict[str, Any]):
    # Process tool execution results
    # ...
```

## Application Implementation

Applications interact with the Central AI Platform while maintaining control over their data and business logic.

### Core Components

#### 1. Central AI Client
```python
class CentralAIClient:
    def __init__(self, central_api_url: str, app_id: str, api_key: str, app_callback_url: str):
        self.central_api_url = central_api_url
        self.app_id = app_id
        self.api_key = api_key
        self.app_callback_url = app_callback_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        self.local_tools = {}
        self.active_contexts = {}
    
    async def create_context(self, metadata: Dict[str, Any] = None) -> str:
        # Create context with application metadata
        # ...
    
    async def invoke_model(self, prompt: str, context_id: str, 
                          system_prompt: str = None, 
                          model_options: Dict[str, Any] = None) -> Dict[str, Any]:
        # Send prompt to central platform with context
        # ...
    
    async def _process_tool_calls(self, model_response: Dict[str, Any], context_id: str) -> Dict[str, Any]:
        # Handle tool calls from model
        # ...
    
    def register_tool(self, name: str, description: str, 
                     parameters_schema: Dict[str, Any], 
                     handler: Callable):
        # Register tool with central platform
        # ...
```

#### 2. Tool Implementation
```python
# Example inventory search tool
async def search_inventory(parameters: Dict[str, Any], context_id: str) -> Dict[str, Any]:
    """Tool to search inventory database"""
    query = parameters.get("query", "")
    category = parameters.get("category", None)
    limit = parameters.get("limit", 10)
    
    # Your actual database query logic here
    # ...
    
    return {
        "results": results,
        "total_count": len(results),
        "query": query
    }

# Register with client
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
            # ...
        },
        "required": ["query"]
    },
    handler=search_inventory
)

# API endpoint for tool execution
@app.post("/tools/search_inventory")
async def search_inventory_endpoint(request: ToolRequest):
    return await search_inventory(request.parameters, request.context_id)
```

#### 3. Application Context Management
```python
class AppContextManager:
    def __init__(self, ai_client: CentralAIClient):
        self.ai_client = ai_client
        self.local_context_data = {}
    
    async def create_user_session(self, user_id: str, user_permissions: List[str]) -> str:
        # Create AI context with user metadata
        # ...
    
    async def execute_ai_query(self, context_id: str, user_query: str) -> Dict[str, Any]:
        # Execute query through central platform
        # ...
```

#### 4. Callback Endpoints
```python
# Tool callback endpoint
@app.post("/tools/{tool_name}")
async def tool_endpoint(tool_name: str, request: ToolRequest):
    # Execute the requested tool
    # ...

# Context update callback
@app.post("/context/update")
async def context_update(request: Request):
    # Handle context updates from central platform
    # ...

# Session end callback
@app.post("/context/end")
async def context_end(request: Request):
    # Clean up when context ends
    # ...
```

## Key Features of this MCP Implementation

1. **Centralized Model Access**: All model invocations go through a unified platform
2. **Distributed Data & Logic**: Applications maintain control of sensitive data and business logic
3. **Context Management**: Long-running contexts persist across multiple interactions
4. **Tool Registration**: Applications can register tools for models to use
5. **Bidirectional Communication**: Both synchronous and asynchronous communication patterns
6. **Security**: API key authentication and context-based access control

## Implementation Steps

### For Central Platform:

1. Set up FastAPI application
2. Implement context registry
3. Create model invocation wrapper
4. Build tool registry and execution framework
5. Implement security and authentication
6. Add monitoring and logging

### For Applications:

1. Integrate the Central AI Client
2. Register application-specific tools
3. Implement tool callback endpoints
4. Create context management logic
5. Build UI for user interactions (if needed)

## Best Practices

1. **Context Enrichment**: Include relevant application state in context metadata
2. **Tool Design**: Design tools with clear input/output schemas
3. **Error Handling**: Implement robust error handling for tool calls
4. **Security**: Validate context IDs and tool parameters
5. **Observability**: Add logging for debugging and monitoring
6. **Performance**: Consider caching frequently used context data

## Security Considerations

1. Use API keys or OAuth tokens for authentication
2. Implement request signing for tool callbacks
3. Validate all request parameters
4. Use HTTPS for all communications
5. Implement rate limiting
6. Follow the principle of least privilege when designing tool permissions
