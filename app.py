import streamlit as st
from utils.supabase_client import get_supabase_client
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Inventario", layout="wide")
st.title("Sistema de Inventario 📦")

# Inicializar cliente de Supabase
supabase = get_supabase_client()

# Función para insertar datos de ejemplo
def insertar_datos_ejemplo():
    try:
        # Verificar si ya hay datos
        resultado = supabase.table("inventario").select("id").limit(1).execute()
        
        if not resultado.data:
            st.info("📝 Insertando datos de ejemplo...")
            
            datos_ejemplo = [
                {
                    "nombre": "Laptop HP Pavilion",
                    "cantidad": 15,
                    "categoria": "Tecnología",
                    "proveedor": "HP Inc."
                },
                {
                    "nombre": "Mouse Inalámbrico",
                    "cantidad": 50,
                    "categoria": "Tecnología", 
                    "proveedor": "Logitech"
                },
                {
                    "nombre": "Monitor 24 Pulgadas",
                    "cantidad": 8,
                    "categoria": "Tecnología",
                    "proveedor": "Samsung"
                },
                {
                    "nombre": "Silla de Oficina",
                    "cantidad": 12,
                    "categoria": "Mobiliario",
                    "proveedor": "ErgoChair"
                },
                {
                    "nombre": "Escritorio Ejecutivo",
                    "cantidad": 5,
                    "categoria": "Mobiliario",
                    "proveedor": "OfficeMax"
                },
                {
                    "nombre": "Tóner Negro",
                    "cantidad": 25,
                    "categoria": "Insumos",
                    "proveedor": "Canon"
                }
            ]
            
            # Insertar todos los datos
            for producto in datos_ejemplo:
                supabase.table("inventario").insert(producto).execute()
            
            st.success("✅ Datos de ejemplo insertados correctamente")
            return True
        else:
            st.success("✅ Base de datos cargada")
            return True
            
    except Exception as e:
        st.error(f"❌ Error al insertar datos: {e}")
        return False

# Función para mostrar el inventario con mejor formato
def mostrar_inventario():
    try:
        data = supabase.table("inventario").select("*").order("id").execute()
        
        if data.data:
            # Convertir a DataFrame para mejor visualización
            df = pd.DataFrame(data.data)
            
            # Mostrar métricas rápidas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Productos", len(df))
            with col2:
                st.metric("Stock Total", df['cantidad'].sum())
            with col3:
                st.metric("Categorías", df['categoria'].nunique())
            with col4:
                st.metric("Proveedores", df['proveedor'].nunique())
            
            st.subheader("📋 Lista de Productos")
            
            # Agregar filtros
            col1, col2 = st.columns(2)
            with col1:
                categorias = ['Todas'] + list(df['categoria'].unique())
                categoria_filtro = st.selectbox("Filtrar por categoría:", categorias)
            
            with col2:
                proveedores = ['Todos'] + list(df['proveedor'].unique())
                proveedor_filtro = st.selectbox("Filtrar por proveedor:", proveedores)
            
            # Aplicar filtros
            if categoria_filtro != 'Todas':
                df = df[df['categoria'] == categoria_filtro]
            if proveedor_filtro != 'Todos':
                df = df[df['proveedor'] == proveedor_filtro]
            
            # Mostrar tabla
            st.dataframe(df, use_container_width=True)
            
            # Mostrar gráfico simple
            st.subheader("📊 Stock por Categoría")
            stock_categoria = df.groupby('categoria')['cantidad'].sum()
            st.bar_chart(stock_categoria)
            
        else:
            st.info("No hay productos en el inventario. Agrega el primero abajo.")
            
    except Exception as e:
        st.error(f"Error al cargar inventario: {e}")

# Función para agregar productos
def agregar_producto(nombre, cantidad, categoria, proveedor):
    try:
        if nombre and cantidad >= 0 and categoria and proveedor:
            supabase.table("inventario").insert({
                "nombre": nombre,
                "cantidad": cantidad,
                "categoria": categoria,
                "proveedor": proveedor
            }).execute()
            st.success("✅ Producto agregado correctamente!")
            st.rerun()  # Recargar la página para mostrar los nuevos datos
        else:
            st.warning("⚠️ Completa todos los campos correctamente")
    except Exception as e:
        st.error(f"❌ Error al agregar producto: {e}")

# --- INTERFAZ PRINCIPAL ---

# Insertar datos de ejemplo al iniciar
if 'datos_insertados' not in st.session_state:
    if insertar_datos_ejemplo():
        st.session_state.datos_insertados = True

# Sidebar para agregar productos
with st.sidebar:
    st.header("➕ Agregar Nuevo Producto")
    
    with st.form("agregar_producto"):
        nombre = st.text_input("Nombre del producto*")
        cantidad = st.number_input("Cantidad*", min_value=0, value=1)
        categoria = st.text_input("Categoría*", placeholder="Tecnología, Mobiliario...")
        proveedor = st.text_input("Proveedor*")
        
        if st.form_submit_button("Agregar al Inventario"):
            agregar_producto(nombre, cantidad, categoria, proveedor)

# Mostrar inventario principal
mostrar_inventario()

# Información adicional en el sidebar
with st.sidebar:
    st.markdown("---")
    st.subheader("ℹ️ Instrucciones")
    st.markdown("""
    - Usa los filtros para buscar productos
    - Agrega nuevos productos con el formulario
    - Los campos con * son obligatorios
    """)

