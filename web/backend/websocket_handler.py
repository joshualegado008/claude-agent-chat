"""
WebSocket Handler - Real-time conversation streaming
Handles live agent-to-agent conversations with streaming responses
"""

import asyncio
import json
from typing import Optional, Dict, Any
from fastapi import WebSocket
import yaml
from pathlib import Path

from bridge import get_bridge
from cost_calculator import CostCalculator


class ConversationStreamHandler:
    """
    Handles WebSocket connection for a single conversation.
    Streams agent responses in real-time to the web frontend.
    """

    def __init__(self, conversation_id: str):
        """
        Initialize handler for a conversation.

        Args:
            conversation_id: UUID of the conversation
        """
        self.conversation_id = conversation_id
        self.bridge = get_bridge()
        self.conv_manager = None
        self.agent_pool = None
        self.agents = []
        self.agent_qualifications = {}  # Track agent qualifications by agent name
        self.config = self._load_config()
        self.is_paused = False
        self.should_stop = False

    def _load_config(self) -> dict:
        """Load configuration from config.yaml."""
        config_path = Path(__file__).parent.parent.parent / 'config.yaml'
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    async def handle_connection(self, websocket: WebSocket):
        """
        Main handler for WebSocket connection.

        Args:
            websocket: FastAPI WebSocket connection
        """
        # Load conversation
        self.conv_manager = self.bridge.create_conversation_manager()

        if not self.conv_manager.load_conversation(self.conversation_id):
            await websocket.send_json({
                "type": "error",
                "message": "Failed to load conversation"
            })
            await websocket.close()
            return

        # Send initial conversation data
        await websocket.send_json({
            "type": "conversation_loaded",
            "data": {
                "id": self.conversation_id,
                "title": self.conv_manager.metadata.get('title'),
                "agent_a_name": self.conv_manager.metadata.get('agent_a_name'),
                "agent_b_name": self.conv_manager.metadata.get('agent_b_name'),
                "current_turn": self.conv_manager.current_turn,
                "exchanges": self.conv_manager.exchanges
            }
        })

        # Initialize agents
        self.agent_pool = self.bridge.create_agent_pool()

        try:
            # Load agents from conversation metadata (supports both multi-agent and legacy 2-agent format)
            agents_array = self.conv_manager.metadata.get('agents')

            if agents_array:
                # Multi-agent format - load all agents from array
                for agent_data in agents_array:
                    agent_id = agent_data.get('id')
                    agent_name = agent_data.get('name')
                    agent_qualification = agent_data.get('qualification')
                    if not agent_id or not agent_name:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Invalid agent data in metadata: {agent_data}"
                        })
                        return

                    agent = self.agent_pool.create_agent(agent_id, agent_name)
                    self.agents.append(agent)

                    # Track agent qualification
                    if agent_qualification:
                        self.agent_qualifications[agent_name] = agent_qualification

                    print(f"✅ Agent {agent_name} (@{agent_id}) is ready")
            else:
                # Legacy 2-agent format
                agent_a_id = self.conv_manager.metadata.get('agent_a_id')
                agent_a_name = self.conv_manager.metadata.get('agent_a_name')
                agent_b_id = self.conv_manager.metadata.get('agent_b_id')
                agent_b_name = self.conv_manager.metadata.get('agent_b_name')

                if not agent_a_id or not agent_b_id:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Agent IDs not found in conversation metadata"
                    })
                    return

                agent_a = self.agent_pool.create_agent(agent_a_id, agent_a_name)
                agent_b = self.agent_pool.create_agent(agent_b_id, agent_b_name)
                self.agents = [agent_a, agent_b]

                print(f"✅ Agent {agent_a_name} (@{agent_a_id}) is ready")
                print(f"✅ Agent {agent_b_name} (@{agent_b_id}) is ready")

            if not self.agent_pool.validate_all_agents():
                await websocket.send_json({
                    "type": "error",
                    "message": "Agent validation failed"
                })
                return

            # Send ready signal
            await websocket.send_json({
                "type": "ready",
                "message": "Agents initialized, ready to start conversation"
            })

            # Listen for client commands and run conversation
            await self._run_conversation_loop(websocket)

        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "message": f"Failed to initialize agents: {str(e)}"
            })

    async def _run_conversation_loop(self, websocket: WebSocket):
        """
        Main conversation loop - handles agent turns and client commands.

        Args:
            websocket: WebSocket connection
        """
        max_turns = self.config.get('conversation', {}).get('max_turns', 20)
        show_thinking = self.config.get('conversation', {}).get('show_thinking', True)
        start_turn = self.conv_manager.current_turn

        # Prepare initial message
        if start_turn == 0:
            # New conversation
            current_message = self.conv_manager.metadata.get('initial_prompt', '')
        else:
            # Continuing conversation
            current_message = self.conv_manager.get_context_for_continuation(window_size=5)

        # Round-robin through N agents (works for 2, 3, 4, etc.)
        current_agent_idx = start_turn % len(self.agents)
        total_tokens = 0
        total_cost = 0.0

        # Check if conversation is already at or beyond max_turns
        if start_turn >= max_turns:
            print(f"⚠️  Conversation already at max_turns ({start_turn} >= {max_turns}). Marking as complete.")
            self.conv_manager.finalize_conversation(status='completed')
            await websocket.send_json({
                "type": "conversation_complete",
                "total_turns": start_turn,
                "total_tokens": sum(ex.get('tokens_used', 0) for ex in self.conv_manager.exchanges),
                "total_cost": 0.0,
                "message": "Conversation already reached maximum turns"
            })
            return

        # Create tasks for conversation and command listening
        conversation_task = asyncio.create_task(
            self._agent_conversation(
                websocket,
                current_message,
                current_agent_idx,
                start_turn,
                max_turns,
                show_thinking,
                total_tokens,
                total_cost
            )
        )

        command_task = asyncio.create_task(
            self._listen_for_commands(websocket)
        )

        # Wait for either task to complete
        done, pending = await asyncio.wait(
            [conversation_task, command_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        # Cancel pending tasks
        for task in pending:
            task.cancel()

        # Get result from completed task
        for task in done:
            try:
                result = task.result()
            except Exception as e:
                print(f"Task error: {e}")

    async def _agent_conversation(
        self,
        websocket: WebSocket,
        current_message: str,
        current_agent_idx: int,
        start_turn: int,
        max_turns: int,
        show_thinking: bool,
        total_tokens: int,
        total_cost: float
    ):
        """
        Run the agent-to-agent conversation.

        Args:
            websocket: WebSocket connection
            current_message: Initial message or context
            current_agent_idx: Index of starting agent (0 or 1)
            start_turn: Starting turn number
            max_turns: Maximum number of turns
            show_thinking: Whether to show thinking
            total_tokens: Running token count
            total_cost: Running cost total
        """
        for turn in range(start_turn, max_turns):
            # Check for pause/stop
            while self.is_paused and not self.should_stop:
                await asyncio.sleep(0.5)

            if self.should_stop:
                await websocket.send_json({
                    "type": "conversation_stopped",
                    "turn": turn,
                    "total_tokens": total_tokens,
                    "total_cost": total_cost
                })
                break

            current_agent = self.agents[current_agent_idx]

            # Send turn start signal
            await websocket.send_json({
                "type": "turn_start",
                "turn": turn,
                "agent_name": current_agent.agent_name,
                "agent_id": current_agent.agent_id
            })

            # Stream agent response
            try:
                response_text = ""
                thinking_text = ""
                input_tokens = 0
                output_tokens = 0
                thinking_tokens = 0
                model_name = None
                temperature = 1.0
                max_tokens_setting = 0

                stream = current_agent.send_message_streaming(
                    context_messages=[],
                    message=current_message,
                    enable_thinking=show_thinking,
                    thinking_budget=5000
                )

                for content_type, chunk, info in stream:
                    # Check for pause/stop during streaming
                    while self.is_paused and not self.should_stop:
                        await asyncio.sleep(0.5)

                    if self.should_stop:
                        # Stop immediately during streaming
                        await websocket.send_json({
                            "type": "conversation_stopped",
                            "turn": turn,
                            "total_tokens": total_tokens,
                            "total_cost": total_cost,
                            "message": "Stopped during turn"
                        })
                        return

                    if content_type == 'thinking_start':
                        await websocket.send_json({
                            "type": "thinking_start",
                            "turn": turn,
                            "agent_name": current_agent.agent_name
                        })

                    elif content_type == 'thinking':
                        thinking_text += chunk
                        await websocket.send_json({
                            "type": "thinking_chunk",
                            "turn": turn,
                            "chunk": chunk
                        })

                    elif content_type == 'text':
                        response_text += chunk
                        await websocket.send_json({
                            "type": "response_chunk",
                            "turn": turn,
                            "chunk": chunk
                        })

                    elif content_type == 'tool_use':
                        # Agent is using a tool (e.g., fetching a URL)
                        await websocket.send_json({
                            "type": "tool_use",
                            "turn": turn,
                            "agent_name": current_agent.agent_name,
                            "message": chunk
                        })

                    elif content_type == 'complete':
                        input_tokens = info.get('input_tokens', 0)
                        output_tokens = info.get('output_tokens', 0)
                        thinking_tokens = info.get('thinking_tokens', 0)
                        model_name = info.get('model_name')
                        temperature = info.get('temperature', 1.0)
                        max_tokens_setting = info.get('max_tokens', 0)

                    elif content_type == 'error':
                        await websocket.send_json({
                            "type": "error",
                            "message": chunk
                        })
                        return

                # Calculate costs
                tokens = input_tokens + output_tokens
                total_tokens += tokens

                turn_cost = 0.0
                if model_name and input_tokens > 0:
                    cost_info = CostCalculator.calculate_cost(model_name, input_tokens, output_tokens)
                    turn_cost = cost_info['total_cost']
                    total_cost += turn_cost

                # Calculate context stats (for geeky mode)
                context_text = self.conv_manager.get_context_for_continuation(window_size=5)
                context_stats = {
                    'total_exchanges': len(self.conv_manager.exchanges),
                    'window_size': 5,
                    'context_chars': len(context_text),
                    'context_tokens_estimate': len(context_text) // 4,
                    'referenced_turns': list(range(max(0, len(self.conv_manager.exchanges) - 5), len(self.conv_manager.exchanges)))
                }

                # Session stats
                session_turns = turn - start_turn + 1
                avg_tokens = total_tokens // session_turns if session_turns > 0 else 0
                remaining_turns = max_turns - turn - 1
                projected_total = total_tokens + (avg_tokens * remaining_turns)
                projected_cost = total_cost * (projected_total / total_tokens) if total_tokens > 0 else 0

                session_stats = {
                    'current_turn': turn + 1,
                    'max_turns': max_turns,
                    'avg_tokens_per_turn': avg_tokens,
                    'projected_total_tokens': projected_total,
                    'projected_total_cost': projected_cost
                }

                # Send turn complete with stats
                await websocket.send_json({
                    "type": "turn_complete",
                    "turn": turn,
                    "agent_name": current_agent.agent_name,
                    "response": response_text,
                    "thinking": thinking_text,
                    "stats": {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "thinking_tokens": thinking_tokens,
                        "total_tokens": tokens,
                        "turn_cost": turn_cost,
                        "total_cost": total_cost,
                        "model_name": model_name,
                        "temperature": temperature,
                        "max_tokens": max_tokens_setting,
                        "context_stats": context_stats,
                        "session_stats": session_stats
                    }
                })

                # Save to database
                self.conv_manager.add_exchange(
                    agent_name=current_agent.agent_name,
                    agent_qualification=self.agent_qualifications.get(current_agent.agent_name),
                    response_content=response_text,
                    thinking_content=thinking_text if thinking_text else None,
                    tokens_used=tokens
                )

                # Save periodic snapshots
                if turn % 5 == 0:
                    self.conv_manager.save_snapshot()

                # Check for autonomous search triggers
                search_results_text = ""
                search_coordinator = self.bridge.get_search_coordinator()
                datetime_provider = self.bridge.get_datetime_provider()

                if search_coordinator and datetime_provider:
                    try:
                        # Check if search should be triggered
                        should_search, trigger_type, query = search_coordinator.should_search(
                            response=response_text,
                            thinking=thinking_text,
                            turn_number=turn,
                            agent_name=current_agent.agent_name
                        )

                        if should_search:
                            # Notify frontend that search is starting
                            await websocket.send_json({
                                "type": "search_triggered",
                                "turn": turn,
                                "trigger_type": trigger_type,
                                "query": query,
                                "agent_name": current_agent.agent_name
                            })

                            # Execute search
                            search_ctx = await search_coordinator.execute_search(
                                query=query,
                                agent_name=current_agent.agent_name,
                                turn_number=turn,
                                trigger_type=trigger_type
                            )

                            if search_ctx:
                                # Format results for injection
                                search_results_text = search_coordinator.format_search_for_context(search_ctx)

                                # Send search results to frontend
                                await websocket.send_json({
                                    "type": "search_complete",
                                    "turn": turn,
                                    "query": query,
                                    "sources_count": len(search_ctx.extracted_content),
                                    "citations": search_ctx.citations_added,
                                    "sources": [
                                        {
                                            "title": content.title,
                                            "url": content.url,
                                            "site": content.site,
                                            "published_date": content.published_date,
                                            "excerpt": content.excerpt
                                        }
                                        for content in search_ctx.extracted_content
                                    ]
                                })
                            else:
                                await websocket.send_json({
                                    "type": "search_failed",
                                    "turn": turn,
                                    "query": query
                                })

                    except Exception as e:
                        print(f"⚠️  Search error: {e}")
                        await websocket.send_json({
                            "type": "search_error",
                            "turn": turn,
                            "message": str(e)
                        })

                # Prepare message for next agent
                context = self.conv_manager.get_context_for_continuation(window_size=5)

                # Inject datetime context and search results if available
                additional_context = ""
                if datetime_provider:
                    additional_context += f"\n{datetime_provider.get_current_datetime()}\n"
                if search_results_text:
                    additional_context += search_results_text

                current_message = f"""{context}{additional_context}

Please respond to continue the discussion."""

                # Switch to next agent in round-robin fashion (works for N agents)
                current_agent_idx = (current_agent_idx + 1) % len(self.agents)

                # Small delay between turns
                await asyncio.sleep(1.0)

            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error during turn {turn}: {str(e)}"
                })
                break

        # Conversation complete
        self.conv_manager.finalize_conversation(status='completed')

        await websocket.send_json({
            "type": "conversation_complete",
            "total_turns": turn - start_turn + 1,
            "total_tokens": total_tokens,
            "total_cost": total_cost
        })

        # Generate conversation summary
        await self._generate_summary(websocket, total_tokens, total_cost)

    async def _listen_for_commands(self, websocket: WebSocket):
        """
        Listen for commands from the client (pause, resume, stop).

        Args:
            websocket: WebSocket connection
        """
        try:
            while True:
                message = await websocket.receive_json()
                command = message.get('command')

                if command == 'pause':
                    self.is_paused = True
                    # Update status to 'paused' in database
                    if self.conv_manager:
                        self.conv_manager.finalize_conversation(status='paused')
                    await websocket.send_json({
                        "type": "paused",
                        "message": "Conversation paused"
                    })

                elif command == 'resume':
                    self.is_paused = False
                    # Update status back to 'active' in database
                    if self.conv_manager:
                        self.conv_manager.finalize_conversation(status='active')
                    await websocket.send_json({
                        "type": "resumed",
                        "message": "Conversation resumed"
                    })

                elif command == 'stop':
                    self.should_stop = True
                    self.is_paused = False
                    # Immediately finalize conversation as completed (user explicitly stopped)
                    if self.conv_manager:
                        self.conv_manager.finalize_conversation(status='completed')
                    await websocket.send_json({
                        "type": "stopped",
                        "message": "Conversation stopped"
                    })
                    break

                elif command == 'inject':
                    # Inject user content into the conversation
                    content = message.get('content', '').strip()

                    if not content:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Cannot inject empty content"
                        })
                        continue

                    if self.conv_manager:
                        try:
                            # Use the existing inject_user_content method from conversation_manager
                            self.conv_manager.inject_user_content(content)

                            print(f"💬 User content injected: {content[:100]}...")

                            await websocket.send_json({
                                "type": "injected",
                                "content": content,
                                "turn": self.conv_manager.current_turn,
                                "message": "Content injected successfully"
                            })
                        except Exception as e:
                            print(f"   ❌ Error injecting content: {e}")
                            await websocket.send_json({
                                "type": "error",
                                "message": f"Failed to inject content: {str(e)}"
                            })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Conversation manager not available"
                        })

                elif command == 'get_metadata':
                    # Extract rich metadata if available
                    metadata_extractor = self.bridge.get_metadata_extractor()

                    # Debug logging
                    print(f"🔍 DEBUG: get_metadata command received")
                    print(f"   metadata_extractor: {metadata_extractor}")
                    print(f"   metadata_extractor type: {type(metadata_extractor)}")
                    print(f"   self.conv_manager: {self.conv_manager}")
                    print(f"   self.conv_manager type: {type(self.conv_manager)}")
                    if self.conv_manager:
                        print(f"   conv_manager.exchanges length: {len(self.conv_manager.exchanges)}")
                        print(f"   conv_manager.metadata: {self.conv_manager.metadata}")

                    if metadata_extractor and self.conv_manager:
                        try:
                            recent_exchanges = self.conv_manager.exchanges[-10:] if self.conv_manager.exchanges else []
                            print(f"   Calling analyze_conversation_snapshot with {len(recent_exchanges)} exchanges")
                            metadata = metadata_extractor.analyze_conversation_snapshot(
                                recent_exchanges=recent_exchanges,
                                title=self.conv_manager.metadata.get('title', 'Untitled'),
                                total_turns=self.conv_manager.current_turn
                            )
                            print(f"   ✅ Metadata extracted successfully")
                            await websocket.send_json({
                                "type": "metadata",
                                "data": metadata
                            })
                        except Exception as e:
                            print(f"   ❌ Error extracting metadata: {e}")
                            await websocket.send_json({
                                "type": "error",
                                "message": f"Failed to extract metadata: {str(e)}"
                            })
                    else:
                        print(f"   ❌ Condition failed: metadata_extractor={bool(metadata_extractor)}, conv_manager={bool(self.conv_manager)}")
                        await websocket.send_json({
                            "type": "metadata_unavailable",
                            "message": "Metadata extraction not available"
                        })

        except Exception as e:
            print(f"Command listener error: {e}")

    async def _generate_summary(
        self,
        websocket: WebSocket,
        total_tokens: int,
        total_cost: float
    ):
        """
        Generate comprehensive conversation summary using GPT-4o-mini.

        Args:
            websocket: WebSocket connection
            total_tokens: Total tokens used in conversation
            total_cost: Total cost of conversation
        """
        # Check if summarizer is available
        summarizer = self.bridge.get_summarizer()

        if not summarizer:
            print("⚠️  Conversation summarizer not available, skipping summary generation")
            await websocket.send_json({
                "type": "summary_unavailable",
                "message": "Summary generation not available"
            })
            return

        try:
            # Notify client that summary generation is starting
            await websocket.send_json({
                "type": "summary_generation_start",
                "message": "Generating conversation summary..."
            })

            print(f"\n📊 Generating conversation summary for {self.conversation_id}...")

            # Get conversation data
            conversation_title = self.conv_manager.metadata.get('title', 'Untitled')
            initial_prompt = self.conv_manager.metadata.get('initial_prompt', '')
            exchanges = self.conv_manager.exchanges
            total_turns = self.conv_manager.current_turn

            # Get agents data
            agents_array = self.conv_manager.metadata.get('agents')
            if not agents_array:
                # Fallback to legacy format
                agents_array = [
                    {
                        'id': self.conv_manager.metadata.get('agent_a_id'),
                        'name': self.conv_manager.metadata.get('agent_a_name'),
                        'qualification': None
                    },
                    {
                        'id': self.conv_manager.metadata.get('agent_b_id'),
                        'name': self.conv_manager.metadata.get('agent_b_name'),
                        'qualification': None
                    }
                ]

            # Generate summary
            result = summarizer.generate_summary(
                conversation_title=conversation_title,
                initial_prompt=initial_prompt,
                exchanges=exchanges,
                agents=agents_array,
                total_turns=total_turns,
                total_tokens=total_tokens,
                total_cost=total_cost
            )

            # Save summary to database
            db = self.bridge.get_database_manager()
            summary_id = db.save_conversation_summary(
                conversation_id=self.conversation_id,
                summary_data=result['summary_data'],
                generation_model='gpt-4o-mini',
                input_tokens=result['summary_data']['generation_metadata']['input_tokens'],
                output_tokens=result['summary_data']['generation_metadata']['output_tokens'],
                total_tokens=result['tokens_used'],
                generation_cost=result['generation_cost'],
                generation_time_ms=result['generation_time_ms']
            )

            print(f"   ✅ Summary generated successfully!")
            print(f"   Tokens: {result['tokens_used']}")
            print(f"   Cost: ${result['generation_cost']:.4f}")
            print(f"   Time: {result['generation_time_ms']}ms")
            print(f"   Summary ID: {summary_id}")

            # Send summary to client
            await websocket.send_json({
                "type": "summary_generated",
                "summary": result['summary_data'],
                "metadata": {
                    "summary_id": summary_id,
                    "tokens_used": result['tokens_used'],
                    "generation_cost": result['generation_cost'],
                    "generation_time_ms": result['generation_time_ms'],
                    "model": "gpt-4o-mini"
                }
            })

        except Exception as e:
            print(f"❌ Failed to generate summary: {e}")
            import traceback
            traceback.print_exc()

            await websocket.send_json({
                "type": "summary_error",
                "message": f"Failed to generate summary: {str(e)}"
            })

    async def cleanup(self):
        """Cleanup resources."""
        if self.conv_manager and not self.should_stop:
            # Check if conversation has reached or exceeded max_turns
            max_turns = self.config.get('conversation', {}).get('max_turns', 20)
            if self.conv_manager.current_turn >= max_turns:
                # Conversation completed by reaching turn limit
                print(f"✅ Cleanup: Conversation reached {self.conv_manager.current_turn} turns (max: {max_turns}), marking as completed")
                self.conv_manager.finalize_conversation(status='completed')
            elif self.is_paused:
                # User explicitly paused before disconnect
                print(f"⏸️  Cleanup: Conversation was paused at turn {self.conv_manager.current_turn}, keeping status as paused")
                # Don't change status - it's already 'paused' from the pause command
            else:
                # WebSocket disconnected mid-conversation (browser closed, network issue, etc.)
                print(f"💾 Cleanup: Conversation interrupted at turn {self.conv_manager.current_turn}, marking as paused")
                self.conv_manager.finalize_conversation(status='paused')
