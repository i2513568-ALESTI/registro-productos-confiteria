import streamlit as st
from datetime import datetime
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# ------------------- CONFIG -------------------
load_dotenv()

SUPABASE_URL = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error(
        "Faltan credenciales de Supabase. Agrega SUPABASE_URL y SUPABASE_KEY en .streamlit/secrets.toml, o configúralas como variables de entorno."
    )
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

ALLOWED_CATEGORIES = [
    "Chocolates", "Caramelos", "Mashmelos", "Galletas", "Salamos", "Gomas de mascar"
]

# ------------------- HELPERS -------------------
def validate(nombre: str, precio, categorias: list, en_venta_label: str):
    if len(nombre.strip()) == 0 or len(nombre.strip()) > 20:
        raise ValueError("El nombre no puede estar vacío ni superar 20 caracteres.")
    if precio is None:
        raise ValueError("Por favor verifique el campo del precio")
    try:
        p = float(precio)
    except Exception:
        raise ValueError("Por favor verifique el campo precio")
    if not (0 < p < 999):
        raise ValueError("El precio debe ser mayor a 0 y menor a 999.")
    if not categorias:
        raise ValueError("Debe elegir al menos una categoría.")
    for c in categorias:
        if c not in ALLOWED_CATEGORIES:
            raise ValueError(f"Categoría inválida: {c}")
    if en_venta_label not in ["Si", "No"]:
        raise ValueError("Valor inválido para ¿está en venta?")

    return (
        nombre.strip(),
        round(p, 2),
        sorted(list(set(categorias))),
        (en_venta_label == "Si"),
    )

# ------------------- UI -------------------
st.title("Confitería Duicino - Registro de productos (Supabase)")

# ---------- Formulario: Crear producto ----------
with st.form("form-producto", clear_on_submit=True):
    col1, col2 = st.columns([2, 1])
    with col1:
        nombre = st.text_input("Nombre del Producto")
    with col2:
        precio = st.number_input("Precio (S/)", min_value=0.0, max_value=998.99, step=0.10, format="%.2f")
    categorias = st.multiselect("Categorías", ALLOWED_CATEGORIES)
    en_venta_label = st.radio("¿El producto está en venta?", options=["Si", "No"], horizontal=True)

    submitted = st.form_submit_button("Guardar")

    if submitted:
        try:
            nombre, precio, categorias, en_venta = validate(nombre, precio, categorias, en_venta_label)
            supabase.table("products").insert({
                "nombre": nombre,
                "precio": precio,
                "categorias": ";".join(categorias),
                "en_venta": en_venta,
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }).execute()
            st.success("✅ Producto guardado correctamente")
            st.rerun()
        except Exception as e:
            st.error(f"❌ {str(e)}")

# ---------- Mostrar tabla ----------
st.subheader("📋 Lista de productos registrados")

data = supabase.table("products").select("*").execute()
rows = data.data if data.data else []

if rows:
    for row in rows:
        with st.expander(f"🟢 {row['nombre']} (S/{row['precio']})"):
            st.write(f"**ID:** {row['id_product']}")
            st.write(f"**Categorías:** {row['categorias']}")
            st.write(f"**En venta:** {'✅ Sí' if row['en_venta'] else '❌ No'}")
            st.write(f"**Fecha registro:** {row['ts']}")

            col1, col2 = st.columns(2)
            # Botón eliminar
            if col1.button("🗑️ Eliminar", key=f"delete-{row['id_product']}"):
                supabase.table("products").delete().eq("id_product", row["id_product"]).execute()
                st.rerun()

            # Botón editar
            if col2.button("✏️ Editar", key=f"edit-{row['id_product']}"):
                st.session_state["edit_id"] = row["id_product"]

    # ---------- Editar producto ----------
    if "edit_id" in st.session_state:
        edit_id = st.session_state["edit_id"]
        row = supabase.table("products").select("*").eq("id_product", edit_id).execute().data[0]

        st.subheader(f"✏️ Editar producto: {row['nombre']}")
        with st.form("form-editar", clear_on_submit=False):
            new_nombre = st.text_input("Nuevo nombre", value=row["nombre"])
            new_precio = st.number_input("Nuevo precio", value=float(row["precio"]), min_value=0.0, max_value=998.99, step=0.10)
            new_categorias = st.multiselect("Nuevas categorías", ALLOWED_CATEGORIES, default=row["categorias"].split(";"))
            new_en_venta = st.radio("¿En venta?", ["Si","No"], index=0 if row["en_venta"] else 1, horizontal=True)
            
            actualizar = st.form_submit_button("💾 Actualizar")
            if actualizar:
                try:
                    nombre, precio, categorias, en_venta = validate(new_nombre, new_precio, new_categorias, new_en_venta)
                    supabase.table("products").update({
                        "nombre": nombre,
                        "precio": precio,
                        "categorias": ";".join(categorias),
                        "en_venta": en_venta,
                        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }).eq("id_product", edit_id).execute()
                    st.success("✅ Producto actualizado correctamente")
                    del st.session_state["edit_id"]
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {str(e)}")

    # ---------- Botón para borrar todo ----------
    if st.button("⚠️ Borrar toda la tabla de productos"):
        supabase.table("products").delete().neq("id_product", 0).execute()
        st.warning("⚠️ Toda la data ha sido eliminada")
        st.rerun()

    # ---------- Botón para descargar ----------
    import pandas as pd
    df = pd.DataFrame(rows)
    st.download_button(
        label="📥 Descargar CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="products.csv",
        mime="text/csv",
    )
else:
    st.info("⚠️ No hay productos registrados todavía.")
