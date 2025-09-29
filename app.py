import streamlit as st
from utils.supabase_client import get_supabase_client
import pandas as pd
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Sistema de Inventario", layout="wide")
st.title("🏢 Sistema de Inventario Completo")

# Inicializar cliente de Supabase
supabase = get_supabase_client()

# Función para obtener categorías actualizadas
def obtener_categorias_actualizadas():
    """Obtiene categorías directamente de la base de datos"""
    try:
        response = supabase.table("inventario").select("categoria").execute()
        if response.data:
            categorias = list(set([item['categoria'] for item in response.data]))
            return sorted([cat for cat in categorias if cat])
        return []
    except Exception as e:
        st.error(f"Error al obtener categorías: {e}")
        return []

# Función para obtener todos los productos
def obtener_productos():
    try:
        response = supabase.table("inventario").select("*").order("id").execute()
        return response.data
    except Exception as e:
        st.error(f"Error al obtener productos: {e}")
        return []

# Función para insertar datos de ejemplo
def insertar_datos_ejemplo():
    try:
        productos = obtener_productos()
        if not productos:
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

# Funciones CRUD
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
    # Inicializar datos si es necesario
    if 'inicializado' not in st.session_state:
        insertar_datos_ejemplo()
        st.session_state.inicializado = True
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Navegación")
        opcion = st.radio(
            "Selecciona una opción:",
            ["📊 Dashboard", "📦 Gestión de Productos", "📈 Reportes"]
        )
        
        # Mostrar categorías existentes en sidebar
        categorias_sidebar = obtener_categorias_actualizadas()
        
        if categorias_sidebar:
            st.markdown("---")
            st.subheader("🏷️ Categorías Existentes")
            for categoria in categorias_sidebar:
                st.write(f"• {categoria}")
    
    if opcion == "📊 Dashboard":
        mostrar_dashboard()
    elif opcion == "📦 Gestión de Productos":
        gestionar_productos()
    elif opcion == "📈 Reportes":
        mostrar_reportes()

def mostrar_dashboard():
    st.header("📊 Dashboard de Inventario")
    
    productos = obtener_productos()
    if not productos:
        st.warning("No hay productos en el inventario")
        return
    
    df = pd.DataFrame(productos)
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_valor = (df['cantidad'] * df['precio']).sum()
        st.metric("Valor Total Inventario", f"${total_valor:,.2f}")
    with col2:
        st.metric("Total Productos", len(df))
    with col3:
        st.metric("Stock Total", df['cantidad'].sum())
    with col4:
        productos_bajos = df[df['cantidad'] <= df['min_stock']]
        st.metric("Stock Bajo", len(productos_bajos))
    
    # Alertas de stock bajo
    if not productos_bajos.empty:
        st.warning("🚨 **Productos con Stock Bajo**")
        st.dataframe(productos_bajos[['nombre', 'cantidad', 'min_stock']], use_container_width=True)
    
    # Gráficos
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Stock por Categoría")
        stock_categoria = df.groupby('categoria')['cantidad'].sum()
        st.bar_chart(stock_categoria)
    
    with col2:
        st.subheader("Productos por Categoría")
        conteo_categorias = df['categoria'].value_counts()
        st.bar_chart(conteo_categorias)

