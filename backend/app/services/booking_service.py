import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from app.config import settings
from app.models.booking import (
    BookingRequest, 
    Booking, 
    BookingItem, 
    BookingType,
    BookingStatus,
    BookingConfirmation
)

class BookingService:
    def __init__(self):
        self.emt_base_url = settings.emt_api_base_url
        self.emt_api_key = settings.emt_api_key
        self.client = httpx.AsyncClient()
    
    async def create_booking(self, booking_request: BookingRequest) -> Booking:
        """Create a new booking"""
        try:
            # Generate booking ID
            booking_id = str(uuid.uuid4())
            
            # Process each booking item
            processed_items = []
            total_amount = 0
            
            for item_data in booking_request.booking_items:
                # Create booking with EMT API
                emt_booking = await self._create_emt_booking(item_data)
                
                booking_item = BookingItem(
                    item_id=str(uuid.uuid4()),
                    booking_type=BookingType(item_data['type']),
                    name=item_data['name'],
                    description=item_data.get('description', ''),
                    provider=item_data.get('provider', 'EMT'),
                    date=datetime.fromisoformat(item_data['date']),
                    quantity=item_data.get('quantity', 1),
                    unit_price=item_data['price'],
                    total_price=item_data['price'] * item_data.get('quantity', 1),
                    details=item_data,
                    confirmation_code=emt_booking.get('confirmation_code')
                )
                
                processed_items.append(booking_item)
                total_amount += booking_item.total_price
            
            # Create booking object
            booking = Booking(
                booking_id=booking_id,
                trip_id=booking_request.trip_id,
                user_id=booking_request.user_id,
                booking_items=processed_items,
                total_amount=total_amount,
                status=BookingStatus.PENDING,
                payment_method=booking_request.payment_method,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Save to database (implement database storage)
            await self._save_booking(booking)
            
            return booking
            
        except Exception as e:
            print(f"Error creating booking: {str(e)}")
            raise
    
    async def _create_emt_booking(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create booking with EMT API"""
        try:
            # Mock EMT API call
            # In production, this would make actual API calls to EMT
            
            booking_type = item_data.get('type')
            
            if booking_type == 'flight':
                return await self._book_flight(item_data)
            elif booking_type == 'hotel':
                return await self._book_hotel(item_data)
            elif booking_type == 'transport':
                return await self._book_transport(item_data)
            elif booking_type == 'activity':
                return await self._book_activity(item_data)
            else:
                return {
                    'confirmation_code': f"EMT-{uuid.uuid4().hex[:8].upper()}",
                    'status': 'confirmed'
                }
                
        except Exception as e:
            print(f"Error with EMT booking: {str(e)}")
            return {
                'confirmation_code': None,
                'status': 'failed',
                'error': str(e)
            }
    
    async def _book_flight(self, flight_data: Dict[str, Any]) -> Dict[str, Any]:
        """Book flight through EMT"""
        try:
            # Mock implementation
            # Real implementation would call EMT flight booking API
            
            endpoint = f"{self.emt_base_url}/flights/book"
            headers = {
                "Authorization": f"Bearer {self.emt_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "origin": flight_data.get('origin'),
                "destination": flight_data.get('destination'),
                "departure_date": flight_data.get('date'),
                "passengers": flight_data.get('passengers', 1),
                "class": flight_data.get('class', 'economy'),
                "airline": flight_data.get('airline')
            }
            
            # Mock response
            return {
                'confirmation_code': f"FL-{uuid.uuid4().hex[:8].upper()}",
                'pnr': f"PNR{uuid.uuid4().hex[:6].upper()}",
                'status': 'confirmed',
                'ticket_url': f"https://emt.com/tickets/{uuid.uuid4().hex}"
            }
            
        except Exception as e:
            print(f"Error booking flight: {str(e)}")
            raise
    
    async def _book_hotel(self, hotel_data: Dict[str, Any]) -> Dict[str, Any]:
        """Book hotel through EMT"""
        try:
            # Mock implementation
            endpoint = f"{self.emt_base_url}/hotels/book"
            
            payload = {
                "hotel_id": hotel_data.get('hotel_id'),
                "check_in": hotel_data.get('check_in'),
                "check_out": hotel_data.get('check_out'),
                "rooms": hotel_data.get('rooms', 1),
                "guests": hotel_data.get('guests', 2),
                "room_type": hotel_data.get('room_type', 'standard')
            }
            
            # Mock response
            return {
                'confirmation_code': f"HT-{uuid.uuid4().hex[:8].upper()}",
                'reservation_id': f"RES{uuid.uuid4().hex[:6].upper()}",
                'status': 'confirmed',
                'voucher_url': f"https://emt.com/vouchers/{uuid.uuid4().hex}"
            }
            
        except Exception as e:
            print(f"Error booking hotel: {str(e)}")
            raise
    
    async def _book_transport(self, transport_data: Dict[str, Any]) -> Dict[str, Any]:
        """Book local transport through EMT"""
        try:
            transport_type = transport_data.get('transport_type', 'cab')
            
            if transport_type == 'train':
                return await self._book_train(transport_data)
            elif transport_type == 'bus':
                return await self._book_bus(transport_data)
            else:
                return await self._book_cab(transport_data)
                
        except Exception as e:
            print(f"Error booking transport: {str(e)}")
            raise
    
    async def _book_train(self, train_data: Dict[str, Any]) -> Dict[str, Any]:
        """Book train through EMT/IRCTC integration"""
        return {
            'confirmation_code': f"TR-{uuid.uuid4().hex[:8].upper()}",
            'pnr': f"PNR{uuid.uuid4().hex[:10].upper()}",
            'status': 'confirmed',
            'ticket_url': f"https://emt.com/train-tickets/{uuid.uuid4().hex}"
        }
    
    async def _book_bus(self, bus_data: Dict[str, Any]) -> Dict[str, Any]:
        """Book bus through EMT"""
        return {
            'confirmation_code': f"BS-{uuid.uuid4().hex[:8].upper()}",
            'booking_id': f"BUS{uuid.uuid4().hex[:6].upper()}",
            'status': 'confirmed',
            'ticket_url': f"https://emt.com/bus-tickets/{uuid.uuid4().hex}"
        }
    
    async def _book_cab(self, cab_data: Dict[str, Any]) -> Dict[str, Any]:
        """Book cab through EMT"""
        return {
            'confirmation_code': f"CB-{uuid.uuid4().hex[:8].upper()}",
            'ride_id': f"RIDE{uuid.uuid4().hex[:6].upper()}",
            'status': 'confirmed',
            'driver_details': {
                'name': 'Driver Name',
                'phone': '+91-9999999999',
                'vehicle': 'Vehicle Model',
                'number': 'DL01AB1234'
            }
        }
    
    async def _book_activity(self, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Book activity/experience through EMT"""
        return {
            'confirmation_code': f"AC-{uuid.uuid4().hex[:8].upper()}",
            'booking_ref': f"ACT{uuid.uuid4().hex[:6].upper()}",
            'status': 'confirmed',
            'voucher_url': f"https://emt.com/activities/{uuid.uuid4().hex}",
            'qr_code': f"QR-{uuid.uuid4().hex[:12].upper()}"
        }
    
    async def confirm_booking(self, booking_id: str, payment_id: str) -> BookingConfirmation:
        """Confirm booking after payment"""
        try:
            # Retrieve booking
            booking = await self._get_booking(booking_id)
            
            if not booking:
                raise ValueError(f"Booking {booking_id} not found")
            
            # Update booking status
            booking.status = BookingStatus.CONFIRMED
            booking.payment_id = payment_id
            booking.confirmed_at = datetime.now()
            booking.updated_at = datetime.now()
            
            # Generate EMT reference
            booking.emt_booking_reference = f"EMT-{datetime.now().strftime('%Y%m%d')}-{booking_id[:8].upper()}"
            
            # Save updated booking
            await self._update_booking(booking)
            
            # Generate confirmation
            confirmation_codes = []
            for item in booking.booking_items:
                if item.confirmation_code:
                    confirmation_codes.append({
                        'item': item.name,
                        'code': item.confirmation_code
                    })
            
            confirmation = BookingConfirmation(
                booking_id=booking.booking_id,
                status=booking.status.value,
                confirmation_codes=confirmation_codes,
                total_amount=booking.total_amount,
                booking_date=booking.created_at,
                trip_summary={
                    'trip_id': booking.trip_id,
                    'items_count': len(booking.booking_items),
                    'emt_reference': booking.emt_booking_reference
                },
                invoice_url=f"https://emt.com/invoices/{booking_id}",
                tickets_url=f"https://emt.com/tickets/{booking_id}"
            )
            
            # Send confirmation email
            await self._send_confirmation_email(booking, confirmation)
            
            return confirmation
            
        except Exception as e:
            print(f"Error confirming booking: {str(e)}")
            raise
    
    async def cancel_booking(self, booking_id: str, reason: str) -> Dict[str, Any]:
        """Cancel a booking"""
        try:
            booking = await self._get_booking(booking_id)
            
            if not booking:
                raise ValueError(f"Booking {booking_id} not found")
            
            # Check if cancellation is allowed
            if booking.status in [BookingStatus.CANCELLED, BookingStatus.REFUNDED]:
                return {
                    'status': 'already_cancelled',
                    'message': 'Booking is already cancelled'
                }
            
            # Cancel with EMT
            cancellation_results = []
            for item in booking.booking_items:
                if item.confirmation_code:
                    result = await self._cancel_emt_booking(
                        item.booking_type,
                        item.confirmation_code
                    )
                    cancellation_results.append(result)
            
            # Update booking status
            booking.status = BookingStatus.CANCELLED
            booking.cancelled_at = datetime.now()
            booking.cancellation_reason = reason
            booking.updated_at = datetime.now()
            
            # Calculate refund
            refund_amount = await self._calculate_refund(booking)
            booking.refund_amount = refund_amount
            
            await self._update_booking(booking)
            
            return {
                'status': 'cancelled',
                'booking_id': booking_id,
                'refund_amount': refund_amount,
                'cancellation_results': cancellation_results
            }
            
        except Exception as e:
            print(f"Error cancelling booking: {str(e)}")
            raise
    
    async def _cancel_emt_booking(
        self, 
        booking_type: BookingType, 
        confirmation_code: str
    ) -> Dict[str, Any]:
        """Cancel individual EMT booking"""
        # Mock implementation
        return {
            'confirmation_code': confirmation_code,
            'cancelled': True,
            'refund_status': 'processing'
        }
    
    async def _calculate_refund(self, booking: Booking) -> float:
        """Calculate refund amount based on cancellation policy"""
        # Mock implementation - implement actual refund policy logic
        hours_until_booking = (booking.booking_items[0].date - datetime.now()).total_seconds() / 3600
        
        if hours_until_booking > 48:
            return booking.total_amount * 0.9  # 90% refund
        elif hours_until_booking > 24:
            return booking.total_amount * 0.5  # 50% refund
        else:
            return 0  # No refund
    
    async def get_booking_status(self, booking_id: str) -> Dict[str, Any]:
        """Get current booking status"""
        try:
            booking = await self._get_booking(booking_id)
            
            if not booking:
                return {'status': 'not_found'}
            
            return {
                'booking_id': booking.booking_id,
                'status': booking.status.value,
                'total_amount': booking.total_amount,
                'items': len(booking.booking_items),
                'created_at': booking.created_at.isoformat(),
                'confirmed_at': booking.confirmed_at.isoformat() if booking.confirmed_at else None,
                'emt_reference': booking.emt_booking_reference
            }
            
        except Exception as e:
            print(f"Error getting booking status: {str(e)}")
            raise
    
    async def _save_booking(self, booking: Booking):
        """Save booking to database"""
        # Implement database storage
        pass
    
    async def _get_booking(self, booking_id: str) -> Optional[Booking]:
        """Retrieve booking from database"""
        # Implement database retrieval
        # Mock implementation
        return None
    
    async def _update_booking(self, booking: Booking):
        """Update booking in database"""
        # Implement database update
        pass
    
    async def _send_confirmation_email(
        self, 
        booking: Booking, 
        confirmation: BookingConfirmation
    ):
        """Send booking confirmation email"""
        # Implement email sending
        pass