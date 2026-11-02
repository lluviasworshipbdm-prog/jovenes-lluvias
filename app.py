import streamlit as st
from supabase import create_client
import pandas as pd
import re
from datetime import date

# --- CONFIGURACIÓN DE PÁGINA (MODO OSCURO ESTILO NOTION) ---
st.set_page_config(
    page_title="Jóvenes Lluvias | Centro de Operaciones",
    page_icon="🌧️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos CSS personalizados para igualar la estética oscura de Notion y optimizar en móvil
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
@st.cache_resource
def init_db():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_db()

# --- FUNCIONES DE CARGA DE DATOS ---
def cargar_datos():
    servicios = supabase.table("servicios_maestro").select("*").order("fecha", desc=False).execute().data
    repertorio = supabase.table("repertorio").select("*").order("titulo").execute().data
    directorio = supabase.table("directorio_alabanza").select("*").order("nombre").execute().data
    fundamentos = supabase.table("fundamentos").select("*").order("id", desc=True).execute().data
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
    patron = r'\b([A-G][b#]?)(m|maj7|m7|7|sus4|sus2|add9|dim|aug)?(?=\s|$|/|\n)'
    return re.sub(patron, reemplazar_acorde, texto)

# --- SISTEMA DE LOGIN RÁPIDO (BARRA SUPERIOR / LATERAL) ---
if "usuario_activo" not in st.session_state:
    st.session_state.usuario_activo = None
    st.session_state.nivel_acceso = "Lectura"

with st.sidebar:
    st.subheader("🔐 Acceso de Equipo")
    if st.session_state.usuario_activo is None:
        user_sel = st.selectbox("Tu nombre", [""] + [d["nombre"] for d in directorio])
        pin_in = st.text_input("PIN de acceso", type="password", placeholder="Ej: 1234")
        if st.button("Desbloquear Edición", use_container_width=True):
            u_match = next((d for d in directorio if d["nombre"] == user_sel and str(d.get("pin_acceso")) == pin_in), None)
            if u_match:
                st.session_state.usuario_activo = u_match["nombre"]
                st.session_state.nivel_acceso = u_match["nivel_acceso"]
                st.rerun()
            else:
                st.error("PIN incorrecto")
    else:
        st.success(f"Conectado: **{st.session_state.usuario_activo}** ({st.session_state.nivel_acceso})")
        if st.button("Cerrar sesión", use_container_width=True):
            st.session_state.usuario_activo = None
            st.session_state.nivel_acceso = "Lectura"
            st.rerun()

# --- CABECERA PRINCIPAL ---
st.title("🌧️ Jóvenes Lluvias")
if st.session_state.usuario_activo:
    st.caption(f"Modo Edición Activo ({st.session_state.usuario_activo}) • Actualiza cualquier dato desde tu teléfono")
else:
    st.caption("Espacio de organización de Jóvenes Lluvias • Abre el menú lateral (>) si eres líder para editar")

# --- PESTAÑAS DE NAVEGACIÓN ---
tabs = st.tabs([
    "🏠 Jóvenes Lluvias (Vista General)",
    "⚡ Editar / Programar Servicio",
    "🎵 Repertorio y Cifrados",
    "📖 Fundamentos de la Fe",
    "⚙️ Centro de Operaciones"
])

# =========================================================================
# PESTAÑA 1: VISTA PÚBLICA (JÓVENES LLUVIAS)
# =========================================================================
with tabs[0]:
    st.markdown("""
    <div class="notion-callout">
        <strong>Información General:</strong><br>
        Bienvenidos al espacio de organización de Jóvenes Lluvias. Aquí encontrarán el resumen de cada servicio con los elementos clave para su ejecución. Recuerden que somos un mismo cuerpo, trabajando juntos para alcanzar, cuidar y desarrollar a nuestros jóvenes para el Señor Jesucristo.
    </div>
    """, unsafe_allow_html=True)

    st.subheader("📅 Servicio de la Semana")
    st.markdown("""
    * El enfoque debe ser realizar **transiciones limpias** entre cambios de elementos del programa.
    * La paleta de colores siempre permitirá utilizar **colores neutros** (negro, blanco o gris) siempre considerándolos como no principales.
    """)

    if servicios:
        hoy_str = str(date.today())
        futuros = [s for s in servicios if s["fecha"] >= hoy_str]
        default_idx = servicios.index(futuros[0]) if futuros else len(servicios) - 1

        opciones_srv = [f"{s['fecha']} — {s['nombre_servicio']} ({s.get('lugar_servicio', '')})" for s in servicios]
        sel_idx = st.selectbox("Seleccionar fecha de servicio para visualizar:", range(len(servicios)), format_func=lambda x: opciones_srv[x], index=default_idx)
        srv_actual = servicios[sel_idx]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📍 Lugar / Banda", f"{srv_actual.get('lugar_servicio') or 'Jóvenes'}", srv_actual.get("banda_templo"))
        c2.metric("🎤 Director Alabanza", srv_actual.get("director_alabanza") or "Por definir", srv_actual.get("estado"))
        c3.metric("🎧 Stage Manager", srv_actual.get("stage_manager") or "Por asignar", srv_actual.get("info_adicional"))
        banda_lista = srv_actual.get("banda_asignada") or []
        c4.metric("🎸 Músicos Asignados", f"{len(banda_lista)} integrantes")

        if banda_lista:
            st.info(f"**Banda Asignada:** {', '.join(banda_lista)}")

        # --- SECCIÓN FUNDAMENTOS VINCULADO ---
        st.markdown("### 📖 Fundamentos (Mensaje del Domingo)")
        fun_id = srv_actual.get("fundamento_id")
        if fun_id and fun_id in fun_dict:
            f_obj = fun_dict[fun_id]
            with st.expander(f"📘 **{f_obj['tema']}** — Predicador: {f_obj.get('predicador') or 'Por confirmar'} (Toca para leer resumen)", expanded=True):
                st.write(f"**Fecha:** {f_obj.get('fecha') or srv_actual['fecha']} | **Estado:** `{f_obj.get('estado')}`")
                st.markdown(f"**Contenido / Resumen:**\n{f_obj.get('contenido') or '_Sin resumen cargado todavía._'}")
                if f_obj.get("recomendacion"):
                    st.warning(f"💡 **Recomendación para equipos:** {f_obj['recomendacion']}")
        else:
            st.caption("No hay un tema de Fundamentos vinculado a esta fecha todavía.")

        # --- SETLIST DE DOMINGO ---
        st.markdown("### 🎶 Lista de la Semana (Setlist & Cifrados)")
        setlist_actual = srv_actual.get("setlist_canciones") or []
        if setlist_actual:
            for idx_c, nombre_c in enumerate(setlist_actual, 1):
                datos_c = rep_dict.get(nombre_c, {})
                nota = datos_c.get("nota") or "-"
                tipo = datos_c.get("tipo") or "-"
                bpm = f"{datos_c.get('tiempo')} BPM" if datos_c.get("tiempo") else ""
                artista = datos_c.get("artista") or ""
                badge_class = "badge-fast" if tipo == "Rápida" else "badge-slow"

                st.markdown(f"""
                <div class="song-card">
                    <strong>{idx_c}. {nombre_c}</strong> <span style="color:#a1a1aa;">— {artista}</span><br>
                    <span class="badge badge-tone">Tono: {nota}</span>
                    <span class="badge {badge_class}">{tipo}</span>
                    <span style="color:#a1a1aa; font-size:0.85rem;">{bpm}</span>
                </div>
                """, unsafe_allow_html=True)

                b_col1, b_col2, b_col3 = st.columns([1, 1, 2])
                if datos_c.get("link_spotify"):
                    b_col1.link_button("🟢 Escuchar en Spotify", datos_c["link_spotify"], use_container_width=True)
                if datos_c.get("link_drive_cifrado"):
                    b_col2.link_button("📄 Abrir Cifrado (Drive)", datos_c["link_drive_cifrado"], use_container_width=True)
                if datos_c.get("cifrado_texto"):
                    with st.expander(f"🎸 Ver Cifrado Interactivo y Transponer ({nombre_c})"):
                        semitonos = st.slider(f"Cambiar tono ({nombre_c})", -6, 6, 0, key=f"trans_{srv_actual['id']}_{idx_c}")
                        st.code(transponer_texto(datos_c["cifrado_texto"], semitonos), language="text")
        else:
            st.caption("No se han seleccionado canciones para este domingo todavía.")

    st.divider()

    col_crono, col_spot = st.columns([1, 1])
    with col_crono:
        st.subheader("⏰ Cronograma Completo")
        st.markdown("""
        * **7:00 am:** Llegada Stage Manager y Sonido
        * **7:00 - 7:30:** Instalación equipo de Sonido
        * **7:30 am:** Llegada Equipo de Alabanza
        * **7:30 - 7:50:** Prueba de Sonido (Individual y Grupal)
        * **7:50 - 8:40:** Ensayo Alabanza
        * **8:00 am:** Llegada Multimedia
        * **8:00 - 8:40:** Instalación multimedia, revisión de recursos y letras
        * **8:40 - 8:50:** Prueba de Multimedia
        * **8:50 - 9:00:** Revisión últimos detalles
        * **9:00 - 9:40:** 🥐 Desayuno
        * **9:40 - 9:45:** 🙏 Oración grupal
        * **9:50 - 10:00:** 🎬 Cuenta regresiva y recursos audiovisuales
        """)

    with col_spot:
        st.subheader("🎧 Playlists Oficiales")
        st.caption("Lista de la Semana / Domingos Jóvenes")
        st.components.v1.iframe("https://open.spotify.com/embed/playlist/0ex0eTYn0HHkJL7TacRyTL?utm_source=generator&theme=0", height=152)
        st.caption("Playlist de Repertorio (Lista Jóvenes 2025)")
        st.components.v1.iframe("https://open.spotify.com/embed/playlist/52GrGliMSAQC198ToXuMSw?utm_source=generator&theme=0", height=152)
        st.caption("Playlist de Sugerencias (Musiquita Jóvenes)")
        st.components.v1.iframe("https://open.spotify.com/embed/playlist/01tGlmmQVsexvK0q9jyvVv?utm_source=generator&theme=0", height=152)
