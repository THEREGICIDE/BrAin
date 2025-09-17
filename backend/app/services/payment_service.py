import stripe
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
from app.config import settings
from app.models.booking import PaymentRequest, PaymentResponse, PaymentMethod

class PaymentService:
    def __init__(self):
        stripe.api_key = settings.stripe_secret_key
        self.currency = "INR"
    
    async def process_payment(self, payment_request: PaymentRequest) -> PaymentResponse:
        """Process payment for booking"""
        try:
            payment_id = str(uuid.uuid4())
            
            if payment_request.payment_method == PaymentMethod.CREDIT_CARD:
                result = await self._process_card_payment(payment_request)
            elif payment_request.payment_method == PaymentMethod.DEBIT_CARD:
                result = await self._process_card_payment(payment_request)
            elif payment_request.payment_method == PaymentMethod.UPI:
                result = await self._process_upi_payment(payment_request)
            elif payment_request.payment_method == PaymentMethod.NET_BANKING:
                result = await self._process_netbanking_payment(payment_request)
            elif payment_request.payment_method == PaymentMethod.WALLET:
                result = await self._process_wallet_payment(payment_request)
            else:
                raise ValueError(f"Unsupported payment method: {payment_request.payment_method}")
            
            if result['status'] == 'succeeded':
                return PaymentResponse(
                    payment_id=payment_id,
                    status='success',
                    amount=payment_request.amount,
                    currency=payment_request.currency,
                    payment_method=payment_request.payment_method.value,
                    transaction_id=result['transaction_id'],
                    timestamp=datetime.now(),
                    receipt_url=result.get('receipt_url')
                )
            else:
                return PaymentResponse(
                    payment_id=payment_id,
                    status='failed',
                    amount=payment_request.amount,
                    currency=payment_request.currency,
                    payment_method=payment_request.payment_method.value,
                    transaction_id=result.get('transaction_id', ''),
                    timestamp=datetime.now()
                )
            
        except stripe.error.CardError as e:
            return PaymentResponse(
                payment_id=payment_id,
                status='failed',
                amount=payment_request.amount,
                currency=payment_request.currency,
                payment_method=payment_request.payment_method.value,
                transaction_id='',
                timestamp=datetime.now()
            )
        except Exception as e:
            print(f"Payment processing error: {str(e)}")
            raise
    
    async def _process_card_payment(self, payment_request: PaymentRequest) -> Dict[str, Any]:
        """Process credit/debit card payment using Stripe"""
        try:
            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(payment_request.amount * 100),  # Convert to paise
                currency=self.currency.lower(),
                payment_method_types=['card'],
                description=f"Booking payment for {payment_request.booking_id}",
                metadata={
                    'booking_id': payment_request.booking_id
                }
            )
            
            # Mock successful payment for demo
            # In production, this would handle actual card tokenization
            return {
                'status': 'succeeded',
                'transaction_id': intent.id,
                'receipt_url': f"https://pay.stripe.com/receipts/{intent.id}"
            }
            
        except Exception as e:
            print(f"Card payment error: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def _process_upi_payment(self, payment_request: PaymentRequest) -> Dict[str, Any]:
        """Process UPI payment"""
        try:
            # Mock UPI payment processing
            # In production, integrate with UPI payment gateway
            
            upi_transaction_id = f"UPI{uuid.uuid4().hex[:12].upper()}"
            
            # Simulate UPI payment flow
            return {
                'status': 'succeeded',
                'transaction_id': upi_transaction_id,
                'upi_ref': payment_request.upi_id,
                'receipt_url': f"https://payments.example.com/upi/{upi_transaction_id}"
            }
            
        except Exception as e:
            print(f"UPI payment error: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def _process_netbanking_payment(self, payment_request: PaymentRequest) -> Dict[str, Any]:
        """Process Net Banking payment"""
        try:
            # Mock net banking payment
            # In production, integrate with payment gateway
            
            netbanking_ref = f"NB{uuid.uuid4().hex[:12].upper()}"
            
            return {
                'status': 'succeeded',
                'transaction_id': netbanking_ref,
                'bank_ref': netbanking_ref,
                'receipt_url': f"https://payments.example.com/netbanking/{netbanking_ref}"
            }
            
        except Exception as e:
            print(f"Net banking payment error: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def _process_wallet_payment(self, payment_request: PaymentRequest) -> Dict[str, Any]:
        """Process wallet payment"""
        try:
            # Mock wallet payment
            wallet_ref = f"WL{uuid.uuid4().hex[:12].upper()}"
            
            return {
                'status': 'succeeded',
                'transaction_id': wallet_ref,
                'wallet_ref': wallet_ref,
                'receipt_url': f"https://payments.example.com/wallet/{wallet_ref}"
            }
            
        except Exception as e:
            print(f"Wallet payment error: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    async def create_payment_session(
        self,
        amount: float,
        booking_id: str,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """Create Stripe checkout session"""
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': self.currency.lower(),
                        'product_data': {
                            'name': f'Trip Booking #{booking_id}',
                            'description': 'Complete trip package booking'
                        },
                        'unit_amount': int(amount * 100)
                    },
                    'quantity': 1
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'booking_id': booking_id
                }
            )
            
            return {
                'session_id': session.id,
                'payment_url': session.url
            }
            
        except Exception as e:
            print(f"Error creating payment session: {str(e)}")
            raise
    
    async def verify_payment(self, session_id: str) -> Dict[str, Any]:
        """Verify payment status"""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            
            return {
                'status': session.payment_status,
                'payment_intent': session.payment_intent,
                'amount': session.amount_total / 100,
                'currency': session.currency.upper()
            }
            
        except Exception as e:
            print(f"Error verifying payment: {str(e)}")
            return {
                'status': 'unknown',
                'error': str(e)
            }
    
    async def process_refund(
        self,
        payment_id: str,
        amount: Optional[float] = None,
        reason: str = "requested_by_customer"
    ) -> Dict[str, Any]:
        """Process refund for a payment"""
        try:
            refund = stripe.Refund.create(
                payment_intent=payment_id,
                amount=int(amount * 100) if amount else None,
                reason=reason
            )
            
            return {
                'refund_id': refund.id,
                'status': refund.status,
                'amount': refund.amount / 100,
                'currency': refund.currency.upper(),
                'created_at': datetime.fromtimestamp(refund.created)
            }
            
        except Exception as e:
            print(f"Error processing refund: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
            