import streamlit as st
from utils.supabase_client import get_supabase_client
import pandas as pd
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Sistema de Inventario", layout="wide")
st.title("🏢 Sistema de Inventario Completo")

# Inicializar cliente de Supabase
supabase = get_supabase_client()

# Función para obtener categorías únicas
with tab2:
    categorias_existentes = obtener_categorias()
    
    with st.form("agregar_producto"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre del producto*")
            
            # 🚨 CÓDIGO CORREGIDO - CATEGORÍAS
            st.markdown("**Categoría***")
            
            # Opción 1: Usar categoría existente
            usar_existente = st.checkbox("Usar categoría existente", value=True if categorias_existentes else False)
            
            if usar_existente and categorias_existentes:
                categoria = st.selectbox(
                    "Selecciona categoría:",
                    options=categorias_existentes,
                    key="select_categoria"
                )
            else:
                categoria = st.text_input(
                    "Escribe nueva categoría:*",
                    placeholder="Ej: Electrodomésticos, Ropa, Herramientas...",
                    key="input_categoria"
                )
            
            precio = st.number_input("Precio unitario*", min_value=0.0, value=0.0, step=0.01)
            
        with col2:
            cantidad = st.number_input("Cantidad inicial*", min_value=0, value=0)
            proveedor = st.text_input("Proveedor")
            min_stock = st.number_input("Stock mínimo alerta", min_value=0, value=5)
        
        # Información clara para el usuario
        st.info("💡 **Para nueva categoría:** Desmarca 'Usar categoría existente' y escribe cualquier categoría nueva")
        
        if st.form_submit_button("➕ Agregar Producto"):
            if nombre and categoria and categoria.strip() and precio >= 0:
                nuevo_producto = {
                    "nombre": nombre,
                    "categoria": categoria.strip(),
                    "precio": precio,
                    "cantidad": cantidad,
                    "proveedor": proveedor,
                    "min_stock": min_stock
                }
                try:
                    supabase.table("inventario").insert(nuevo_producto).execute()
                    st.success(f"✅ Producto '{nombre}' agregado en categoría '{categoria}'")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("❌ Completa todos los campos obligatorios (*)")

# Función para insertar datos de ejemplo (actualizada)
def insertar_datos_ejemplo():
    try:
        resultado = supabase.table("inventario").select("id").limit(1).execute()
        
        if not resultado.data:
            datos_ejemplo = [
                {"nombre": "Laptop HP Pavilion", "cantidad": 15, "categoria": "Tecnología", "proveedor": "HP Inc.", "precio": 899.99, "min_stock": 5},
                {"nombre": "Mouse Inalámbrico", "cantidad": 50, "categoria": "Tecnología", "proveedor": "Logitech", "precio": 29.99, "min_stock": 10},
                {"nombre": "Monitor 24 Pulgadas", "cantidad": 8, "categoria": "Tecnología", "proveedor": "Samsung", "precio": 199.99, "min_stock": 3},
                {"nombre": "Silla de Oficina", "cantidad": 12, "categoria": "Mobiliario", "proveedor": "ErgoChair", "precio": 299.99, "min_stock": 2},
                {"nombre": "Escritorio Ejecutivo", "cantidad": 5, "categoria": "Mobiliario", "proveedor": "OfficeMax", "precio": 499.99, "min_stock": 1},
                {"nombre": "Tóner Negro", "cantidad": 25, "categoria": "Insumos", "proveedor": "Canon", "precio": 89.99, "min_stock": 15},
            ]
            
            for producto in datos_ejemplo:
                supabase.table("inventario").insert(producto).execute()
            
            st.success("✅ Datos de ejemplo insertados")
            return True
    except Exception as e:
        st.error(f"Error: {e}")
    return False

# Funciones CRUD (mantener igual)
def obtener_productos():
    try:
        return supabase.table("inventario").select("*").order("id").execute().data
    except Exception as e:
        st.error(f"Error al obtener productos: {e}")
        return []

def actualizar_producto(producto_id, datos):
    try:
        datos['fecha_actualizacion'] = datetime.now().isoformat()
        supabase.table("inventario").update(datos).eq("id", producto_id).execute()
        return True
    except Exception as e:
        st.error(f"Error al actualizar: {e}")
        return False

def eliminar_producto(producto_id):
    try:
        supabase.table("inventario").delete().eq("id", producto_id).execute()
        return True
    except Exception as e:
        st.error(f"Error al eliminar: {e}")
        return False

# Interfaz principal
def main():
    if 'inicializado' not in st.session_state:
        if insertar_datos_ejemplo():
            st.session_state.inicializado = True
    
    with st.sidebar:
        st.header("🔧 Navegación")
        opcion = st.radio(
            "Selecciona una opción:",
            ["📊 Dashboard", "📦 Gestión de Productos", "🏷️ Categorías", "📈 Reportes"]
        )
        
        # Mostrar categorías existentes en el sidebar
        categorias = obtener_categorias()
        if categorias:
            st.markdown("---")
            st.subheader("🏷️ Categorías Existentes")
            for categoria in categorias:
                st.write(f"• {categoria}")
    
    if opcion == "📊 Dashboard":
        mostrar_dashboard()
    elif opcion == "📦 Gestión de Productos":
        gestionar_productos()
    elif opcion == "🏷️ Categorías":
        mostrar_categorias()
    elif opcion == "📈 Reportes":
        mostrar_reportes()

def mostrar_categorias():
    st.header("🏷️ Gestión de Categorías")
    
    categorias = obtener_categorias()
    productos = obtener_productos()
    
    if productos:
        # Crear DataFrame con estadísticas por categoría
        df = pd.DataFrame(productos)
        stats_categorias = df.groupby('categoria').agg({
            'id': 'count',
            'cantidad': 'sum',
            'precio': lambda x: (df[df['categoria'] == x.name]['cantidad'] * df[df['categoria'] == x.name]['precio']).sum()
        }).reset_index()
        
        stats_categorias.columns = ['Categoría', 'N° Productos', 'Stock Total', 'Valor Total']
        stats_categorias['Valor Total'] = stats_categorias['Valor Total'].round(2)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Estadísticas por Categoría")
            st.dataframe(stats_categorias, use_container_width=True)
        
        with col2:
            st.subheader("Resumen")
            st.metric("Total Categorías", len(categorias))
            st.metric("Total Productos", len(productos))
            
            st.subheader("Nueva Categoría")
            st.info("💡 Las categorías se crean automáticamente al agregar productos. Solo escribe el nombre de la nueva categoría al agregar un producto.")
    else:
        st.info("No hay categorías aún. Agrega el primer producto para comenzar.")

def gestionar_productos():
    st.header("📦 Gestión de Productos")
    
    tab1, tab2, tab3 = st.tabs(["Ver Todos", "Agregar Nuevo", "Editar/Buscar"])
    
    with tab1:
        productos = obtener_productos()
        if productos:
            df = pd.DataFrame(productos)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay productos registrados")
    
    with tab2:
        categorias_existentes = obtener_categorias()
        
        with st.form("agregar_producto"):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre del producto*")
                
                # Input de categoría flexible
                if categorias_existentes:
                    categoria = st.selectbox(
                        "Categoría*", 
                        options=categorias_existentes + ["➕ CREAR NUEVA CATEGORÍA"],
                        help="Selecciona una existente o crea una nueva"
                    )
                    if categoria == "➕ CREAR NUEVA CATEGORÍA":
                        categoria = st.text_input("Nueva categoría*", placeholder="Nombre de la nueva categoría")
                else:
                    categoria = st.text_input("Categoría*", placeholder="Tecnología, Mobiliario, Insumos...")
                
                precio = st.number_input("Precio unitario*", min_value=0.0, value=0.0, step=0.01)
                
            with col2:
                cantidad = st.number_input("Cantidad inicial*", min_value=0, value=0)
                proveedor = st.text_input("Proveedor")
                min_stock = st.number_input("Stock mínimo alerta", min_value=0, value=5)
            
            if st.form_submit_button("➕ Agregar Producto"):
                if nombre and categoria and categoria.strip() and precio >= 0:
                    nuevo_producto = {
                        "nombre": nombre,
                        "categoria": categoria.strip(),
                        "precio": precio,
                        "cantidad": cantidad,
                        "proveedor": proveedor,
                        "min_stock": min_stock
                    }
                    try:
                        supabase.table("inventario").insert(nuevo_producto).execute()
                        st.success("✅ Producto agregado correctamente")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Completa los campos obligatorios (*) y asegúrate que la categoría no esté vacía")

    with tab3:
        # ... (mantener el código existente de edición/búsqueda)
        pass

# Las funciones mostrar_dashboard() y mostrar_reportes() se mantienen igual
def mostrar_dashboard():
    # ... (código existente)
    pass

def mostrar_reportes():
    # ... (código existente)
    pass

if __name__ == "__main__":
    main()

