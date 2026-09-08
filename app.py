import streamlit as st
from fpdf import FPDF

# --- FUNCIÓN DE LIMPIEZA DE TEXTO PARA FPDF ---
def limpiar_texto(texto):
    if not isinstance(texto, str):
        return texto
    
    reemplazos = {
        "³": "3", "²": "2", "°": " deg", "–": "-", "—": "-",
        "“": '"', "”": '"', "‘": "'", "’": "'", "…": "...",
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U",
        "ñ": "n", "Ñ": "N"
    }
    for orig, reemplazo in reemplazos.items():
        texto = texto.replace(orig, reemplazo)
    return texto


# --- BASE DE DATOS TÉCNICA: FACTORES DE ESPONJAMIENTO Y SUGERENCIAS ---
TABLA_ESPONJAMIENTO = {
    "Tierra Común / Limos (Dificultad Normal)": {
        "factor_sugerido": 1.20,
        "rango": "20% - 25%",
        "desc": "Terreno vegetal, limos y arenas consolidadas."
    },
    "Pumacita / Toba Volcánica": {
        "factor_sugerido": 1.50,
        "rango": "40% - 50%",
        "desc": "Material volcánico poroso y friable; genera alto porcentaje de huecos al disgregarse."
    },
    "Arcilla Seca / Compacta": {
        "factor_sugerido": 1.30,
        "rango": "25% - 35%",
        "desc": "Arcillas secas, firmes o de cohesión media."
    },
    "Arcilla Húmeda / Pegajosa": {
        "factor_sugerido": 1.40,
        "rango": "35% - 45%",
        "desc": "Arcillas plásticas con alta retención de agua."
    },
    "Grava / Maicillo": {
        "factor_sugerido": 1.15,
        "rango": "10% - 20%",
        "desc": "Materiales granulares de composición mixta."
    },
    "Roca Fragmentada / Tronada": {
        "factor_sugerido": 1.50,
        "rango": "40% - 65%",
        "desc": "Roca desintegrada mecánicamente o mediante explosivos."
    },
    "Hormigón Armado / Escombros de Demolición": {
        "factor_sugerido": 1.45,
        "rango": "40% - 50%",
        "desc": "Estructuras demolidas, losas y fundaciones."
    }
}


# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Cotizador Profesional EDOS SpA",
    page_icon="🚜",
    layout="wide"
)

st.title("🚜 EDOS SpA - Generador Integral de Presupuestos")
st.caption("Plataforma técnica-comercial para movimiento de tierras, demoliciones, geomensura y obras civiles.")

# --- SIDEBAR / ENTRADA DE DATOS ---
st.sidebar.header("Parámetros del Proyecto")

# 1. Datos del Mandante
st.sidebar.subheader("📄 Datos del Mandante")
cliente = st.sidebar.text_input("Cliente / Constructora", "Constructora Minimal")
ubicacion = st.sidebar.text_input("Ubicación de la Obra", "Avenida El Salto 2255, Recoleta")
representante = st.sidebar.text_input("Representante EDOS SpA", "Vicente Ortiz Amestelli")

# 2. Demolición (Opcional)
st.sidebar.subheader("💥 Servicio de Demolición")
incluir_demolicion = st.sidebar.checkbox("Incluir Servicio de Demolición", value=False)

if incluir_demolicion:
    tipo_demolicion = st.sidebar.selectbox(
        "Tipo de Estructura a Demoler",
        ["Hormigón Armado", "Albañilería / Ladrillo", "Pavimentos / Pavimentos de Asfalto", "Estructura Liviana / Mixta"]
    )
    volumen_demolicion = st.sidebar.number_input("Volumen / Superficie a Demoler (m³ o m²)", min_value=1.0, value=150.0, step=10.0)
    precio_unitario_demolicion = st.sidebar.number_input("Precio Unitario Demolición ($/m³ o $/m²)", min_value=0.0, value=22000.0, step=500.0)
    costo_total_demolicion = volumen_demolicion * precio_unitario_demolicion
