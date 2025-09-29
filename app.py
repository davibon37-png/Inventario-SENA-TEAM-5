import streamlit as st
from utils.supabase_client import get_supabase_client
import pandas as pd
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Sistema de Inventario", layout="wide")
st.title("🏢 Sistema de Inventario")

# Inicializar cliente de Supabase
supabase = get_supabase_client()

# Función para insertar datos de ejemplo
def insertar_datos_ejemplo():
    """Inserta datos de ejemplo si la tabla está vacía"""
    try:
        resultado = supabase.table("inventario").select("id").limit(1).execute()
            
            for producto in datos_ejemplo:
                supabase.table("inventario").insert(producto).execute()
            
            st.success("✅ Datos de ejemplo insertados")
            return True
    except Exception as e:
        st.error(f"Error: {e}")
    return False

# Funciones CRUD
def obtener_productos():
    """Obtiene todos los productos"""
    try:
        return supabase.table("inventario").select("*").order("id").execute().data
    except Exception as e:
        st.error(f"Error al obtener productos: {e}")
        return []

def buscar_productos(termino):
    """Busca productos por nombre o categoría"""
    try:
        resultado = supabase.table("inventario").select("*").ilike("nombre", f"%{termino}%").execute()
        return resultado.data
    except:
        return []

def actualizar_producto(producto_id, datos):
    """Actualiza un producto existente"""
    try:
        datos['fecha_actualizacion'] = datetime.now().isoformat()
        supabase.table("inventario").update(datos).eq("id", producto_id).execute()
        return True
    except Exception as e:
        st.error(f"Error al actualizar: {e}")
        return False

def eliminar_producto(producto_id):
    """Elimina un producto"""
    try:
        supabase.table("inventario").delete().eq("id", producto_id).execute()
        return True
    except Exception as e:
        st.error(f"Error al eliminar: {e}")
        return False

# Interfaz principal
def main():
    # Insertar datos de ejemplo si es necesario
    if 'inicializado' not in st.session_state:
        if insertar_datos_ejemplo():
            st.session_state.inicializado = True
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Navegación")
        opcion = st.radio(
            "Selecciona una opción:",
            ["📊 Dashboard", "📦 Gestión de Productos", "📈 Reportes"]
        )
        
        st.markdown("---")
        st.info("💡 **Sistema de Inventario v2.0**")
    
    # Contenido principal según opción seleccionada
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
        st.metric("Productos con Stock Bajo", len(productos_bajos))
    
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
        st.subheader("Top Productos por Valor")
        top_productos = df.nlargest(5, 'precio')[['nombre', 'precio']]
        st.dataframe(top_productos, use_container_width=True)

