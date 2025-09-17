import streamlit as st

def render(route: dict):
    st.subheader("Map (mock)")
    st.json(route)
