"""
Enhanced Google Maps Service with Comprehensive Logging and Caching
"""
import googlemaps
import structlog
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import settings
from app.services.bigquery_service import bigquery_service
import redis.asyncio as redis
import asyncio

logger = structlog.get_logger(__name__)

class MapsService:
    """Enhanced Maps Service with full Google Maps API integration"""
    
    def __init__(self):
        logger.info("Initializing Maps Service",
                   api_key_configured=bool(settings.google_maps_api_key))
        
        if not settings.google_maps_api_key:
            logger.warning("Google Maps API key not configured, using mock data")
            self.gmaps = None
        else:
            self.gmaps = googlemaps.Client(
                key=settings.google_maps_api_key,
                timeout=30,
                retry_timeout=60
            )
            logger.info("Google Maps client initialized successfully")
        
        # Initialize Redis for caching
        if settings.use_redis_cache:
            self.redis_client = redis.from_url(settings.redis_url)
            logger.info("Redis caching enabled for Maps data")
        else:
            self.redis_client = None
        
        # Cache settings
        self.cache_ttl = 3600  # 1 hour for place data
        self.directions_cache_ttl = 1800  # 30 minutes for directions
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_place_details(self, place_name: str, location: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed place information with caching and error handling"""
        try:
            logger.info("Getting place details",
                       place_name=place_name,
                       location=location)
            
            # Check cache first
            cache_key = f"place:{place_name}:{location or 'global'}"
            cached_data = await self._get_from_cache(cache_key)
            if cached_data:
                logger.info("Returning cached place details", place_name=place_name)
                return cached_data
            
            if not self.gmaps:
                logger.warning("Maps API not configured, returning mock data")
                return self._get_mock_place_details(place_name, location)
            
            # Build search query
            query = f"{place_name} in {location}" if location else place_name
            
            # Search for the place
            places_result = self.gmaps.places(
                query=query,
                region=settings.maps_default_region,
                language=settings.maps_default_language
            )
            
            if not places_result.get('results'):
                logger.warning("No results found for place",
                             place_name=place_name)
                return {}
            
            place = places_result['results'][0]
            place_id = place['place_id']
            
            # Get detailed information
            detail_result = self.gmaps.place(
                place_id=place_id,
                fields=[
                    'name', 'formatted_address', 'geometry', 'rating',
                    'user_ratings_total', 'types', 'opening_hours',
                    'formatted_phone_number', 'website', 'photos',
                    'price_level', 'reviews', 'url', 'vicinity',
                    'business_status', 'plus_code'
                ],
                language=settings.maps_default_language
            )
            
            detail = detail_result.get('result', {})
            
            # Process and structure the response
            place_data = {
                'place_id': place_id,
                'name': detail.get('name'),
                'address': detail.get('formatted_address'),
                'location': {
                    'lat': detail.get('geometry', {}).get('location', {}).get('lat'),
                    'lng': detail.get('geometry', {}).get('location', {}).get('lng')
                },
                'rating': detail.get('rating'),
                'reviews_count': detail.get('user_ratings_total'),
                'types': detail.get('types', []),
                'opening_hours': self._process_opening_hours(detail.get('opening_hours', {})),
                'phone': detail.get('formatted_phone_number'),
                'website': detail.get('website'),
                'photos': self._extract_photo_references(detail.get('photos', [])),
                'price_level': detail.get('price_level'),
                'reviews': self._process_reviews(detail.get('reviews', [])),
                'maps_url': detail.get('url'),
                'vicinity': detail.get('vicinity'),
                'business_status': detail.get('business_status'),
                'plus_code': detail.get('plus_code', {}).get('global_code')
            }
            
            # Cache the result
            await self._save_to_cache(cache_key, place_data, self.cache_ttl)
            
            # Log analytics
            await bigquery_service.log_analytics_event(
                "place_search",
                {
                    "place_name": place_name,
                    "location": location,
                    "found": True,
                    "rating": place_data.get('rating')
                }
            )
            
            logger.info("Place details retrieved successfully",
                       place_name=place_name,
                       place_id=place_id)
            
            return place_data
            
        except Exception as e:
            logger.error(f"Error getting place details: {str(e)}",
                        place_name=place_name)
            await bigquery_service.log_application_log({
                "level": "ERROR",
                "logger": "MapsService",
                "message": f"Place details error: {str(e)}",
                "context": {"place_name": place_name, "location": location}
            })
            return {}
    
    async def search_nearby(self, location: Tuple[float, float], radius: int = 5000,
                           place_type: Optional[str] = None, 
                           keyword: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for nearby places with filtering and ranking"""
        try:
            logger.info("Searching nearby places",
                       location=location,
                       radius=radius,
                       place_type=place_type)
            
            if not self.gmaps:
                return self._get_mock_nearby_places(location, place_type)
            
            # Build search parameters
            params = {
                'location': location,
                'radius': radius,
                'language': settings.maps_default_language
            }
            
            if place_type:
                params['type'] = place_type
            if keyword:
                params['keyword'] = keyword
            
            # Execute search
            results = self.gmaps.places_nearby(**params)
            
            places = []
            for place in results.get('results', []):
                place_info = {
                    'place_id': place['place_id'],
                    'name': place['name'],
                    'vicinity': place.get('vicinity'),
                    'location': {
                        'lat': place['geometry']['location']['lat'],
                        'lng': place['geometry']['location']['lng']
                    },
                    'rating': place.get('rating'),
                    'user_ratings_total': place.get('user_ratings_total', 0),
                    'types': place.get('types', []),
                    'price_level': place.get('price_level'),
                    'opening_now': place.get('opening_hours', {}).get('open_now'),
                    'photos': self._extract_photo_references(place.get('photos', [])),
                    'distance': self._calculate_distance(location, 
                        (place['geometry']['location']['lat'], 
                         place['geometry']['location']['lng']))
                }
                places.append(place_info)
            
            # Sort by rating and distance
            places.sort(key=lambda x: (-(x.get('rating', 0)), x.get('distance', 0)))
            
            logger.info(f"Found {len(places)} nearby places")
            
            # Log analytics
            await bigquery_service.log_analytics_event(
                "nearby_search",
                {
                    "location": f"{location[0]},{location[1]}",
                    "radius": radius,
                    "place_type": place_type,
                    "results_count": len(places)
                }
            )
            
            return places
            
        except Exception as e:
            logger.error(f"Error searching nearby places: {str(e)}")
            return []
    
    async def get_directions(self, origin: str, destination: str, 
                           mode: str = "driving",
                           departure_time: Optional[datetime] = None,
                           alternatives: bool = True,
                           waypoints: List[str] = None) -> Dict[str, Any]:
        """Get detailed directions with traffic and alternatives"""
        try:
            logger.info("Getting directions",
                       origin=origin,
                       destination=destination,
                       mode=mode)
            
            # Check cache
            cache_key = f"directions:{origin}:{destination}:{mode}"
            cached_data = await self._get_from_cache(cache_key)
            if cached_data:
                logger.info("Returning cached directions")
                return cached_data
            
            if not self.gmaps:
                return self._get_mock_directions(origin, destination, mode)
            
            # Build parameters
            params = {
                'origin': origin,
                'destination': destination,
                'mode': mode,
                'alternatives': alternatives,
                'units': 'metric',
                'region': settings.maps_default_region,
                'language': settings.maps_default_language
            }
            
            if departure_time:
                params['departure_time'] = departure_time
            
            if waypoints:
                params['waypoints'] = waypoints
                params['optimize_waypoints'] = True
            
            # Get directions
            directions_result = self.gmaps.directions(**params)
            
            if not directions_result:
                logger.warning("No routes found",
                             origin=origin,
                             destination=destination)
                return {}
            
            # Process routes
            routes = []
            for route_data in directions_result:
                route = {
                    'summary': route_data.get('summary'),
                    'distance': route_data['legs'][0]['distance'],
                    'duration': route_data['legs'][0]['duration'],
                    'duration_in_traffic': route_data['legs'][0].get('duration_in_traffic'),
                    'steps': self._process_steps(route_data['legs'][0]['steps']),
                    'polyline': route_data['overview_polyline']['points'],
                    'warnings': route_data.get('warnings', []),
                    'fare': route_data.get('fare'),
                    'waypoint_order': route_data.get('waypoint_order', [])
                }
                routes.append(route)
            
            result = {
                'routes': routes,
                'origin_address': directions_result[0]['legs'][0]['start_address'],
                'destination_address': directions_result[0]['legs'][0]['end_address'],
                'origin_location': directions_result[0]['legs'][0]['start_location'],
                'destination_location': directions_result[0]['legs'][0]['end_location'],
                'total_routes': len(routes)
            }
            
            # Cache result
            await self._save_to_cache(cache_key, result, self.directions_cache_ttl)
            
            # Log analytics
            await bigquery_service.log_analytics_event(
                "directions_search",
                {
                    "origin": origin,
                    "destination": destination,
                    "mode": mode,
                    "routes_found": len(routes),
                    "primary_distance_km": routes[0]['distance']['value'] / 1000 if routes else 0
                }
            )
            
            logger.info(f"Found {len(routes)} routes")
            return result
            
        except Exception as e:
            logger.error(f"Error getting directions: {str(e)}")
            return {}
    
    async def calculate_distance_matrix(self, origins: List[str], 
                                       destinations: List[str],
                                       mode: str = "driving",
                                       avoid: List[str] = None) -> Dict[str, Any]:
        """Calculate distance and time matrix between multiple points"""
        try:
            logger.info("Calculating distance matrix",
                       origins_count=len(origins),
                       destinations_count=len(destinations))
            
            if not self.gmaps:
                return self._get_mock_distance_matrix(origins, destinations)
            
            # Build parameters
            params = {
                'origins': origins,
                'destinations': destinations,
                'mode': mode,
                'units': 'metric',
                'region': settings.maps_default_region,
                'language': settings.maps_default_language
            }
            
            if avoid:
                params['avoid'] = '|'.join(avoid)
            
            # Get matrix
            matrix = self.gmaps.distance_matrix(**params)
            
            # Process results
            results = []
            for i, origin in enumerate(matrix['origin_addresses']):
                for j, destination in enumerate(matrix['destination_addresses']):
                    element = matrix['rows'][i]['elements'][j]
                    
                    if element['status'] == 'OK':
                        results.append({
                            'origin': origin,
                            'destination': destination,
                            'origin_index': i,
                            'destination_index': j,
                            'distance': element['distance'],
                            'duration': element['duration'],
                            'duration_in_traffic': element.get('duration_in_traffic'),
                            'fare': element.get('fare'),
                            'status': 'OK'
                        })
                    else:
                        results.append({
                            'origin': origin,
                            'destination': destination,
                            'origin_index': i,
                            'destination_index': j,
                            'status': element['status']
                        })
            
            output = {
                'results': results,
                'origin_addresses': matrix['origin_addresses'],
                'destination_addresses': matrix['destination_addresses'],
                'status': matrix['status']
            }
            
            logger.info(f"Distance matrix calculated for {len(results)} pairs")
            return output
            
        except Exception as e:
            logger.error(f"Error calculating distance matrix: {str(e)}")
            return {}
    
    async def geocode_address(self, address: str) -> Optional[Dict[str, Any]]:
        """Convert address to coordinates with component breakdown"""
        try:
            logger.info("Geocoding address", address=address)
            
            if not self.gmaps:
                return self._get_mock_geocode(address)
            
            geocode_result = self.gmaps.geocode(
                address=address,
                region=settings.maps_default_region,
                language=settings.maps_default_language
            )
            
            if not geocode_result:
                logger.warning("No geocoding results", address=address)
                return None
            
            result = geocode_result[0]
            
            geocoded_data = {
                'formatted_address': result['formatted_address'],
                'location': {
                    'lat': result['geometry']['location']['lat'],
                    'lng': result['geometry']['location']['lng']
                },
                'place_id': result.get('place_id'),
                'types': result.get('types', []),
                'components': self._process_address_components(result.get('address_components', [])),
                'viewport': result.get('geometry', {}).get('viewport'),
                'plus_code': result.get('plus_code', {}).get('global_code')
            }
            
            logger.info("Address geocoded successfully", address=address)
            return geocoded_data
            
        except Exception as e:
            logger.error(f"Error geocoding address: {str(e)}")
            return None
    
    async def find_hotels(self, location: str, check_in: datetime, 
                        check_out: datetime, min_price: Optional[int] = None,
                        max_price: Optional[int] = None, 
                        amenities: List[str] = None) -> List[Dict[str, Any]]:
        """Find hotels with detailed filtering"""
        try:
            logger.info("Searching for hotels",
                       location=location,
                       check_in=check_in.date(),
                       check_out=check_out.date())
            
            if not self.gmaps:
                return self._get_mock_hotels(location, check_in, check_out)
            
            # Search for hotels
            places_result = self.gmaps.places(
                query=f"hotels in {location}",
                type='lodging',
                language=settings.maps_default_language
            )
            
            hotels = []
            for place in places_result.get('results', [])[:20]:  # Limit to 20 results
                # Get detailed info for each hotel
                try:
                    detail = self.gmaps.place(
                        place['place_id'],
                        fields=['name', 'formatted_address', 'rating', 'user_ratings_total',
                               'price_level', 'photos', 'website', 'formatted_phone_number',
                               'opening_hours', 'types', 'geometry']
                    )['result']
                    
                    # Apply price filtering
                    price_level = detail.get('price_level', 2)
                    estimated_price = price_level * 2500  # Rough estimation in INR
                    
                    if min_price and estimated_price < min_price:
                        continue
                    if max_price and estimated_price > max_price:
                        continue
                    
                    hotel_info = {
                        'place_id': place['place_id'],
                        'name': detail['name'],
                        'address': detail.get('formatted_address'),
                        'location': {
                            'lat': detail['geometry']['location']['lat'],
                            'lng': detail['geometry']['location']['lng']
                        },
                        'rating': detail.get('rating'),
                        'reviews_count': detail.get('user_ratings_total', 0),
                        'price_level': price_level,
                        'estimated_price_per_night': estimated_price,
                        'photos': self._extract_photo_references(detail.get('photos', [])),
                        'website': detail.get('website'),
                        'phone': detail.get('formatted_phone_number'),
                        'types': detail.get('types', []),
                        'check_in_date': check_in.date().isoformat(),
                        'check_out_date': check_out.date().isoformat(),
                        'nights': (check_out - check_in).days
                    }
                    
                    hotels.append(hotel_info)
                    
                except Exception as e:
                    logger.debug(f"Error getting hotel details: {str(e)}")
                    continue
            
            # Sort by rating
            hotels.sort(key=lambda x: x.get('rating', 0), reverse=True)
            
            logger.info(f"Found {len(hotels)} hotels")
            
            # Log analytics
            await bigquery_service.log_analytics_event(
                "hotel_search",
                {
                    "location": location,
                    "check_in": check_in.isoformat(),
                    "check_out": check_out.isoformat(),
                    "results_count": len(hotels),
                    "price_range": f"{min_price or 0}-{max_price or 'unlimited'}"
                }
            )
            
            return hotels
            
        except Exception as e:
            logger.error(f"Error finding hotels: {str(e)}")
            return []
    
    async def find_restaurants(self, location: str, cuisine: Optional[str] = None,
                             price_level: Optional[int] = None, open_now: bool = False,
                             dietary_restrictions: List[str] = None) -> List[Dict[str, Any]]:
        """Find restaurants with dietary and cuisine filters"""
        try:
            logger.info("Searching for restaurants",
                       location=location,
                       cuisine=cuisine)
            
            if not self.gmaps:
                return self._get_mock_restaurants(location, cuisine)
            
            # Build query
            query_parts = ["restaurants in", location]
            if cuisine:
                query_parts.insert(0, cuisine)
            
            query = " ".join(query_parts)
            
            # Search parameters
            params = {
                'query': query,
                'type': 'restaurant',
                'language': settings.maps_default_language
            }
            
            if open_now:
                params['open_now'] = True
            
            places_result = self.gmaps.places(**params)
            
            restaurants = []
            for place in places_result.get('results', [])[:15]:
                # Apply filters
                if price_level and place.get('price_level', 0) > price_level:
                    continue
                
                restaurant_info = {
                    'place_id': place['place_id'],
                    'name': place['name'],
                    'address': place.get('formatted_address', place.get('vicinity')),
                    'location': {
                        'lat': place['geometry']['location']['lat'],
                        'lng': place['geometry']['location']['lng']
                    },
                    'rating': place.get('rating'),
                    'reviews_count': place.get('user_ratings_total', 0),
                    'price_level': place.get('price_level'),
                    'types': place.get('types', []),
                    'photos': self._extract_photo_references(place.get('photos', [])),
                    'opening_now': place.get('opening_hours', {}).get('open_now'),
                    'cuisine': cuisine or 'Multi-cuisine',
                    'dietary_friendly': self._check_dietary_compatibility(
                        place.get('types', []), dietary_restrictions
                    )
                }
                
                restaurants.append(restaurant_info)
            
            # Sort by rating
            restaurants.sort(key=lambda x: x.get('rating', 0), reverse=True)
            
            logger.info(f"Found {len(restaurants)} restaurants")
            return restaurants
            
        except Exception as e:
            logger.error(f"Error finding restaurants: {str(e)}")
            return []
    
    async def get_place_photos(self, place_id: str, max_photos: int = 5) -> List[str]:
        """Get photo URLs for a place"""
        try:
            logger.info("Getting place photos", place_id=place_id)
            
            if not self.gmaps:
                return []
            
            place_details = self.gmaps.place(place_id, fields=['photos'])
            photos = place_details.get('result', {}).get('photos', [])
            
            photo_urls = []
            for photo in photos[:max_photos]:
                if 'photo_reference' in photo:
                    # Note: This would need actual implementation to get URLs
                    # Google requires fetching each photo individually
                    photo_urls.append(f"photo_ref_{photo['photo_reference'][:10]}")
            
            logger.info(f"Retrieved {len(photo_urls)} photo references")
            return photo_urls
            
        except Exception as e:
            logger.error(f"Error getting place photos: {str(e)}")
            return []
    
    # Helper methods
    
    def _process_opening_hours(self, opening_hours: Dict[str, Any]) -> Dict[str, Any]:
        """Process opening hours into structured format"""
        return {
            'open_now': opening_hours.get('open_now'),
            'periods': opening_hours.get('periods', []),
            'weekday_text': opening_hours.get('weekday_text', [])
        }
    
    def _process_reviews(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and sanitize reviews"""
        processed = []
        for review in reviews[:5]:  # Limit to 5 reviews
            processed.append({
                'author': review.get('author_name'),
                'rating': review.get('rating'),
                'text': review.get('text', '')[:500],  # Limit text length
                'time': review.get('relative_time_description'),
                'language': review.get('language')
            })
        return processed
    
    def _extract_photo_references(self, photos: List[Dict]) -> List[str]:
        """Extract photo references"""
        return [photo.get('photo_reference', '') for photo in photos[:5] if 'photo_reference' in photo]
    
    def _process_steps(self, steps: List[Dict]) -> List[Dict[str, Any]]:
        """Process direction steps"""
        processed = []
        for step in steps:
            processed.append({
                'instruction': step.get('html_instructions', '').replace('<b>', '').replace('</b>', ''),
                'distance': step['distance'],
                'duration': step['duration'],
                'travel_mode': step.get('travel_mode'),
                'maneuver': step.get('maneuver')
            })
        return processed
    
    def _process_address_components(self, components: List[Dict]) -> Dict[str, str]:
        """Process address components into structured format"""
        processed = {}
        for component in components:
            types = component.get('types', [])
            if 'country' in types:
                processed['country'] = component['long_name']
            elif 'administrative_area_level_1' in types:
                processed['state'] = component['long_name']
            elif 'locality' in types:
                processed['city'] = component['long_name']
            elif 'postal_code' in types:
                processed['postal_code'] = component['long_name']
        return processed
    
    def _calculate_distance(self, point1: Tuple[float, float], 
                          point2: Tuple[float, float]) -> float:
        """Calculate distance between two points in km"""
        from math import radians, sin, cos, sqrt, atan2
        
        lat1, lon1 = point1
        lat2, lon2 = point2
        
        R = 6371  # Earth's radius in km
        
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return round(R * c, 2)
    
    def _check_dietary_compatibility(self, types: List[str], 
                                    dietary_restrictions: Optional[List[str]]) -> bool:
        """Check if restaurant matches dietary restrictions"""
        if not dietary_restrictions:
            return True
        
        # Simple matching logic - can be enhanced
        for restriction in dietary_restrictions:
            if restriction.lower() in ' '.join(types).lower():
                return True
        
        return False
    
    async def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get data from Redis cache"""
        if not self.redis_client:
            return None
        
        try:
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.debug(f"Cache retrieval error: {str(e)}")
        
        return None
    
    async def _save_to_cache(self, key: str, data: Dict[str, Any], ttl: int) -> None:
        """Save data to Redis cache"""
        if not self.redis_client:
            return
        
        try:
            await self.redis_client.set(key, json.dumps(data), ex=ttl)
        except Exception as e:
            logger.debug(f"Cache save error: {str(e)}")
    
    # Mock data methods for when Maps API is not configured
    
    def _get_mock_place_details(self, place_name: str, location: Optional[str]) -> Dict[str, Any]:
        """Return mock place details"""
        return {
            'place_id': 'mock_place_123',
            'name': place_name,
            'address': f"{place_name}, {location or 'India'}",
            'location': {'lat': 28.6139, 'lng': 77.2090},
            'rating': 4.5,
            'reviews_count': 1234,
            'types': ['tourist_attraction'],
            'opening_hours': {'open_now': True, 'weekday_text': ['Monday: 9:00 AM – 6:00 PM']},
            'mock_data': True
        }
    
    def _get_mock_nearby_places(self, location: Tuple[float, float], 
                               place_type: Optional[str]) -> List[Dict[str, Any]]:
        """Return mock nearby places"""
        return [
            {
                'place_id': f'mock_{i}',
                'name': f'Place {i}',
                'vicinity': 'Nearby',
                'location': {'lat': location[0] + 0.01*i, 'lng': location[1] + 0.01*i},
                'rating': 4.0 + (i * 0.1),
                'types': [place_type or 'establishment'],
                'mock_data': True
            }
            for i in range(5)
        ]
    
    def _get_mock_directions(self, origin: str, destination: str, mode: str) -> Dict[str, Any]:
        """Return mock directions"""
        return {
            'routes': [{
                'summary': f'{origin} to {destination}',
                'distance': {'text': '10 km', 'value': 10000},
                'duration': {'text': '30 mins', 'value': 1800},
                'steps': [],
                'polyline': 'mock_polyline'
            }],
            'origin_address': origin,
            'destination_address': destination,
            'mock_data': True
        }
    
    def _get_mock_distance_matrix(self, origins: List[str], 
                                 destinations: List[str]) -> Dict[str, Any]:
        """Return mock distance matrix"""
        return {
            'results': [
                {
                    'origin': origin,
                    'destination': dest,
                    'distance': {'text': '5 km', 'value': 5000},
                    'duration': {'text': '15 mins', 'value': 900},
                    'status': 'OK'
                }
                for origin in origins for dest in destinations
            ],
            'status': 'OK',
            'mock_data': True
        }
    
    def _get_mock_geocode(self, address: str) -> Dict[str, Any]:
        """Return mock geocoded address"""
        return {
            'formatted_address': address,
            'location': {'lat': 28.6139, 'lng': 77.2090},
            'place_id': 'mock_geocode_123',
            'types': ['locality'],
            'mock_data': True
        }
    
    def _get_mock_hotels(self, location: str, check_in: datetime, 
                        check_out: datetime) -> List[Dict[str, Any]]:
        """Return mock hotels"""
        return [
            {
                'place_id': f'mock_hotel_{i}',
                'name': f'Hotel {i}',
                'address': f'{location}',
                'location': {'lat': 28.6139 + 0.01*i, 'lng': 77.2090 + 0.01*i},
                'rating': 4.0 + (i * 0.2),
                'price_level': 2 + (i % 3),
                'estimated_price_per_night': 3000 + (i * 500),
                'mock_data': True
            }
            for i in range(5)
        ]
    
    def _get_mock_restaurants(self, location: str, cuisine: Optional[str]) -> List[Dict[str, Any]]:
        """Return mock restaurants"""
        return [
            {
                'place_id': f'mock_restaurant_{i}',
                'name': f'{cuisine or "Multi-cuisine"} Restaurant {i}',
                'address': location,
                'location': {'lat': 28.6139 + 0.01*i, 'lng': 77.2090 + 0.01*i},
                'rating': 4.0 + (i * 0.1),
                'price_level': 1 + (i % 3),
                'cuisine': cuisine or 'Multi-cuisine',
                'mock_data': True
            }
            for i in range(5)
        ]

# Initialize Maps Service
maps_service = MapsService()