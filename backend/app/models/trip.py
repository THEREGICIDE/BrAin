from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum

class TripTheme(str, Enum):
    HERITAGE = "heritage"
    ADVENTURE = "adventure"
    NIGHTLIFE = "nightlife"
    CULTURAL = "cultural"
    RELAXATION = "relaxation"
    FAMILY = "family"
    BUSINESS = "business"
    ROMANTIC = "romantic"
    FOODIE = "foodie"
    SHOPPING = "shopping"

class TransportMode(str, Enum):
    FLIGHT = "flight"
    TRAIN = "train"
    BUS = "bus"
    CAR = "car"
    TAXI = "taxi"
    WALK = "walk"
    BIKE = "bike"

class AccommodationType(str, Enum):
    HOTEL = "hotel"
    HOSTEL = "hostel"
    RESORT = "resort"
    HOMESTAY = "homestay"
    AIRBNB = "airbnb"
    VILLA = "villa"

class Activity(BaseModel):
    name: str
    description: str
    duration_hours: float
    cost: float
    location: Dict[str, Any]  # lat, lng, address
    category: str
    rating: Optional[float] = None
    booking_required: bool = False
    booking_url: Optional[str] = None
    tips: Optional[List[str]] = None

class DayItinerary(BaseModel):
    day_number: int
    date: date
    activities: List[Activity]
    meals: List[Dict[str, Any]]
    transport: List[Dict[str, Any]]
    accommodation: Optional[Dict[str, Any]] = None
    total_cost: float
    notes: Optional[str] = None

class TripRequest(BaseModel):
    destination: str
    start_date: date
    end_date: date
    budget: float
    travelers_count: int = 1
    themes: List[TripTheme]
    accommodation_preference: Optional[AccommodationType] = None
    transport_preference: Optional[TransportMode] = None
    dietary_restrictions: Optional[List[str]] = None
    special_requirements: Optional[str] = None
    language_preference: str = "en"
    include_flights: bool = True
    flexible_dates: bool = False

class TripItinerary(BaseModel):
    trip_id: str
    user_id: Optional[str] = None
    destination: str
    start_date: date
    end_date: date
    duration_days: int
    total_budget: float
    actual_cost: float
    travelers_count: int
    themes: List[TripTheme]
    daily_itineraries: List[DayItinerary]
    accommodation_details: List[Dict[str, Any]]
    transport_details: List[Dict[str, Any]]
    booking_status: str = "draft"
    payment_status: str = "pending"
    created_at: datetime
    updated_at: datetime
    weather_forecast: Optional[List[Dict[str, Any]]] = None
    local_tips: Optional[List[str]] = None
    emergency_contacts: Optional[Dict[str, Any]] = None
    
class TripUpdate(BaseModel):
    day_number: Optional[int] = None
    activity_id: Optional[str] = None
    update_type: str  # "add", "remove", "modify", "reschedule"
    update_data: Dict[str, Any]
    reason: Optional[str] = None

class TripSummary(BaseModel):
    trip_id: str
    destination: str
    dates: str
    total_cost: float
    status: str
    highlights: List[str]
    shareable_link: Optional[str] = None