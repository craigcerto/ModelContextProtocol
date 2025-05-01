import uuid
from datetime import datetime
from typing import Dict, Any, Optional

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
        context = self.contexts.get(context_id)
        if context:
            context["last_accessed"] = datetime.now()
            return {
                "context": context,
                "metadata": self.context_metadata.get(context_id, {})
            }
        return None
