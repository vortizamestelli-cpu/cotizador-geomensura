import streamlit as st
from fpdf import FPDF

# --- FUNCIÓN DE LIMPIEZA DE TEXTO PARA FPDF (Evita caracteres UTF-8 no soportados en latin-1) ---
def limpiar_texto(texto):
    if not isinstance(texto, str):
        return texto
    
    reemplazos = {
        "³": "3",
        "²": "2",
        "°": " deg",
        "–": "-",
        "—": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "…": "...",
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U",
        "ñ": "n", "Ñ": "N"
    }
    for orig, reemplazo in reemplazos.items():
        texto = texto.replace(orig, reemplazo)
    return texto


# --- CONFIGURACIÓN DE PÁGINA STREAMLIT ---
st.set_page_config(
    page_title="Cotizador Profesional EDOS SpA",
    page_icon="🚜",
    layout="wide"
)

st.title("🚜 EDOS SpA - Generador Integral de Presupuestos")
st.caption("Plataforma técnica-comercial para movimiento de tierras, geomensura y obras civiles.")

# --- SIDEBAR / ENTRADA DE DATOS ---
st.sidebar.header("Parámetros del Proyecto")

# 1. Datos del Mandante
st.sidebar.subheader("📄 Datos del Mandante")
cliente = st.sidebar.text_input("Cliente / Constructora", "Constructora Minimal")
ubicacion = st.sidebar.text_input("Ubicación de la Obra", "Avenida El Salto 2255, Recoleta")
representante = st.sidebar.text_input("Representante EDOS SpA", "Vicente Ortiz Amestelli")

# 2. Cubicaciones y Terreno
st.sidebar.subheader("1. Cubicaciones y Suelo")
criterio_volumen = st.sidebar.radio(
    "Criterio / Base de Medición de Volumen",
    ["Volumen Geométrico en Banco (Topografía)", "Volumen Esponjado (Sobre Camión)"]
)
volumen_util = st.sidebar.number_input("Volumen Geométrico en Banco (m³)", min_value=1.0, value=2914.0, step=10.0)
clasificacion_suelo = st.sidebar.selectbox("Clasificación del Terreno", ["Tierra Común / Limos (Dificultad Normal)", "Roca / Terreno Duro"])
factor_esponjamiento = st.sidebar.number_input("Factor Esponjamiento", min_value=1.0, max_value=2.0, value=1.0, step=0.05)

# 3. Logística
st.sidebar.subheader("🚛 Logística de Transporte")
distancia_botadero = st.sidebar.number_input("Distancia a Botadero (Km ida/vuelta)", value=35.0)
capacidad_camion = st.sidebar.number_input("Capacidad del Camión (m³ tolva)", value=15.0)
tiempo_ciclo = st.sidebar.number_input("Tiempo estimado por ciclo (minutos)", value=90)

# 4. Tiempos
st.sidebar.subheader("⏱️ Planificación")
rendimiento_base = st.sidebar.number_input("Rendimiento Base (m³/día)", value=350.0)
dias_totales = st.sidebar.number_input("Duración Calculada de Faena (días)", value=9)

# 5. Precios
st.sidebar.subheader("7. Oferta Comercial")
precio_unitario_neto = st.sidebar.number_input("Precio Unitario Final Neto ($/m³)", value=15750.0)

# 6. Condiciones Comercial
st.sidebar.subheader("📜 Condiciones")
validez_oferta = st.sidebar.number_input("Validez Oferta (días)", value=15)
minimo_horas_garantizadas = st.sidebar.number_input("Mínimo Horas Diarias Garantizadas", value=8)
condicion_pago = st.sidebar.text_input("Condición de Pago", "A tratar según previo acuerdo")

# Cálculos Derivados
oferta_total_neto = volumen_util * precio_unitario_neto
total_bruto = oferta_total_neto * 1.19
texto_control_volumen = "El volumen final será controlado y cubicado strictly mediante levantamiento topográfico de terreno en banco (cota inicial vs. cota final)."

# --- VISTA PREVIA EN INTERFAZ ---
st.subheader("📋 Vista Previa de la Propuesta Formal")
st.markdown(f"**PRESUPUESTO DE SERVICIO DE RETIRO Y MOVIMIENTO DE TIERRAS**")
st.write(f"- **Para:** {cliente}")
st.write(f"- **De:** EDOS SpA")
st.write(f"- **Ubicación:** {ubicacion}")
st.write(f"- **Plazo de Ejecución:** {dias_totales} días de faena")
st.write(f"- **Validez de la Oferta:** {validez_oferta} días corridos")

