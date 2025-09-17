from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class BookingType(str, Enum):
    FLIGHT = "flight"
    HOTEL = "hotel"
    TRANSPORT = "transport"
    ACTIVITY = "activity"
    PACKAGE = "package"

class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    UPI = "upi"
    NET_BANKING = "net_banking"
    WALLET = "wallet"

class BookingItem(BaseModel):
    item_id: str
    booking_type: BookingType
    name: str
    description: str
    provider: str
    date: datetime
    quantity: int = 1
    unit_price: float
    total_price: float
    details: Dict[str, Any]
    cancellation_policy: Optional[str] = None
    confirmation_code: Optional[str] = None

class Booking(BaseModel):
    booking_id: str
    trip_id: str
    user_id: str
    booking_items: List[BookingItem]
    total_amount: float
    currency: str = "INR"
    status: BookingStatus = BookingStatus.PENDING
    payment_method: Optional[PaymentMethod] = None
    payment_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    confirmed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    refund_amount: Optional[float] = None
    emt_booking_reference: Optional[str] = None
    
class BookingRequest(BaseModel):
    trip_id: str
    user_id: str
    booking_items: List[Dict[str, Any]]
    payment_method: PaymentMethod
    card_token: Optional[str] = None
    billing_details: Dict[str, Any]

class BookingConfirmation(BaseModel):
    booking_id: str
    status: str
    confirmation_codes: List[Dict[str, str]]
    total_amount: float
    booking_date: datetime
    trip_summary: Dict[str, Any]
    invoice_url: Optional[str] = None
    tickets_url: Optional[str] = None

class PaymentRequest(BaseModel):
    booking_id: str
    amount: float
    currency: str = "INR"
    payment_method: PaymentMethod
    card_details: Optional[Dict[str, Any]] = None
    upi_id: Optional[str] = None
    return_url: Optional[str] = None

class PaymentResponse(BaseModel):
    payment_id: str
    status: str
    amount: float
    currency: str
    payment_method: str
    transaction_id: str
    timestamp: datetime
    receipt_url: Optional[str] = None