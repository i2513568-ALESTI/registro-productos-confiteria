import os
import pandas as pd
import streamlit as st
from datetime import datetime
from supabase import create_client

# ------------------------------------------
# Conexión a supabase
# ------------------------------------------

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

ALLOWED_CATEGORIES = [
    "Chocolates", "Caramelos", "Mashmelos", "Galletas", "Salados", "Gomas de mascar"
]

# ------------------------------------------
# Funciones CRUD
# ------------------------------------------

def sb_list() -> pd.DataFrame:
    res = supabase.table("products").select("*").order("ts", desc=True).execute()
    return pd.DataFrame(res.data or [])

def sb_insert(nombre: str, precio:float, categorias: list, en_venta: bool):
    payload = {
        "nombre": nombre,
        "precio": precio,
        "categorias": categorias,
        "en_venta": en_venta,
        "ts": datetime.utcnow().isoformat()
    }
    supabase.table("products").insert(payload).execute()

def sb_update(id_:int, nombre: str, precio: float, categorias: list, en_venta:bool ):
    payload = {
        "nombre": nombre,
        "precio": precio,
        "categorias": categorias,
        "en_venta": en_venta,
    }
    supabase.table("products").update(payload).eq("id", id_).execute()

def sb_delete(id_: int):
    supabase.table("products").delete().eq("id", id_).execute()

def validar(nombre: str, precio:float, categorias: list[str]) -> str | None:
    if not nombre or len(nombre.strip()) == 0 or len(nombre.strip()) > 20:
        return "El nombre es obligatorio y debe de tener <= 20 caracteres."
    try:
        p = float(precio)
    except Exception:
        return "Por favor verifique el campo precio."
    if not (0 < p < 999):
        return "El precio debe ser mayor a 0 y menor a 999"
    if not categorias:
        return "Debe elegir al menos una categoría"
    for c in categorias:
        if c not in ALLOWED_CATEGORIES:
            return f"Categoría inválida: {c}"
    return None

#------------------------------------- UI -----------------------------------

st.title("Confitería Dulcino - Registro de productos")

# ------- Crear Producto -------
st.header("Agregar Producto")
with st.form("form-add", clear_on_submit=True):
    nombre = st.text_input("Nombre de producto")
    precio = st.number_input("Precio (S/)", min_value=0.01, max_value=998.99, step=0.10)
    categorias = st.multiselect("Categorias", ALLOWED_CATEGORIES)
    en_venta = st.radio("¿En Venta?",["Sí","No"]) == "Sí"
    submitted = st.form_submit_button("Guardar")

if submitted:
    err = validar(nombre, precio, categorias)
    if err:
        if "precio" in err.lower():
            st.error("Por favor verifique el campo precio")
        else:
            st.error("Lo sentimos no pudo crear este producto")
        st.info(err)
    else:
        sb_insert(nombre.strip(), float(precio), categorias, en_venta)
        st.success("Felicidades su producto se agregó")
        st.rerun()
st.divider()