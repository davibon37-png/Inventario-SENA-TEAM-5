import streamlit as st
import pandas as pd
from supabase import create_client

# Configuración simple
st.set_page_config(page_title="Inventario Simple", layout="wide")
st.title("🛠️ INVENTARIO SIMPLE - CATEGORÍAS LIBRES")

# Conexión directa
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

# Función simple para obtener productos
def get_productos():
    try:
        return supabase.table("inventario").select("*").order("id").execute().data
    except:
        return []

# Función simple para agregar
def add_producto(nombre, categoria, precio, cantidad, proveedor, min_stock):
    try:
        data = {
            "nombre": nombre.strip(),
            "categoria": categoria.strip(), 
            "precio": precio,
            "cantidad": cantidad,
            "proveedor": proveedor.strip(),
            "min_stock": min_stock
        }
        return supabase.table("inventario").insert(data).execute()
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# INTERFAZ SUPER SIMPLE
st.header("➕ AGREGAR PRODUCTO")

with st.form("form_simple"):
    nombre = st.text_input("Nombre del producto*")
    categoria = st.text_input("Categoría*", placeholder="CUALQUIER categoría - ej: Electrodomésticos")
    precio = st.number_input("Precio*", min_value=0.0, value=0.0)
    cantidad = st.number_input("Cantidad*", min_value=0, value=0)
    proveedor = st.text_input("Proveedor")
    
    if st.form_submit_button("🎯 AGREGAR PRODUCTO"):
        if nombre and categoria:
            result = add_producto(nombre, categoria, precio, cantidad, proveedor, 5)
            if result and result.data:
                st.success(f"✅ AGREGADO: {nombre} en categoría {categoria}")
                st.rerun()
        else:
            st.error("❌ Nombre y categoría son obligatorios")

st.header("📦 PRODUCTOS EXISTENTES")
productos = get_productos()
if productos:
    df = pd.DataFrame(productos)
    st.dataframe(df)
else:
    st.info("No hay productos aún")
