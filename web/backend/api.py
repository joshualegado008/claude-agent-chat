"""
FastAPI Web Backend - REST API for Claude Agent Chat
Provides HTTP and WebSocket endpoints for the web frontend
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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
    agent_ids: Optional[List[str]] = None  # For dynamic agent selection
    agent_selection_metadata: Optional[Dict] = None  # Metadata from agent selection (refined topic, expertise)

class ContinueConversationRequest(BaseModel):
    continuation_prompt: Optional[str] = None

class SearchRequest(BaseModel):
    query: str
    limit: int = 10

class GeneratePromptRequest(BaseModel):
    title: str

class SelectAgentsRequest(BaseModel):
    topic: str

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
        db = bridge.get_database_manager()
        result = []
        for conv in conversations:
            conv_id = str(conv.get("id"))
            # Check if this conversation has a summary
            has_summary = db.conversation_has_summary(conv_id)

            result.append({
                "id": conv_id,
                "title": conv.get("title"),
                "initial_prompt": conv.get("initial_prompt"),
                "agent_a_name": conv.get("agent_a_name"),
                "agent_b_name": conv.get("agent_b_name"),
                "total_turns": conv.get("total_turns", 0),
                "total_tokens": conv.get("total_tokens", 0),
                "status": conv.get("status"),
                "tags": conv.get("tags", []),
                "has_summary": has_summary,
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

        # Extract agent qualifications from markdown files
        def get_agent_qualification(agent_id: str) -> Optional[str]:
            """Extract classification/specialization from agent markdown file."""
            try:
                # Check both static and dynamic agent paths
                static_path = Path(__file__).parent.parent.parent / '.claude' / 'agents' / f'{agent_id}.md'
                dynamic_path = Path(__file__).parent.parent.parent / '.claude' / 'agents' / 'dynamic' / f'{agent_id}.md'

                agent_file = static_path if static_path.exists() else (dynamic_path if dynamic_path.exists() else None)

                if not agent_file:
                    return None

                # Read markdown file and extract classification from footer
                with open(agent_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Look for "**Classification**: " line near the end
                for line in content.split('\n'):
                    if line.startswith('**Classification**:'):
                        # Extract text after "**Classification**: "
                        classification = line.split('**Classification**:')[1].strip()
                        # Return just the primary classification (e.g., "Public Policy" from "Humanities → Public Policy")
                        if '→' in classification:
                            parts = classification.split('→')
                            return parts[1].strip() if len(parts) > 1 else parts[0].strip()
                        return classification

                return None
            except Exception as e:
                print(f"Warning: Could not extract qualification for {agent_id}: {e}")
                return None

        agent_a_qualification = get_agent_qualification(agent_a_id)
        agent_b_qualification = get_agent_qualification(agent_b_id)

        # Build agents array from JSONB column if available, otherwise construct from agent_a/agent_b
        agents_array = conversation.get("agents")
        if agents_array:
            # Multi-agent format - enrich with qualifications and models
            agents = []
            for agent_data in agents_array:
                agent_id = agent_data.get('id')
                agent_qualification = agent_data.get('qualification') or get_agent_qualification(agent_id)
                agent_model = config['agents'].get(agent_id, {}).get('model', 'claude-sonnet-4-5-20250929')

                agents.append({
                    'id': agent_id,
                    'name': agent_data.get('name'),
                    'qualification': agent_qualification,
                    'model': agent_model
                })
        else:
            # Legacy format - construct from agent_a/agent_b
            agents = [
                {
                    'id': agent_a_id,
                    'name': conversation.get("agent_a_name"),
                    'qualification': agent_a_qualification,
                    'model': agent_a_model
                },
                {
                    'id': agent_b_id,
                    'name': conversation.get("agent_b_name"),
                    'qualification': agent_b_qualification,
                    'model': agent_b_model
                }
            ]

        # Check if this conversation has a summary
        has_summary = db.conversation_has_summary(conversation_id)

        return {
            "id": str(conversation.get("id")),
            "title": conversation.get("title"),
            "initial_prompt": conversation.get("initial_prompt"),
            "prompt_metadata": conversation.get("prompt_metadata"),  # Include prompt evolution metadata
            # Legacy fields for backward compatibility
            "agent_a_id": agent_a_id,
            "agent_a_name": conversation.get("agent_a_name"),
            "agent_a_qualification": agent_a_qualification,
            "agent_a_model": agent_a_model,
            "agent_b_id": agent_b_id,
            "agent_b_name": conversation.get("agent_b_name"),
            "agent_b_qualification": agent_b_qualification,
            "agent_b_model": agent_b_model,
            # New multi-agent field
            "agents": agents,
            "total_turns": conversation.get("total_turns", 0),
            "total_tokens": conversation.get("total_tokens", 0),
            "status": conversation.get("status"),
            "tags": conversation.get("tags", []),
            "has_summary": has_summary,
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
        concise_title = request.title  # Default to user's input

        # Get metadata extractor for AI-powered title/prompt generation
        metadata_extractor = bridge.get_metadata_extractor()

        # Build prompt_metadata to track the evolution
        prompt_metadata = {
            "original_user_input": request.title,
            "timestamps": {}
        }

        if request.generate_prompt:
            if not metadata_extractor:
                raise HTTPException(
                    status_code=400,
                    detail="Automatic prompt generation not available. Provide initial_prompt manually."
                )

            # Generate concise title from user's input (may be long)
            concise_title = metadata_extractor.generate_concise_title(request.title)
            prompt_metadata["generated_title"] = concise_title
            prompt_metadata["timestamps"]["title_generated_at"] = datetime.now().isoformat()

            # Generate initial prompt if not provided
            if not initial_prompt:
                initial_prompt = metadata_extractor.generate_initial_prompt(request.title)
                prompt_metadata["generated_prompt"] = initial_prompt
                prompt_metadata["timestamps"]["prompt_generated_at"] = datetime.now().isoformat()

            # Extract tags if not provided
            if not tags:
                tags = metadata_extractor.extract_tags_from_title(request.title)
                prompt_metadata["generated_tags"] = tags
        else:
            # If not auto-generating, still try to create concise title for long inputs
            if metadata_extractor and len(request.title) > 100:
                concise_title = metadata_extractor.generate_concise_title(request.title)
                prompt_metadata["generated_title"] = concise_title

        if not initial_prompt:
            raise HTTPException(status_code=400, detail="initial_prompt is required")

        # Create conversation
        conv_manager = bridge.create_conversation_manager()

        # Determine which agents to use
        if request.agent_ids and len(request.agent_ids) >= 1:
            # Use dynamically selected agents (supports N agents, not just 2)
            coordinator = bridge.get_agent_coordinator()
            if not coordinator:
                raise HTTPException(
                    status_code=400,
                    detail="Dynamic agents requested but coordinator not available"
                )

            # Get agent profiles from coordinator for ALL selected agents
            agents = []
            for agent_id in request.agent_ids:
                agent_profile = coordinator.active_agents.get(agent_id)
                if not agent_profile:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Agent {agent_id} not found in coordinator"
                    )

                # Extract qualification from agent's primary_class
                qualification = agent_profile.primary_class

                agents.append({
                    'id': agent_id,
                    'name': agent_profile.name,
                    'qualification': qualification
                })

            # Add agent selection metadata if provided (refined topic, expertise analysis)
            if request.agent_selection_metadata:
                prompt_metadata["refined_topic"] = request.agent_selection_metadata.get("refined_topic")
                prompt_metadata["expertise_requirements"] = request.agent_selection_metadata.get("expertise_requirements")
                prompt_metadata["timestamps"]["topic_refined_at"] = datetime.now().isoformat()

            # Create conversation with agents array
            conversation_id = conv_manager.start_new_conversation(
                title=concise_title,  # Use concise title for UI
                initial_prompt=initial_prompt,  # Full prompt for conversation
                tags=tags,
                agents=agents,  # Pass all agents as array
                prompt_metadata=prompt_metadata  # Pass prompt evolution metadata
            )
        else:
            # Use static agents from config.yaml (legacy 2-agent format)
            import yaml
            from pathlib import Path
            config_path = Path(__file__).parent.parent.parent / 'config.yaml'
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            agent_a_config = config['agents']['agent_a']
            agent_b_config = config['agents']['agent_b']

            agent_a_id = agent_a_config['id']
            agent_a_name = agent_a_config['name']
            agent_b_id = agent_b_config['id']
            agent_b_name = agent_b_config['name']

            # Legacy 2-agent conversation
            conversation_id = conv_manager.start_new_conversation(
                title=concise_title,  # Use concise title for UI
                initial_prompt=initial_prompt,  # Full prompt for conversation
                agent_a_id=agent_a_id,
                agent_a_name=agent_a_name,
                agent_b_id=agent_b_id,
                agent_b_name=agent_b_name,
                tags=tags,
                prompt_metadata=prompt_metadata  # Pass prompt evolution metadata
            )

        return {
            "id": conversation_id,
            "title": concise_title,  # Return concise title
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

@app.get("/api/conversations/{conversation_id}/summary")
async def get_conversation_summary(conversation_id: str):
    """Get AI-generated summary for a conversation."""
    bridge = get_bridge()
    db = bridge.get_database_manager()

    try:
        # Check if conversation exists
        conversation_data = db.load_conversation(conversation_id)
        if not conversation_data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Get summary
        summary = db.get_conversation_summary(conversation_id)

        if not summary:
            raise HTTPException(status_code=404, detail="Summary not found for this conversation")

        # Convert datetime to ISO format for JSON serialization
        summary_response = {
            "id": str(summary.get("id")),
            "conversation_id": str(summary.get("conversation_id")),
            "summary_data": summary.get("summary_data"),
            "generation_model": summary.get("generation_model"),
            "input_tokens": summary.get("input_tokens"),
            "output_tokens": summary.get("output_tokens"),
            "total_tokens": summary.get("total_tokens"),
            "generation_cost": float(summary.get("generation_cost", 0.0)),
            "generation_time_ms": summary.get("generation_time_ms"),
            "generated_at": summary.get("generated_at").isoformat() if isinstance(summary.get("generated_at"), datetime) else summary.get("generated_at")
        }

        return summary_response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve summary: {str(e)}")

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

@app.post("/api/agents/select")
async def select_agents(request: SelectAgentsRequest):
    """Select dynamic agents based on conversation topic."""
    bridge = get_bridge()
    coordinator = bridge.get_agent_coordinator()

    if not coordinator:
        raise HTTPException(
            status_code=503,
            detail="Dynamic agent selection not available. Agent coordinator not initialized."
        )

    try:
        # Get agents from coordinator
        agents_profiles, metadata = await coordinator.get_or_create_agents(request.topic)

        # Serialize agent profiles
        agents_data = []
        for profile in agents_profiles:
            agent_dict = profile.to_dict()
            # Add domain icon for frontend display
            agent_dict['domain_icon'] = profile.domain.icon
            agents_data.append(agent_dict)

        return {
            "agents": agents_data,
            "metadata": metadata
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to select agents: {str(e)}")

@app.get("/api/agents/select-stream")
async def select_agents_stream(topic: str):
    """Select dynamic agents with real-time progress streaming (SSE)."""
    bridge = get_bridge()
    coordinator = bridge.get_agent_coordinator()

    if not coordinator:
        raise HTTPException(
            status_code=503,
            detail="Dynamic agent selection not available. Agent coordinator not initialized."
        )

    async def generate_progress():
        """Generator that yields Server-Sent Events with progress updates."""
        try:
            # Send initial status
            yield f"data: {json.dumps({'type': 'start', 'message': 'Starting agent selection...'})}\n\n"
            await asyncio.sleep(0)  # Force flush to client

            # Step 1: Refine topic
            yield f"data: {json.dumps({'type': 'refining_topic', 'message': 'Refining topic...'})}\n\n"
            await asyncio.sleep(0)  # Force flush to client

            # We need to manually do what get_or_create_agents does, but with progress updates
            metadata = {
                'refined_topic': '',
                'expertise_requirements': [],
                'agents_created': 0,
                'agents_reused': 0,
                'creation_cost': 0.0,
                'cache_savings': 0.0
            }

            # Refine topic
            metadata_extractor = coordinator.metadata_extractor
            refined_topic = await metadata_extractor.refine_topic(topic)
            metadata['refined_topic'] = refined_topic

            yield f"data: {json.dumps({'type': 'topic_refined', 'message': 'Topic refined', 'refined_topic': refined_topic})}\n\n"
            await asyncio.sleep(0)  # Force flush to client

            # Step 2: Analyze expertise
            yield f"data: {json.dumps({'type': 'analyzing_expertise', 'message': 'Analyzing expertise requirements...'})}\n\n"
            await asyncio.sleep(0)  # Force flush to client

            expertise_analysis = await metadata_extractor.analyze_expertise_requirements(refined_topic)
            metadata['expertise_requirements'] = expertise_analysis.get('expertise_needed', [])

            total_agents = len(metadata['expertise_requirements'])
            yield f"data: {json.dumps({'type': 'expertise_analyzed', 'message': f'Found {total_agents} expertise areas needed', 'count': total_agents})}\n\n"
            await asyncio.sleep(0)  # Force flush to client

            # Step 3: Create/reuse agents with progress updates
            agents_to_use = []

            for idx, expertise_desc in enumerate(metadata['expertise_requirements'], 1):
                yield f"data: {json.dumps({'type': 'checking_agent', 'message': f'Checking agent {idx}/{total_agents}...', 'current': idx, 'total': total_agents})}\n\n"
                await asyncio.sleep(0)  # Force flush to client

                # Check deduplication
                decision = coordinator.deduplication.check_before_create(
                    expertise_desc,
                    strict=True
                )

                if decision['action'] == 'reuse':
                    # Reuse existing agent
                    agent_id = decision['agent_id']
                    agent = coordinator.active_agents[agent_id]

                    yield f"data: {json.dumps({'type': 'agent_reused', 'message': f'Reusing: {agent.name}', 'agent_name': agent.name, 'current': idx, 'total': total_agents})}\n\n"
                    await asyncio.sleep(0)  # Force flush to client

                    agents_to_use.append(agent)
                    metadata['agents_reused'] += 1
                    metadata['cache_savings'] += 0.004

                elif decision['action'] in ['create', 'create_with_warning']:
                    # Create new agent
                    yield f"data: {json.dumps({'type': 'creating_agent', 'message': f'Creating agent {idx}/{total_agents}...', 'expertise': expertise_desc[:60], 'current': idx, 'total': total_agents})}\n\n"
                    await asyncio.sleep(0)  # Force flush to client before long operation

                    # Create agent (this takes 10-15 seconds with multiple Claude API calls)
                    agent = await coordinator.factory.create_agent(
                        expertise_desc,
                        classification=decision.get('classification'),
                        context=refined_topic
                    )

                    # Register in all systems
                    coordinator.active_agents[agent.agent_id] = agent
                    coordinator.deduplication.register_agent(agent)
                    coordinator.rating_system.register_agent(agent.agent_id, agent.name)
                    coordinator.store.save_agent(agent)

                    yield f"data: {json.dumps({'type': 'agent_created', 'message': f'Created: {agent.name}', 'agent_name': agent.name, 'domain': agent.domain.value, 'class': agent.primary_class, 'current': idx, 'total': total_agents, 'cost': coordinator.factory.get_total_cost()})}\n\n"
                    await asyncio.sleep(0)  # Force flush to client

                    agents_to_use.append(agent)
                    metadata['agents_created'] += 1
                    metadata['creation_cost'] += coordinator.factory.get_total_cost()

                else:
                    # Suggest reuse or deny
                    if decision.get('similar_agents'):
                        similar_agent, similarity = decision['similar_agents'][0]
                        agents_to_use.append(similar_agent)
                        metadata['agents_reused'] += 1

            # Mark agents as HOT
            for agent in agents_to_use:
                coordinator.lifecycle_manager.mark_hot(agent.agent_id)
                if agent.agent_id in coordinator.rating_system.performance_profiles:
                    profile = coordinator.rating_system.performance_profiles[agent.agent_id]
                    profile.last_used = datetime.now()
                    coordinator.store.save_performance_profile(profile)

            # Serialize agent profiles
            agents_data = []
            for profile in agents_to_use:
                agent_dict = profile.to_dict()
                agent_dict['domain_icon'] = profile.domain.icon
                agents_data.append(agent_dict)

            # Send final result
            result = {
                'type': 'complete',
                'agents': agents_data,
                'metadata': metadata
            }
            yield f"data: {json.dumps(result)}\n\n"
            await asyncio.sleep(0)  # Force flush to client

        except Exception as e:
            error_msg = {
                'type': 'error',
                'message': str(e)
            }
            yield f"data: {json.dumps(error_msg)}\n\n"
            await asyncio.sleep(0)  # Force flush to client

    return StreamingResponse(
        generate_progress(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )

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
