from typing import Dict, Any, Callable, Optional, List
import requests
import json
import uuid
import asyncio
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel

# FastAPI app for the application's tool endpoints
app = FastAPI()

class CentralAIClient:
    def __init__(self, central_api_url: str, app_id: str, api_key: str):
        self.central_api_url = central_api_url
        self.app_id = app_id
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        self.local_tools = {}
        self.active_contexts = {}

    async def create_context(self, metadata: Dict[str, Any] = None) -> str:
        if metadata is None:
            metadata = {}
        
        # Add application-specific metadata including callback info
        app_metadata = {
            "app_name": "inventory_management",
            "app_version": "1.2.3",
            "user_id": metadata.get("user_id", "anonymous"),
            "session_id": str(uuid.uuid4()) if "session_id" not in metadata else metadata["session_id"],
            "callbacks": {
                "context_update": f"{self.app_callback_url}/context/update",
                "session_end": f"{self.app_callback_url}/context/end",
                "default_tool_handler": f"{self.app_callback_url}/tools/default"
            },
            "permissions": metadata.get("permissions", []),
            "data_sources": metadata.get("data_sources", [])
        }
        
        response = requests.post(
            f"{self.central_api_url}/api/contexts",
            headers=self.headers,
            json={
                "app_id": self.app_id,
                "metadata": {**metadata, **app_metadata}
            }
        )
        
        response.raise_for_status()
        context_id = response.json()["context_id"]
        
        # Store context locally for reference
        self.active_contexts[context_id] = {
            "metadata": {**metadata, **app_metadata},
            "created_at": response.json().get("created_at", None)
        }
        
        return context_id
    
    async def invoke_model(self, prompt: str, context_id: str, 
                          system_prompt: str = None, 
                          model_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Invoke the model through the central platform"""
        if model_options is None:
            model_options = {}
            
        if context_id not in self.active_contexts:
            raise ValueError(f"Context ID {context_id} not found or expired")
        
        # Prepare model parameters with application context
        model_params = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "max_tokens": model_options.get("max_tokens", 1000),
            "temperature": model_options.get("temperature", 0.7),
            # Add other model parameters as needed
        }
        
        # Include available tools in the context
        available_tools = list(self.local_tools.keys())
        
        response = requests.post(
            f"{self.central_api_url}/api/models/invoke",
            headers=self.headers,
            json={
                "model_params": model_params,
                "context_id": context_id,
                "app_id": self.app_id,
                "available_tools": available_tools
            }
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Check for tool calls in the response
        if "tool_calls" in result:
            result = await self._process_tool_calls(result, context_id)
            
        return result
    
    async def _process_tool_calls(self, model_response: Dict[str, Any], context_id: str) -> Dict[str, Any]:
        """Process any tool calls in the model response"""
        if "tool_calls" not in model_response:
            return model_response
            
        tool_calls = model_response["tool_calls"]
        tool_results = []
        
        for tool_call in tool_calls:
            tool_id = tool_call.get("id")
            tool_name = tool_call.get("name")
            tool_params = tool_call.get("parameters", {})
            
            if tool_name in self.local_tools:
                try:
                    result = await self.local_tools[tool_name](tool_params, context_id)
                    tool_results.append({
                        "tool_call_id": tool_id,
                        "result": result,
                        "status": "success"
                    })
                except Exception as e:
                    tool_results.append({
                        "tool_call_id": tool_id,
                        "error": str(e),
                        "status": "error"
                    })
            else:
                tool_results.append({
                    "tool_call_id": tool_id,
                    "error": f"Tool {tool_name} not found",
                    "status": "not_found"
                })
        
        # Send tool results back to the central platform
        response = requests.post(
            f"{self.central_api_url}/api/tool-results",
            headers=self.headers,
            json={
                "context_id": context_id,
                "tool_results": tool_results,
                "app_id": self.app_id
            }
        )
        
        response.raise_for_status()
        return response.json()
    
    def register_tool(self, name: str, description: str, 
                     parameters_schema: Dict[str, Any], 
                     handler: Callable):
        """Register a local tool that can be called by the model"""
        self.local_tools[name] = handler
        
        # Register the tool with the central platform
        tool_spec = {
            "name": name,
            "description": description,
            "parameters": parameters_schema
        }
        
        # Here's where you specify the callback URL for this tool
        response = requests.post(
            f"{self.central_api_url}/api/tools/register",
            headers=self.headers,
            json={
                "app_id": self.app_id,
                "tool_spec": tool_spec,
                "callback_url": f"{self.app_callback_url}/tools/{name}"  # Specific tool endpoint
            }
        )
        
        response.raise_for_status()
        return response.json()
    
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if the central platform is available"""
        try:
            response = requests.get(
                f"{self.central_api_url}/health",
                headers=self.headers,
                timeout=5
            )
            response.raise_for_status()
            return {
                "status": "healthy",
                "latency_ms": response.elapsed.total_seconds() * 1000,
                "version": response.headers.get("X-API-Version", "unknown")
            }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
        

# Add health check endpoint
@app.get("/health")
async def health():
    central_health = await ai_client.health_check()
    
    # Check your own app's health
    app_health = {
        "database": check_database_connection(),
        "redis": check_redis_connection(),
        "tools_registered": len(ai_client.local_tools) > 0
    }
    
    overall_status = "healthy" if all(app_health.values()) and central_health["status"] == "healthy" else "degraded"
    
    return {
        "status": overall_status,
        "components": {
            "central_ai": central_health,
            "application": app_health
        },
        "timestamp": datetime.now().isoformat()
    }
    

class ToolRequest(BaseModel):
    parameters: Dict[str, Any]
    context_id: str


ai_client = CentralAIClient(
    central_api_url="https://ai-central-platform.example.com",
    app_id="inventory_management_app",
    api_key="your_api_key_here",
    app_callback_url="https://your-inventory-app.example.com/api"  # Your app's public URL
)

# Example tool: Inventory Search
async def search_inventory(parameters: Dict[str, Any], context_id: str) -> Dict[str, Any]:
    """Tool to search inventory database"""
    query = parameters.get("query", "")
    category = parameters.get("category", None)
    limit = parameters.get("limit", 10)
    
    # Your actual database query logic here
    results = [
        {"id": "item1", "name": "Product A", "quantity": 15, "location": "Warehouse B"},
        {"id": "item2", "name": "Product B", "quantity": 8, "location": "Warehouse A"}
    ]
    
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
            "category": {
                "type": "string",
                "description": "Product category to filter by"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return"
            }
        },
        "required": ["query"]
    },
    handler=search_inventory
)

