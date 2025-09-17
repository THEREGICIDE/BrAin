import streamlit as st

def render(item: dict):
    st.markdown(f"**Day {item['day']} - {item['title']}**")
    st.write(item['description'])
