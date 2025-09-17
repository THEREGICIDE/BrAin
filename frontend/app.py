import streamlit as st
import os
from dotenv import load_dotenv
from streamlit_option_menu import option_menu
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pages.trip_planner import TripPlannerPage
from pages.chat_assistant import ChatAssistantPage
from pages.booking_confirmation import BookingConfirmationPage

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title=os.getenv("APP_TITLE", "AI Trip Planner"),
    page_icon=os.getenv("PAGE_ICON", "🌍"),
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #FF6B6B;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem;
        font-weight: bold;
        transition: background-color 0.3s;
    }
    .stButton>button:hover {
        background-color: #FF5252;
    }
    .trip-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .activity-card {
        background-color: white;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #FF6B6B;
    }
    .price-tag {
        background-color: #4CAF50;
        color: white;
        padding: 5px 10px;
        border-radius: 15px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

class TripPlannerApp:
    def __init__(self):
        self.init_session_state()
    
    def init_session_state(self):
        """Initialize session state variables"""
        if 'current_trip' not in st.session_state:
            st.session_state.current_trip = None
        if 'booking_id' not in st.session_state:
            st.session_state.booking_id = None
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'user_preferences' not in st.session_state:
            st.session_state.user_preferences = {}
    
    def render_header(self):
        """Render app header"""
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            st.markdown(
                f"<h1 style='text-align: center;'>"
                f"{os.getenv('APP_ICON', '✈️')} {os.getenv('APP_TITLE', 'AI Trip Planner')}"
                f"</h1>",
                unsafe_allow_html=True
            )
            st.markdown(
                "<p style='text-align: center; color: gray;'>"
                "Your personalized AI-powered trip planning assistant with seamless booking"
                "</p>",
                unsafe_allow_html=True
            )
    
    def render_navigation(self):
        """Render navigation menu"""
        selected = option_menu(
            menu_title=None,
            options=["🗺️ Plan Trip", "💬 AI Assistant", "🎫 My Bookings", "ℹ️ About"],
            icons=None,
            menu_icon="cast",
            default_index=0,
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "orange", "font-size": "20px"},
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "center",
                    "margin": "0px",
                    "--hover-color": "#eee"
                },
                "nav-link-selected": {"background-color": "#FF6B6B"},
            }
        )
        return selected
    
    def render_sidebar(self):
        """Render sidebar with quick actions"""
        with st.sidebar:
            st.markdown("### 🚀 Quick Actions")
            
            if st.button("🆕 New Trip"):
                st.session_state.current_trip = None
                st.rerun()
            
            if st.button("📍 Nearby Suggestions"):
                self.show_nearby_suggestions()
            
            if st.button("🌤️ Weather Updates"):
                self.show_weather_updates()
            
            st.markdown("---")
            
            # Trip Summary if available
            if st.session_state.current_trip:
                st.markdown("### 📋 Current Trip")
                trip = st.session_state.current_trip
                st.info(f"**Destination:** {trip.get('destination', 'N/A')}")
                st.info(f"**Duration:** {trip.get('duration_days', 0)} days")
                st.info(f"**Budget:** ₹{trip.get('total_budget', 0):,.0f}")
                
                if st.button("📥 Download Itinerary"):
                    self.download_itinerary()
            
            st.markdown("---")
            st.markdown("### 📞 Support")
            st.markdown("🔹 **Email:** support@tripplanner.com")
            st.markdown("🔹 **Phone:** +91-1800-TRAVEL")
            st.markdown("🔹 **Chat:** Available 24/7")
    
    def show_nearby_suggestions(self):
        """Show nearby activity suggestions"""
        with st.spinner("Finding nearby attractions..."):
            # Mock implementation - would call API
            st.success("Found 5 attractions nearby!")
    
    def show_weather_updates(self):
        """Show weather updates"""
        if st.session_state.current_trip:
            st.info("☀️ Weather forecast: Sunny, 25-30°C")
        else:
            st.warning("Plan a trip to see weather updates")
    
    def download_itinerary(self):
        """Download itinerary as PDF"""
        st.success("📄 Itinerary downloaded successfully!")
    
    def render_footer(self):
        """Render footer"""
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 🌟 Features")
            st.markdown("• AI-Powered Planning")
            st.markdown("• Real-time Updates")
            st.markdown("• Seamless Booking")
            st.markdown("• Multi-language Support")
        
        with col2:
            st.markdown("### 🤝 Partners")
            st.markdown("• EMT Booking System")
            st.markdown("• Google Maps")
            st.markdown("• Stripe Payments")
            st.markdown("• 500+ Hotels")
        
        with col3:
            st.markdown("### 📱 Connect")
            st.markdown("• [Facebook](https://facebook.com)")
            st.markdown("• [Twitter](https://twitter.com)")
            st.markdown("• [Instagram](https://instagram.com)")
            st.markdown("• [LinkedIn](https://linkedin.com)")
        
        st.markdown(
            "<p style='text-align: center; color: gray; margin-top: 2rem;'>"
            "© 2024 AI Trip Planner. All rights reserved. | "
            "Powered by Google AI & EMT"
            "</p>",
            unsafe_allow_html=True
        )
    
    def run(self):
        """Run the application"""
        # Render header
        self.render_header()
        
        # Render navigation
        selected_page = self.render_navigation()
        
        # Render sidebar
        self.render_sidebar()
        
        # Main content area
        if selected_page == "🗺️ Plan Trip":
            trip_planner = TripPlannerPage()
            trip_planner.render()
        
        elif selected_page == "💬 AI Assistant":
            chat_assistant = ChatAssistantPage()
            chat_assistant.render()
        
        elif selected_page == "🎫 My Bookings":
            booking_page = BookingConfirmationPage()
            booking_page.render()
        
        elif selected_page == "ℹ️ About":
            self.render_about_page()
        
        # Render footer
        self.render_footer()
    
    def render_about_page(self):
        """Render about page"""
        st.markdown("## About AI Trip Planner")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 🎯 Our Mission
            To revolutionize travel planning by combining artificial intelligence 
            with seamless booking capabilities, making dream trips accessible to everyone.
            
            ### 💡 What We Offer
            - **Personalized Itineraries**: Tailored to your budget and interests
            - **Real-time Adaptation**: Dynamic updates based on weather and events
            - **One-click Booking**: Complete EMT integration for hassle-free bookings
            - **24/7 AI Assistant**: Your personal travel companion
            """)
        
        with col2:
            st.markdown("""
            ### 🏆 Why Choose Us
            - ✅ **AI-Powered**: Advanced algorithms for perfect trip planning
            - ✅ **Budget-Friendly**: Optimize costs without compromising experience
            - ✅ **Local Insights**: Hidden gems and authentic experiences
            - ✅ **Secure Payments**: Industry-standard security protocols
            
            ### 📊 Statistics
            - 🌍 **50,000+** Happy Travelers
            - 📍 **200+** Destinations
            - ⭐ **4.8/5** Average Rating
            - 🎫 **1M+** Bookings Processed
            """)

if __name__ == "__main__":
    app = TripPlannerApp()
    app.run()