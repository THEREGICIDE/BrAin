import requests
import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv()

class APIClient:
    def __init__(self):
        self.base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        self.timeout = int(os.getenv("API_TIMEOUT", "30"))
        self.session = requests.Session()
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make API request"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request error: {str(e)}")
            raise
    
    # Trip Planning APIs
    def create_trip(self, trip_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new trip itinerary"""
        return self._make_request("POST", "/api/v1/trips/create", data=trip_data)
    
    def get_trip(self, trip_id: str) -> Dict[str, Any]:
        """Get trip details"""
        return self._make_request("GET", f"/api/v1/trips/{trip_id}")
    
    def update_trip(self, trip_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update trip itinerary"""
        return self._make_request("PUT", f"/api/v1/trips/{trip_id}/update", data=update_data)
    
    def get_trip_summary(self, trip_id: str) -> Dict[str, Any]:
        """Get trip summary"""
        return self._make_request("GET", f"/api/v1/trips/{trip_id}/summary")
    
    # AI Chat APIs
    def chat_with_ai(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Chat with AI assistant"""
        data = {"message": message}
        if context:
            data["context"] = context
        
        response = self._make_request("POST", "/api/v1/chat", data=data)
        return response.get("response", "")
    
    def get_suggestions(
        self,
        location: str,
        preferences: List[str],
        time_of_day: str
    ) -> List[Dict[str, Any]]:
        """Get real-time suggestions"""
        data = {
            "location": location,
            "preferences": preferences,
            "time_of_day": time_of_day
        }
        response = self._make_request("POST", "/api/v1/suggestions", data=data)
        return response.get("suggestions", [])
    
    # Booking APIs
    def create_booking(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new booking"""
        return self._make_request("POST", "/api/v1/bookings/create", data=booking_data)
    
    def confirm_booking(self, booking_id: str, payment_id: str) -> Dict[str, Any]:
        """Confirm booking"""
        params = {"payment_id": payment_id}
        return self._make_request("POST", f"/api/v1/bookings/{booking_id}/confirm", params=params)
    
    def cancel_booking(self, booking_id: str, reason: str) -> Dict[str, Any]:
        """Cancel booking"""
        params = {"reason": reason}
        return self._make_request("POST", f"/api/v1/bookings/{booking_id}/cancel", params=params)
    
    def get_booking_status(self, booking_id: str) -> Dict[str, Any]:
        """Get booking status"""
        return self._make_request("GET", f"/api/v1/bookings/{booking_id}/status")
    
    # Payment APIs
    def process_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment"""
        return self._make_request("POST", "/api/v1/payments/process", data=payment_data)
    
    def create_payment_session(
        self,
        amount: float,
        booking_id: str,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """Create payment session"""
        data = {
            "amount": amount,
            "booking_id": booking_id,
            "success_url": success_url,
            "cancel_url": cancel_url
        }
        return self._make_request("POST", "/api/v1/payments/create-session", data=data)
    
    def verify_payment(self, session_id: str) -> Dict[str, Any]:
        """Verify payment"""
        return self._make_request("GET", f"/api/v1/payments/verify/{session_id}")
    
    # Maps/Location APIs
    def search_places(self, query: str, location: Optional[str] = None) -> Dict[str, Any]:
        """Search for places"""
        params = {"query": query}
        if location:
            params["location"] = location
        return self._make_request("GET", "/api/v1/places/search", params=params)
    
    def search_nearby_places(
        self,
        lat: float,
        lng: float,
        radius: int = 5000,
        place_type: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search nearby places"""
        data = {
            "lat": lat,
            "lng": lng,
            "radius": radius
        }
        if place_type:
            data["place_type"] = place_type
        if keyword:
            data["keyword"] = keyword
        
        return self._make_request("POST", "/api/v1/places/nearby", data=data)
    
    def get_directions(
        self,
        origin: str,
        destination: str,
        mode: str = "driving"
    ) -> Dict[str, Any]:
        """Get directions"""
        data = {
            "origin": origin,
            "destination": destination,
            "mode": mode
        }
        return self._make_request("POST", "/api/v1/directions", data=data)
    
    def search_hotels(
        self,
        location: str,
        check_in: str,
        check_out: str,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None
    ) -> Dict[str, Any]:
        """Search hotels"""
        data = {
            "location": location,
            "check_in": check_in,
            "check_out": check_out
        }
        if min_price:
            data["min_price"] = min_price
        if max_price:
            data["max_price"] = max_price
        
        return self._make_request("POST", "/api/v1/hotels/search", data=data)
    
    def search_restaurants(
        self,
        location: str,
        cuisine: Optional[str] = None,
        price_level: Optional[int] = None,
        open_now: bool = False
    ) -> Dict[str, Any]:
        """Search restaurants"""
        data = {
            "location": location,
            "open_now": open_now
        }
        if cuisine:
            data["cuisine"] = cuisine
        if price_level:
            data["price_level"] = price_level
        
        return self._make_request("POST", "/api/v1/restaurants/search", data=data)
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        return self._make_request("GET", "/api/v1/health")