# Expose the tool endpoint for the central platform to call
@app.post("/tools/search_inventory")
async def search_inventory_endpoint(request: ToolRequest):
    return await search_inventory(request.parameters, request.context_id)


# Update your AppContextManager to use this
class AppContextManager:
    def __init__(self, ai_client: CentralAIClient, persistence: PersistentContextManager):
        self.ai_client = ai_client
        self.persistence = persistence
    
    async def create_user_session(self, user_id: str, user_permissions: List[str]) -> str:
        """Create a new AI context for a user session"""
        context_id = await self.ai_client.create_context({
            "user_id": user_id,
            "permissions": user_permissions,
            # Other metadata...
        })
        
        # Store in persistent storage
        self.persistence.store_context(context_id, {
            "user_id": user_id,
            "session_start": datetime.now().isoformat(),
            "interaction_count": 0,
            "recent_queries": []
        })
        
        return context_id

# Update your AppContextManager to use this
class AppContextManager:
    def __init__(self, ai_client: CentralAIClient, persistence: PersistentContextManager):
        self.ai_client = ai_client
        self.persistence = persistence
    
    async def create_user_session(self, user_id: str, user_permissions: List[str]) -> str:
        """Create a new AI context for a user session"""
        context_id = await self.ai_client.create_context({
            "user_id": user_id,
            "permissions": user_permissions,
            "client_ip": "192.168.1.100",  # Example data
            "client_type": "web",
            "application_state": {
                "current_view": "inventory_dashboard",
                "filters_active": True
            }
        })
        
        # Store in persistent storage
        self.persistence.store_context(context_id, {
            "user_id": user_id,
            "session_start": datetime.now().isoformat(),
            "interaction_count": 0,
            "recent_queries": []
        })
        
        return context_id
    
    def update_local_context(self, context_id: str, key: str, value: Any) -> None:
        """Update local context data"""
        if context_id in self.local_context_data:
            self.local_context_data[context_id][key] = value
    
    def get_local_context(self, context_id: str) -> Dict[str, Any]:
        """Get local context data"""
        return self.local_context_data.get(context_id, {})
    
    async def execute_ai_query(self, context_id: str, user_query: str) -> Dict[str, Any]:
        """Execute an AI query with proper context"""
        # Update interaction count
        if context_id in self.local_context_data:
            self.local_context_data[context_id]["interaction_count"] += 1
            
            # Store recent query
            recent_queries = self.local_context_data[context_id].get("recent_queries", [])
            recent_queries.append(user_query)
            self.local_context_data[context_id]["recent_queries"] = recent_queries[-5:]  # Keep last 5
        
        # Create system prompt with application-specific context
        system_prompt = """
        You are an AI assistant for the Inventory Management System.
        You can help users search inventory, check stock levels, and manage orders.
        When you need specific data, use the available tools to fetch it.
        """
        
        # Execute the query via central platform
        result = await self.ai_client.invoke_model(
            prompt=user_query,
            context_id=context_id,
            system_prompt=system_prompt,
            model_options={
                "temperature": 0.3,  # Lower temperature for more deterministic responses
                "max_tokens": 1500
            }
        )
        
        return result
    