def gestionar_productos():
    st.header("📦 Gestión de Productos")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Ver Todos", "Agregar Nuevo", "Editar Existente", "Buscar"])
    
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
        with st.form("agregar_producto"):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre del producto*")
                categoria = st.selectbox("Categoría*", ["Tecnología", "Mobiliario", "Insumos", "Otros"])
                precio = st.number_input("Precio unitario*", min_value=0.0, value=0.0)
            with col2:
                cantidad = st.number_input("Cantidad inicial*", min_value=0, value=0)
                proveedor = st.text_input("Proveedor")
                min_stock = st.number_input("Stock mínimo alerta", min_value=0, value=5)
            
            if st.form_submit_button("➕ Agregar Producto"):
                if nombre and categoria and precio >= 0:
                    nuevo_producto = {
                        "nombre": nombre,
                        "categoria": categoria,
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
                    st.warning("Completa los campos obligatorios (*)")
    
    with tab3:
        productos = obtener_productos()
        if productos:
            producto_seleccionado = st.selectbox(
                "Selecciona producto a editar:",
                options=[f"{p['id']} - {p['nombre']}" for p in productos],
                key="editar_select"
            )
            
            if producto_seleccionado:
                producto_id = int(producto_seleccionado.split(" - ")[0])
                producto = next((p for p in productos if p['id'] == producto_id), None)
                
                if producto:
                    # Formulario de edición (SOLO para editar)
                    with st.form(f"editar_producto_{producto_id}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            nombre = st.text_input("Nombre", value=producto['nombre'], key=f"nombre_{producto_id}")
                            categoria = st.text_input("Categoría", value=producto['categoria'], key=f"categoria_{producto_id}")
                            precio = st.number_input("Precio", value=float(producto['precio']), key=f"precio_{producto_id}")
                        with col2:
                            cantidad = st.number_input("Cantidad", value=producto['cantidad'], key=f"cantidad_{producto_id}")
                            proveedor = st.text_input("Proveedor", value=producto.get('proveedor', ''), key=f"proveedor_{producto_id}")
                            min_stock = st.number_input("Stock mínimo", value=producto.get('min_stock', 0), key=f"min_stock_{producto_id}")
                        
                        # Botón de guardar DENTRO del formulario
                        guardado = st.form_submit_button("💾 Guardar Cambios")
                        if guardado:
                            if actualizar_producto(producto_id, {
                                "nombre": nombre,
                                "categoria": categoria,
                                "precio": precio,
                                "cantidad": cantidad,
                                "proveedor": proveedor,
                                "min_stock": min_stock
                            }):
                                st.success("✅ Producto actualizado")
                                st.rerun()
                    
                    # Botón de eliminar FUERA del formulario
                    st.markdown("---")
                    st.warning("Zona de peligro")
                    col1, col2 = st.columns([3, 1])
                    with col2:
                        if st.button("🗑️ Eliminar Producto", type="secondary", key=f"eliminar_{producto_id}"):
                            # Confirmación antes de eliminar
                            with st.expander("⚠️ Confirmar eliminación", expanded=True):
                                st.error(f"¿Estás seguro de eliminar **{producto['nombre']}**?")
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("✅ Sí, eliminar", type="primary", key=f"confirmar_eliminar_{producto_id}"):
                                        if eliminar_producto(producto_id):
                                            st.success("✅ Producto eliminado")
                                            st.rerun()
                                with col2:
                                    if st.button("❌ Cancelar", key=f"cancelar_eliminar_{producto_id}"):
                                        st.info("Eliminación cancelada")
    
    with tab4:
        termino = st.text_input("🔍 Buscar producto por nombre o categoría:")
        if termino:
            resultados = buscar_productos(termino)
            if resultados:
                st.write(f"**Resultados encontrados:** {len(resultados)}")
                st.dataframe(pd.DataFrame(resultados), use_container_width=True)
            else:
                st.info("No se encontraron productos")

def mostrar_reportes():
    st.header("📈 Reportes e Analytics")
    
    productos = obtener_productos()
    if not productos:
        st.warning("No hay datos para mostrar")
        return
    
    df = pd.DataFrame(productos)
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        categorias_seleccionadas = st.multiselect(
            "Filtrar por categoría:",
            options=df['categoria'].unique(),
            default=df['categoria'].unique()
        )
    
    # Aplicar filtros
    df_filtrado = df[df['categoria'].isin(categorias_seleccionadas)]
    
    # Métricas
    st.subheader("Métricas Filtradas")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Valor Total", f"${(df_filtrado['cantidad'] * df_filtrado['precio']).sum():,.2f}")
    with col2:
        st.metric("Productos", len(df_filtrado))
    with col3:
        st.metric("Stock Promedio", int(df_filtrado['cantidad'].mean()))
    
    # Gráficos
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Distribución por Categoría")
        if not df_filtrado.empty:
            st.bar_chart(df_filtrado['categoria'].value_counts())
    
    with col2:
        st.subheader("Top 5 Productos por Valor")
        top_productos = df_filtrado.nlargest(5, 'precio')[['nombre', 'precio']]
        st.dataframe(top_productos, use_container_width=True)

if __name__ == "__main__":
    main()


