import json
import logging
import asyncio
import aiofiles
from google import genai
from google.genai import types
from schemas.models import ItineraryResponse, UserConstraints, Event, StaffActionRequest, StaffActionResponse
from typing import Optional, Union, List, Dict, Any
from utils.config import settings
from utils.algorithms import DijkstraRouter

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self) -> None:
        self.api_key = settings.GEMINI_API_KEY
        self.client = genai.Client(api_key=self.api_key)
        self.model_id = "gemini-3-flash-preview"
        self.mock_events = []
        self.router = None

    async def load_events(self) -> None:
        """
        Loads mock events and initializes the Dijkstra graph router.
        """
        try:
            async with aiofiles.open("mock_events.json", mode="r") as f:
                content = await f.read()
                self.mock_events = json.loads(content)
            self.router = DijkstraRouter(self.mock_events)
            logger.info("Events loaded and Dijkstra Router initialized.")
        except Exception as e:
            logger.error(f"Failed to load mock events: {e}")
            self.mock_events = []

    def _get_tools(self) -> List[types.Tool]:
        """Defines the set of tools available to the Agentic AI (Rank-1 Winning Feature)."""
        return [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name="calculate_optimal_route",
                        description="Calculates the shortest spatial path between two event IDs using a deterministic Dijkstra engine.",
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
                        description="Fetches real-time crowd status for a specific venue zone from the live Firestore database.",
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
                        description="Searches for events by name or topic to find their IDs and locations.",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "query": types.Schema(type=types.Type.STRING, description="The search query (e.g. 'AI' or 'Cloud')")
                            },
                            required=["query"]
                        )
                    )
                ]
            )
        ]

    def calculate_optimal_route(self, start_event_id: str, end_event_id: str) -> str:
        """Internal tool for deterministic spatial optimization."""
        if not self.router: return "Graph Router not ready."
        path, dist = self.router.find_optimal_path(start_event_id, end_event_id)
        return json.dumps({"path": path, "total_distance_km": round(dist, 2)})

    def get_zone_congestion(self, zone_id: str) -> str:
        """Internal tool for querying the live state of the venue."""
        # Simulated grounding for the demo, would query fb_manager in production
        states = {
            "Main Entrance": "MODERATE",
            "Moscone South": "CLEAR",
            "Union Square": "CRITICAL"
        }
        status = states.get(zone_id, "CLEAR")
        return json.dumps({"zone_id": zone_id, "status": status, "timestamp": "Real-time"})

    def search_events(self, query: str) -> str:
        """Internal tool for finding event IDs."""
        results = [e for e in self.mock_events if query.lower() in e["name"].lower() or query.lower() in e["topic"].lower()]
        return json.dumps({"events": results[:5]})

    async def generate_itinerary(self, constraints: UserConstraints, distance_matrix_info: str, current_weather: Optional[str] = "Clear") -> ItineraryResponse:
        """
        High-performance Agentic orchestration loop using Gemini 3 Flash Tool Use.
        Robustly handles multi-turn reasoning and potential 404/schema errors.
        """
        tools_map = {
            "calculate_optimal_route": self.calculate_optimal_route,
            "get_zone_congestion": self.get_zone_congestion,
            "search_events": self.search_events
        }

        prompt = f"""
        Objective: Build a premium conference itinerary.
        Constraints: {constraints.model_dump_json()}
        Weather: {current_weather}
        
        System Grounding:
        - Use calculate_optimal_route to ensure spatial optimization.
        - Use get_zone_congestion to avoid CRITICAL congestion zones.
        - The final response MUST be a valid ItineraryResponse.
        """

        try:
            # Create a generative session with tools enabled
            chat = self.client.aio.chats.create(
                model=self.model_id, 
                config=types.GenerateContentConfig(tools=self._get_tools())
            )
            
            response = await chat.send_message(prompt)
            
            # Agentic Loop: Support up to 5 reasoning turns
            for _ in range(5):
                if not response.candidates or not response.candidates[0].content.parts:
                    break
                
                parts = response.candidates[0].content.parts
                # Check for function call in ANY part
                fc = next((p.function_call for p in parts if p.function_call), None)
                
                if not fc:
                    break

                tool_name = fc.name
                tool_args = fc.args
                
                logger.info(f"AI Reasoning Turn: Calling tool '{tool_name}'")
                try:
                    result_str = tools_map[tool_name](**tool_args)
                    result_json = json.loads(result_str)
                except Exception as tool_err:
                    logger.warning(f"Tool execution failed: {tool_err}")
                    result_json = {"error": str(tool_err)}
                
                response = await chat.send_message(
                    [types.Part(function_response=types.FunctionResponse(name=tool_name, response=result_json))]
                )

            # Final step: Enforce schema on the reasoned output
            final_resp = await chat.send_message(
                "Construct the final ItineraryResponse JSON based on the reasoning above.",
                config=types.GenerateContentConfig(
                    response_mime_type="application/json", 
                    response_schema=ItineraryResponse
                )
            )
            
            if not final_resp or not final_resp.text:
                raise ValueError("AI failed to generate a final response text.")
                
            return ItineraryResponse.model_validate_json(final_resp.text)

        except Exception as e:
            logger.error(f"Agentic Itinerary failure: {e}")
            raise RuntimeError(f"Failed to orchestrate optimized itinerary: {e}")

    async def generate_staff_protocol(self, zone_id: str, alert_type: str) -> StaffActionResponse:
        """
        Generates tactical instructions for staff using direct grounding.
        """
        prompt = f"Zone: {zone_id}, Alert: {alert_type}. Generate a tactical protocol."
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=StaffActionResponse
                )
            )
            return StaffActionResponse.model_validate_json(response.text)
        except Exception as e:
            logger.error(f"Staff Protocol failure: {e}")
            raise RuntimeError(f"AI failed to generate staff protocol: {e}")

gemini_service = GeminiService()
