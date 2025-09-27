import os
from supabase import create_client
from dotenv import load_dotenv
import streamlit as st

# Cargar variables de entorno locales
try:
    load_dotenv()
except:
    pass

@st.cache_resource
def get_supabase_client():
    try:
        # Intentar desde Streamlit Secrets (producción)
        url = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL"))
        key = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY"))
        
        if not url or not key:
            st.error("""
            ❌ No se encontraron las credenciales de Supabase.
            
            **Solución:**
            - Local: Crea un archivo `.env` con SUPABASE_URL y SUPABASE_KEY
            - Producción: Agrega los Secrets en Streamlit Cloud
            """)
            st.stop()
        
        client = create_client(url, key)
        
        # Test de conexión
        client.table("inventario").select("id", count="exact").limit(1).execute()
        
        return client
        
    except Exception as e:
        st.error(f"❌ Error de conexión a Supabase: {e}")
        st.stop()