st.table([
    {
        "Descripción": f"Servicio de retiro / excavación ({criterio_volumen.lower()})",
        "Cantidad Estimada": f"{volumen_util:,.0f} m³".replace(",", "."),
        "P. Unitario Neto": f"${precio_unitario_neto:,.0f} / m³".replace(",", "."),
        "Total Neto Estimado": f"${oferta_total_neto:,.0f}".replace(",", ".")
    }
])

st.subheader("Condiciones Comerciales y Legales")
st.write(f"- **Forma de Pago:** {condicion_pago}")
st.write(f"- **Control de Volumen:** {texto_control_volumen}")
st.write(f"- **Mínimo Diario Garantizado:** Se establece un mínimo de {minimo_horas_garantizadas} horas/día por equipo contratado.")
st.write("- **Stand-by por Clima o Paralización Imputable:** En caso de paralización de la obra por causas ajenas a EDOS SpA o eventos meteorológicos, se facturará la tarifa de stand-by correspondiente al mínimo diario garantizado de los equipos en obra.")

st.write(f"*{representante} - EDOS SpA*")


# --- FUNCIÓN GENERADORA DE PDF CORREGIDA ---
def generar_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Ancho útil disponible de la página A4 (210mm total - márgenes)
    ancho_util = pdf.w - pdf.l_margin - pdf.r_margin

    # Encabezado
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(ancho_util, 8, limpiar_texto("PRESUPUESTO DE SERVICIO DE RETIRO Y MOVIMIENTO DE TIERRAS"), ln=True, align="C")
    pdf.ln(4)

    # Datos Principales
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(ancho_util, 6, limpiar_texto(f"- Para: {cliente}"), ln=True)
    pdf.cell(ancho_util, 6, limpiar_texto(f"- De: {representante} (EDOS SpA)"), ln=True)
    pdf.cell(ancho_util, 6, limpiar_texto(f"- Ubicación: {ubicacion}"), ln=True)
    pdf.cell(ancho_util, 6, limpiar_texto(f"- Plazo de Ejecución: {dias_totales} días de faena"), ln=True)
    pdf.cell(ancho_util, 6, limpiar_texto(f"- Validez de la Oferta: {validez_oferta} días corridos"), ln=True)
    pdf.ln(5)

    # Tabla de Resumen
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(90, 7, limpiar_texto("Descripción"), 1, 0, "C")
    pdf.cell(30, 7, limpiar_texto("Cantidad"), 1, 0, "C")
    pdf.cell(35, 7, limpiar_texto("P. Unitario"), 1, 0, "C")
    pdf.cell(35, 7, limpiar_texto("Total Neto"), 1, 1, "C")

    pdf.set_font("Helvetica", "", 9)
    pdf.cell(90, 7, limpiar_texto(f"Servicio de retiro / excavación ({criterio_volumen.lower()})"), 1)
    pdf.cell(30, 7, limpiar_texto(f"{volumen_util:,.0f} m3".replace(",", ".")), 1, 0, "C")
    pdf.cell(35, 7, limpiar_texto(f"${precio_unitario_neto:,.0f}".replace(",", ".")), 1, 0, "R")
    pdf.cell(35, 7, limpiar_texto(f"${oferta_total_neto:,.0f}".replace(",", ".")), 1, 1, "R")
    pdf.ln(8)

    # Sección de Condiciones Comerciales
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_x(pdf.l_margin)
    pdf.cell(ancho_util, 7, limpiar_texto("Condiciones Comerciales y Legales"), ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 9)
    
    # Reset del cursor horizontal antes de cada multi_cell
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(ancho_util, 5, limpiar_texto(f"- Forma de Pago: {condicion_pago}"))
    pdf.ln(2)

    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(ancho_util, 5, limpiar_texto(f"- Control de Volumen: {texto_control_volumen}"))
    pdf.ln(2)

    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(ancho_util, 5, limpiar_texto(f"- Mínimo Diario Garantizado: Se establece un mínimo de {minimo_horas_garantizadas} horas/día por equipo contratado."))
    pdf.ln(2)

    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(ancho_util, 5, limpiar_texto("- Stand-by por Clima o Paralización Imputable: En caso de paralización de la obra por causas ajenas a EDOS SpA o eventos meteorológicos, se facturará la tarifa de stand-by correspondiente al mínimo diario garantizado de los equipos en obra."))
    pdf.ln(10)

    # Firma
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_x(pdf.l_margin)
    pdf.cell(ancho_util, 6, limpiar_texto(f"{representante} - EDOS SpA"), ln=True, align="R")

    # Retorna directamente los bytes del PDF generado para Streamlit
    return bytes(pdf.output())


# --- BOTÓN DE DESCARGA PDF ---
st.download_button(
    label="📄 Descargar Propuesta Formal en PDF",
    data=generar_pdf(),
    file_name=f"Presupuesto_EDOS_SpA_{cliente.replace(' ', '_')}.pdf",
    mime="application/pdf"
)
