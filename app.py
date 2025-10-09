import os
import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Inventario",
    page_icon="📦",
    layout="wide"
)

# Inicializar Supabase
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# Función segura para obtener productos
def obtener_productos():
    try:
        response = supabase.table("inventario").select("""
            id, nombre, cantidad, categoria, precio, activo, fecha_actualizacion,
            proveedores (id, nombre, telefono)
        """).execute()
        
        if hasattr(response, 'data'):
            return response.data
        else:
            st.error("Error en la estructura de la respuesta")
            return []
            
    except Exception as e:
        st.error(f"Error al obtener productos: {e}")
        # Fallback: obtener datos sin join
        try:
            response = supabase.table("inventario").select("*").execute()
            proveedores_response = supabase.table("proveedores").select("*").execute()
            
            productos = response.data if hasattr(response, 'data') else []
            proveedores = proveedores_response.data if hasattr(proveedores_response, 'data') else []
            
            # Unir manualmente
            for producto in productos:
                proveedor_id = producto.get('proveedor_id')
                proveedor = next((p for p in proveedores if p['id'] == proveedor_id), {})
                producto['proveedores'] = proveedor
                
            return productos
        except Exception as e2:
            st.error(f"Error en fallback: {e2}")
            return []

# Función para obtener proveedores
def obtener_proveedores():
    try:
        response = supabase.table("proveedores").select("*").eq("activo", True).execute()
        return response.data if hasattr(response, 'data') else []
    except Exception as e:
        st.error(f"Error al obtener proveedores: {e}")
        return []

# Función para agregar producto
def agregar_producto(nombre, cantidad, categoria, precio, proveedor_id):
    try:
        producto_data = {
            "nombre": nombre,
            "cantidad": cantidad,
            "categoria": categoria,
            "precio": float(precio),
            "proveedor_id": proveedor_id,
            "fecha_actualizacion": datetime.now().isoformat()
        }
        
        response = supabase.table("inventario").insert(producto_data).execute()
        
        if hasattr(response, 'data') and response.data:
            st.success("✅ Producto agregado exitosamente!")
            return True
        else:
            st.error("❌ Error al agregar producto")
            return False
            
    except Exception as e:
        st.error(f"❌ Error: {e}")
        return False

# Función para actualizar producto
def actualizar_producto(producto_id, cantidad, precio):
    try:
        update_data = {
            "cantidad": cantidad,
            "precio": float(precio),
            "fecha_actualizacion": datetime.now().isoformat()
        }
        
        response = supabase.table("inventario").update(update_data).eq("id", producto_id).execute()
        
        if hasattr(response, 'data') and response.data:
            st.success("✅ Producto actualizado exitosamente!")
            return True
        else:
            st.error("❌ Error al actualizar producto")
            return False
            
    except Exception as e:
        st.error(f"❌ Error: {e}")
        return False

# INTERFAZ PRINCIPAL
st.title("📦 Sistema de Gestión de Inventario")

# Sidebar para navegación
menu = st.sidebar.selectbox("Menú", [
    "Dashboard de Inventario", 
    "Agregar Producto", 
    "Gestionar Proveedores"
])

