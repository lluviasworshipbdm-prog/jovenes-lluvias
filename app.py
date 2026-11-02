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
    patron = r'\b([A-G][b#]?)(m|maj7|m7|7|sus4|sus2|add9|dim|aug)?(?=\s|$|/|\n)'
    return re.sub(patron, reemplazar_acorde, texto)

# --- SISTEMA DE LOGIN ---
if "usuario_activo" not in st.session_state:
    st.session_state.usuario_activo = None
    st.session_state.nivel_acceso = "Lectura"

with st.sidebar:
    st.subheader("🔐 Acceso de Equipo")
    if st.session_state.usuario_activo is None:
        user_sel = st.selectbox("Tu nombre", [""] + dir_nombres)
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

# =========================================================================
# PESTAÑA 2: EDICIÓN RÁPIDA MÓVIL
# =========================================================================
with tabs[1]:
    st.subheader("⚡ Programar o Actualizar un Servicio")
    if st.session_state.nivel_acceso not in ["Admin", "Editor"]:
        st.warning("🔒 Inicia sesión con tu PIN en la barra lateral izquierda para poder editar o crear fechas.")
    else:
        modo_srv = st.radio("Acción:", ["✏️ Editar servicio existente", "➕ Crear nueva fecha de servicio"], horizontal=True)

        if modo_srv == "✏️ Editar servicio existente" and servicios:
            s_edit_idx = st.selectbox("Elige el servicio a modificar:", range(len(servicios)), format_func=lambda x: f"{servicios[x]['fecha']} — {servicios[x]['nombre_servicio']}")
            s_actual = servicios[s_edit_idx]
        else:
            s_actual = {}

        with st.form("form_servicio_movil"):
            col_a, col_b = st.columns(2)
            f_fecha = col_a.date_input("Fecha del Servicio", value=date.fromisoformat(s_actual["fecha"]) if s_actual.get("fecha") else date.today())
            f_nombre = col_b.text_input("Nombre del Servicio", value=s_actual.get("nombre_servicio") or "Servicio de Jóvenes Lluvias")

            col_c, col_d, col_e = st.columns(3)
            estados_opc = ["Sin empezar", "En progreso", "Listo"]
            f_estado = col_c.selectbox("Estado", estados_opc, index=estados_opc.index(s_actual["estado"]) if s_actual.get("estado") in estados_opc else 0)

            lugares_opc = ["Espacio de Jóvenes", "Templo", "CAMPA"]
            f_lugar = col_d.selectbox("Lugar de Servicio", lugares_opc, index=lugares_opc.index(s_actual["lugar_servicio"]) if s_actual.get("lugar_servicio") in lugares_opc else 0)

            bandas_opc = ["Banda 1", "Banda 2", "Jóvenes", "CAMPA"]
            f_banda_t = col_e.selectbox("Banda en Templo", bandas_opc, index=bandas_opc.index(s_actual["banda_templo"]) if s_actual.get("banda_templo") in bandas_opc else 0)

            col_f, col_g, col_h = st.columns(3)
            dir_opc = [""] + dir_nombres
            f_dir = col_f.selectbox("Director de Alabanza", dir_opc, index=dir_opc.index(s_actual["director_alabanza"]) if s_actual.get("director_alabanza") in dir_opc else 0)
            f_sm = col_g.text_input("Stage Manager", value=s_actual.get("stage_manager") or "")
            f_info = col_h.text_input("Info Adicional (Ej: Santa Cena, Aniversario)", value=s_actual.get("info_adicional") or "")

            f_banda_asig = st.multiselect("🎸 Banda Asignada (Músicos y Voces)", dir_nombres, default=[m for m in (s_actual.get("banda_asignada") or []) if m in dir_nombres])
            f_setlist = st.multiselect("🎵 Setlist del Domingo (En orden)", canciones_nombres, default=[c for c in (s_actual.get("setlist_canciones") or []) if c in canciones_nombres])

            fun_opciones = {0: "-- Ninguno --"} | {f["id"]: f"{f['tema']} ({f.get('fecha', '')})" for f in fundamentos}
            f_fun_id = st.selectbox("📖 Tema de Fundamentos vinculado", list(fun_opciones.keys()), format_func=lambda x: fun_opciones[x], index=list(fun_opciones.keys()).index(s_actual["fundamento_id"]) if s_actual.get("fundamento_id") in fun_opciones else 0)

            with st.expander("📊 Datos Post-Servicio"):
                f_hora_real = st.text_input("Hora de inicio real", value=s_actual.get("hora_inicio_real") or "")
                f_res_ensayo = st.text_area("Resultado del ensayo", value=s_actual.get("resultado_ensayo") or "")
                f_autoeval = st.text_area("Autoevaluación", value=s_actual.get("autoevaluacion") or "")

            guardar_srv = st.form_submit_button("💾 Guardar Cambios del Servicio", use_container_width=True)
            if guardar_srv:
                payload = {
                    "fecha": str(f_fecha),
                    "fecha_texto": str(f_fecha),
                    "nombre_servicio": f_nombre,
                    "estado": f_estado,
                    "lugar_servicio": f_lugar,
                    "banda_templo": f_banda_t,
                    "director_alabanza": f_dir if f_dir else None,
                    "stage_manager": f_sm if f_sm else None,
                    "info_adicional": f_info if f_info else None,
                    "banda_asignada": f_banda_asig,
                    "setlist_canciones": f_setlist,
                    "fundamento_id": f_fun_id if f_fun_id != 0 else None,
                    "hora_inicio_real": f_hora_real if f_hora_real else None,
                    "resultado_ensayo": f_res_ensayo if f_res_ensayo else None,
                    "autoevaluacion": f_autoeval if f_autoeval else None
                }
                if modo_srv == "✏️ Editar servicio existente":
                    supabase.table("servicios_maestro").update(payload).eq("id", s_actual["id"]).execute()
                    st.success("¡Servicio actualizado correctamente!")
                else:
                    supabase.table("servicios_maestro").insert(payload).execute()
                    st.success("¡Nueva fecha creada en el calendario!")
                st.rerun()

