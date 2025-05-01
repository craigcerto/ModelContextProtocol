import boto3
import json
from typing import Dict, Any, Optional

class ModelInvoker:
    def __init__(self, context_registry: ContextRegistry):
        self.context_registry = context_registry
        self.bedrock_client = boto3.client('bedrock-runtime')
    
    def prepare_prompt_with_context(self, prompt: str, context_data: Optional[Dict]) -> str:
        """Enhance the prompt with context information"""
        if not context_data:
            return prompt
            
        # Add context-specific information to the prompt
        context_enhanced = f"Context ID: {context_data.get('context', {}).get('id')}\n"
        # Add other relevant context information
        
        return f"{context_enhanced}\n{prompt}"
    
    def get_mcp_instructions(self) -> str:
        """Return instructions for the model on how to use MCP"""
        return """
        You have access to application data and tools through the Model Context Protocol.
        When you need information from an application, use the format:
        <tool_request app_id="app_id" tool_id="tool_name">
        {
            "parameters": {
                "param1": "value1",
                "param2": "value2"
            }
        }
        </tool_request>
        """
    
    async def invoke_model_with_context(self, model_params: Dict[str, Any], context_id: str) -> Dict[str, Any]:
        # Retrieve context if it exists
        context_data = self.context_registry.get_context(context_id)
        
        # Prepare the model input with context
        enhanced_prompt = self.prepare_prompt_with_context(
            model_params.get("prompt", ""), 
            context_data
        )
        
        # Add MCP instructions to system prompt
        system_prompt = f"{model_params.get('system_prompt', '')}\n\n{self.get_mcp_instructions()}"
        
        # Invoke the model (AWS Bedrock in your case)
        response = self.bedrock_client.invoke_model(
            modelId='anthropic.claude-3-5-sonnet',
            body=json.dumps({
                "prompt": enhanced_prompt,
                "system": system_prompt,
                "max_tokens": model_params.get("max_tokens", 1000),
                "temperature": model_params.get("temperature", 0.7),
                "context_id": context_id  # If supported by the model provider
            })
        )
        
        response_body = json.loads(response['body'].read())
        
        # Process response for tool calls if needed
        processed_response = self.handle_tool_calls(response_body, context_data)
        
        return processed_response
    
    def handle_tool_calls(self, response: Dict[str, Any], context_data: Optional[Dict]) -> Dict[str, Any]:
        """Process the response for any tool calls"""
        # Implementation for parsing and handling tool calls
        return response