else:
    costo_total_demolicion = 0.0

# 3. Cubicaciones, Suelo y Sugerencia de Esponjamiento
st.sidebar.subheader("1. Cubicaciones y Suelo")
criterio_volumen = st.sidebar.radio(
    "Criterio / Base de Medición de Volumen",
    ["Volumen Geométrico en Banco (Topografía)", "Volumen Esponjado (Sobre Camión)"]
)
volumen_util = st.sidebar.number_input("Volumen Geométrico en Banco (m³)", min_value=1.0, value=2914.0, step=10.0)

# Selección de Suelo y Sugerencia
clasificacion_suelo = st.sidebar.selectbox(
    "Clasificación del Terreno",
    list(TABLA_ESPONJAMIENTO.keys())
)

info_suelo = TABLA_ESPONJAMIENTO[clasificacion_suelo]

# Cuadro informativo con la sugerencia técnica
st.sidebar.info(
    f"💡 **Sugerencia Técnica:**\n"
    f"- Esponjamiento típico: **{info_suelo['rango']}**\n"
    f"- Factor recomendado: **{info_suelo['factor_sugerido']:.2f}**\n"
    f"_{info_suelo['desc']}_"
)

factor_esponjamiento = st.sidebar.number_input(
    "Factor de Esponjamiento Aplicado",
    min_value=1.0,
    max_value=2.0,
    value=info_suelo["factor_sugerido"],
    step=0.05
)

volumen_esponjado_real = volumen_util * factor_esponjamiento

# 4. Logística de Transporte
st.sidebar.subheader("🚛 Logística de Transporte")
distancia_botadero = st.sidebar.number_input("Distancia a Botadero (Km ida/vuelta)", value=35.0, step=5.0)
capacidad_camion = st.sidebar.number_input("Capacidad del Camión (m³ tolva)", value=15.0, step=1.0)
tiempo_ciclo = st.sidebar.number_input("Tiempo estimado por ciclo (minutos)", value=90, step=5)

# 5. Planificación y Tiempos
st.sidebar.subheader("⏱️ Planificación")
rendimiento_base = st.sidebar.number_input("Rendimiento Base Excavación (m³/día)", value=350.0, step=25.0)
dias_totales = st.sidebar.number_input("Duración Calculada de Faena (días)", value=9, step=1)

# 6. Precios Movimiento de Tierra
st.sidebar.subheader("7. Oferta Comercial Explotación")
precio_unitario_neto = st.sidebar.number_input("Precio Unitario Final Neto ($/m³)", value=15750.0, step=250.0)

# 7. Condiciones Comerciales
st.sidebar.subheader("📜 Condiciones")
validez_oferta = st.sidebar.number_input("Validez Oferta (días)", value=15, step=1)
minimo_horas_garantizadas = st.sidebar.number_input("Mínimo Horas Diarias Garantizadas", value=8, step=1)
condicion_pago = st.sidebar.text_input("Condición de Pago", "A tratar según previo acuerdo")

# --- CÁLCULOS TÉCNICO-COMERCIALES ---
subtotal_mov_tierra = volumen_util * precio_unitario_neto
oferta_total_neto = subtotal_mov_tierra + costo_total_demolicion
monto_iva = oferta_total_neto * 0.19
total_bruto = oferta_total_neto + monto_iva

