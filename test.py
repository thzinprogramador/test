import streamlit as st
import firebase_admin
import requests
import datetime 
import random
import time
from firebase_admin import credentials, db
from io import BytesIO
from PIL import Image


# ==============================
# CONFIGURAÇÃO DA PÁGINA
# ==============================
st.set_page_config(
    page_title="Wave 2.0",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)
