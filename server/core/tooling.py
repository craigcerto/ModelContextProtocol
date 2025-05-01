# Tool Calling
from typing import Dict, Any, Callable, List
import asyncio

class ToolRegistry:
    def __init__(self):
        self.tools = {}
    
    def register_tool(self, app_id: str, tool_id: str, tool_spec: Dict[str, Any], handler: Callable):
        if app_id not in self.tools:
            self.tools[app_id] = {}
        
        self.tools[app_id][tool_id] = {
            "spec": tool_spec,
            "handler": handler
        }
    
    async def invoke_tool(self, app_id: str, tool_id: str, params: Dict[str, Any], context_id: str) -> Any:
        if app_id not in self.tools or tool_id not in self.tools[app_id]:
            raise ValueError(f"Tool {tool_id} not found for app {app_id}")
        
        tool = self.tools[app_id][tool_id]
        return await tool["handler"](params, context_id)
    
    def get_tools_manifest(self, app_id: str) -> List[Dict[str, Any]]:
        if app_id not in self.tools:
            return []
        
        app_tools = self.tools[app_id]
        return [{"id": tool_id, **tool["spec"]} for tool_id, tool in app_tools.items()]