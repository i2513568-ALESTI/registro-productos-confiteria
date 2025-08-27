import streamlit as st
from datetime import datetime
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# ------------------- CONFIG -------------------
load_dotenv()

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

categorias = ["Chocolates", "Caramelos", "Mashmelos", "Galletas", "Salamos", "Gomas de mascar"]

# ------------------- VALIDACIONES -------------------
def validar_producto(nombre, precio, categorias_seleccionadas, en_venta):
    errores = []
    
    # 1. Validar nombre del producto (no mayor a 20 caracteres)
    if len(nombre.strip()) == 0:
        errores.append("El nombre del producto no puede estar vacío")
    elif len(nombre.strip()) > 20:
        errores.append("El nombre del producto no debe ser mayor a 20 caracteres")
    
    # 2. Validar precio (mayor a 0 y menor a 999 soles)
    try:
        precio_float = float(precio)
        if precio_float <= 0:
            errores.append("El precio del producto debe ser mayor a 0")
        elif precio_float >= 999:
            errores.append("El precio del producto debe ser menor a 999 soles")
    except ValueError:
        errores.append("Por favor verifique el campo del precio")
    
    # 3. Validar categorías seleccionadas
    if not categorias_seleccionadas:
        errores.append("Debe seleccionar al menos una categoría")
    else:
        # 4. Verificar que todas las categorías estén en el array permitido
        for categoria in categorias_seleccionadas:
            if categoria not in categorias:
                errores.append(f"La categoría '{categoria}' no está permitida")
    
    # 5. Validar estado del producto en venta
    if en_venta not in ["Si", "No"]:
        errores.append("Debe seleccionar si el producto está en venta o no")
    
    return errores

# ------------------- UI -------------------
st.title("🍬 Confitería Duicino")
st.write("Registro de productos")

# Formulario para crear producto
st.subheader("Nuevo Producto")
with st.form("crear_producto"):
    nombre = st.text_input("Nombre del producto")
    precio = st.number_input("Precio (S/)", min_value=0.0, max_value=998.99, step=0.10)
    categorias_seleccionadas = st.multiselect("Categorías", categorias)
    en_venta = st.radio("¿El producto está en venta?", ["Si", "No"])
    
    if st.form_submit_button("Guardar"):
        try:
            # Validar todos los campos
            errores = validar_producto(nombre, precio, categorias_seleccionadas, en_venta)
            
            if errores:
                # Mostrar errores de validación
                st.error("Lo sentimos no pudo crear este producto.")
                for error in errores:
                    st.write(f"• {error}")
            else:
                # Si no hay errores, guardar el producto
                supabase.table("confiteria-duicino").insert({
                    "nombre": nombre.strip(),
                    "precio": float(precio),
                    "categorias": ";".join(categorias_seleccionadas),
                    "en_venta": en_venta == "Si",
                    "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }).execute()
                st.success("¡Felicidades su producto se agregó!")
                st.rerun()
                
        except Exception as e:
            # Manejo de excepciones generales
            st.error("Lo sentimos no pudo crear este producto.")
            st.write("Error interno del sistema. Por favor intente nuevamente.")

# Mostrar tabla
st.subheader("Productos Registrados")
data = supabase.table("confiteria-duicino").select("*").execute()

if data.data:
    # Crear tabla con los datos
    import pandas as pd
    from datetime import datetime
    
    # Preparar datos para la tabla
    tabla_datos = []
    for producto in data.data:
        # Formatear la fecha de manera más bonita
        try:
            fecha_obj = datetime.fromisoformat(producto['ts'].replace('Z', '+00:00'))
            fecha_formateada = fecha_obj.strftime("%d/%m/%Y %H:%M")
        except:
            fecha_formateada = producto['ts']
        
        tabla_datos.append({
            "Nombre": producto['nombre'],
            "Precio (S/)": f"S/{producto['precio']}",
            "Categorías": producto['categorias'],
            "En Venta": "Sí" if producto['en_venta'] else "No",
            "Fecha": fecha_formateada
        })
    
    # Crear DataFrame y mostrar como tabla
    df = pd.DataFrame(tabla_datos)
    st.table(df)
else:
    st.info("No hay productos registrados")