num_viajes_estimados = int(-(-volumen_esponjado_real // capacidad_camion))

texto_control_volumen = (
    f"El volumen base se cubicará en banco mediante levantamiento topográfico (cota inicial vs. cota final). "
    f"Considerando un factor de esponjamiento de {factor_esponjamiento:.2f} ({clasificacion_suelo}), "
    f"se estima un volumen real a retirar en camión de {volumen_esponjado_real:,.0f} m³ "
    f"({num_viajes_estimados} viajes de camiones de {capacidad_camion:.0f} m³, distancia botadero: {distancia_botadero:.0f} km)."
)

# --- VISTA PREVIA EN INTERFAZ ---
st.subheader("📋 Vista Previa de la Propuesta Formal")
st.markdown("**PRESUPUESTO DE SERVICIO DE DEMOLICIÓN, RETIRO Y MOVIMIENTO DE TIERRAS**")
st.write(f"- **Para:** {cliente}")
st.write(f"- **De:** EDOS SpA ({representante})")
st.write(f"- **Ubicación:** {ubicacion}")
st.write(f"- **Plazo de Ejecución:** {dias_totales} días de faena (Rendimiento: {rendimiento_base:,.0f} m³/día)")
st.write(f"- **Validez de la Oferta:** {validez_oferta} días corridos")

# Tarjetas Métricas
col1, col2, col3, col4 = st.columns(4)
col1.metric("Volumen Banco (Topografía)", f"{volumen_util:,.0f} m³".replace(",", "."))
col2.metric("Factor Esponjamiento", f"{factor_esponjamiento:.2f}")
col3.metric("Volumen Estimado a Retirar", f"{volumen_esponjado_real:,.0f} m³".replace(",", "."))
col4.metric("Viajes Estimados Camión", f"{num_viajes_estimados} viajes")

# Tabla Resumen de Ítems
items_tabla = []

if incluir_demolicion:
    items_tabla.append({
        "Descripción": f"Servicio de demolición de {tipo_demolicion.lower()}",
        "Cantidad Estimada": f"{volumen_demolicion:,.0f}",
        "P. Unitario Neto": f"${precio_unitario_demolicion:,.0f}".replace(",", "."),
        "Total Neto Estimado": f"${costo_total_demolicion:,.0f}".replace(",", ".")
    })

items_tabla.append({
    "Descripción": f"Servicio de retiro / excavación ({criterio_volumen.lower()})",
    "Cantidad Estimada": f"{volumen_util:,.0f} m³".replace(",", "."),
    "P. Unitario Neto": f"${precio_unitario_neto:,.0f} / m³".replace(",", "."),
    "Total Neto Estimado": f"${subtotal_mov_tierra:,.0f}".replace(",", ".")
})

st.table(items_tabla)

# Resumen de Valores (Neto, IVA, Bruto)
c1, c2, c3 = st.columns(3)
c1.markdown(f"**Neto:** ${oferta_total_neto:,.0f}".replace(",", "."))
c2.markdown(f"**19% IVA:** ${monto_iva:,.0f}".replace(",", "."))
c3.markdown(f"### **Total Bruto: ${total_bruto:,.0f}**".replace(",", "."))

st.subheader("Condiciones Comerciales y Legales")
st.write(f"- **Forma de Pago:** {condicion_pago}")
st.write(f"- **Control de Volumen y Logística:** {texto_control_volumen}")
st.write(f"- **Mínimo Diario Garantizado:** Se establece un mínimo de {minimo_horas_garantizadas} horas/día por equipo contratado.")
st.write("- **Stand-by por Clima o Paralización Imputable:** En caso de paralización de la obra por causas ajenas a EDOS SpA o eventos meteorológicos, se facturará la tarifa de stand-by correspondiente al mínimo diario garantizado de los equipos en obra.")

st.write(f"*{representante} - EDOS SpA*")


# --- FUNCIÓN GENERADORA DE PDF ---
def generar_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    ancho_util = pdf.w - pdf.l_margin - pdf.r_margin

    # Encabezado
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(ancho_util, 8, limpiar_texto("PRESUPUESTO DE SERVICIO DE DEMOLICION Y MOVIMIENTO DE TIERRAS"), ln=True, align="C")
    pdf.ln(4)

    # Datos Principales
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(ancho_util, 6, limpiar_texto(f"- Para: {cliente}"), ln=True)
    pdf.cell(ancho_util, 6, limpiar_texto(f"- De: {representante} (EDOS SpA)"), ln=True)
    pdf.cell(ancho_util, 6, limpiar_texto(f"- Ubicación: {ubicacion}"), ln=True)
    pdf.cell(ancho_util, 6, limpiar_texto(f"- Plazo de Ejecución: {dias_totales} días de faena (Rendimiento: {rendimiento_base:,.0f} m3/día)"), ln=True)
    pdf.cell(ancho_util, 6, limpiar_texto(f"- Validez de la Oferta: {validez_oferta} días corridos"), ln=True)
    pdf.ln(5)

    # Tabla de Resumen
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(90, 7, limpiar_texto("Descripción"), 1, 0, "C")
    pdf.cell(30, 7, limpiar_texto("Cantidad"), 1, 0, "C")
    pdf.cell(35, 7, limpiar_texto("P. Unitario"), 1, 0, "C")
    pdf.cell(35, 7, limpiar_texto("Total Neto"), 1, 1, "C")

    pdf.set_font("Helvetica", "", 9)

    if incluir_demolicion:
        pdf.cell(90, 7, limpiar_texto(f"Demolición ({tipo_demolicion.lower()})"), 1)
        pdf.cell(30, 7, limpiar_texto(f"{volumen_demolicion:,.0f}".replace(",", ".")), 1, 0, "C")
        pdf.cell(35, 7, limpiar_texto(f"${precio_unitario_demolicion:,.0f}".replace(",", ".")), 1, 0, "R")
        pdf.cell(35, 7, limpiar_texto(f"${costo_total_demolicion:,.0f}".replace(",", ".")), 1, 1, "R")

    pdf.cell(90, 7, limpiar_texto(f"Retiro / excavación ({criterio_volumen.lower()})"), 1)
    pdf.cell(30, 7, limpiar_texto(f"{volumen_util:,.0f} m3".replace(",", ".")), 1, 0, "C")
    pdf.cell(35, 7, limpiar_texto(f"${precio_unitario_neto:,.0f}".replace(",", ".")), 1, 0, "R")
    pdf.cell(35, 7, limpiar_texto(f"${subtotal_mov_tierra:,.0f}".replace(",", ".")), 1, 1, "R")

    # Filas Totales (Neto, IVA y Total Bruto)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(155, 6, limpiar_texto("SUBTOTAL NETO"), 1, 0, "R")
    pdf.cell(35, 6, limpiar_texto(f"${oferta_total_neto:,.0f}".replace(",", ".")), 1, 1, "R")
    
    pdf.cell(155, 6, limpiar_texto("19% IVA"), 1, 0, "R")
    pdf.cell(35, 6, limpiar_texto(f"${monto_iva:,.0f}".replace(",", ".")), 1, 1, "R")

    pdf.cell(155, 7, limpiar_texto("TOTAL BRUTO"), 1, 0, "R")
    pdf.cell(35, 7, limpiar_texto(f"${total_bruto:,.0f}".replace(",", ".")), 1, 1, "R")

    pdf.ln(8)

    # Sección de Condiciones Comerciales
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_x(pdf.l_margin)
    pdf.cell(ancho_util, 7, limpiar_texto("Condiciones Comerciales y Legales"), ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 9)
    
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(ancho_util, 5, limpiar_texto(f"- Forma de Pago: {condicion_pago}"))
    pdf.ln(2)

    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(ancho_util, 5, limpiar_texto(f"- Control de Volumen y Logística: {texto_control_volumen}"))
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

    return bytes(pdf.output())


# --- BOTÓN DE DESCARGA PDF ---
st.download_button(
    label="📄 Descargar Propuesta Formal en PDF",
    data=generar_pdf(),
    file_name=f"Presupuesto_EDOS_SpA_{cliente.replace(' ', '_')}.pdf",
    mime="application/pdf"
)