import redis
from typing import Optional, Dict, Any
import json

class PersistentContextManager:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.key_prefix = "ai_context:"
        self.expiry_time = 3600 * 24  # 24 hours
    
    def store_context(self, context_id: str, data: Dict[str, Any]) -> None:
        """Store context data in Redis"""
        key = f"{self.key_prefix}{context_id}"
        self.redis.setex(key, self.expiry_time, json.dumps(data))
    
    def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve context data from Redis"""
        key = f"{self.key_prefix}{context_id}"
        data = self.redis.get(key)
        if data:
            # Reset expiry time on access
            self.redis.expire(key, self.expiry_time)
            return json.loads(data)
        return None
    
    def update_context(self, context_id: str, updates: Dict[str, Any]) -> bool:
        """Update specific fields in the context"""
        data = self.get_context(context_id)
        if data:
            data.update(updates)
            self.store_context(context_id, data)
            return True
        return False
    
    def delete_context(self, context_id: str) -> bool:
        """Delete a context"""
        key = f"{self.key_prefix}{context_id}"
        return self.redis.delete(key) > 0
    
    
# Create the context manager
context_manager = AppContextManager(ai_client)

@app.post("/api/chat")
async def chat_endpoint(request: Dict[str, Any]):
    user_id = request.get("user_id")
    query = request.get("query")
    context_id = request.get("context_id")
    
    # Create new context if not provided
    if not context_id:
        # Get user permissions from your auth system
        user_permissions = ["inventory.read", "orders.read"]
        context_id = await context_manager.create_user_session(user_id, user_permissions)
    
    # Execute the query with context
    result = await context_manager.execute_ai_query(context_id, query)
    
    # Return results to the client
    return {
        "response": result.get("completion", ""),
        "context_id": context_id,
        # Other metadata as needed
    }

@app.post("/webhooks/tool-callback")
async def tool_callback(request: Request):
    """Webhook for asynchronous tool call results"""
    payload = await request.json()
    context_id = payload.get("context_id")
    tool_call_id = payload.get("tool_call_id")
    
    # Process the tool call result and send back to central platform
    result = {
        "status": "completed",
        "data": {
            # Your tool result data
        }
    }
    
    # Notify the central platform of the result
    requests.post(
        f"{ai_client.central_api_url}/api/tool-results/{tool_call_id}",
        headers=ai_client.headers,
        json={
            "context_id": context_id,
            "tool_call_id": tool_call_id,
            "result": result
        }
    )
    
    return {"status": "received"}

# Tool endpoint (as shown previously)
@app.post("/tools/{tool_name}")
async def tool_endpoint(tool_name: str, request: ToolRequest):
    if tool_name in ai_client.local_tools:
        return await ai_client.local_tools[tool_name](request.parameters, request.context_id)
    else:
        raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")

# Context update callback
@app.post("/context/update")
async def context_update(request: Request):
    data = await request.json()
    context_id = data.get("context_id")
    updates = data.get("updates", {})
    
    # Process context updates from the central platform
    if context_id in context_manager.local_context_data:
        for key, value in updates.items():
            context_manager.update_local_context(context_id, key, value)
    
    return {"status": "success"}

# Session end callback
@app.post("/context/end")
async def context_end(request: Request):
    data = await request.json()
    context_id = data.get("context_id")
    
    # Clean up resources when the central platform ends a context
    if context_id in context_manager.local_context_data:
        # Perform cleanup
        del context_manager.local_context_data[context_id]
    
    return {"status": "success"}


async def verify_callbacks(self) -> bool:
    """Verify that the central platform can reach your callbacks"""
    response = requests.post(
        f"{self.central_api_url}/api/verify-callbacks",
        headers=self.headers,
        json={
            "app_id": self.app_id,
            "callback_urls": [
                f"{self.app_callback_url}/tools/ping",
                f"{self.app_callback_url}/context/update",
                f"{self.app_callback_url}/context/end"
            ]
        }
    )
    
    try:
        response.raise_for_status()
        result = response.json()
        return all(result.get("results", {}).values())
    except:
        return False

# Add a simple ping endpoint for verification
@app.post("/tools/ping")
async def ping():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}