if menu == "Dashboard de Inventario":
    st.header("📊 Dashboard de Inventario")
    
    # Obtener y mostrar productos
    productos = obtener_productos()
    
    if productos:
        # Convertir a DataFrame para mejor visualización
        df_data = []
        for producto in productos:
            proveedor_nombre = producto.get('proveedores', {}).get('nombre', 'N/A') if producto.get('proveedores') else 'N/A'
            df_data.append({
                'ID': producto['id'],
                'Nombre': producto['nombre'],
                'Cantidad': producto['cantidad'],
                'Categoría': producto['categoria'],
                'Precio': f"${producto['precio']:,.0f}",
                'Proveedor': proveedor_nombre,
                'Última Actualización': producto['fecha_actualizacion'][:10] if producto['fecha_actualizacion'] else 'N/A'
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True)
        
        # Métricas rápidas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Productos", len(productos))
        with col2:
            st.metric("Productos en Stock", sum(1 for p in productos if p['cantidad'] > 0))
        with col3:
            st.metric("Stock Bajo", sum(1 for p in productos if p['cantidad'] < 10))
        with col4:
            valor_total = sum(p['precio'] * p['cantidad'] for p in productos)
            st.metric("Valor Total Inventario", f"${valor_total:,.0f}")
            
        # Sección para actualizar productos
        st.subheader("🔄 Actualizar Producto")
        with st.form("actualizar_producto"):
            productos_lista = {f"{p['id']} - {p['nombre']}": p['id'] for p in productos}
            producto_seleccionado = st.selectbox("Seleccionar Producto", options=list(productos_lista.keys()))
            nueva_cantidad = st.number_input("Nueva Cantidad", min_value=0, value=0)
            nuevo_precio = st.number_input("Nuevo Precio", min_value=0.0, value=0.0)
            
            if st.form_submit_button("Actualizar Producto"):
                producto_id = productos_lista[producto_seleccionado]
                if actualizar_producto(producto_id, nueva_cantidad, nuevo_precio):
                    st.rerun()
                    
    else:
        st.warning("No hay productos en el inventario")

elif menu == "Agregar Producto":
    st.header("➕ Agregar Nuevo Producto")
    
    with st.form("agregar_producto"):
        nombre = st.text_input("Nombre del Producto")
        cantidad = st.number_input("Cantidad", min_value=0, value=0)
        categoria = st.selectbox("Categoría", ["Tecnología", "Accesorios", "Mobiliario", "Oficina", "Otros"])
        precio = st.number_input("Precio", min_value=0.0, value=0.0)
        
        # Obtener proveedores para el select
        proveedores = obtener_proveedores()
        proveedores_opciones = {f"{p['id']} - {p['nombre']}": p['id'] for p in proveedores}
        
        if proveedores_opciones:
            proveedor_seleccionado = st.selectbox("Proveedor", options=list(proveedores_opciones.keys()))
            proveedor_id = proveedores_opciones[proveedor_seleccionado]
        else:
            st.warning("No hay proveedores disponibles. Primero agrega proveedores.")
            proveedor_id = None
        
        if st.form_submit_button("Agregar Producto"):
            if nombre and proveedor_id is not None:
                if agregar_producto(nombre, cantidad, categoria, precio, proveedor_id):
                    st.rerun()
            else:
                st.error("Por favor completa todos los campos requeridos")

elif menu == "Gestionar Proveedores":
    st.header("🏢 Gestionar Proveedores")
    
    proveedores = obtener_proveedores()
    
    if proveedores:
        df_proveedores = pd.DataFrame(proveedores)
        st.dataframe(df_proveedores[['id', 'nombre', 'contacto', 'telefono', 'email', 'activo']], use_container_width=True)
    else:
        st.info("No hay proveedores registrados")
    
    # Agregar nuevo proveedor
    st.subheader("Agregar Nuevo Proveedor")
    with st.form("agregar_proveedor"):
        col1, col2 = st.columns(2)
        with col1:
            nombre_prov = st.text_input("Nombre del Proveedor")
            contacto_prov = st.text_input("Persona de Contacto")
            telefono_prov = st.text_input("Teléfono")
        with col2:
            email_prov = st.text_input("Email")
            direccion_prov = st.text_area("Dirección")
        
        if st.form_submit_button("Agregar Proveedor"):
            if nombre_prov:
                try:
                    proveedor_data = {
                        "nombre": nombre_prov,
                        "contacto": contacto_prov,
                        "telefono": telefono_prov,
                        "email": email_prov,
                        "direccion": direccion_prov
                    }
                    response = supabase.table("proveedores").insert(proveedor_data).execute()
                    if hasattr(response, 'data') and response.data:
                        st.success("✅ Proveedor agregado exitosamente!")
                        st.rerun()
                    else:
                        st.error("❌ Error al agregar proveedor")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.error("El nombre del proveedor es requerido")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("Sistema de Inventario v1.0 - Desarrollado con Streamlit y Supabase")
