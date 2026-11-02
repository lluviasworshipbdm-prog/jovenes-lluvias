import streamlit as st
from supabase import create_client
import pandas as pd
import re
from datetime import date

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Jóvenes Lluvias | Centro de Operaciones",
    page_icon="🌧️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    .notion-callout {
        background-color: #1e293b;
        border-left: 4px solid #3b82f6;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    .song-card {
        background-color: #18181b;
        border: 1px solid #27272a;
        padding: 14px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .badge-tone { background-color: #3f3f46; color: #f4f4f5; }
    .badge-fast { background-color: #854d0e; color: #fef08a; }
    .badge-slow { background-color: #7f1d1d; color: #fecaca; }
    .badge-place { background-color: #1e3a8a; color: #bfdbfe; }
</style>
""", unsafe_allow_html=True)

# --- CONEXIÓN A SUPABASE ---
def init_db():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_db()

# --- CARGA DE DATOS DIRECTA ---
def cargar_datos():
    try:
        servicios = supabase.table("servicios_maestro").select("*").order("fecha", desc=False).execute().data or []
    except Exception:
        servicios = []
    try:
        repertorio = supabase.table("repertorio").select("*").order("titulo").execute().data or []
    except Exception:
        repertorio = []
    try:
        directorio = supabase.table("directorio_alabanza").select("*").order("nombre").execute().data or []
    except Exception:
        directorio = []
    try:
        fundamentos = supabase.table("fundamentos").select("*").order("id", desc=True).execute().data or []
    except Exception:
        fundamentos = []
    return servicios, repertorio, directorio, fundamentos

servicios, repertorio, directorio, fundamentos = cargar_datos()
rep_dict = {c["titulo"]: c for c in repertorio}
fun_dict = {f["id"]: f for f in fundamentos}
dir_nombres = [d["nombre"] for d in directorio]
canciones_nombres = [c["titulo"] for c in repertorio]

# --- TRANSPONEDOR DE ACORDES ---
NOTAS = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
EQUIV = {'Db': 'C#', 'D#': 'Eb', 'Gb': 'F#', 'G#': 'Ab', 'A#': 'Bb'}

def transponer_texto(texto, semitonos):
    if not texto or semitonos == 0:
        return texto
    def reemplazar_acorde(match):
        raiz = match.group(1)
        resto = match.group(2) or ""
        raiz_norm = EQUIV.get(raiz, raiz)
        if raiz_norm in NOTAS:
            nuevo_idx = (NOTAS.index(raiz_norm) + semitonos) % 12
            return NOTAS[nuevo_idx] + resto
        return match.group(0)
    patron = r'\b([A-G][b#]?)(m|maj7|m7|7|sus4|sus2|add9|dim|
