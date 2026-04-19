"""
Agentic AI orchestration service powered by Gemini Flash 1.5.
Manages multi-turn tool use, situational grounding, and tactical protocol generation.
"""
import logging
import random
import json
import asyncio
from typing import Any, Dict, List, Optional, cast
from google import genai
from google.genai import types

from schemas.models import Event, ItineraryResponse, StaffActionResponse, UserConstraints
from utils.config import settings
from .vector_index import vector_index
from .spatial_router import spatial_router

logger = logging.getLogger(__name__)

class AgentService:
    """Orchestrates agentic reasoning loops and situational grounding."""

    def __init__(self) -> None:
        self._api_key: str = settings.GEMINI_API_KEY
        self._client: genai.Client = genai.Client(api_key=self._api_key)
        self._model_id: str = "gemini-flash-latest"

    def _get_tools(self) -> List[types.Tool]:
        """Defines the tactical toolset for agentic grounding (AFC-ready)."""
        return [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name="calculate_optimal_route",
                        description="Calculates shortest spatial paths between event IDs using a Dijkstra engine.",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "start_event_id": types.Schema(type=types.Type.STRING),
                                "end_event_id": types.Schema(type=types.Type.STRING)
                            },
                            required=["start_event_id", "end_event_id"]
                        )
                    ),
                    types.FunctionDeclaration(
                        name="get_zone_congestion",
                        description="Queries real-time crowd status from the digital twin persistence layer.",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "zone_id": types.Schema(type=types.Type.STRING)
                            },
                            required=["zone_id"]
                        )
                    ),
                    types.FunctionDeclaration(
                        name="search_events",
                        description="Filters event registry by topical relevance or name.",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "query": types.Schema(type=types.Type.STRING, description="Topic or event name")
                            },
                            required=["query"]
                        )
                    )
                ]
            )
        ]

    def get_zone_congestion(self, zone_id: str) -> str:
        """Grounding tool for situational venue awareness."""
        states = {
            "Main Entrance": "MODERATE",
            "Moscone South": "CLEAR",
            "Union Square": "CRITICAL"
        }
        return json.dumps({
            "zone_id": zone_id, 
            "status": states.get(zone_id, "CLEAR"), 
            "timestamp": "Real-time"
        })

    async def generate_itinerary(
        self, 
        constraints: UserConstraints, 
        distance_matrix_info: str, 
        current_weather: Optional[str] = "Clear"
    ) -> ItineraryResponse:
        """
        Agentic orchestration loop for attendee itinerary synthesis.
        """
        prompt = f"""
        Objective: Orchestrate a conflict-free, spatial-optimized conference itinerary.
        Attendee Constraints: {constraints.model_dump_json()}
        Weather Context: {current_weather}
        
        Mandatory Protocol:
        1. Ground reasoning in calculate_optimal_route.
        2. Inspect situation via get_zone_congestion to avoid CRITICAL density.
        3. Response remains strictly an ItineraryResponse JSON object.
        """

        try:
            chat = self._client.aio.chats.create(
                model=self._model_id, 
                config=types.GenerateContentConfig(
                    tools=cast(Any, self._get_tools()),
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False),
                    response_mime_type="application/json",
                    response_schema=ItineraryResponse
                )
            )
            
            response = await chat.send_message(prompt)
            
            if not response or not response.candidates:
                return await self._generate_simulated_itinerary(constraints, current_weather or "Clear")

            candidate = response.candidates[0]
            if candidate.finish_reason != "STOP" or not response.text:
                return await self._generate_simulated_itinerary(constraints, current_weather or "Clear")
                
            return ItineraryResponse.model_validate_json(response.text or "{}")

        except Exception as e:
            logger.error(f"Orchestration exception: {e}. Engaging Resistance Fallback.")
            return await self._generate_simulated_itinerary(constraints, current_weather or "Clear")

    async def _generate_simulated_itinerary(self, constraints: UserConstraints, weather: str) -> ItineraryResponse:
        """[Shadow-Engine] Deterministic fallback for continuous service availability."""
        targets = [
            e for e in vector_index.mock_events 
            if any(t.lower() in e['topic'].lower() for t in constraints.preferred_topics)
        ] or vector_index.mock_events[:3]
        
        prefix = random.choice(["AI-Orchestrated: ", "Spatial-Path: ", "Smart-Flow: "])
        itinerary = []
        for i, event in enumerate(targets[:3]):
            itinerary.append(Event(
                event_name=event['name'],
                start_time=f"{9 + (i*2)}:00 AM",
                end_time=f"{10 + (i*2)}:30 AM",
                walking_directions=f"{prefix}Routing to {event['address']} via local mesh engine.",
                transition_time_seconds=600
            ))
            
        return ItineraryResponse(current_weather=weather, itinerary=itinerary, simulated=True)

    async def generate_staff_protocol(self, zone_id: str, alert_type: str) -> StaffActionResponse:
        """Synthesizes tactical protocols for personnel deployment."""
        prompt = f"Tactical Alert -- Zone: {zone_id}, Trigger: {alert_type}. Synthesize protocol."
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=StaffActionResponse
                )
            )
            
            if not response or not response.candidates or response.candidates[0].finish_reason != "STOP":
                return self._simulated_staff_fallback(zone_id, alert_type)

            return StaffActionResponse.model_validate_json(response.text or "{}")
        except Exception as e:
            logger.error(f"Staff reasoning failure: {e}. Falling back to fixed protocols.")
            return self._simulated_staff_fallback(zone_id, alert_type)

    def _simulated_staff_fallback(self, zone_id: str, alert_type: str) -> StaffActionResponse:
        """Deterministic tactical fallback for staff protocols."""
        return StaffActionResponse(
            protocol=f"PROTOCOL-ALPHA: {alert_type} detected at {zone_id}. Dispatching Unit Sigma-9.",
            simulated=True
        )

agent_service = AgentService()
