"""
Enhanced AI Service with Full Gemini Integration and Context Management
"""
import google.generativeai as genai
from google.cloud import aiplatform
import structlog
from typing import List, Dict, Any, Optional
import json
from datetime import datetime, date, timedelta
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings
from app.services.bigquery_service import bigquery_service
import redis.asyncio as redis

logger = structlog.get_logger(__name__)

class AIService:
    """Enhanced AI Service with comprehensive Gemini integration"""
    
    def __init__(self):
        logger.info("Initializing AI Service",
                   model=settings.gemini_model,
                   temperature=settings.gemini_temperature)
        
        # Configure Gemini
        genai.configure(api_key=settings.gemini_api_key)
        
        # Initialize model with custom settings
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={
                "temperature": settings.gemini_temperature,
                "top_p": settings.gemini_top_p,
                "top_k": settings.gemini_top_k,
                "max_output_tokens": settings.gemini_max_tokens,
            }
        )
        
        # Initialize conversation history storage
        self.conversation_history = {}
        
        # Initialize Redis for context caching if enabled
        if settings.use_redis_cache:
            self.redis_client = redis.from_url(settings.redis_url)
            logger.info("Redis caching enabled for AI context")
        else:
            self.redis_client = None
        
        # Initialize Vertex AI if in production
        if settings.is_production and settings.google_cloud_project:
            try:
                aiplatform.init(
                    project=settings.google_cloud_project,
                    location='us-central1'
                )
                logger.info("Vertex AI initialized for production use")
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI: {str(e)}")
        
        logger.info("AI Service initialized successfully")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_itinerary(self, trip_request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized itinerary using Gemini with retry logic"""
        try:
            logger.info("Starting itinerary generation",
                       destination=trip_request.get('destination'),
                       budget=trip_request.get('budget'))
            
            # Check cache first if enabled
            cache_key = self._generate_cache_key(trip_request)
            cached_response = await self._get_cached_response(cache_key)
            
            if cached_response:
                logger.info("Returning cached itinerary", cache_key=cache_key)
                return cached_response
            
            # Create comprehensive prompt
            prompt = self._create_enhanced_prompt(trip_request)
            
            # Log the prompt for debugging
            logger.debug("Generated prompt for Gemini", 
                        prompt_length=len(prompt),
                        destination=trip_request.get('destination'))
            
            # Generate content with Gemini
            logger.info("Calling Gemini API for itinerary generation")
            response = self.model.generate_content(prompt)
            
            # Parse and validate response
            itinerary_data = self._parse_and_validate_response(response.text, trip_request)
            
            # Enhance with additional context
            enhanced_itinerary = await self._enhance_itinerary_with_context(
                itinerary_data, 
                trip_request
            )
            
            # Store in cache if enabled
            await self._cache_response(cache_key, enhanced_itinerary)
            
            # Log to BigQuery for analytics
            await bigquery_service.log_analytics_event(
                "itinerary_generated",
                {
                    "destination": trip_request.get('destination'),
                    "budget": trip_request.get('budget'),
                    "duration": trip_request.get('duration_days'),
                    "themes": trip_request.get('themes'),
                    "model_used": settings.gemini_model
                },
                user_id=trip_request.get('user_id')
            )
            
            logger.info("Itinerary generation completed successfully",
                       destination=trip_request.get('destination'),
                       total_cost=enhanced_itinerary.get('total_estimated_cost'))
            
            return enhanced_itinerary
            
        except Exception as e:
            logger.error(f"Error generating itinerary: {str(e)}",
                        destination=trip_request.get('destination'))
            
            # Log error to BigQuery
            await bigquery_service.log_application_log({
                "level": "ERROR",
                "logger": "AIService",
                "message": f"Itinerary generation failed: {str(e)}",
                "context": trip_request,
                "error_trace": str(e)
            })
            
            # Return fallback itinerary
            return self._create_fallback_itinerary(trip_request)
    
    def _create_enhanced_prompt(self, trip_request: Dict[str, Any]) -> str:
        """Create enhanced prompt with dynamic content"""
        
        # Calculate dynamic values
        duration = trip_request.get('duration_days', 3)
        budget_per_day = trip_request['budget'] / duration
        travelers = trip_request.get('travelers_count', 1)
        themes = ', '.join(trip_request.get('themes', ['general']))
        
        # Get user preferences if available
        user_preferences = trip_request.get('user_preferences', {})
        dietary = ', '.join(user_preferences.get('dietary_restrictions', ['None']))
        language = user_preferences.get('language', 'English')
        
        prompt = f"""
        You are an expert travel planner specializing in personalized itineraries for India.
        Create a detailed, practical, and exciting {duration}-day travel itinerary with the following requirements:

        TRIP PARAMETERS:
        - Destination: {trip_request['destination']}
        - Travel Dates: {trip_request.get('start_date')} to {trip_request.get('end_date')}
        - Duration: {duration} days
        - Total Budget: ₹{trip_request['budget']} INR
        - Daily Budget: ₹{budget_per_day:.0f} INR
        - Number of Travelers: {travelers} {'person' if travelers == 1 else 'people'}
        - Trip Themes/Interests: {themes}
        - Accommodation Preference: {trip_request.get('accommodation_preference', 'Any')}
        - Transport Preference: {trip_request.get('transport_preference', 'Any')}
        - Dietary Restrictions: {dietary}
        - Language Preference: {language}
        - Special Requirements: {trip_request.get('special_requirements', 'None')}

        IMPORTANT GUIDELINES:
        1. Stay strictly within the budget of ₹{trip_request['budget']}
        2. Focus heavily on {themes} experiences
        3. Include a mix of popular attractions and hidden gems
        4. Provide specific timings, costs, and locations for everything
        5. Consider realistic travel times between locations
        6. Include local food recommendations with must-try dishes
        7. Add practical tips for each activity
        8. Suggest both budget and slightly upscale options
        9. Account for rest time and not over-pack the schedule
        10. Include emergency contacts and local tips

        RESPONSE FORMAT:
        Provide a JSON response with EXACTLY this structure:
        {{
            "trip_summary": {{
                "destination": "{trip_request['destination']}",
                "duration_days": {duration},
                "total_budget": {trip_request['budget']},
                "themes": {json.dumps(trip_request.get('themes', []))},
                "key_highlights": ["highlight1", "highlight2", "highlight3"]
            }},
            "daily_itineraries": [
                {{
                    "day_number": 1,
                    "date": "YYYY-MM-DD",
                    "day_theme": "Exploration and Arrival",
                    "weather_consideration": "Expected weather and best time to visit each place",
                    "activities": [
                        {{
                            "time_slot": "09:00-11:00",
                            "activity_name": "Activity Name",
                            "description": "Detailed description of the activity",
                            "location": {{
                                "name": "Exact Location Name",
                                "address": "Full Address",
                                "area": "Area/District",
                                "coordinates": {{"lat": 0.0, "lng": 0.0}},
                                "how_to_reach": "Specific directions"
                            }},
                            "duration_hours": 2.0,
                            "cost_per_person": 500,
                            "total_cost": {500 * travelers},
                            "category": "sightseeing/dining/shopping/adventure/cultural",
                            "booking_required": true,
                            "booking_platform": "Platform name or 'On-site'",
                            "tips": ["Tip 1", "Tip 2"],
                            "alternatives": ["Alternative if this is closed/booked"]
                        }}
                    ],
                    "meals": [
                        {{
                            "meal_type": "breakfast/lunch/dinner",
                            "time": "08:00",
                            "restaurant_name": "Restaurant Name",
                            "cuisine_type": "Cuisine Type",
                            "location": "Area",
                            "cost_estimate": {500 * travelers},
                            "must_try_dishes": ["Dish 1", "Dish 2"],
                            "dietary_options": ["Veg", "Non-veg", "Vegan"],
                            "reservation_needed": false
                        }}
                    ],
                    "accommodation": {{
                        "hotel_name": "Hotel Name",
                        "type": "hotel/hostel/resort/homestay",
                        "address": "Full Address",
                        "area": "Location Area",
                        "check_in_time": "14:00",
                        "check_out_time": "11:00",
                        "cost_per_night": 3000,
                        "total_cost": {3000 * (duration - 1)},
                        "amenities": ["WiFi", "Breakfast", "Pool", "Gym"],
                        "rating": 4.2,
                        "booking_platform": "Booking.com/Direct",
                        "cancellation_policy": "Free cancellation up to 24 hours"
                    }},
                    "transport": [
                        {{
                            "from_location": "Location A",
                            "to_location": "Location B",
                            "mode": "taxi/auto/metro/bus/walk",
                            "distance_km": 5.5,
                            "duration_minutes": 20,
                            "cost": 200,
                            "booking_app": "Uber/Ola/Local",
                            "tips": "Best time to travel, traffic considerations"
                        }}
                    ],
                    "day_total_cost": 8000,
                    "free_time_suggestions": ["Evening walk at beach", "Local market visit"]
                }}
            ],
            "accommodation_summary": {{
                "total_nights": {duration - 1},
                "total_accommodation_cost": 15000,
                "check_in_date": "{trip_request.get('start_date')}",
                "check_out_date": "{trip_request.get('end_date')}",
                "properties": [
                    {{
                        "name": "Hotel Name",
                        "nights": 3,
                        "total_cost": 9000,
                        "booking_reference": "To be confirmed"
                    }}
                ]
            }},
            "transport_summary": {{
                "arrival": {{
                    "mode": "flight/train/bus",
                    "from": "Origin City",
                    "to": "{trip_request['destination']}",
                    "departure_time": "HH:MM",
                    "arrival_time": "HH:MM",
                    "cost": 5000,
                    "booking_status": "To be confirmed"
                }},
                "departure": {{
                    "mode": "flight/train/bus",
                    "from": "{trip_request['destination']}",
                    "to": "Origin City",
                    "departure_time": "HH:MM",
                    "arrival_time": "HH:MM",
                    "cost": 5000,
                    "booking_status": "To be confirmed"
                }},
                "local_transport_cost": 2000,
                "transport_apps": ["Ola", "Uber", "Local Auto"],
                "transport_cards": ["Metro Card", "Bus Pass if applicable"]
            }},
            "cost_breakdown": {{
                "accommodation": 15000,
                "meals": 10000,
                "activities": 12000,
                "transport": 8000,
                "miscellaneous": 5000,
                "total": {trip_request['budget']},
                "cost_per_person": {trip_request['budget'] / travelers},
                "daily_average": {trip_request['budget'] / duration}
            }},
            "packing_essentials": [
                "Comfortable walking shoes",
                "Weather-appropriate clothing",
                "Sunscreen and sunglasses",
                "Power bank",
                "First aid kit",
                "Local currency in cash"
            ],
            "local_tips": [
                "Best time to visit monuments is early morning",
                "Download offline maps for navigation",
                "Keep photocopies of important documents",
                "Learn basic local language greetings",
                "Bargain at local markets",
                "Stay hydrated and carry water bottle"
            ],
            "emergency_contacts": {{
                "police": "100",
                "ambulance": "108",
                "fire": "101",
                "tourist_helpline": "1363",
                "local_hospital": "Hospital name and number",
                "embassy": "If applicable"
            }},
            "weather_forecast": "General weather expectations and what to prepare for",
            "cultural_notes": "Important cultural considerations and dress codes",
            "payment_tips": "Cash vs card acceptance, ATM availability",
            "connectivity": "SIM card options, WiFi availability",
            "total_estimated_cost": {trip_request['budget'] * 0.95},
            "buffer_amount": {trip_request['budget'] * 0.05}
        }}

        Ensure the response is valid JSON and the total cost does not exceed ₹{trip_request['budget']}.
        Make it practical, exciting, and perfectly tailored to the traveler's preferences.
        """
        
        logger.debug("Prompt created", prompt_length=len(prompt))
        return prompt
    
    def _parse_and_validate_response(self, response_text: str, trip_request: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate Gemini response"""
        try:
            logger.info("Parsing Gemini response")
            
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end != 0:
                json_str = response_text[json_start:json_end]
                itinerary_data = json.loads(json_str)
            else:
                itinerary_data = json.loads(response_text)
            
            # Validate required fields
            required_fields = ['daily_itineraries', 'cost_breakdown', 'total_estimated_cost']
            for field in required_fields:
                if field not in itinerary_data:
                    logger.warning(f"Missing required field: {field}")
                    itinerary_data[field] = self._get_default_value(field)
            
            # Validate budget constraint
            if itinerary_data.get('total_estimated_cost', 0) > trip_request['budget']:
                logger.warning("Generated itinerary exceeds budget, adjusting...")
                itinerary_data = self._adjust_for_budget(itinerary_data, trip_request['budget'])
            
            logger.info("Response parsed and validated successfully")
            return itinerary_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            return self._create_fallback_itinerary(trip_request)
    
    async def _enhance_itinerary_with_context(self, itinerary: Dict[str, Any], 
                                             trip_request: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance itinerary with additional context and data"""
        try:
            logger.info("Enhancing itinerary with additional context")
            
            # Add metadata
            itinerary['metadata'] = {
                'generated_at': datetime.utcnow().isoformat(),
                'model_version': settings.gemini_model,
                'request_id': trip_request.get('request_id'),
                'user_preferences': trip_request.get('user_preferences', {}),
                'generation_time_ms': 0  # Will be calculated
            }
            
            # Add trip metadata
            itinerary['trip_metadata'] = {
                'destination': trip_request['destination'],
                'start_date': str(trip_request.get('start_date')),
                'end_date': str(trip_request.get('end_date')),
                'duration_days': trip_request.get('duration_days'),
                'travelers_count': trip_request.get('travelers_count'),
                'themes': trip_request.get('themes', []),
                'created_at': datetime.now().isoformat()
            }
            
            # Add booking readiness flags
            itinerary['booking_ready'] = True
            itinerary['requires_confirmation'] = []
            
            # Validate and enhance each day
            for day in itinerary.get('daily_itineraries', []):
                # Ensure date formatting
                if 'date' not in day:
                    day['date'] = str(trip_request.get('start_date', date.today()) + 
                                     timedelta(days=day.get('day_number', 1) - 1))
                
                # Add unique IDs to activities
                for activity in day.get('activities', []):
                    activity['activity_id'] = f"act_{day['day_number']}_{activity.get('activity_name', '').replace(' ', '_')[:20]}"
                    activity['bookable'] = activity.get('booking_required', False)
            
            logger.info("Itinerary enhancement completed")
            return itinerary
            
        except Exception as e:
            logger.error(f"Error enhancing itinerary: {str(e)}")
            return itinerary
    
    async def chat_assistance(self, message: str, context: Dict[str, Any], 
                             user_id: Optional[str] = None) -> str:
        """Provide intelligent chat assistance with context awareness"""
        try:
            logger.info("Processing chat message",
                       message_length=len(message),
                       has_context=bool(context))
            
            # Get conversation history
            conversation_id = context.get('conversation_id', 'default')
            history = await self._get_conversation_history(conversation_id, user_id)
            
            # Build context-aware prompt
            system_prompt = f"""
            You are an expert AI travel assistant for India with deep knowledge of:
            - All Indian destinations, cultures, and languages
            - Budget optimization and money-saving tips
            - Local transportation, accommodation, and food
            - Safety guidelines and emergency procedures
            - Current events and seasonal considerations
            - Booking procedures and travel documentation
            
            User Context:
            {json.dumps(context, indent=2)}
            
            Conversation History (last 5 messages):
            {json.dumps(history[-5:] if history else [], indent=2)}
            
            Guidelines:
            1. Provide specific, actionable advice
            2. Include costs in INR with budget alternatives
            3. Consider the user's stated preferences
            4. Suggest booking platforms and apps
            5. Include safety tips when relevant
            6. Be friendly, helpful, and encouraging
            7. If discussing a trip, reference the itinerary context
            8. Provide emergency contacts when discussing safety
            
            Current Date: {datetime.now().strftime('%Y-%m-%d')}
            User Location: {context.get('user_location', 'India')}
            Language Preference: {context.get('language', 'English')}
            """
            
            # Combine system prompt with user message
            full_prompt = f"{system_prompt}\n\nUser: {message}\n\nAssistant:"
            
            # Generate response
            logger.info("Calling Gemini for chat response")
            response = self.model.generate_content(full_prompt)
            
            # Store in conversation history
            await self._update_conversation_history(
                conversation_id, user_id, message, response.text
            )
            
            # Log chat interaction
            await bigquery_service.log_analytics_event(
                "chat_interaction",
                {
                    "message_length": len(message),
                    "response_length": len(response.text),
                    "conversation_id": conversation_id,
                    "context_keys": list(context.keys())
                },
                user_id=user_id
            )
            
            logger.info("Chat response generated successfully")
            return response.text
            
        except Exception as e:
            logger.error(f"Error in chat assistance: {str(e)}")
            return "I apologize for the inconvenience. I'm having trouble processing your request. Please try rephrasing or ask me something else about travel planning!"
    
    async def optimize_itinerary(self, itinerary: Dict[str, Any], 
                                optimization_params: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize existing itinerary based on parameters"""
        try:
            logger.info("Optimizing itinerary",
                       optimization_type=optimization_params.get('type'))
            
            optimization_prompt = f"""
            Optimize the following itinerary based on these parameters:
            
            Current Itinerary:
            {json.dumps(itinerary, indent=2)}
            
            Optimization Requirements:
            {json.dumps(optimization_params, indent=2)}
            
            Focus on:
            1. Route optimization to minimize travel time
            2. Cost optimization while maintaining quality
            3. Time management for better experience
            4. Alternative suggestions for sold-out/closed venues
            5. Weather-based adjustments if needed
            
            Return the optimized itinerary in the same JSON format.
            """
            
            response = self.model.generate_content(optimization_prompt)
            optimized = self._parse_and_validate_response(response.text, {'budget': itinerary.get('total_estimated_cost')})
            
            # Log optimization
            await bigquery_service.log_analytics_event(
                "itinerary_optimized",
                {
                    "optimization_type": optimization_params.get('type'),
                    "original_cost": itinerary.get('total_estimated_cost'),
                    "optimized_cost": optimized.get('total_estimated_cost')
                }
            )
            
            logger.info("Itinerary optimization completed")
            return optimized
            
        except Exception as e:
            logger.error(f"Error optimizing itinerary: {str(e)}")
            return itinerary
    
    async def get_real_time_suggestions(self, location: str, preferences: List[str], 
                                       context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get real-time AI-powered suggestions"""
        try:
            logger.info("Generating real-time suggestions",
                       location=location,
                       preferences=preferences)
            
            current_time = datetime.now().strftime('%H:%M')
            day_of_week = datetime.now().strftime('%A')
            
            prompt = f"""
            Suggest 5 activities for someone currently in {location} at {current_time} on {day_of_week}.
            
            User Preferences: {', '.join(preferences)}
            Weather: {context.get('weather', 'Normal')}
            Budget Range: {context.get('budget_range', 'Medium')}
            Group Size: {context.get('group_size', 1)}
            
            For each suggestion provide:
            {{
                "name": "Activity Name",
                "description": "Brief description",
                "location": "Specific location/address",
                "duration_hours": 2,
                "cost_estimate": 500,
                "distance_km": 5,
                "category": "Category",
                "why_recommended": "Reason for recommendation",
                "booking_required": false,
                "best_time": "Optimal time to visit",
                "tips": ["Tip 1", "Tip 2"]
            }}
            
            Return as a JSON array of 5 suggestions, ordered by relevance.
            """
            
            response = self.model.generate_content(prompt)
            suggestions = json.loads(response.text) if isinstance(response.text, str) else response.text
            
            logger.info(f"Generated {len(suggestions)} suggestions")
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {str(e)}")
            return []
    
    async def translate_content(self, content: str, target_language: str) -> str:
        """Translate content to target language using Gemini"""
        try:
            logger.info(f"Translating content to {target_language}")
            
            prompt = f"""
            Translate the following travel content to {target_language}.
            Maintain the tone, formatting, and any special travel terms.
            
            Content:
            {content}
            
            Provide only the translation, no explanations.
            """
            
            response = self.model.generate_content(prompt)
            
            logger.info("Translation completed")
            return response.text
            
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")
            return content
    
    def _generate_cache_key(self, trip_request: Dict[str, Any]) -> str:
        """Generate cache key for trip request"""
        key_parts = [
            trip_request.get('destination', ''),
            str(trip_request.get('budget', 0)),
            str(trip_request.get('duration_days', 0)),
            ','.join(sorted(trip_request.get('themes', [])))
        ]
        return f"itinerary:{'_'.join(key_parts)}"
    
    async def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response from Redis"""
        if not self.redis_client:
            return None
        
        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                logger.info("Cache hit", cache_key=cache_key)
                return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Cache retrieval error: {str(e)}")
        
        return None
    
    async def _cache_response(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Cache response in Redis"""
        if not self.redis_client:
            return
        
        try:
            await self.redis_client.set(
                cache_key,
                json.dumps(data),
                ex=settings.redis_ttl_seconds
            )
            logger.debug("Response cached", cache_key=cache_key)
        except Exception as e:
            logger.error(f"Cache storage error: {str(e)}")
    
    async def _get_conversation_history(self, conversation_id: str, 
                                       user_id: Optional[str]) -> List[Dict[str, Any]]:
        """Get conversation history from storage"""
        try:
            if conversation_id in self.conversation_history:
                return self.conversation_history[conversation_id]
            
            # Try to load from Redis if available
            if self.redis_client and user_id:
                cache_key = f"conversation:{user_id}:{conversation_id}"
                cached_history = await self.redis_client.get(cache_key)
                if cached_history:
                    return json.loads(cached_history)
            
            return []
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {str(e)}")
            return []
    
    async def _update_conversation_history(self, conversation_id: str, user_id: Optional[str],
                                          user_message: str, ai_response: str) -> None:
        """Update conversation history"""
        try:
            if conversation_id not in self.conversation_history:
                self.conversation_history[conversation_id] = []
            
            history_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "user_message": user_message,
                "ai_response": ai_response
            }
            
            self.conversation_history[conversation_id].append(history_entry)
            
            # Keep only last 20 messages
            if len(self.conversation_history[conversation_id]) > 20:
                self.conversation_history[conversation_id] = self.conversation_history[conversation_id][-20:]
            
            # Store in Redis if available
            if self.redis_client and user_id:
                cache_key = f"conversation:{user_id}:{conversation_id}"
                await self.redis_client.set(
                    cache_key,
                    json.dumps(self.conversation_history[conversation_id]),
                    ex=86400  # 24 hours
                )
        except Exception as e:
            logger.error(f"Error updating conversation history: {str(e)}")
    
    def _adjust_for_budget(self, itinerary: Dict[str, Any], budget: float) -> Dict[str, Any]:
        """Adjust itinerary to fit within budget"""
        try:
            current_cost = itinerary.get('total_estimated_cost', 0)
            
            if current_cost > budget:
                adjustment_ratio = budget / current_cost
                
                # Adjust all costs proportionally
                if 'cost_breakdown' in itinerary:
                    for category in itinerary['cost_breakdown']:
                        if isinstance(itinerary['cost_breakdown'][category], (int, float)):
                            itinerary['cost_breakdown'][category] *= adjustment_ratio
                
                # Adjust daily costs
                for day in itinerary.get('daily_itineraries', []):
                    if 'day_total_cost' in day:
                        day['day_total_cost'] *= adjustment_ratio
                    
                    for activity in day.get('activities', []):
                        if 'cost_per_person' in activity:
                            activity['cost_per_person'] *= adjustment_ratio
                        if 'total_cost' in activity:
                            activity['total_cost'] *= adjustment_ratio
                
                itinerary['total_estimated_cost'] = budget
                itinerary['budget_adjusted'] = True
                
                logger.info("Budget adjustment applied",
                           original_cost=current_cost,
                           adjusted_cost=budget)
            
            return itinerary
            
        except Exception as e:
            logger.error(f"Error adjusting budget: {str(e)}")
            return itinerary
    
    def _create_fallback_itinerary(self, trip_request: Dict[str, Any]) -> Dict[str, Any]:
        """Create fallback itinerary when AI generation fails"""
        logger.warning("Creating fallback itinerary")
        
        duration = trip_request.get('duration_days', 3)
        daily_budget = trip_request['budget'] / duration
        
        daily_itineraries = []
        for day in range(duration):
            daily_itineraries.append({
                "day_number": day + 1,
                "date": str(trip_request.get('start_date', date.today()) + timedelta(days=day)),
                "activities": [
                    {
                        "time_slot": "09:00-12:00",
                        "activity_name": "Morning Sightseeing",
                        "description": "Explore popular local attractions",
                        "duration_hours": 3,
                        "cost_per_person": daily_budget * 0.2,
                        "category": "sightseeing"
                    },
                    {
                        "time_slot": "14:00-17:00",
                        "activity_name": "Cultural Experience",
                        "description": "Immerse in local culture and traditions",
                        "duration_hours": 3,
                        "cost_per_person": daily_budget * 0.15,
                        "category": "cultural"
                    }
                ],
                "day_total_cost": daily_budget
            })
        
        return {
            "daily_itineraries": daily_itineraries,
            "total_estimated_cost": trip_request['budget'],
            "fallback_mode": True,
            "message": "This is a basic itinerary. Please refine your preferences for a more detailed plan."
        }
    
    def _get_default_value(self, field: str) -> Any:
        """Get default value for missing field"""
        defaults = {
            'daily_itineraries': [],
            'cost_breakdown': {
                'accommodation': 0,
                'meals': 0,
                'activities': 0,
                'transport': 0,
                'miscellaneous': 0
            },
            'total_estimated_cost': 0,
            'local_tips': [],
            'emergency_contacts': {
                'police': '100',
                'ambulance': '108',
                'tourist_helpline': '1363'
            }
        }
        return defaults.get(field, None)

# Initialize AI Service
ai_service = AIService()