# =========================================================================
# PESTAÑA 3: REPERTORIO Y CIFRADOS
# =========================================================================
with tabs[2]:
    st.subheader("🎵 Repertorio General de Canciones")
    filtro_clas = st.radio("Filtrar por lista:", ["Todas", "Repertorio", "Extra"], horizontal=True)
    df_rep_vista = pd.DataFrame(repertorio)
    if filtro_clas != "Todas" and not df_rep_vista.empty:
        df_rep_vista = df_rep_vista[df_rep_vista["clasificacion"] == filtro_clas]

    if not df_rep_vista.empty:
        st.dataframe(
            df_rep_vista[["titulo", "artista", "nota", "tiempo", "tipo", "clasificacion", "link_spotify", "link_drive_cifrado"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.caption("No hay canciones para mostrar.")

    if st.session_state.nivel_acceso in ["Admin", "Editor"]:
        with st.expander("➕ Agregar o Editar Canción"):
            c_sel = st.selectbox("Seleccionar canción para editar:", ["➕ Nueva Canción"] + canciones_nombres)
            c_obj = rep_dict.get(c_sel, {}) if c_sel != "➕ Nueva Canción" else {}

            with st.form("form_cancion"):
                col1, col2, col3 = st.columns(3)
                c_titulo = col1.text_input("Título de la Canción", value=c_obj.get("titulo") or "")
                c_artista = col2.text_input("Artista", value=c_obj.get("artista") or "")
                c_nota = col3.text_input("Tono (Nota)", value=c_obj.get("nota") or "C")

                col4, col5, col6 = st.columns(3)
                c_tiempo = col4.number_input("Tiempo (BPM)", value=int(c_obj["tiempo"]) if c_obj.get("tiempo") else 128, step=1)
                tipos_c = ["Rápida", "Lenta", "Intermedia", "Chunga"]
                c_tipo = col5.selectbox("Tipo", tipos_c, index=tipos_c.index(c_obj["tipo"]) if c_obj.get("tipo") in tipos_c else 0)
                clas_c = ["Repertorio", "Extra"]
                c_clas = col6.selectbox("Clasificación", clas_c, index=clas_c.index(c_obj["clasificacion"]) if c_obj.get("clasificacion") in clas_c else 0)

                c_spot = st.text_input("🟢 Link de Spotify", value=c_obj.get("link_spotify") or "")
                c_drive = st.text_input("📄 Link del PDF en Google Drive", value=c_obj.get("link_drive_cifrado") or "")
                c_texto = st.text_area("🎸 Cifrado en Texto", value=c_obj.get("cifrado_texto") or "", height=200)

                if st.form_submit_button("💾 Guardar Canción", use_container_width=True):
                    datos_up = {
                        "titulo": c_titulo, "artista": c_artista, "nota": c_nota,
                        "tiempo": c_tiempo, "tipo": c_tipo, "clasificacion": c_clas,
                        "link_spotify": c_spot or None, "link_drive_cifrado": c_drive or None,
                        "cifrado_texto": c_texto or None
                    }
                    if c_sel == "➕ Nueva Canción":
                        supabase.table("repertorio").insert(datos_up).execute()
                    else:
                        supabase.table("repertorio").update(datos_up).eq("id", c_obj["id"]).execute()
                    st.success("¡Canción guardada!")
                    st.rerun()

# =========================================================================
# PESTAÑA 4: FUNDAMENTOS DE LA FE
# =========================================================================
with tabs[3]:
    st.subheader("📖 Fundamentos de la Fe — Mensajes Semanales")
    for f in fundamentos:
        with st.expander(f"📘 **{f['tema']}** — {f.get('fecha') or ''} ({f.get('estado')})"):
            st.write(f"**Predicador:** {f.get('predicador') or 'Por definir'}")
            st.write(f"**Contenido / Resumen:**\n{f.get('contenido') or 'Pendiente de redactar.'}")
            if f.get("recomendacion"):
                st.info(f"**Recomendación:** {f['recomendacion']}")

    if st.session_state.nivel_acceso in ["Admin", "Editor"]:
        st.divider()
        st.markdown("#### ✍️ Agregar o Editar Resumen de Fundamentos")
        f_lista_opc = ["➕ Nuevo Tema"] + [f"{f['id']} - {f['tema']}" for f in fundamentos]
        f_sel_str = st.selectbox("Elegir mensaje:", f_lista_opc)
        f_edit_obj = fun_dict[int(f_sel_str.split(" - ")[0])] if f_sel_str != "➕ Nuevo Tema" else {}

        with st.form("form_fundamentos"):
            col_f1, col_f2 = st.columns(2)
            in_tema = col_f1.text_input("Tema del Mensaje", value=f_edit_obj.get("tema") or "")
            in_pred = col_f2.text_input("Predicador", value=f_edit_obj.get("predicador") or "")
            col_f3, col_f4 = st.columns(2)
            in_fecha = col_f3.text_input("Fecha", value=f_edit_obj.get("fecha") or "")
            est_f_opc = ["Sin empezar", "En progreso", "Listo"]
            in_est = col_f4.selectbox("Estado", est_f_opc, index=est_f_opc.index(f_edit_obj["estado"]) if f_edit_obj.get("estado") in est_f_opc else 0)
            in_cont = st.text_area("Contenido / Resumen del Mensaje", value=f_edit_obj.get("contenido") or "", height=150)
            in_rec = st.text_area("Recomendación para los equipos", value=f_edit_obj.get("recomendacion") or "")

            if st.form_submit_button("💾 Guardar Fundamento", use_container_width=True):
                f_pay = {
                    "tema": in_tema, "predicador": in_pred, "fecha": in_fecha,
                    "estado": in_est, "contenido": in_cont, "recomendacion": in_rec
                }
                if f_sel_str == "➕ Nuevo Tema":
                    supabase.table("fundamentos").insert(f_pay).execute()
                else:
                    supabase.table("fundamentos").update(f_pay).eq("id", f_edit_obj["id"]).execute()
                st.success("¡Mensaje actualizado!")
                st.rerun()

# =========================================================================
# PESTAÑA 5: CENTRO DE OPERACIONES
# =========================================================================
with tabs[4]:
    st.subheader("⚙️ Centro de Operaciones — Tabla Maestra Unificada")
    df_srv_full = pd.DataFrame(servicios)
    if not df_srv_full.empty:
        st.dataframe(
            df_srv_full[["fecha", "nombre_servicio", "estado", "lugar_servicio", "banda_templo", "info_adicional", "director_alabanza", "stage_manager", "banda_asignada", "setlist_canciones"]],
            use_container_width=True,
            hide_index=True
        )

    st.divider()
    st.subheader("👥 Directorio de Servidores Alabanza y Control de Acceso")
    df_dir_full = pd.DataFrame(directorio)
    if not df_dir_full.empty:
        st.dataframe(
            df_dir_full[["nombre", "rol_principal", "instrumento_secundario", "banda_templo", "nivel_acceso"]],
            use_container_width=True,
            hide_index=True
        )

    if st.session_state.nivel_acceso == "Admin":
        with st.expander("🔑 Administrar Permisos y PINs"):
            m_sel = st.selectbox("Seleccionar integrante:", ["➕ Nuevo Integrante"] + dir_nombres)
            m_obj = next((d for d in directorio if d["nombre"] == m_sel), {}) if m_sel != "➕ Nuevo Integrante" else {}

            with st.form("form_directorio"):
                c_m1, c_m2, c_m3 = st.columns(3)
                m_nom = c_m1.text_input("Nombre", value=m_obj.get("nombre") or "")
                m_rol = c_m2.text_input("Rol Principal", value=m_obj.get("rol_principal") or "Voz")
                m_sec = c_m3.text_input("Instrumento Secundario", value=m_obj.get("instrumento_secundario") or "")

                c_m4, c_m5, c_m6 = st.columns(3)
                m_ban = c_m4.text_input("Banda de Templo", value=m_obj.get("banda_templo") or "Banda 2")
                niv_opc = ["Lectura", "Editor", "Admin"]
                m_niv = c_m5.selectbox("Nivel de Permiso", niv_opc, index=niv_opc.index(m_obj["nivel_acceso"]) if m_obj.get("nivel_acceso") in niv_opc else 0)
                m_pin = c_m6.text_input("PIN de Acceso (4 dígitos)", value=str(m_obj.get("pin_acceso") or ""))

                if st.form_submit_button("💾 Guardar Integrante", use_container_width=True):
                    m_pay = {
                        "nombre": m_nom, "rol_principal": m_rol, "instrumento_secundario": m_sec or None,
                        "banda_templo": m_ban or None, "nivel_acceso": m_niv, "pin_acceso": m_pin or None
                    }
                    if m_sel == "➕ Nuevo Integrante":
                        supabase.table("directorio_alabanza").insert(m_pay).execute()
                    else:
                        supabase.table("directorio_alabanza").update(m_pay).eq("id", m_obj["id"]).execute()
                    st.success("¡Permisos actualizados!")
                    st.rerun()
