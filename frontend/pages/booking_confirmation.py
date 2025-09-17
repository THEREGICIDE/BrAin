import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List
import qrcode
from io import BytesIO
import base64

from utils.api_client import APIClient

class BookingConfirmationPage:
    def __init__(self):
        self.api_client = APIClient()
    
    def render(self):
        """Render booking confirmation page"""
        # Header
        st.markdown(
            """
            <div style='background: linear-gradient(135deg, #43cea2 0%, #185a9d 100%);
                        padding: 2rem; border-radius: 15px; margin-bottom: 2rem;'>
                <h2 style='color: white; margin: 0;'>🎫 My Bookings</h2>
                <p style='color: rgba(255,255,255,0.9); margin-top: 0.5rem;'>
                    View and manage all your trip bookings in one place
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Tabs for different booking views
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 Current Bookings",
            "✅ Completed Trips",
            "❌ Cancelled",
            "📊 Statistics"
        ])
        
        with tab1:
            self.render_current_bookings()
        
        with tab2:
            self.render_completed_trips()
        
        with tab3:
            self.render_cancelled_bookings()
        
        with tab4:
            self.render_travel_statistics()
    
    def render_current_bookings(self):
        """Render current bookings"""
        # Check if there's a recent booking
        if st.session_state.get('booking_id'):
            # Success message for new booking
            st.markdown(
                """
                <div style='background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                            padding: 2rem; border-radius: 15px; margin-bottom: 2rem;
                            box-shadow: 0 10px 30px rgba(0,0,0,0.2);'>
                    <h2 style='color: white; margin: 0; text-align: center;'>
                        🎉 Booking Confirmed Successfully!
                    </h2>
                    <p style='color: white; text-align: center; margin: 1rem 0; font-size: 1.2rem;'>
                        Your dream trip is all set! Get ready for an amazing adventure.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Current bookings list
        bookings = self.get_mock_bookings()
        
        if bookings:
            for booking in bookings:
                self.render_booking_card(booking)
        else:
            # Empty state
            st.markdown(
                """
                <div style='text-align: center; padding: 3rem; background: #f8f9fa;
                            border-radius: 15px; border: 2px dashed #dee2e6;'>
                    <h3 style='color: #6c757d;'>No Active Bookings</h3>
                    <p style='color: #6c757d;'>Start planning your next adventure!</p>
                    <p style='font-size: 4rem;'>🗺️</p>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    def render_booking_card(self, booking: Dict[str, Any]):
        """Render individual booking card"""
        # Main booking card with gradient border
        st.markdown(
            f"""
            <div style='background: white; border-radius: 15px; padding: 2rem;
                        margin-bottom: 2rem; box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                        border-top: 5px solid #FF6B6B;'>
                <div style='display: flex; justify-content: space-between; align-items: start;'>
                    <div>
                        <h3 style='margin: 0; color: #2c3e50;'>
                            {booking['destination']} Trip
                        </h3>
                        <p style='color: #7f8c8d; margin: 0.5rem 0;'>
                            Booking ID: <strong>{booking['booking_id']}</strong>
                        </p>
                    </div>
                    <div style='text-align: right;'>
                        <span style='background: #4CAF50; color: white; padding: 0.5rem 1rem;
                                   border-radius: 20px; font-weight: bold;'>
                            {booking['status']}
                        </span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Booking details in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(
                f"""
                <div style='background: #f8f9fa; padding: 1rem; border-radius: 10px;
                            text-align: center;'>
                    <p style='color: #6c757d; margin: 0; font-size: 0.9rem;'>Travel Dates</p>
                    <h4 style='margin: 0.5rem 0; color: #2c3e50;'>
                        {booking['start_date']} - {booking['end_date']}
                    </h4>
                    <p style='color: #FF6B6B; margin: 0; font-weight: bold;'>
                        {booking['duration']} Days
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col2:
            st.markdown(
                f"""
                <div style='background: #f8f9fa; padding: 1rem; border-radius: 10px;
                            text-align: center;'>
                    <p style='color: #6c757d; margin: 0; font-size: 0.9rem;'>Travelers</p>
                    <h4 style='margin: 0.5rem 0; color: #2c3e50;'>
                        {booking['travelers']} {'Person' if booking['travelers'] == 1 else 'People'}
                    </h4>
                    <p style='color: #4CAF50; margin: 0;'>
                        {'👤' * min(booking['travelers'], 5)}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col3:
            st.markdown(
                f"""
                <div style='background: #f8f9fa; padding: 1rem; border-radius: 10px;
                            text-align: center;'>
                    <p style='color: #6c757d; margin: 0; font-size: 0.9rem;'>Total Amount</p>
                    <h4 style='margin: 0.5rem 0; color: #2c3e50;'>
                        ₹{booking['amount']:,.0f}
                    </h4>
                    <p style='color: #2196F3; margin: 0; font-size: 0.9rem;'>
                        Paid via {booking['payment_method']}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col4:
            st.markdown(
                f"""
                <div style='background: #f8f9fa; padding: 1rem; border-radius: 10px;
                            text-align: center;'>
                    <p style='color: #6c757d; margin: 0; font-size: 0.9rem;'>Booked On</p>
                    <h4 style='margin: 0.5rem 0; color: #2c3e50;'>
                        {booking['booking_date']}
                    </h4>
                    <p style='color: #9c27b0; margin: 0; font-size: 0.9rem;'>
                        EMT Ref: {booking['emt_ref']}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Expandable sections
        with st.expander("📋 Booking Details"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🏨 Accommodations")
                for hotel in booking['hotels']:
                    st.write(f"• {hotel['name']} - {hotel['nights']} nights")
                
                st.markdown("#### ✈️ Flights")
                for flight in booking['flights']:
                    st.write(f"• {flight['route']} - {flight['airline']}")
            
            with col2:
                st.markdown("#### 🎫 Activities")
                for activity in booking['activities']:
                    st.write(f"• {activity['name']} - Day {activity['day']}")
                
                st.markdown("#### 🚗 Local Transport")
                st.write(f"• {booking['transport']['type']} included")
        
        # QR Code for booking
        with st.expander("📱 Digital Tickets & QR Code"):
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                # Generate QR code
                qr_data = f"BOOKING:{booking['booking_id']}|EMT:{booking['emt_ref']}"
                qr_img = self.generate_qr_code(qr_data)
                
                st.markdown(
                    """
                    <div style='text-align: center; padding: 1rem;'>
                        <h4>Scan for Digital Tickets</h4>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        # Action buttons
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("📄 Download Invoice", key=f"invoice_{booking['booking_id']}", use_container_width=True):
                st.success("Invoice downloaded!")
        
        with col2:
            if st.button("📧 Email Tickets", key=f"email_{booking['booking_id']}", use_container_width=True):
                st.success("Tickets sent to your email!")
        
        with col3:
            if st.button("📅 Add to Calendar", key=f"calendar_{booking['booking_id']}", use_container_width=True):
                st.success("Added to calendar!")
        
        with col4:
            if st.button("🔄 Modify Booking", key=f"modify_{booking['booking_id']}", use_container_width=True):
                st.info("Redirecting to modification page...")
        
        with col5:
            if st.button("❌ Cancel Booking", key=f"cancel_{booking['booking_id']}", use_container_width=True):
                self.show_cancellation_dialog(booking)
    
    def render_completed_trips(self):
        """Render completed trips"""
        completed_trips = [
            {
                "destination": "Kerala Backwaters",
                "dates": "Oct 15-20, 2024",
                "rating": 5,
                "photos": 45,
                "highlights": ["Houseboat Stay", "Kathakali Performance", "Tea Gardens"]
            },
            {
                "destination": "Rajasthan Heritage Tour",
                "dates": "Aug 5-12, 2024",
                "rating": 4,
                "photos": 128,
                "highlights": ["Amber Fort", "Desert Safari", "Blue City"]
            }
        ]
        
        st.markdown("### 🏆 Your Travel Memories")
        
        for trip in completed_trips:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(
                    f"""
                    <div style='background: white; padding: 1.5rem; border-radius: 10px;
                                box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 1rem;'>
                        <h4 style='margin: 0; color: #2c3e50;'>{trip['destination']}</h4>
                        <p style='color: #7f8c8d; margin: 0.5rem 0;'>{trip['dates']}</p>
                        <div style='display: flex; gap: 1rem; margin-top: 1rem;'>
                            {'⭐' * trip['rating']}
                        </div>
                        <p style='color: #3498db; margin-top: 0.5rem;'>
                            📸 {trip['photos']} photos • 
                            {' • '.join(trip['highlights'])}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button(f"View Gallery", key=f"gallery_{trip['destination']}", use_container_width=True):
                    st.info("Opening photo gallery...")
                if st.button(f"Write Review", key=f"review_{trip['destination']}", use_container_width=True):
                    st.info("Share your experience!")
    
    def render_cancelled_bookings(self):
        """Render cancelled bookings"""
        st.markdown(
            """
            <div style='background: #ffebee; padding: 1.5rem; border-radius: 10px;
                        border-left: 4px solid #f44336;'>
                <h4 style='color: #c62828; margin: 0;'>Cancelled Bookings</h4>
                <p style='color: #ef5350; margin: 0.5rem 0;'>
                    No cancelled bookings. Your travel record is perfect! 🎉
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    def render_travel_statistics(self):
        """Render travel statistics dashboard"""
        st.markdown(
            """
            <div style='background: linear-gradient(135deg, #6B73FF 0%, #000DFF 100%);
                        padding: 2rem; border-radius: 15px; margin-bottom: 2rem;'>
                <h3 style='color: white; margin: 0;'>📊 Your Travel Dashboard</h3>
                <p style='color: rgba(255,255,255,0.9); margin-top: 0.5rem;'>
                    Track your travel patterns and achievements
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Statistics cards
        col1, col2, col3, col4 = st.columns(4)
        
        stats = [
            {"label": "Total Trips", "value": "12", "icon": "✈️", "color": "#4CAF50"},
            {"label": "Cities Visited", "value": "28", "icon": "🏙️", "color": "#2196F3"},
            {"label": "Total Spent", "value": "₹2.5L", "icon": "💰", "color": "#FF9800"},
            {"label": "Travel Days", "value": "67", "icon": "📅", "color": "#9C27B0"}
        ]
        
        for col, stat in zip([col1, col2, col3, col4], stats):
            with col:
                st.markdown(
                    f"""
                    <div style='background: white; padding: 1.5rem; border-radius: 10px;
                                box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center;
                                border-top: 4px solid {stat['color']};'>
                        <h2 style='margin: 0; color: {stat['color']};'>{stat['icon']}</h2>
                        <h3 style='margin: 0.5rem 0; color: #2c3e50;'>{stat['value']}</h3>
                        <p style='margin: 0; color: #7f8c8d;'>{stat['label']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Monthly travel trend
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            trips = [0, 1, 0, 2, 1, 0, 1, 2, 1, 2, 1, 1]
            
            fig = go.Figure(data=[
                go.Bar(x=months, y=trips, marker_color='#FF6B6B')
            ])
            fig.update_layout(
                title="Monthly Travel Pattern",
                xaxis_title="Month",
                yaxis_title="Number of Trips",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Spending by category
            categories = ['Hotels', 'Flights', 'Food', 'Activities', 'Transport']
            spending = [35, 30, 15, 12, 8]
            
            fig = px.pie(
                values=spending,
                names=categories,
                title="Spending Distribution (%)",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Travel map
        st.markdown("### 🗺️ Your Travel Map")
        visited_states = [
            "Goa", "Kerala", "Rajasthan", "Himachal Pradesh",
            "Uttarakhand", "Tamil Nadu", "Karnataka", "Maharashtra"
        ]
        
        st.info(f"🎯 You've explored **{len(visited_states)}** states in India!")
        
        # Achievement badges
        st.markdown("### 🏆 Travel Achievements")
        
        achievements = [
            {"title": "Beach Lover", "desc": "5+ beach destinations", "icon": "🏖️", "unlocked": True},
            {"title": "Mountain Explorer", "desc": "3+ hill stations", "icon": "🏔️", "unlocked": True},
            {"title": "Culture Enthusiast", "desc": "10+ heritage sites", "icon": "🏛️", "unlocked": True},
            {"title": "Adventure Seeker", "desc": "5+ adventure activities", "icon": "🎢", "unlocked": False},
            {"title": "Foodie Traveler", "desc": "20+ local cuisines", "icon": "🍛", "unlocked": True},
            {"title": "Budget Master", "desc": "Save 20% on 5 trips", "icon": "💰", "unlocked": False}
        ]
        
        cols = st.columns(6)
        for idx, achievement in enumerate(achievements):
            with cols[idx % 6]:
                if achievement['unlocked']:
                    st.markdown(
                        f"""
                        <div style='background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
                                    padding: 1rem; border-radius: 10px; text-align: center;
                                    box-shadow: 0 2px 10px rgba(0,0,0,0.2);'>
                            <h2 style='margin: 0;'>{achievement['icon']}</h2>
                            <p style='margin: 0.5rem 0; font-weight: bold; color: white;'>
                                {achievement['title']}
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"""
                        <div style='background: #f5f5f5; padding: 1rem; border-radius: 10px;
                                    text-align: center; opacity: 0.5;'>
                            <h2 style='margin: 0; filter: grayscale(100%);'>{achievement['icon']}</h2>
                            <p style='margin: 0.5rem 0; color: #999;'>Locked</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
    
    def get_mock_bookings(self) -> List[Dict[str, Any]]:
        """Get mock booking data"""
        bookings = []
        
        if st.session_state.get('booking_id'):
            bookings.append({
                'booking_id': st.session_state.booking_id,
                'destination': 'Goa',
                'start_date': 'Dec 20',
                'end_date': 'Dec 23',
                'duration': 4,
                'travelers': 2,
                'amount': 45000,
                'payment_method': 'Card',
                'booking_date': datetime.now().strftime('%b %d, %Y'),
                'status': 'CONFIRMED',
                'emt_ref': 'EMT-2024-GOA123',
                'hotels': [
                    {'name': 'Taj Vivanta', 'nights': 3}
                ],
                'flights': [
                    {'route': 'DEL-GOI', 'airline': 'IndiGo'},
                    {'route': 'GOI-DEL', 'airline': 'IndiGo'}
                ],
                'activities': [
                    {'name': 'Beach Water Sports', 'day': 2},
                    {'name': 'Dudhsagar Falls', 'day': 3}
                ],
                'transport': {'type': 'Private Car'}
            })
        
        # Add more sample bookings
        bookings.append({
            'booking_id': 'BOOK789012',
            'destination': 'Manali',
            'start_date': 'Jan 5',
            'end_date': 'Jan 9',
            'duration': 5,
            'travelers': 4,
            'amount': 80000,
            'payment_method': 'UPI',
            'booking_date': 'Nov 15, 2024',
            'status': 'CONFIRMED',
            'emt_ref': 'EMT-2025-MAN456',
            'hotels': [
                {'name': 'The Himalayan', 'nights': 4}
            ],
            'flights': [
                {'route': 'DEL-KUU', 'airline': 'Air India'},
                {'route': 'KUU-DEL', 'airline': 'Air India'}
            ],
            'activities': [
                {'name': 'Solang Valley', 'day': 2},
                {'name': 'Rohtang Pass', 'day': 3},
                {'name': 'River Rafting', 'day': 4}
            ],
            'transport': {'type': 'SUV Rental'}
        })
        
        return bookings
    
    def generate_qr_code(self, data: str) -> bytes:
        """Generate QR code image"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
    
    def show_cancellation_dialog(self, booking: Dict[str, Any]):
        """Show cancellation dialog"""
        st.warning(
            f"""
            ⚠️ **Cancellation Policy**
            
            • More than 7 days before travel: 90% refund
            • 3-7 days before travel: 50% refund
            • Less than 3 days: No refund
            
            Your estimated refund: ₹{booking['amount'] * 0.9:,.0f}
            """
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Confirm Cancellation", key=f"confirm_cancel_{booking['booking_id']}", type="primary"):
                st.success("Booking cancelled. Refund will be processed in 3-5 business days.")
        with col2:
            if st.button("Keep Booking", key=f"keep_{booking['booking_id']}"):
                st.info("Great choice! Your adventure awaits.")
                st.image(qr_img, use_container_width=True)
                
                st.markdown(
                    f"""
                    <div style='background: #e3f2fd; padding: 1rem; border-radius: 10px;
                                margin-top: 1rem;'>
                        <p style='margin: 0;'><strong>Booking ID:</strong> {booking['booking_id']}</p>
                        <p style='margin: 0;'><strong>EMT Reference:</strong> {booking['emt_ref']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )