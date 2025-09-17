from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import uuid
import json
from app.models.trip import (
    TripRequest, 
    TripItinerary, 
    DayItinerary,
    Activity,
    TripUpdate,
    TripSummary
)
from app.services.ai_service import AIService
from app.services.maps_service import MapsService

class ItineraryService:
    def __init__(self):
        self.ai_service = AIService()
        self.maps_service = MapsService()
    
    async def create_itinerary(self, trip_request: TripRequest) -> TripItinerary:
        """Create a complete itinerary"""
        try:
            # Generate AI-powered itinerary
            ai_itinerary = await self.ai_service.generate_itinerary(trip_request)
            
            # Enhance with maps data
            enhanced_itinerary = await self._enhance_with_maps_data(
                ai_itinerary,
                trip_request.destination
            )
            
            # Create structured itinerary
            trip_itinerary = await self._structure_itinerary(
                enhanced_itinerary,
                trip_request
            )
            
            # Optimize routes
            optimized_itinerary = await self._optimize_routes(trip_itinerary)
            
            # Add weather forecast
            optimized_itinerary = await self._add_weather_forecast(
                optimized_itinerary,
                trip_request.destination
            )
            
            # Save itinerary
            await self._save_itinerary(optimized_itinerary)
            
            return optimized_itinerary
            
        except Exception as e:
            print(f"Error creating itinerary: {str(e)}")
            raise
    
    async def _enhance_with_maps_data(
        self,
        ai_itinerary: Dict[str, Any],
        destination: str
    ) -> Dict[str, Any]:
        """Enhance itinerary with real maps data"""
        try:
            for day_itinerary in ai_itinerary.get('daily_itineraries', []):
                for activity in day_itinerary.get('activities', []):
                    # Get place details from Maps
                    place_name = activity.get('name')
                    if place_name:
                        place_details = await self.maps_service.get_place_details(
                            place_name,
                            destination
                        )
                        
                        if place_details:
                            activity['location'].update({
                                'lat': place_details['location']['lat'],
                                'lng': place_details['location']['lng'],
                                'place_id': place_details.get('place_id'),
                                'rating': place_details.get('rating'),
                                'full_address': place_details.get('address')
                            })
                
                # Enhance accommodation details
                accommodation = day_itinerary.get('accommodation')
                if accommodation:
                    hotel_details = await self.maps_service.get_place_details(
                        accommodation.get('name'),
                        destination
                    )
                    
                    if hotel_details:
                        accommodation.update({
                            'location': hotel_details['location'],
                            'rating': hotel_details.get('rating'),
                            'address': hotel_details.get('address')
                        })
            
            return ai_itinerary
            
        except Exception as e:
            print(f"Error enhancing with maps data: {str(e)}")
            return ai_itinerary
    
    async def _structure_itinerary(
        self,
        enhanced_itinerary: Dict[str, Any],
        trip_request: TripRequest
    ) -> TripItinerary:
        """Structure the itinerary into proper format"""
        try:
            trip_id = str(uuid.uuid4())
            
            # Process daily itineraries
            daily_itineraries = []
            for day_data in enhanced_itinerary.get('daily_itineraries', []):
                # Process activities
                activities = []
                for act_data in day_data.get('activities', []):
                    activity = Activity(
                        name=act_data.get('name', ''),
                        description=act_data.get('description', ''),
                        duration_hours=act_data.get('duration_hours', 1.0),
                        cost=act_data.get('cost_per_person', 0) * trip_request.travelers_count,
                        location=act_data.get('location', {}),
                        category=act_data.get('category', 'general'),
                        rating=act_data.get('location', {}).get('rating'),
                        booking_required=act_data.get('booking_required', False),
                        booking_url=act_data.get('booking_url'),
                        tips=act_data.get('tips', [])
                    )
                    activities.append(activity)
                
                # Create day itinerary
                day_itinerary = DayItinerary(
                    day_number=day_data.get('day_number', 1),
                    date=trip_request.start_date + timedelta(days=day_data.get('day_number', 1) - 1),
                    activities=activities,
                    meals=day_data.get('meals', []),
                    transport=day_data.get('transport', []),
                    accommodation=day_data.get('accommodation'),
                    total_cost=day_data.get('total_cost', 0) * trip_request.travelers_count,
                    notes=day_data.get('notes')
                )
                daily_itineraries.append(day_itinerary)
            
            # Create trip itinerary
            trip_itinerary = TripItinerary(
                trip_id=trip_id,
                user_id=None,  # Will be set when user books
                destination=trip_request.destination,
                start_date=trip_request.start_date,
                end_date=trip_request.end_date,
                duration_days=(trip_request.end_date - trip_request.start_date).days + 1,
                total_budget=trip_request.budget,
                actual_cost=enhanced_itinerary.get('total_estimated_cost', 0),
                travelers_count=trip_request.travelers_count,
                themes=trip_request.themes,
                daily_itineraries=daily_itineraries,
                accommodation_details=enhanced_itinerary.get('accommodation_summary', []),
                transport_details=[enhanced_itinerary.get('transport_summary', {})],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                local_tips=enhanced_itinerary.get('local_tips', []),
                emergency_contacts=enhanced_itinerary.get('emergency_contacts', {})
            )
            
            return trip_itinerary
            
        except Exception as e:
            print(f"Error structuring itinerary: {str(e)}")
            raise
    
    async def _optimize_routes(self, itinerary: TripItinerary) -> TripItinerary:
        """Optimize routes between activities"""
        try:
            for day_itinerary in itinerary.daily_itineraries:
                if len(day_itinerary.activities) > 1:
                    # Get optimal order of activities
                    optimized_order = await self._get_optimal_route(
                        day_itinerary.activities
                    )
                    
                    # Reorder activities
                    if optimized_order:
                        day_itinerary.activities = optimized_order
                    
                    # Calculate transport between activities
                    transport_details = await self._calculate_transport(
                        day_itinerary.activities
                    )
                    
                    day_itinerary.transport.extend(transport_details)
            
            return itinerary
            
        except Exception as e:
            print(f"Error optimizing routes: {str(e)}")
            return itinerary
    
    async def _get_optimal_route(self, activities: List[Activity]) -> List[Activity]:
        """Get optimal order of activities to minimize travel time"""
        try:
            if len(activities) <= 2:
                return activities
            
            # Extract locations
            locations = []
            for activity in activities:
                if activity.location and 'address' in activity.location:
                    locations.append(activity.location['address'])
            
            if len(locations) < len(activities):
                return activities  # Can't optimize without all locations
            
            # Calculate distance matrix
            matrix = await self.maps_service.calculate_distance_matrix(
                locations,
                locations
            )
            
            # Simple nearest neighbor algorithm for route optimization
            # In production, use more sophisticated algorithms
            optimized = [activities[0]]
            remaining = activities[1:]
            
            while remaining:
                current = optimized[-1]
                nearest = min(
                    remaining,
                    key=lambda x: self._get_distance(current, x, matrix)
                )
                optimized.append(nearest)
                remaining.remove(nearest)
            
            return optimized
            
        except Exception as e:
            print(f"Error getting optimal route: {str(e)}")
            return activities
    
    def _get_distance(
        self,
        activity1: Activity,
        activity2: Activity,
        matrix: Dict[str, Any]
    ) -> float:
        """Get distance between two activities from matrix"""
        # Simplified implementation
        return 1.0  # Default distance
    
    async def _calculate_transport(self, activities: List[Activity]) -> List[Dict[str, Any]]:
        """Calculate transport details between activities"""
        transport_details = []
        
        for i in range(len(activities) - 1):
            from_location = activities[i].location.get('address', '')
            to_location = activities[i + 1].location.get('address', '')
            
            if from_location and to_location:
                directions = await self.maps_service.get_directions(
                    from_location,
                    to_location
                )
                
                if directions and directions.get('routes'):
                    route = directions['routes'][0]
                    transport_details.append({
                        'from': activities[i].name,
                        'to': activities[i + 1].name,
                        'mode': 'taxi',
                        'distance': route.get('distance'),
                        'duration': route.get('duration'),
                        'cost_estimate': 50  # Calculate based on distance
                    })
        
        return transport_details
    
    async def _add_weather_forecast(
        self,
        itinerary: TripItinerary,
        destination: str
    ) -> TripItinerary:
        """Add weather forecast to itinerary"""
        try:
            # Mock weather forecast
            # In production, integrate with weather API
            forecast = []
            for day in range(itinerary.duration_days):
                forecast.append({
                    'date': str(itinerary.start_date + timedelta(days=day)),
                    'temperature': {
                        'min': 20,
                        'max': 30
                    },
                    'condition': 'Partly Cloudy',
                    'precipitation_chance': 20
                })
            
            itinerary.weather_forecast = forecast
            return itinerary
            
        except Exception as e:
            print(f"Error adding weather forecast: {str(e)}")
            return itinerary
    
    async def update_itinerary(
        self,
        trip_id: str,
        update_request: TripUpdate
    ) -> TripItinerary:
        """Update an existing itinerary"""
        try:
            # Retrieve itinerary
            itinerary = await self._get_itinerary(trip_id)
            
            if not itinerary:
                raise ValueError(f"Itinerary {trip_id} not found")
            
            # Apply update based on type
            if update_request.update_type == "add":
                itinerary = await self._add_activity(itinerary, update_request)
            elif update_request.update_type == "remove":
                itinerary = await self._remove_activity(itinerary, update_request)
            elif update_request.update_type == "modify":
                itinerary = await self._modify_activity(itinerary, update_request)
            elif update_request.update_type == "reschedule":
                itinerary = await self._reschedule_activity(itinerary, update_request)
            
            # Update timestamp
            itinerary.updated_at = datetime.now()
            
            # Save updated itinerary
            await self._save_itinerary(itinerary)
            
            return itinerary
            
        except Exception as e:
            print(f"Error updating itinerary: {str(e)}")
            raise
    
    async def get_itinerary_summary(self, trip_id: str) -> TripSummary:
        """Get summary of an itinerary"""
        try:
            itinerary = await self._get_itinerary(trip_id)
            
            if not itinerary:
                raise ValueError(f"Itinerary {trip_id} not found")
            
            # Extract highlights
            highlights = []
            for day in itinerary.daily_itineraries:
                for activity in day.activities[:2]:  # Top 2 activities per day
                    highlights.append(activity.name)
            
            summary = TripSummary(
                trip_id=trip_id,
                destination=itinerary.destination,
                dates=f"{itinerary.start_date} to {itinerary.end_date}",
                total_cost=itinerary.actual_cost,
                status=itinerary.booking_status,
                highlights=highlights[:5],  # Top 5 highlights
                shareable_link=f"https://tripplanner.com/share/{trip_id}"
            )
            
            return summary
            
        except Exception as e:
            print(f"Error getting itinerary summary: {str(e)}")
            raise
    
    async def _save_itinerary(self, itinerary: TripItinerary):
        """Save itinerary to database"""
        # Implement database storage
        pass
    
    async def _get_itinerary(self, trip_id: str) -> Optional[TripItinerary]:
        """Retrieve itinerary from database"""
        # Implement database retrieval
        return None
    
    async def _add_activity(
        self,
        itinerary: TripItinerary,
        update: TripUpdate
    ) -> TripItinerary:
        """Add activity to itinerary"""
        # Implementation
        return itinerary
    
    async def _remove_activity(
        self,
        itinerary: TripItinerary,
        update: TripUpdate
    ) -> TripItinerary:
        """Remove activity from itinerary"""
        # Implementation
        return itinerary
    
    async def _modify_activity(
        self,
        itinerary: TripItinerary,
        update: TripUpdate
    ) -> TripItinerary:
        """Modify activity in itinerary"""
        # Implementation
        return itinerary
    
    async def _reschedule_activity(
        self,
        itinerary: TripItinerary,
        update: TripUpdate
    ) -> TripItinerary:
        """Reschedule activity in itinerary"""
        # Implementation
        return itinerary