import os
from supabase import create_client, Client
from dotenv import load_dotenv
import streamlit as st

# Cargar variables de entorno locales (para desarrollo)
try:
    load_dotenv()
except:
    pass

@st.cache_resource
def get_supabase_client() -> Client:
    """
    Obtiene el cliente de Supabase para conectarse a la base de datos.
    Funciona tanto en desarrollo local como en producción en Streamlit Cloud.
    """
    
    # Obtener credenciales de diferentes fuentes
    url = None
    key = None
    
    # 1. Intentar desde Streamlit Secrets (producción en Streamlit Cloud)
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
    except Exception as e:
        st.warning("No se pudieron cargar los Secrets de Streamlit")
    
    # 2. Intentar desde variables de entorno (desarrollo local con .env)
    if not url or not key:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
    
    # 3. Si aún no hay credenciales, mostrar error claro
    if not url or not key:
        st.error("""
        🔐 **Error de Configuración - Credenciales no encontradas**
        
        **Para solucionar:**
        
        **Opción A: Streamlit Cloud (Recomendado)**
        1. Ve a tu app en share.streamlit.io
        2. Click en Settings → Secrets
        3. Agrega:
        ```
        SUPABASE_URL = "https://tu-proyecto.supabase.co"
        SUPABASE_KEY = "tu-clave-publica"
        ```
        
        **Opción B: Desarrollo Local**
        1. Crea un archivo `.env` en la raíz con:
        ```
        SUPABASE_URL=https://tu-proyecto.supabase.co
        SUPABASE_KEY=tu-clave-publica
        ```
        """)
        st.stop()
    
    # Crear y verificar el cliente
    try:
        client = create_client(url, key)
        
        # Test de conexión simple
        test_response = client.table("inventario").select("id", count="exact").limit(1).execute()
        
        return client
        
    except Exception as e:
        st.error(f"""
        ❌ **Error de conexión a Supabase**
        
        **Detalles:** {e}
        
        **Verifica:**
        1. Que la URL y KEY sean correctas
        2. Que tu proyecto Supabase esté activo
        3. Que la tabla 'inventario' exista
        """)
        st.stop()
