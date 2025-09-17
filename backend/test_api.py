import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint returns expected response"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Welcome to AI Trip Planner API"
    assert response.json()["version"] == "1.0.0"
    assert "docs" in response.json()

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "AI Trip Planner API"

def test_create_trip():
    """Test trip creation endpoint"""
    trip_data = {
        "destination": "Tokyo",
        "duration": 7,
        "budget": 5000
    }
    response = client.post("/api/v1/trips/create", json=trip_data)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "trip_request" in response.json()
    assert response.json()["trip_request"]["destination"] == "Tokyo"

def test_get_trip():
    """Test getting trip details"""
    trip_id = "test-trip-123"
    response = client.get(f"/api/v1/trips/{trip_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["trip_id"] == trip_id

def test_chat_endpoint():
    """Test AI chat endpoint"""
    chat_data = {
        "message": "What are the best restaurants in Paris?",
        "context": {"location": "Paris"}
    }
    response = client.post("/api/v1/chat", json=chat_data)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "response" in response.json()

def test_place_search():
    """Test place search endpoint"""
    response = client.get("/api/v1/places/search?query=Louvre&location=Paris")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["query"] == "Louvre"
    assert response.json()["location"] == "Paris"

def test_create_booking():
    """Test booking creation"""
    booking_data = {
        "trip_id": "trip-123",
        "user_id": "user-456",
        "services": ["hotel", "transport"]
    }
    response = client.post("/api/v1/bookings/create", json=booking_data)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "booking_id" in response.json()

def test_payment_process():
    """Test payment processing"""
    payment_data = {
        "amount": 1500.00,
        "currency": "USD",
        "booking_id": "booking-789"
    }
    response = client.post("/api/v1/payments/process", json=payment_data)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "payment_id" in response.json()

def test_suggestions_endpoint():
    """Test suggestions endpoint"""
    suggestion_data = {
        "location": "New York",
        "preferences": ["museums", "restaurants"],
        "time_of_day": "afternoon"
    }
    response = client.post("/api/v1/suggestions", json=suggestion_data)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "suggestions" in response.json()

def test_hotels_search():
    """Test hotel search endpoint"""
    hotel_data = {
        "location": "London",
        "check_in": "2024-12-01",
        "check_out": "2024-12-05"
    }
    response = client.post("/api/v1/hotels/search", json=hotel_data)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "hotels" in response.json()

def test_restaurants_search():
    """Test restaurant search endpoint"""
    restaurant_data = {
        "location": "Rome",
        "cuisine": "Italian",
        "price_level": 2
    }
    response = client.post("/api/v1/restaurants/search", json=restaurant_data)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "restaurants" in response.json()

def test_directions():
    """Test directions endpoint"""
    directions_data = {
        "origin": "Times Square, New York",
        "destination": "Central Park, New York",
        "mode": "walking"
    }
    response = client.post("/api/v1/directions", json=directions_data)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "directions" in response.json()

def test_booking_status():
    """Test booking status endpoint"""
    booking_id = "booking-test-123"
    response = client.get(f"/api/v1/bookings/{booking_id}/status")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["booking_id"] == booking_id

def test_payment_verification():
    """Test payment verification"""
    session_id = "session-test-456"
    response = client.get(f"/api/v1/payments/verify/{session_id}")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["session_id"] == session_id

if __name__ == "__main__":
    pytest.main(["-v", __file__])