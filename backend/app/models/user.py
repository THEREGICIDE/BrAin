from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class UserPreferences(BaseModel):
    preferred_themes: List[str] = []
    preferred_accommodation: List[str] = []
    preferred_transport: List[str] = []
    dietary_restrictions: List[str] = []
    languages: List[str] = ["en"]
    travel_pace: str = "moderate"  # slow, moderate, fast
    budget_preference: str = "mid-range"  # budget, mid-range, luxury
    accessibility_needs: Optional[Dict[str, Any]] = None

class User(BaseModel):
    user_id: str
    email: EmailStr
    full_name: str
    phone_number: Optional[str] = None
    preferences: UserPreferences
    travel_history: List[str] = []  # List of trip_ids
    saved_itineraries: List[str] = []
    payment_methods: List[Dict[str, Any]] = []
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    verified: bool = False

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone_number: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    preferences: Optional[UserPreferences] = None

class UserResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    preferences: UserPreferences
    created_at: datetime