import os
import uuid
import pandas as pd
import streamlit as st
from datetime import datetime

DATA_DIR = "datos_sinteticos"
CSV_PATH = os.path.join(DATA_DIR, "products.csv")

ALLOWED_CATEGORIES = [
    "Chocolates", "Caramelos", "Mashmelos", "Galletas", "Salamos", "Gomas de mascar"
]

def ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def load_df() -> pd.DataFrame:
    if os.path.exists(CSV_PATH):
        return pd.read_csv(CSV_PATH, encoding="utf-8")
    return pd.DataFrame(columns=["id_product", "nombre", "precio", "categorias", "en_venta", "ts"])

def save_df(df: pd.DataFrame):
    ensure_dir()
    df.to_csv(CSV_PATH, index=False, encoding="utf-8")

def validate(nombre: str, precio, categorias: list, en_venta_label: str):
    # nombre
    if len(nombre.strip()) == 0 or len(nombre.strip()) > 20:
        raise ValueError("El nombre no puede estar vacío ni superar 20 caracteres.")
    # precio
    if precio is None:
        raise ValueError("Por favor verifique el campo del precio")
    try:
        p = float(precio)
    except Exception:
        raise ValueError("Por favor verifique el campo precio")
    if not (0 < p < 999):
        raise ValueError("El precio debe ser mayor a 0 y menor a 999.")
    # categorías
    if not categorias:
        raise ValueError("Debe elegir al menos una categoría.")
    for c in categorias:
        if c not in ALLOWED_CATEGORIES:
            raise ValueError(f"Categoría inválida: {c}")
    # en venta
    if en_venta_label not in ["Si", "No"]:
        raise ValueError("Valor inválido para ¿está en venta?")
    return (
        nombre.strip(),
        round(p, 2),
        sorted(list(set(categorias))),
        (en_venta_label == "Si"),
    )

#----------------------------------------------- UI ------------------------------------------------------

st.title("Confitería Duicino - Registro de productos")

with st.form("form-producto", clear_on_submit=True):
    col1, col2 = st.columns([2,1])
    with col1:
        nombre = st.text_input("Nombre del Producto")
    with col2:
        precio = st.number_input("Precio (S/)", min_value=0.0, max_value=998.99, step=0.10, format="%.2f")
    categorias = st.multiselect("Categorías", ALLOWED_CATEGORIES)
    en_venta_label = st.radio("¿El producto está en venta?", options=["Si","No"], horizontal=True)

    submitted = st.form_submit_button("Guardar")

    if submitted:
        try:
            nombre, precio, categorias, en_venta = validate(nombre, precio, categorias, en_venta_label)
            df = load_df()
            nuevo = pd.DataFrame([{
                "id_product": str(uuid.uuid4()),  # 🔑 UUID único
                "nombre": nombre,
                "precio": precio,
                "categorias": ";".join(categorias),
                "en_venta": en_venta,
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }])
            df = pd.concat([df, nuevo], ignore_index=True)
            save_df(df)
            st.success("✅ Producto guardado correctamente")
        except Exception as e:
            st.error(f"❌ {str(e)}")

# Mostrar tabla de productos
st.subheader("📋 Lista de productos registrados")
df = load_df()
st.dataframe(df)

# Botón para descargar el CSV
if not df.empty:
    st.download_button(
        label="📥 Descargar CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="products.csv",
        mime="text/csv",
    )
