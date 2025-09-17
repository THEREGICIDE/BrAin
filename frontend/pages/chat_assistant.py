import streamlit as st
from datetime import datetime
import random
import time
from typing import List, Dict
from streamlit_lottie import st_lottie
import json

from utils.api_client import APIClient

class ChatAssistantPage:
    def __init__(self):
        self.api_client = APIClient()
        self.quick_prompts = [
            "🏖️ Plan a beach vacation for 2",
            "🏔️ Adventure trip to Himachal",
            "🍛 Best food destinations in India",
            "💰 Budget trip under ₹30,000",
            "👨‍👩‍👧‍👦 Family trip with kids",
            "🎭 Cultural tour of Rajasthan",
            "🌴 Kerala backwaters experience",
            "🏛️ Historical sites in Delhi",
            "🎿 Winter sports in Kashmir",
            "🌺 Honeymoon destinations"
        ]
        
        self.bot_responses = [
            "I'd be happy to help you plan that!",
            "Great choice! Let me find the best options for you.",
            "That sounds exciting! Here's what I recommend...",
            "I have some wonderful suggestions for you!",
            "Let me create the perfect itinerary for that."
        ]
    
    def render(self):
        """Render chat assistant page"""
        # Header with gradient
        st.markdown(
            """
            <div style='background: linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%);
                        padding: 2rem; border-radius: 15px; margin-bottom: 2rem;'>
                <h2 style='color: white; margin: 0;'>💬 AI Travel Assistant</h2>
                <p style='color: rgba(255,255,255,0.9); margin-top: 0.5rem;'>
                    I'm here 24/7 to help you plan your perfect trip! Ask me anything about travel in India.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Create two columns layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self.render_chat_interface()
        
        with col2:
            self.render_suggestions_panel()
    
    def render_chat_interface(self):
        """Render main chat interface"""
        # Chat container with custom styling
        st.markdown(
            """
            <style>
            .chat-container {
                background: white;
                border-radius: 15px;
                padding: 1rem;
                height: 500px;
                overflow-y: auto;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .user-message {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 0.8rem 1.2rem;
                border-radius: 18px 18px 4px 18px;
                margin: 0.5rem 0;
                max-width: 70%;
                margin-left: auto;
                animation: slideInRight 0.3s ease-out;
            }
            .bot-message {
                background: #f0f2f6;
                color: #2c3e50;
                padding: 0.8rem 1.2rem;
                border-radius: 18px 18px 18px 4px;
                margin: 0.5rem 0;
                max-width: 70%;
                animation: slideInLeft 0.3s ease-out;
            }
            @keyframes slideInRight {
                from { opacity: 0; transform: translateX(20px); }
                to { opacity: 1; transform: translateX(0); }
            }
            @keyframes slideInLeft {
                from { opacity: 0; transform: translateX(-20px); }
                to { opacity: 1; transform: translateX(0); }
            }
            .typing-indicator {
                display: inline-block;
                animation: typing 1.4s infinite;
            }
            @keyframes typing {
                0%, 60%, 100% { opacity: 0.3; }
                30% { opacity: 1; }
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        # Initialize chat history
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = [
                {
                    "role": "assistant",
                    "content": "👋 Hello! I'm your AI travel assistant. How can I help you plan your perfect trip today?",
                    "timestamp": datetime.now()
                }
            ]
        
        # Display chat messages
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.markdown(
                        f"""
                        <div style='text-align: right; margin: 1rem 0;'>
                            <small style='color: #999;'>{message['timestamp'].strftime('%H:%M')}</small>
                            <div class='user-message'>
                                {message['content']}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"""
                        <div style='margin: 1rem 0;'>
                            <div style='display: flex; align-items: center; gap: 0.5rem;'>
                                <span style='font-size: 1.5rem;'>🤖</span>
                                <small style='color: #999;'>{message['timestamp'].strftime('%H:%M')}</small>
                            </div>
                            <div class='bot-message'>
                                {message['content']}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        
        # Quick action buttons
        st.markdown("### 🎯 Quick Actions")
        quick_cols = st.columns(5)
        quick_actions = ["🏨 Hotels", "✈️ Flights", "🍽️ Food", "🎫 Activities", "🚕 Transport"]
        
        for idx, action in enumerate(quick_actions):
            with quick_cols[idx]:
                if st.button(action, key=f"quick_{idx}", use_container_width=True):
                    self.handle_quick_action(action)
        
        # Chat input
        with st.form(key="chat_form", clear_on_submit=True):
            col1, col2 = st.columns([5, 1])
            
            with col1:
                user_input = st.text_input(
                    "Type your message...",
                    placeholder="Ask me anything about travel planning...",
                    label_visibility="collapsed"
                )
            
            with col2:
                send_button = st.form_submit_button("📤 Send", use_container_width=True)
            
            if send_button and user_input:
                self.process_user_message(user_input)
        
        # Voice input button (placeholder)
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("🎤 Voice Input", use_container_width=True):
                st.info("🎤 Voice input coming soon!")
    
    def render_suggestions_panel(self):
        """Render suggestions and help panel"""
        # Trending topics
        st.markdown(
            """
            <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                        padding: 1rem; border-radius: 10px; margin-bottom: 1rem;'>
                <h4 style='color: white; margin: 0;'>🔥 Trending Now</h4>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        trending_topics = [
            {"emoji": "🏖️", "text": "Goa beaches in December", "trend": "+15%"},
            {"emoji": "🎿", "text": "Kashmir skiing packages", "trend": "+23%"},
            {"emoji": "🐅", "text": "Jim Corbett safari", "trend": "+18%"},
            {"emoji": "🏛️", "text": "Golden Triangle tour", "trend": "+12%"},
            {"emoji": "🌊", "text": "Andaman water sports", "trend": "+20%"}
        ]
        
        for topic in trending_topics:
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(
                    f"{topic['emoji']} {topic['text']}",
                    key=f"trend_{topic['text']}",
                    use_container_width=True
                ):
                    self.process_user_message(topic['text'])
            with col2:
                st.markdown(
                    f"<span style='color: #4CAF50; font-weight: bold;'>{topic['trend']}</span>",
                    unsafe_allow_html=True
                )
        
        # Conversation starters
        st.markdown(
            """
            <div style='background: #f8f9fa; padding: 1rem; border-radius: 10px;
                        margin-top: 1.5rem; border-left: 4px solid #00d2ff;'>
                <h4 style='margin-top: 0;'>💡 Try asking me:</h4>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        for prompt in random.sample(self.quick_prompts, 5):
            if st.button(prompt, key=f"prompt_{prompt}", use_container_width=True):
                self.process_user_message(prompt.split(" ", 1)[1])
        
        # Help section
        st.markdown(
            """
            <div style='background: #e8f5e9; padding: 1rem; border-radius: 10px;
                        margin-top: 1.5rem;'>
                <h4 style='margin-top: 0; color: #2e7d32;'>🎯 I can help you with:</h4>
                <ul style='margin: 0; padding-left: 1.5rem;'>
                    <li>Creating personalized itineraries</li>
                    <li>Finding best deals on hotels & flights</li>
                    <li>Suggesting activities & attractions</li>
                    <li>Providing local tips & recommendations</li>
                    <li>Booking your complete trip</li>
                    <li>Real-time weather & traffic updates</li>
                    <li>Multi-language support</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Response quality feedback
        if len(st.session_state.chat_history) > 2:
            st.markdown("### 📊 Rate my response")
            col1, col2, col3, col4, col5 = st.columns(5)
            rating_emojis = ["😞", "😐", "🙂", "😊", "🤩"]
            
            for idx, (col, emoji) in enumerate(zip([col1, col2, col3, col4, col5], rating_emojis)):
                with col:
                    if st.button(emoji, key=f"rating_{idx}", use_container_width=True):
                        st.success("Thanks for your feedback!")
    
    def process_user_message(self, message: str):
        """Process user message and get AI response"""
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now()
        })
        
        # Show typing indicator
        with st.spinner("🤔 Thinking..."):
            time.sleep(1)  # Simulate processing
            
            # Get AI response (mock for demo)
            response = self.get_ai_response(message)
            
            # Add bot response to history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now()
            })
        
        # Rerun to update chat
        st.rerun()
    
    def get_ai_response(self, message: str) -> str:
        """Get AI response for user message"""
        # Mock AI responses based on keywords
        message_lower = message.lower()
        
        if "beach" in message_lower or "goa" in message_lower:
            return """
            🏖️ **Beach Destinations in India:**
            
            **Goa** - Perfect for December-February
            • North Goa: Vibrant nightlife, water sports
            • South Goa: Peaceful, luxury resorts
            • Budget: ₹25,000-50,000 for 3 days
            
            **Alternatives:**
            • Andaman Islands - Crystal clear waters
            • Kerala beaches - Varkala, Kovalam
            • Gokarna - Hidden gem in Karnataka
            
            Would you like me to create a detailed itinerary for any of these?
            """
        
        elif "budget" in message_lower:
            return """
            💰 **Budget Travel Tips:**
            
            **Under ₹30,000 (3-4 days):**
            • Rishikesh - Adventure & spirituality
            • Udaipur - Lakes & palaces
            • Hampi - Historical wonder
            • McLeodganj - Mini Tibet
            
            **Money-saving tips:**
            ✅ Book flights 6-8 weeks in advance
            ✅ Travel during weekdays
            ✅ Use public transport
            ✅ Stay in hostels or homestays
            ✅ Eat at local joints
            
            Shall I plan a budget trip for you?
            """
        
        elif "family" in message_lower:
            return """
            👨‍👩‍👧‍👦 **Family-Friendly Destinations:**
            
            **Top Picks:**
            1. **Kerala** - Houseboats, beaches, wildlife
            2. **Rajasthan** - Forts, culture, camel rides
            3. **Sikkim** - Mountains, monasteries, cable car
            4. **Ooty** - Toy train, gardens, chocolate factory
            
            **Family Package Inclusions:**
            • Child-friendly accommodations
            • Safe transportation
            • Age-appropriate activities
            • Flexible meal options
            
            How many family members? Any specific interests?
            """
        
        elif any(word in message_lower for word in ["hotel", "stay", "accommodation"]):
            return """
            🏨 **Accommodation Options:**
            
            Based on your preferences, I recommend:
            
            **Luxury (₹5000+/night):**
            • Taj, Oberoi, ITC Hotels
            • Premium amenities & services
            
            **Mid-range (₹2000-5000/night):**
            • Lemon Tree, Ginger Hotels
            • Good comfort & value
            
            **Budget (Under ₹2000/night):**
            • OYO, Zostel, FabHotels
            • Clean & comfortable basics
            
            What's your budget and preferred location?
            """
        
        else:
            # Generic helpful response
            return f"""
            {random.choice(self.bot_responses)}
            
            Based on your interest in "{message}", I can help you with:
            
            📍 **Destination Research** - Best places to visit
            📅 **Itinerary Planning** - Day-by-day schedule
            💰 **Budget Optimization** - Get the best value
            🏨 **Bookings** - Hotels, flights, activities
            🎯 **Local Insights** - Hidden gems & tips
            
            Would you like me to start planning something specific for you?
            """
    
    def handle_quick_action(self, action: str):
        """Handle quick action button clicks"""
        action_messages = {
            "🏨 Hotels": "Show me the best hotels for my trip",
            "✈️ Flights": "Find me the cheapest flights",
            "🍽️ Food": "What are the must-try local foods?",
            "🎫 Activities": "Suggest exciting activities and attractions",
            "🚕 Transport": "What are the best transport options?"
        }
        
        message = action_messages.get(action, "Help me with " + action)
        self.process_user_message(message)