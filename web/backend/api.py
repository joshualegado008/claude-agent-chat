"""
FastAPI Web Backend - REST API for Claude Agent Chat
Provides HTTP and WebSocket endpoints for the web frontend
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import asyncio
import traceback

from bridge import get_bridge
from websocket_handler import ConversationStreamHandler

# Initialize FastAPI app
app = FastAPI(
    title="Claude Agent Chat API",
    description="Backend API for Claude Agent Chat Web Interface",
    version="1.0.0"
)

# CORS middleware for development (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response validation
class NewConversationRequest(BaseModel):
    title: str
    initial_prompt: Optional[str] = None
    tags: Optional[List[str]] = None
    generate_prompt: bool = True  # Auto-generate if not provided

class ContinueConversationRequest(BaseModel):
    continuation_prompt: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    limit: int = 10

class GeneratePromptRequest(BaseModel):
    title: str

# API Routes

@app.get("/")
async def root():
    """Root endpoint - API info."""
    return {
        "name": "Claude Agent Chat API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "conversations": "/api/conversations",
            "search": "/api/search",
            "websocket": "/ws/conversation/{conversation_id}"
        }
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    bridge = get_bridge()
    try:
        # Test database connection
        conversations = bridge.get_conversation_browser().list_recent(limit=1)
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.get("/api/conversations")
async def list_conversations(limit: int = 20, status: Optional[str] = None):
    """List recent conversations."""
    bridge = get_bridge()
    browser = bridge.get_conversation_browser()

    try:
        conversations = browser.list_recent(limit=limit)

        # Convert to serializable format
        result = []
        for conv in conversations:
            result.append({
                "id": str(conv.get("id")),
                "title": conv.get("title"),
                "initial_prompt": conv.get("initial_prompt"),
                "agent_a_name": conv.get("agent_a_name"),
                "agent_b_name": conv.get("agent_b_name"),
                "total_turns": conv.get("total_turns", 0),
                "total_tokens": conv.get("total_tokens", 0),
                "status": conv.get("status"),
                "tags": conv.get("tags", []),
                "created_at": conv.get("created_at").isoformat() if isinstance(conv.get("created_at"), datetime) else conv.get("created_at"),
                "updated_at": conv.get("updated_at").isoformat() if isinstance(conv.get("updated_at"), datetime) else conv.get("updated_at")
            })

        return {"conversations": result, "count": len(result)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list conversations: {str(e)}")

@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get a specific conversation with all exchanges."""
    bridge = get_bridge()
    db = bridge.get_database_manager()

    try:
        data = db.load_conversation(conversation_id)

        if not data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Convert to serializable format
        conversation = data['conversation']
        exchanges = data['exchanges']

        # Load config.yaml to get agent models
        import yaml
        from pathlib import Path
        config_path = Path(__file__).parent.parent.parent / 'config.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Extract agent models based on agent IDs
        agent_a_id = conversation.get("agent_a_id")
        agent_b_id = conversation.get("agent_b_id")
        agent_a_model = config['agents'].get(agent_a_id, {}).get('model', 'claude-sonnet-4-5-20250929')
        agent_b_model = config['agents'].get(agent_b_id, {}).get('model', 'claude-sonnet-4-5-20250929')

        return {
            "id": str(conversation.get("id")),
            "title": conversation.get("title"),
            "initial_prompt": conversation.get("initial_prompt"),
            "agent_a_id": agent_a_id,
            "agent_a_name": conversation.get("agent_a_name"),
            "agent_a_model": agent_a_model,
            "agent_b_id": agent_b_id,
            "agent_b_name": conversation.get("agent_b_name"),
            "agent_b_model": agent_b_model,
            "total_turns": conversation.get("total_turns", 0),
            "total_tokens": conversation.get("total_tokens", 0),
            "status": conversation.get("status"),
            "tags": conversation.get("tags", []),
            "created_at": conversation.get("created_at").isoformat() if isinstance(conversation.get("created_at"), datetime) else conversation.get("created_at"),
            "updated_at": conversation.get("updated_at").isoformat() if isinstance(conversation.get("updated_at"), datetime) else conversation.get("updated_at"),
            "exchanges": [
                {
                    "turn_number": ex.get("turn_number"),
                    "agent_name": ex.get("agent_name"),
                    "thinking_content": ex.get("thinking_content"),
                    "response_content": ex.get("response_content"),
                    "tokens_used": ex.get("tokens_used", 0),
                    "created_at": ex.get("created_at").isoformat() if isinstance(ex.get("created_at"), datetime) else ex.get("created_at")
                }
                for ex in exchanges
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load conversation: {str(e)}")

@app.post("/api/conversations")
async def create_conversation(request: NewConversationRequest):
    """Create a new conversation."""
    bridge = get_bridge()

    try:
        # Generate prompt if requested and not provided
        initial_prompt = request.initial_prompt
        tags = request.tags or []

        if request.generate_prompt and not initial_prompt:
            metadata_extractor = bridge.get_metadata_extractor()
            if metadata_extractor:
                # Use AI to generate prompt from title
                initial_prompt = metadata_extractor.generate_initial_prompt(request.title)
                if not tags:
                    tags = metadata_extractor.extract_tags_from_title(request.title)
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Automatic prompt generation not available. Provide initial_prompt manually."
                )

        if not initial_prompt:
            raise HTTPException(status_code=400, detail="initial_prompt is required")

        # Create conversation
        conv_manager = bridge.create_conversation_manager()

        # Get agent config from config.yaml
        import yaml
        from pathlib import Path
        config_path = Path(__file__).parent.parent.parent / 'config.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        agent_a_config = config['agents']['agent_a']
        agent_b_config = config['agents']['agent_b']

        conversation_id = conv_manager.start_new_conversation(
            title=request.title,
            initial_prompt=initial_prompt,
            agent_a_id=agent_a_config['id'],
            agent_a_name=agent_a_config['name'],
            agent_b_id=agent_b_config['id'],
            agent_b_name=agent_b_config['name'],
            tags=tags
        )

        return {
            "id": conversation_id,
            "title": request.title,
            "initial_prompt": initial_prompt,
            "tags": tags,
            "message": "Conversation created successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")

@app.post("/api/conversations/{conversation_id}/continue")
async def continue_conversation(conversation_id: str, request: ContinueConversationRequest):
    """Continue an existing conversation (start the agent exchange)."""
    # This endpoint just validates the conversation exists
    # Actual conversation happens via WebSocket
    bridge = get_bridge()
    db = bridge.get_database_manager()

    try:
        data = db.load_conversation(conversation_id)

        if not data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {
            "id": conversation_id,
            "message": "Ready to continue. Connect via WebSocket to start conversation.",
            "websocket_url": f"/ws/conversation/{conversation_id}"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to prepare conversation: {str(e)}")

@app.post("/api/search")
async def search_conversations(request: SearchRequest):
    """Semantic search across conversations."""
    bridge = get_bridge()
    browser = bridge.get_conversation_browser()

    try:
        results = browser.search(query=request.query, limit=request.limit)

        return {
            "query": request.query,
            "results": [
                {
                    "id": str(r.get("id")),
                    "title": r.get("title"),
                    "turn_number": r.get("turn_number"),
                    "agent_name": r.get("agent_name"),
                    "response_content": r.get("response_content", "")[:200],
                    "similarity_score": r.get("similarity_score", 0),
                    "created_at": r.get("created_at").isoformat() if isinstance(r.get("created_at"), datetime) else r.get("created_at")
                }
                for r in results
            ],
            "count": len(results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    bridge = get_bridge()
    db = bridge.get_database_manager()

    try:
        success = db.delete_conversation(conversation_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete conversation")

        return {"message": "Conversation deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")

@app.post("/api/generate-prompt")
async def generate_prompt(request: GeneratePromptRequest):
    """Generate initial prompt and tags from title using AI."""
    bridge = get_bridge()
    metadata_extractor = bridge.get_metadata_extractor()

    if not metadata_extractor:
        raise HTTPException(
            status_code=503,
            detail="AI prompt generation not available. Configure OpenAI API key."
        )

    try:
        prompt = metadata_extractor.generate_initial_prompt(request.title)
        tags = metadata_extractor.extract_tags_from_title(request.title)

        return {
            "title": request.title,
            "generated_prompt": prompt,
            "suggested_tags": tags
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate prompt: {str(e)}")

# WebSocket endpoint for live conversation streaming
@app.websocket("/ws/conversation/{conversation_id}")
async def conversation_websocket(websocket: WebSocket, conversation_id: str):
    """WebSocket endpoint for real-time conversation streaming."""
    await websocket.accept()

    handler = ConversationStreamHandler(conversation_id)

    try:
        await handler.handle_connection(websocket)
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for conversation {conversation_id}")
    except Exception as e:
        # Print full traceback for debugging
        print(f"WebSocket error for conversation {conversation_id}:")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception message: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()

        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e) if str(e) else f"{type(e).__name__} occurred"
            })
        except:
            pass
    finally:
        await handler.cleanup()

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    print("🚀 Claude Agent Chat API starting...")
    print("📊 Connecting to databases...")

    try:
        bridge = get_bridge()
        print("✅ Backend bridge initialized")
        print("✅ API ready at http://localhost:8000")
        print("📚 API docs at http://localhost:8000/docs")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("🛑 Shutting down API...")
    bridge = get_bridge()
    bridge.close()
    print("✅ Cleanup complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
