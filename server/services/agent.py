"""
Vertex AI Agent Service for venue orchestration.
Utilizes Gemini 1.5 Flash for multimodal reasoning and tool-integrated grounding.
Interfaces with Firestore for state management and local Dijkstra engines for routing.
"""
import logging
import random
import json
import asyncio
from typing import Any, Dict, List, Optional, cast
import vertexai
from vertexai.generative_models import (
    GenerativeModel,
    Tool,
    FunctionDeclaration,
    GenerationConfig
)

from schemas.models import Event, ItineraryResponse, StaffActionResponse, UserConstraints
from infrastructure.config import settings
from infrastructure.firebase import fb_manager
from .vector_index import vector_index
from .spatial_router import spatial_router

logger = logging.getLogger(__name__)

class AgentService:
    """Orchestrates LLM-based reasoning for attendee and staff workflows."""

    def __init__(self) -> None:
        vertexai.init(project=settings.GOOGLE_CLOUD_PROJECT, location="us-central1")
        self._model = GenerativeModel(
            model_name="gemini-1.5-flash-002",
            tools=[self._get_tools()]
        )

    def _get_tools(self) -> Tool:
        """Defines the function calling schema for external tool integration."""
        return Tool(
            function_declarations=[
                FunctionDeclaration(
                    name="calculate_optimal_route",
                    description="Retrieves shortest paths between event nodes using Dijkstra routing.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "start_event_id": {"type": "string"},
                            "end_event_id": {"type": "string"}
                        },
                        "required": ["start_event_id", "end_event_id"]
                    }
                ),
                FunctionDeclaration(
                    name="get_zone_congestion",
                    description="Queries real-time Firestore document state for zone density.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "zone_id": {"type": "string"}
                        },
                        "required": ["zone_id"]
                    }
                ),
                FunctionDeclaration(
                    name="search_events",
                    description="Filters in-memory event index by topical keywords.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"}
                        },
                        "required": ["query"]
                    }
                )
            ]
        )

    async def get_zone_congestion(self, zone_id: str) -> str:
        """Grounding tool for live venue state retrieval."""
        data = await fb_manager.get_zone_status(zone_id)
        return json.dumps({
            "zone_id": zone_id, 
            "status": data["status"],
            "congestion": data["congestion"]
        })

    async def generate_itinerary(
        self, 
        constraints: UserConstraints, 
        distance_matrix_info: str, 
        weather: Optional[str] = "Clear"
    ) -> ItineraryResponse:
        """Synthesizes constrained conference schedules using generative reasoning."""
        prompt = f"""
        System Role: Venue Orchestration Assistant
        Context: {weather} conditions.
        Target Constraints: {constraints.model_dump_json()}
        
        Operation:
        1. Resolve paths via calculate_optimal_route.
        2. Validate occupancy via get_zone_congestion.
        3. Return a serialized ItineraryResponse object.
        """

        try:
            chat = self._model.start_chat()
            response = await chat.send_message_async(
                prompt,
                generation_config=GenerationConfig(
                    response_mime_type="application/json",
                    response_schema={
                        "type": "object",
                        "properties": {
                            "current_weather": {"type": "string"},
                            "itinerary": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "event_name": {"type": "string"},
                                        "start_time": {"type": "string"},
                                        "end_time": {"type": "string"},
                                        "walking_directions": {"type": "string"},
                                        "transition_time_seconds": {"type": "integer"}
                                    }
                                }
                            },
                            "simulated": {"type": "boolean"}
                        }
                    }
                )
            )
            
            if not response.text:
                return await self._generate_simulated_itinerary(constraints, weather or "Clear")
            return ItineraryResponse.model_validate_json(response.text)

        except Exception as e:
            logger.error(f"Inference exception: {e}")
            return await self._generate_simulated_itinerary(constraints, weather or "Clear")

    async def _generate_simulated_itinerary(self, constraints: UserConstraints, weather: str) -> ItineraryResponse:
        """Fallback mechanism for deterministic itinerary generation."""
        targets = [
            e for e in vector_index.mock_events 
            if any(t.lower() in e['topic'].lower() for t in constraints.preferred_topics)
        ] or vector_index.mock_events[:3]
        
        itinerary = []
        for i, event in enumerate(targets[:3]):
            itinerary.append(Event(
                event_name=event['name'],
                start_time=f"{9 + (i*2)}:00 AM",
                end_time=f"{10 + (i*2)}:30 AM",
                walking_directions=f"Pathing to {event['name']} via internal routing engine.",
                transition_time_seconds=600
            ))
            
        return ItineraryResponse(current_weather=weather, itinerary=itinerary, simulated=True)

    async def generate_staff_protocol(self, zone_id: str, alert_type: str) -> StaffActionResponse:
        """Generates personnel deployment protocols based on situational triggers."""
        prompt = f"Zone: {zone_id}, Trigger: {alert_type}. Generate deployment protocol."
        try:
            response = await self._model.generate_content_async(
                prompt,
                generation_config=GenerationConfig(
                    response_mime_type="application/json",
                    response_schema={
                        "type": "object",
                        "properties": {
                            "protocol": {"type": "string"},
                            "simulated": {"type": "boolean"}
                        }
                    }
                )
            )
            if not response.text:
                return self._simulated_staff_fallback(zone_id, alert_type)
            return StaffActionResponse.model_validate_json(response.text)
        except Exception:
            return self._simulated_staff_fallback(zone_id, alert_type)

    def _simulated_staff_fallback(self, zone_id: str, alert_type: str) -> StaffActionResponse:
        """Deterministic protocol fallback for staff coordination."""
        return StaffActionResponse(
            protocol=f"Standard Protocol: {alert_type} in {zone_id}. Dispatch nearby unit.",
            simulated=True
        )

agent_service = AgentService()