def gestionar_productos():
    st.header("📦 Gestión de Productos")
    
    tab1, tab2, tab3 = st.tabs(["Ver Todos", "Agregar Nuevo", "Editar/Buscar"])
    
    with tab1:
        productos = obtener_productos()
        if productos:
            df = pd.DataFrame(productos)
            st.dataframe(df, use_container_width=True)
            
            # Exportar datos
            csv = df.to_csv(index=False)
            st.download_button("📥 Exportar CSV", csv, "inventario.csv", "text/csv")
        else:
            st.info("No hay productos registrados")
    
    with tab2:
        st.subheader("Agregar Nuevo Producto")
        
        # Obtener categorías actuales
        categorias_actuales = obtener_categorias_actualizadas()
        
        if not categorias_actuales:
            st.error("❌ No hay categorías disponibles. Primero agrega categorías desde la base de datos.")
            return
        
        with st.form("agregar_producto_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                nombre = st.text_input("Nombre del producto*", placeholder="Ej: Ventilador de Pie")
                
                # 🎯 DROPDOWN OBLIGATORIO CON CATEGORÍAS EXISTENTES
                categoria = st.selectbox(
                    "Categoría*",
                    options=categorias_actuales,
                    help="Selecciona una categoría existente"
                )
                
                precio = st.number_input("Precio unitario*", min_value=0.0, value=0.0, step=0.01)
            
            with col2:
                cantidad = st.number_input("Cantidad inicial*", min_value=0, value=0)
                proveedor = st.text_input("Proveedor", placeholder="Nombre del proveedor")
                min_stock = st.number_input("Stock mínimo alerta", min_value=0, value=5)
            
            # Información útil
            st.info(f"💡 **Categorías disponibles:** {', '.join(categorias_actuales)}")
            
            submitted = st.form_submit_button("➕ Agregar Producto")
            
            if submitted:
                # Validaciones
                if not nombre or not nombre.strip():
                    st.error("❌ El nombre del producto es obligatorio")
                elif precio < 0:
                    st.error("❌ El precio no puede ser negativo")
                else:
                    # Preparar datos
                    nuevo_producto = {
                        "nombre": nombre.strip(),
                        "categoria": categoria,
                        "precio": float(precio),
                        "cantidad": int(cantidad),
                        "proveedor": proveedor.strip(),
                        "min_stock": int(min_stock),
                        "fecha_actualizacion": datetime.now().isoformat()
                    }
                    
                    # Insertar en la base de datos
                    try:
                        result = supabase.table("inventario").insert(nuevo_producto).execute()
                        if result.data:
                            st.success(f"✅ Producto '{nombre}' agregado exitosamente!")
                            st.success(f"🏷️ Categoría: {categoria}")
                            st.rerun()
                        else:
                            st.error("❌ Error al agregar el producto")
                    except Exception as e:
                        st.error(f"❌ Error de base de datos: {e}")
    
    with tab3:
        st.subheader("Editar o Buscar Productos")
        productos = obtener_productos()
        
        if productos:
            # Buscar productos
            busqueda = st.text_input("🔍 Buscar producto por nombre:")
            productos_filtrados = productos
            
            if busqueda:
                productos_filtrados = [p for p in productos if busqueda.lower() in p['nombre'].lower()]
                st.write(f"📋 {len(productos_filtrados)} productos encontrados")
            
            if productos_filtrados:
                for producto in productos_filtrados:
                    with st.expander(f"📦 {producto['nombre']} (ID: {producto['id']})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Categoría:** {producto['categoria']}")
                            st.write(f"**Precio:** ${producto['precio']}")
                            st.write(f"**Proveedor:** {producto.get('proveedor', 'N/A')}")
                        with col2:
                            st.write(f"**Stock:** {producto['cantidad']} unidades")
                            st.write(f"**Stock mínimo:** {producto.get('min_stock', 'N/A')}")
                        
                        # Formulario de edición
                        with st.form(f"editar_{producto['id']}"):
                            st.subheader("✏️ Editar Producto")
                            
                            categorias_edicion = obtener_categorias_actualizadas()
                            
                            col_edit1, col_edit2 = st.columns(2)
                            with col_edit1:
                                nuevo_nombre = st.text_input("Nombre", value=producto['nombre'], key=f"nombre_edit_{producto['id']}")
                                nueva_categoria = st.selectbox(
                                    "Categoría",
                                    options=categorias_edicion,
                                    index=categorias_edicion.index(producto['categoria']) if producto['categoria'] in categorias_edicion else 0,
                                    key=f"categoria_edit_{producto['id']}"
                                )
                                nuevo_precio = st.number_input("Precio", value=float(producto['precio']), key=f"precio_edit_{producto['id']}")
                            
                            with col_edit2:
                                nueva_cantidad = st.number_input("Cantidad", value=producto['cantidad'], key=f"cantidad_edit_{producto['id']}")
                                nuevo_proveedor = st.text_input("Proveedor", value=producto.get('proveedor', ''), key=f"proveedor_edit_{producto['id']}")
                                nuevo_min_stock = st.number_input("Stock mínimo", value=producto.get('min_stock', 5), key=f"min_stock_edit_{producto['id']}")
                            
                            if st.form_submit_button("💾 Guardar Cambios"):
                                datos_actualizados = {
                                    "nombre": nuevo_nombre.strip(),
                                    "categoria": nueva_categoria,
                                    "precio": nuevo_precio,
                                    "cantidad": nueva_cantidad,
                                    "proveedor": nuevo_proveedor.strip(),
                                    "min_stock": nuevo_min_stock
                                }
                                if actualizar_producto(producto['id'], datos_actualizados):
                                    st.success("✅ Producto actualizado")
                                    st.rerun()
                        
                        # Botón de eliminar
                        if st.button(f"🗑️ Eliminar Producto", key=f"eliminar_{producto['id']}"):
                            if eliminar_producto(producto['id']):
                                st.success("✅ Producto eliminado")
                                st.rerun()
            else:
                st.info("No se encontraron productos")
        else:
            st.info("No hay productos para mostrar")

def mostrar_reportes():
    st.header("📈 Reportes e Analytics")
    
    productos = obtener_productos()
    if not productos:
        st.warning("No hay datos para mostrar")
        return
    
    df = pd.DataFrame(productos)
    
    st.subheader("Resumen por Categoría")
    resumen_categorias = df.groupby('categoria').agg({
        'id': 'count',
        'cantidad': 'sum',
        'precio': 'mean'
    }).round(2)
    
    resumen_categorias.columns = ['Número de Productos', 'Stock Total', 'Precio Promedio']
    st.dataframe(resumen_categorias, use_container_width=True)
    
    # Gráficos
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Distribución de Productos por Categoría")
        conteo_categorias = df['categoria'].value_counts()
        st.bar_chart(conteo_categorias)
    
    with col2:
        st.subheader("Valor de Inventario por Categoría")
        df['valor_total'] = df['cantidad'] * df['precio']
        valor_por_categoria = df.groupby('categoria')['valor_total'].sum()
        st.bar_chart(valor_por_categoria)

if __name__ == "__main__":
    main()
