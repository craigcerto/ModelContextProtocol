from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

app = FastAPI()
context_registry = ContextRegistry()

class ContextRequest(BaseModel):
    app_id: str
    metadata: Dict[str, Any] = {}

class ContextResponse(BaseModel):
    context_id: str

@app.post("/api/contexts", response_model=ContextResponse)
async def create_context(request: ContextRequest):
    context_id = context_registry.register_context(request.app_id, request.metadata)
    return {"context_id": context_id}

@app.get("/api/contexts/{context_id}")
async def get_context(context_id: str):
    context_data = context_registry.get_context(context_id)
    if not context_data:
        raise HTTPException(status_code=404, detail="Context not found")
    return context_data

