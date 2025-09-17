import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List
import folium
from streamlit_folium import st_folium
import json

from utils.api_client import APIClient

class TripPlannerPage:
    def __init__(self):
        self.api_client = APIClient()
        self.themes = {
            "🏛️ Heritage": "heritage",
            "🎒 Adventure": "adventure",
            "🌃 Nightlife": "nightlife",
            "🎭 Cultural": "cultural",
            "🏖️ Relaxation": "relaxation",
            "👨‍👩‍👧‍👦 Family": "family",
            "💼 Business": "business",
            "💑 Romantic": "romantic",
            "🍽️ Foodie": "foodie",
            "🛍️ Shopping": "shopping"
        }
        self.accommodation_types = {
            "🏨 Hotel": "hotel",
            "🏠 Hostel": "hostel",
            "🏖️ Resort": "resort",
            "🏡 Homestay": "homestay",
            "🏢 Airbnb": "airbnb",
            "🏰 Villa": "villa"
        }
        self.transport_modes = {
            "✈️ Flight": "flight",
            "🚂 Train": "train",
            "🚌 Bus": "bus",
            "🚗 Car": "car",
            "🚕 Taxi": "taxi",
            "🚶 Walk": "walk",
            "🚴 Bike": "bike"
        }
    
    def render(self):
        """Render trip planner page"""
        st.markdown(
            """
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 2rem; border-radius: 10px; margin-bottom: 2rem;'>
                <h2 style='color: white; margin: 0;'>🗺️ Create Your Perfect Journey</h2>
                <p style='color: rgba(255,255,255,0.9); margin-top: 0.5rem;'>
                    Tell us your preferences, and our AI will craft a personalized itinerary just for you!
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Create tabs for different sections
        tab1, tab2, tab3, tab4 = st.tabs(["📝 Trip Details", "🎯 Preferences", "📅 Itinerary", "💳 Book Now"])
        
        with tab1:
            self.render_trip_details()
        
        with tab2:
            self.render_preferences()
        
        with tab3:
            self.render_itinerary()
        
        with tab4:
            self.render_booking()
    
    def render_trip_details(self):
        """Render trip details form"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(
                """
                <div style='background: #f8f9fa; padding: 1.5rem; border-radius: 10px; 
                            border-left: 4px solid #FF6B6B;'>
                    <h4 style='margin-top: 0; color: #2c3e50;'>📍 Where & When</h4>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Destination with autocomplete suggestions
            destination = st.text_input(
                "Destination City",
                placeholder="e.g., Goa, Mumbai, Jaipur",
                help="Enter your dream destination"
            )
            
            # Popular destinations
            st.markdown("**🔥 Trending Destinations:**")
            trending_cols = st.columns(3)
            trending_destinations = ["Goa", "Kerala", "Rajasthan", "Himachal", "Kashmir", "Andaman"]
            for idx, dest in enumerate(trending_destinations):
                with trending_cols[idx % 3]:
                    if st.button(dest, key=f"trend_{dest}", use_container_width=True):
                        st.session_state.selected_destination = dest
            
            # Date selection with calendar
            date_col1, date_col2 = st.columns(2)
            with date_col1:
                start_date = st.date_input(
                    "Start Date",
                    min_value=date.today(),
                    value=date.today() + timedelta(days=7)
                )
            
            with date_col2:
                end_date = st.date_input(
                    "End Date",
                    min_value=start_date + timedelta(days=1) if start_date else date.today(),
                    value=start_date + timedelta(days=3) if start_date else date.today() + timedelta(days=10)
                )
            
            # Duration display
            if start_date and end_date:
                duration = (end_date - start_date).days + 1
                st.info(f"📅 Trip Duration: **{duration} days**")
        
        with col2:
            st.markdown(
                """
                <div style='background: #f8f9fa; padding: 1.5rem; border-radius: 10px;
                            border-left: 4px solid #4CAF50;'>
                    <h4 style='margin-top: 0; color: #2c3e50;'>💰 Budget & Travelers</h4>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Budget slider with visual representation
            budget = st.slider(
                "Total Budget (₹)",
                min_value=10000,
                max_value=500000,
                value=50000,
                step=5000,
                format="₹%d"
            )
            
            # Budget breakdown visualization
            if start_date and end_date:
                daily_budget = budget / duration
                st.markdown(f"**Daily Budget:** ₹{daily_budget:,.0f}")
                
                # Mini budget pie chart
                fig = go.Figure(data=[go.Pie(
                    labels=['Accommodation', 'Food', 'Activities', 'Transport', 'Others'],
                    values=[budget*0.3, budget*0.25, budget*0.2, budget*0.15, budget*0.1],
                    hole=.3,
                    marker_colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
                )])
                fig.update_layout(
                    showlegend=False,
                    height=200,
                    margin=dict(t=0, b=0, l=0, r=0)
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Travelers count with icons
            travelers = st.number_input(
                "Number of Travelers",
                min_value=1,
                max_value=20,
                value=2,
                step=1
            )
            
            # Display traveler icons
            traveler_icons = "👤" * min(travelers, 10)
            if travelers > 10:
                traveler_icons += f" +{travelers-10}"
            st.markdown(f"<h3 style='text-align: center;'>{traveler_icons}</h3>", unsafe_allow_html=True)
            
            # Group type suggestions
            if travelers == 1:
                st.info("🎒 **Solo Traveler** - Adventure awaits!")
            elif travelers == 2:
                st.info("💑 **Couple/Duo** - Perfect for romantic getaways!")
            elif travelers <= 4:
                st.info("👨‍👩‍👧‍👦 **Small Group** - Great for family trips!")
            else:
                st.info("👥 **Large Group** - Group discounts available!")
    
    def render_preferences(self):
        """Render preferences selection"""
        st.markdown(
            """
            <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                        padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem;'>
                <h3 style='color: white; margin: 0;'>🎯 Customize Your Experience</h3>
                <p style='color: rgba(255,255,255,0.9); margin-top: 0.5rem;'>
                    Select your interests and preferences to get a tailored itinerary
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 🎭 Trip Themes")
            st.markdown("*Select up to 3 themes*")
            
            selected_themes = []
            theme_cols = st.columns(2)
            for idx, (display_name, theme_value) in enumerate(self.themes.items()):
                with theme_cols[idx % 2]:
                    if st.checkbox(display_name, key=f"theme_{theme_value}"):
                        selected_themes.append(theme_value)
            
            if len(selected_themes) > 3:
                st.warning("⚠️ Please select maximum 3 themes")
        
        with col2:
            st.markdown("### 🏨 Accommodation")
            
            # Accommodation preference with visual cards
            selected_accommodation = st.radio(
                "Preferred Stay Type",
                options=list(self.accommodation_types.keys()),
                key="accommodation_pref"
            )
            
            # Star rating for hotels
            if "Hotel" in selected_accommodation or "Resort" in selected_accommodation:
                star_rating = st.select_slider(
                    "Preferred Star Rating",
                    options=["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"],
                    value="⭐⭐⭐"
                )
            
            st.markdown("### 🚗 Transport")
            selected_transport = st.radio(
                "Preferred Transport",
                options=list(self.transport_modes.keys()),
                key="transport_pref"
            )
            
            include_flights = st.checkbox("✈️ Include flight bookings", value=True)
            flexible_dates = st.checkbox("📅 My dates are flexible (±2 days)", value=False)
        
        with col3:
            st.markdown("### 🍽️ Dietary Preferences")
            
            dietary_options = {
                "🥗 Vegetarian": "vegetarian",
                "🌱 Vegan": "vegan",
                "🍖 Non-Vegetarian": "non_veg",
                "🕉️ Jain": "jain",
                "☪️ Halal": "halal",
                "🥜 Nut Allergy": "nut_allergy",
                "🍞 Gluten Free": "gluten_free"
            }
            
            dietary_restrictions = []
            for display_name, diet_value in dietary_options.items():
                if st.checkbox(display_name, key=f"diet_{diet_value}"):
                    dietary_restrictions.append(diet_value)
            
            st.markdown("### 🗣️ Language")
            language = st.selectbox(
                "Preferred Language",
                ["English", "Hindi", "Tamil", "Telugu", "Kannada", "Malayalam", "Bengali", "Marathi", "Gujarati"]
            )
            
            st.markdown("### 📝 Special Requirements")
            special_requirements = st.text_area(
                "Any special needs?",
                placeholder="e.g., Wheelchair accessible, Pet-friendly, Near beach, etc.",
                height=100
            )
        
        # Generate button with animation
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Generate My Perfect Itinerary", use_container_width=True, type="primary"):
                with st.spinner("✨ Our AI is crafting your perfect journey..."):
                    self.generate_itinerary()
    
    def render_itinerary(self):
        """Render generated itinerary"""
        if st.session_state.get('current_trip'):
            trip = st.session_state.current_trip
            
            # Header with trip summary
            st.markdown(
                f"""
                <div style='background: linear-gradient(135deg, #A8E6CF 0%, #81C784 100%);
                            padding: 2rem; border-radius: 15px; margin-bottom: 2rem;'>
                    <h2 style='color: #1B5E20; margin: 0;'>✨ Your Personalized Itinerary</h2>
                    <div style='display: flex; justify-content: space-around; margin-top: 1rem;'>
                        <div style='text-align: center;'>
                            <h4 style='color: #2E7D32; margin: 0;'>📍 {trip['destination']}</h4>
                            <p style='color: #1B5E20; margin: 0;'>Destination</p>
                        </div>
                        <div style='text-align: center;'>
                            <h4 style='color: #2E7D32; margin: 0;'>{trip['duration_days']} Days</h4>
                            <p style='color: #1B5E20; margin: 0;'>Duration</p>
                        </div>
                        <div style='text-align: center;'>
                            <h4 style='color: #2E7D32; margin: 0;'>₹{trip['actual_cost']:,.0f}</h4>
                            <p style='color: #1B5E20; margin: 0;'>Total Cost</p>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Interactive map
            self.render_trip_map(trip)
            
            # Day-by-day itinerary
            self.render_daily_itinerary(trip)
            
            # Cost breakdown
            self.render_cost_breakdown(trip)
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("💾 Save Itinerary", use_container_width=True):
                    st.success("✅ Itinerary saved to your profile!")
            
            with col2:
                if st.button("🔄 Modify Itinerary", use_container_width=True):
                    st.info("🛠️ Modification feature coming soon!")
            
            with col3:
                if st.button("📧 Share Itinerary", use_container_width=True):
                    st.success("📤 Share link copied to clipboard!")
        else:
            # Empty state
            st.markdown(
                """
                <div style='text-align: center; padding: 4rem; background: #f8f9fa; border-radius: 15px;'>
                    <h2 style='color: #6c757d;'>🗺️ No Itinerary Yet</h2>
                    <p style='color: #6c757d; font-size: 1.1rem;'>
                        Fill in your trip details and preferences to generate a personalized itinerary
                    </p>
                    <p style='font-size: 3rem; margin: 2rem 0;'>✈️ 🏖️ 🏔️ 🏛️</p>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    def render_trip_map(self, trip: Dict[str, Any]):
        """Render interactive map with trip locations"""
        st.markdown("### 🗺️ Trip Map")
        
        # Create folium map
        m = folium.Map(
            location=[20.5937, 78.9629],  # Center of India
            zoom_start=5,
            tiles='CartoDB positron'
        )
        
        # Add markers for each day's activities
        colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige']
        
        for idx, day in enumerate(trip.get('daily_itineraries', [])):
            day_color = colors[idx % len(colors)]
            
            for activity in day.get('activities', []):
                if activity.get('location'):
                    # Mock coordinates (would come from API)
                    lat, lng = 20.5937 + (idx * 0.5), 78.9629 + (idx * 0.5)
                    
                    folium.Marker(
                        [lat, lng],
                        popup=f"<b>{activity['name']}</b><br>{activity['description']}<br>₹{activity['cost']}",
                        tooltip=f"Day {idx + 1}: {activity['name']}",
                        icon=folium.Icon(color=day_color, icon='info-sign')
                    ).add_to(m)
        
        # Display map
        st_folium(m, height=400, use_container_width=True)
    
    def render_daily_itinerary(self, trip: Dict[str, Any]):
        """Render day-by-day itinerary cards"""
        st.markdown("### 📅 Day-by-Day Itinerary")
        
        for day_data in trip.get('daily_itineraries', []):
            # Day header
            st.markdown(
                f"""
                <div style='background: linear-gradient(90deg, #FF6B6B 0%, #FFE66D 100%);
                            padding: 1rem; border-radius: 10px; margin: 1rem 0;'>
                    <h4 style='color: white; margin: 0;'>
                        Day {day_data['day_number']} - {day_data['date']}
                    </h4>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Activities timeline
            for idx, activity in enumerate(day_data.get('activities', [])):
                col1, col2 = st.columns([1, 4])
                
                with col1:
                    st.markdown(
                        f"""
                        <div style='text-align: center; padding: 1rem;'>
                            <h3 style='color: #FF6B6B; margin: 0;'>{activity.get('time', '09:00')}</h3>
                            <p style='color: #999; margin: 0;'>{activity['duration_hours']} hours</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                with col2:
                    st.markdown(
                        f"""
                        <div style='background: white; padding: 1.5rem; border-radius: 10px;
                                    box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 1rem;'>
                            <h4 style='color: #2c3e50; margin: 0;'>{activity['name']}</h4>
                            <p style='color: #7f8c8d; margin: 0.5rem 0;'>{activity['description']}</p>
                            <div style='display: flex; justify-content: space-between; align-items: center; margin-top: 1rem;'>
                                <span style='background: #4CAF50; color: white; padding: 0.3rem 0.8rem;
                                           border-radius: 15px; font-weight: bold;'>₹{activity['cost']}</span>
                                <span style='color: #95a5a6;'>📍 {activity.get('location', {}).get('area', 'Location')}</span>
                                <span style='color: #e74c3c;'>🏷️ {activity['category']}</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            
            # Meals and accommodation
            if day_data.get('meals'):
                with st.expander(f"🍽️ Meals for Day {day_data['day_number']}"):
                    for meal in day_data['meals']:
                        st.write(f"**{meal['type'].title()}:** {meal['restaurant']} - {meal['cuisine']}")
                        st.write(f"Must try: {', '.join(meal.get('must_try', []))}")
                        st.write(f"Estimated cost: ₹{meal['cost_estimate']}")
            
            if day_data.get('accommodation'):
                acc = day_data['accommodation']
                st.info(f"🏨 **Stay:** {acc['name']} ({acc['type']}) - ₹{acc['cost_per_night']}/night")
    
    def render_cost_breakdown(self, trip: Dict[str, Any]):
        """Render cost breakdown visualization"""
        st.markdown("### 💰 Cost Breakdown")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart
            breakdown = trip.get('cost_breakdown', {})
            if breakdown:
                fig = px.pie(
                    values=list(breakdown.values()),
                    names=list(breakdown.keys()),
                    title="Expense Distribution",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Summary cards
            st.markdown(
                f"""
                <div style='background: #f8f9fa; padding: 1.5rem; border-radius: 10px;'>
                    <h4>📊 Trip Summary</h4>
                    <div style='margin: 1rem 0;'>
                        <div style='display: flex; justify-content: space-between; margin: 0.5rem 0;'>
                            <span>Budget:</span>
                            <strong>₹{trip.get('total_budget', 0):,.0f}</strong>
                        </div>
                        <div style='display: flex; justify-content: space-between; margin: 0.5rem 0;'>
                            <span>Estimated Cost:</span>
                            <strong style='color: #4CAF50;'>₹{trip.get('actual_cost', 0):,.0f}</strong>
                        </div>
                        <hr>
                        <div style='display: flex; justify-content: space-between; margin: 0.5rem 0;'>
                            <span>Savings:</span>
                            <strong style='color: #2196F3;'>
                                ₹{max(0, trip.get('total_budget', 0) - trip.get('actual_cost', 0)):,.0f}
                            </strong>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Tips
            if trip.get('local_tips'):
                st.markdown("#### 💡 Local Tips")
                for tip in trip.get('local_tips', [])[:3]:
                    st.info(f"• {tip}")
    
    def render_booking(self):
        """Render booking section"""
        if st.session_state.get('current_trip'):
            trip = st.session_state.current_trip
            
            st.markdown(
                """
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            padding: 2rem; border-radius: 15px; margin-bottom: 2rem;'>
                    <h2 style='color: white; margin: 0;'>🎫 Complete Your Booking</h2>
                    <p style='color: rgba(255,255,255,0.9); margin-top: 0.5rem;'>
                        Book everything with just one click through our EMT integration!
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Booking summary
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(
                    """
                    <div style='background: white; padding: 1.5rem; border-radius: 10px;
                                box-shadow: 0 2px 10px rgba(0,0,0,0.1);'>
                        <h4>📋 Booking Summary</h4>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # List bookable items
                bookable_items = []
                for day in trip.get('daily_itineraries', []):
                    for activity in day.get('activities', []):
                        if activity.get('booking_required'):
                            bookable_items.append({
                                'name': activity['name'],
                                'type': 'activity',
                                'cost': activity['cost']
                            })
                    
                    if day.get('accommodation'):
                        bookable_items.append({
                            'name': day['accommodation']['name'],
                            'type': 'accommodation',
                            'cost': day['accommodation']['cost_per_night']
                        })
                
                for item in bookable_items:
                    st.checkbox(
                        f"{item['name']} - ₹{item['cost']}",
                        value=True,
                        key=f"book_{item['name']}"
                    )
                
                # Transport bookings
                st.markdown("#### 🚗 Transport Bookings")
                st.checkbox("✈️ Flights (Round trip)", value=True)
                st.checkbox("🚕 Local transport (Cabs/Autos)", value=True)
                st.checkbox("🚂 Train tickets", value=False)
            
            with col2:
                st.markdown(
                    """
                    <div style='background: white; padding: 1.5rem; border-radius: 10px;
                                box-shadow: 0 2px 10px rgba(0,0,0,0.1);'>
                        <h4>💳 Payment Details</h4>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Payment method selection
                payment_method = st.radio(
                    "Select Payment Method",
                    ["💳 Credit/Debit Card", "📱 UPI", "🏦 Net Banking", "💰 Wallet"],
                    key="payment_method"
                )
                
                if "Card" in payment_method:
                    st.text_input("Card Number", placeholder="XXXX XXXX XXXX XXXX")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Expiry", placeholder="MM/YY")
                    with col2:
                        st.text_input("CVV", placeholder="XXX", type="password")
                elif "UPI" in payment_method:
                    st.text_input("UPI ID", placeholder="yourname@upi")
                elif "Net Banking" in payment_method:
                    st.selectbox("Select Bank", ["SBI", "HDFC", "ICICI", "Axis", "Kotak", "Others"])
                
                # Promo code
                promo_col1, promo_col2 = st.columns([3, 1])
                with promo_col1:
                    promo_code = st.text_input("Promo Code", placeholder="FIRSTTRIP20")
                with promo_col2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Apply", use_container_width=True):
                        st.success("✅ 20% discount applied!")
                
                # Final amount
                st.markdown(
                    f"""
                    <div style='background: #e8f5e9; padding: 1rem; border-radius: 10px;
                                margin-top: 1rem; border: 2px solid #4CAF50;'>
                        <div style='display: flex; justify-content: space-between;'>
                            <span>Subtotal:</span>
                            <span>₹{trip.get('actual_cost', 0):,.0f}</span>
                        </div>
                        <div style='display: flex; justify-content: space-between;'>
                            <span>GST (18%):</span>
                            <span>₹{trip.get('actual_cost', 0) * 0.18:,.0f}</span>
                        </div>
                        <div style='display: flex; justify-content: space-between;'>
                            <span>Discount:</span>
                            <span style='color: #f44336;'>-₹{trip.get('actual_cost', 0) * 0.2:,.0f}</span>
                        </div>
                        <hr>
                        <div style='display: flex; justify-content: space-between;'>
                            <strong>Total Amount:</strong>
                            <strong style='color: #4CAF50; font-size: 1.5rem;'>
                                ₹{(trip.get('actual_cost', 0) * 0.98):,.0f}
                            </strong>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Terms and conditions
                st.checkbox("I agree to the terms and conditions", key="terms_agreed")
                
                # Book button
                if st.button("🚀 Complete Booking", use_container_width=True, type="primary"):
                    if st.session_state.get('terms_agreed'):
                        with st.spinner("Processing your booking..."):
                            self.process_booking()
                    else:
                        st.error("Please agree to terms and conditions")
        else:
            st.info("📝 Please generate an itinerary first to proceed with booking")
    
    def generate_itinerary(self):
        """Generate itinerary via API"""
        try:
            # Collect form data (simplified for demo)
            trip_data = {
                "destination": "Goa",
                "start_date": str(date.today() + timedelta(days=7)),
                "end_date": str(date.today() + timedelta(days=10)),
                "budget": 50000,
                "travelers_count": 2,
                "themes": ["relaxation", "foodie"],
                "accommodation_preference": "hotel",
                "transport_preference": "flight"
            }
            
            # Mock API response
            st.session_state.current_trip = {
                "trip_id": "trip_123",
                "destination": "Goa",
                "duration_days": 4,
                "total_budget": 50000,
                "actual_cost": 45000,
                "daily_itineraries": [
                    {
                        "day_number": 1,
                        "date": str(date.today() + timedelta(days=7)),
                        "activities": [
                            {
                                "time": "09:00",
                                "name": "Calangute Beach",
                                "description": "Relax at North Goa's most popular beach",
                                "duration_hours": 3,
                                "cost": 500,
                                "location": {"area": "North Goa"},
                                "category": "beach",
                                "booking_required": False
                            },
                            {
                                "time": "14:00",
                                "name": "Baga Beach Water Sports",
                                "description": "Enjoy parasailing, jet skiing, and more",
                                "duration_hours": 2,
                                "cost": 3000,
                                "location": {"area": "North Goa"},
                                "category": "adventure",
                                "booking_required": True
                            }
                        ],
                        "meals": [
                            {
                                "type": "lunch",
                                "restaurant": "Britto's",
                                "cuisine": "Seafood",
                                "cost_estimate": 1500,
                                "must_try": ["Fish Curry", "Prawn Balchao"]
                            }
                        ],
                        "accommodation": {
                            "name": "Taj Vivanta",
                            "type": "hotel",
                            "cost_per_night": 5000
                        }
                    }
                ],
                "cost_breakdown": {
                    "Accommodation": 15000,
                    "Food": 10000,
                    "Activities": 10000,
                    "Transport": 8000,
                    "Others": 2000
                },
                "local_tips": [
                    "Best time to visit beaches is early morning",
                    "Try local Feni drink",
                    "Bargain at flea markets"
                ]
            }
            
            st.success("✨ Itinerary generated successfully!")
            st.balloons()
            
        except Exception as e:
            st.error(f"Error generating itinerary: {str(e)}")
    
    def process_booking(self):
        """Process booking via API"""
        try:
            # Mock booking process
            import time
            time.sleep(2)
            
            st.session_state.booking_id = "BOOK123456"
            st.success("✅ Booking confirmed! Booking ID: BOOK123456")
            st.balloons()
            
            # Show success message
            st.markdown(
                """
                <div style='background: #4CAF50; color: white; padding: 1.5rem;
                            border-radius: 10px; margin-top: 1rem;'>
                    <h3 style='margin: 0;'>🎉 Congratulations!</h3>
                    <p style='margin: 0.5rem 0;'>Your trip has been successfully booked!</p>
                    <p style='margin: 0;'>Check your email for confirmation and tickets.</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        except Exception as e:
            st.error(f"Error processing booking: {str(e)}")