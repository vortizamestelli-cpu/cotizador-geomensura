import json
import math
from fpdf import FPDF
import streamlit as st

# ---------------------------------------------------------
# FUNCIÓN DE LIMPIEZA DE TEXTO PARA FPDF
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# BASE DE DATOS TÉCNICA DE ESPONJAMIENTO
# ---------------------------------------------------------
TABLA_ESPONJAMIENTO = {
    "Tierra Común / Limos (Dificultad Normal)": {
        "factor_sugerido": 1.20,
        "rango": "20% - 25%",
        "desc": "Terreno vegetal, limos y arenas consolidadas.",
        "dificultad": 1.00
    },
    "Pumacita / Toba Volcánica": {
        "factor_sugerido": 1.50,
        "rango": "40% - 50%",
        "desc": "Material volcánico poroso y friable; genera alto porcentaje de huecos al disgregarse.",
        "dificultad": 0.95
    },
    "Arcilla Seca / Compacta (Dificultad Media)": {
        "factor_sugerido": 1.30,
        "rango": "25% - 35%",
        "desc": "Arcillas secas, firmes o de cohesión media.",
        "dificultad": 0.90
    },
    "Arcilla Húmeda / Pegajosa": {
        "factor_sugerido": 1.40,
        "rango": "35% - 45%",
        "desc": "Arcillas plásticas con alta retención de agua.",
        "dificultad": 0.85
    },
    "Maicillo / Grava Cohesiva": {
        "factor_sugerido": 1.15,
        "rango": "10% - 20%",
        "desc": "Materiales granulares de composición mixta.",
        "dificultad": 0.95
    },
    "Roca Fragmentada / Terreno Semi-Rocoso": {
        "factor_sugerido": 1.50,
        "rango": "40% - 65%",
        "desc": "Roca desintegrada mecánicamente o mediante martillo/explosivos.",
        "dificultad": 0.55
    },
    "Escombros Masivos / Hormigón Armado": {
        "factor_sugerido": 1.45,
        "rango": "40% - 50%",
        "desc": "Estructuras demolidas, losas y fundaciones.",
        "dificultad": 0.75
    }
}


# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Cotizador Profesional EDOS SpA",
    page_icon="🚜",
    layout="wide"
)

st.title("🚜 EDOS SpA - Generador Integral de Presupuestos")
st.caption("Plataforma técnica-comercial para movimiento de tierras, demoliciones, arriendos, geomensura y obras civiles.")
st.markdown("---")

# ---------------------------------------------------------
# DATOS DE LA OBRA Y MANDANTE
# ---------------------------------------------------------
st.subheader("📄 Datos del Mandante y Ubicación")
col_m1, col_m2 = st.columns(2)
with col_m1:
    cliente_nombre = st.text_input("Empresa (Cliente / Constructora)", "Constructora Minimal")
    profesional_cliente = st.text_input("Atención a (Profesional a cargo)", "Eduardo Tobar - Administrador de Obra")
with col_m2:
    ubicacion_obra = st.text_input("Ubicación de la Obra", "Avenida El Salto 2255, Recoleta")
    representante = st.text_input("Representante EDOS SpA", "Vicente Ortiz Amestelli")

st.markdown("---")

# ---------------------------------------------------------
# SERVICIOS ADICIONALES (DEMOLICIÓN Y MAQUINARIA EXTRA)
# ---------------------------------------------------------
st.subheader("💥 Servicios Adicionales (Demolición y Arriendos)")
col_serv1, col_serv2 = st.columns(2)

with col_serv1:
    incluir_demolicion = st.checkbox("Incluir Servicio de Demolición", value=False)
    if incluir_demolicion:
        tipo_demolicion = st.selectbox(
            "Estructura a Demoler",
            ["Hormigón Armado", "Albañilería / Ladrillo", "Pavimentos / Asfalto", "Estructura Liviana / Mixta"]
        )
        volumen_demolicion = st.number_input("Volumen / Superficie Demolición (m³ o m²)", min_value=1.0, value=150.0, step=10.0)
        precio_unitario_demolicion = st.number_input("Precio Unitario Demolición ($)", min_value=0.0, value=22000.0, step=500.0)
        costo_total_demolicion = volumen_demolicion * precio_unitario_demolicion
    else:
        costo_total_demolicion = 0.0

with col_serv2:
    incluir_maq_adicional = st.checkbox("Incluir Arriendo / Maquinaria Adicional / Camión Interno", value=False)
    if incluir_maq_adicional:
        nombre_maq_adicional = st.text_input("Descripción del Equipo o Camión", "Camión Tolva Adicional / Arriendo")
        cantidad_maq_adicional = st.number_input("Cantidad (Horas, Días o Viajes)", min_value=1.0, value=8.0, step=1.0)
        unidad_maq_adicional = st.selectbox("Unidad de Cobro", ["Horas", "Días", "Mes", "Global", "Viajes"])
        precio_unitario_maq_adicional = st.number_input("Precio Unitario Neto ($)", min_value=0.0, value=35000.0, step=1000.0)
        costo_total_maq_adicional = cantidad_maq_adicional * precio_unitario_maq_adicional
    else:
        costo_total_maq_adicional = 0.0

st.markdown("---")

# ---------------------------------------------------------
# 1. CUBICACIÓN, SUELO Y LOGÍSTICA
# ---------------------------------------------------------
st.subheader("1. Cubicaciones, Caracterización de Suelo y Logística")

criterio_medicion = st.radio(
    "Criterio / Base de Medición de Volumen",
    [
        "Volumen Geométrico en Banco (Topografía)",
        "Volumen Esponjado (Sobre Camión)"
    ],
    index=0
)

col_v1, col_v2, col_v3 = st.columns(3)

with col_v1:
    label_vol = "Volumen Geométrico en Banco (m³)" if "Banco" in criterio_medicion else "Volumen Esponjado a Retirar (m³)"
    volumen_ingresado = st.number_input(label_vol, min_value=1.0, value=2914.00, step=10.0)

with col_v2:
    tipo_suelo = st.selectbox(
        "Clasificación del Terreno",
        list(TABLA_ESPONJAMIENTO.keys())
    )

info_suelo = TABLA_ESPONJAMIENTO[tipo_suelo]
factor_dificultad_suelo = info_suelo["dificultad"]

st.info(
    f"💡 **Sugerencia Técnica de Esponjamiento:**\n"
    f"- Rango típico: **{info_suelo['rango']}** | Factor recomendado: **{info_suelo['factor_sugerido']:.2f}**\n"
    f"_{info_suelo['desc']}_"
)

if "Banco" in criterio_medicion:
    with col_v3:
        factor_esponjamiento = st.number_input(
            "Factor Esponjamiento Aplicado",
            min_value=1.00,
            max_value=2.00,
            value=info_suelo["factor_sugerido"],
            step=0.05
        )
    volumen_cobrar = volumen_ingresado
    volumen_esponjado_real = volumen_ingresado * factor_esponjamiento
    unidad_medicion = "m³ geométricos (en banco / topografía)"
    texto_control_volumen = (
        f"El volumen base se cubicará en banco mediante levantamiento topográfico (cota inicial vs. cota final). "
        f"Considerando un factor de esponjamiento de {factor_esponjamiento:.2f} ({tipo_suelo}), "
        f"se estima un volumen real a retirar en camión de {volumen_esponjado_real:,.0f} m³."
    )
else:
    with col_v3:
        factor_esponjamiento = st.number_input(
            "Factor Esponjamiento Aplicado",
            value=1.00,
            disabled=True,
            help="Al medir sobre camión, el volumen ya está esponjado y no se multiplica por factor."
        )
    volumen_cobrar = volumen_ingresado
    volumen_esponjado_real = volumen_ingresado
    unidad_medicion = "m³ esponjados (sobre camión)"
    texto_control_volumen = (
        "El volumen final acumulado queda sujeto a control estricto mediante la emisión y firma "
        "de vales de carga o registro diario de salida de camiones en obra."
    )

# --- MÓDULO LOGÍSTICO Y CICLO DE CAMIONES ---
st.markdown("#### 🚛 Logística de Transporte y Botadero")
col_l1, col_l2, col_l3 = st.columns(3)
with col_l1:
    distancia_botadero_km = st.number_input("Distancia a Botadero (Km ida/vuelta)", min_value=1.0, value=35.0, step=5.0)
with col_l2:
    capacidad_camion = st.number_input("Capacidad del Camión (m³ tolva)", min_value=10.0, value=20.0, step=1.0)
with col_l3:
    tiempo_ciclo_min = st.number_input("Tiempo Estimado por Ciclo (minutos)", min_value=10, value=35, step=5)

st.markdown("#### ⏱️ Planificación de Tiempos y Rendimientos")
modo_tiempo = st.radio(
    "Definición de Plazo de Ejecución",
    [
        "Calcular días según rendimiento estimado (m³/día)",
        "Fijar días de faena impuestos por el Mandante (recalcula m³/día necesarios)"
    ],
    index=0
)

col_t1, col_t2, col_t3 = st.columns(3)

if modo_tiempo == "Calcular días según rendimiento estimado (m³/día)":
    with col_t1:
        rendimiento_base = st.number_input(f"Rendimiento Base ({unidad_medicion}/día)", min_value=10.0, value=350.0, step=25.0)
    m3_diarios_est = rendimiento_base * factor_dificultad_suelo
    duracion_dias = math.ceil(volumen_cobrar / m3_diarios_est) if m3_diarios_est > 0 else 1
    with col_t2:
        st.number_input("Duración Calculada de Faena (días)", value=duracion_dias, disabled=True)
else:
    with col_t2:
        duracion_dias = st.number_input("Días de Faena Impuestos por Mandante", min_value=1, value=11, step=1)
    m3_diarios_est = volumen_cobrar / duracion_dias
    with col_t1:
        st.number_input(f"Rendimiento Requerido ({unidad_medicion}/día)", value=m3_diarios_est, disabled=True)

viajes_totales = math.ceil(volumen_esponjado_real / capacidad_camion)
viajes_camion_dia = math.ceil(viajes_totales / duracion_dias) if duracion_dias > 0 else viajes_totales
camiones_simultaneos = math.ceil((viajes_camion_dia * (tiempo_ciclo_min / 60)) / 8)

with col_t3:
    st.number_input("Camiones Necesarios en Flota", value=camiones_simultaneos, disabled=True)

st.info(
    f"💡 **Rendimiento Ajustado por Suelo:** {m3_diarios_est:,.0f} m³/día | "
    f"**Viajes Totales Estimados:** {viajes_totales} de {capacidad_camion:.0f} m³ | "
    f"**Flota Estimada:** {camiones_simultaneos} camiones operando para {viajes_camion_dia} viajes/día."
)

st.markdown("---")

# ---------------------------------------------------------
# OPERACIÓN E IMPUTACIÓN DE COSTOS
# ---------------------------------------------------------
st.subheader("⚙️ Operación e Imputación de Costos Internos")

modalidad_ejecucion = st.radio(
    "Modalidad de Operación Interna",
    [
        "Desglosada (Gestión propia de Maquinaria, Petróleo y Transporte)",
        "Subcontrato Completo / Todo Incluido (Tarifa cerrada por m³)"
    ],
    index=1
)

costo_interno_total = 0.0
if modalidad_ejecucion == "Subcontrato Completo / Todo Incluido (Tarifa cerrada por m³)":
    costo_subcontrato_m3 = st.number_input(f"Costo del Subcontrato por {unidad_medicion} ($/m³)", min_value=0.0, value=13875.0, step=100.0)
    costo_interno_total = volumen_cobrar * costo_subcontrato_m3
else:
    costo_interno_total = volumen_cobrar * 12000.0  # Estimación interna desglosada genérica

st.markdown("---")

# ---------------------------------------------------------
# FINANZAS, PÓLIZAS Y FACTORING
# ---------------------------------------------------------
st.subheader("📜 Condiciones Comerciales, Garantías y Financiamiento")
col_c1, col_c2, col_c3 = st.columns(3)
with col_c1:
    validez_oferta = st.number_input("Validez Oferta (días)", value=15)
with col_c2:
    minimo_horas = st.number_input("Mínimo Horas Diarias Garantizadas", value=8)
with col_c3:
    condicion_pago = st.text_input("Condición de Pago", "A tratar según previo acuerdo")

with st.expander("🏦 Garantías, Pólizas y Factoring"):
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        incluye_poliza = st.checkbox("¿Exige Póliza de Fianza / Boleta Garantía?")
        costo_poliza = 180000.0 if incluye_poliza else 0.0
    with col_f2:
        incluye_factoring = st.checkbox("¿Aplica Cobro Vía Factoring?")

st.markdown("---")

# ---------------------------------------------------------
# OFERTA COMERCIAL Y MARGEN
# ---------------------------------------------------------
st.subheader("7. Oferta Comercial al Mandante")

tipo_oferta = st.radio(
    "Definición del Precio",
    [
        "Ingresar Precio Unitario Neto al Mandante ($/m³)",
        "Definir por porcentaje de margen (%)",
        "Ingresar Precio Final Neto Objetivo ($)"
    ]
)

if tipo_oferta == "Ingresar Precio Unitario Neto al Mandante ($/m³)":
    pu_neto_mandante = st.number_input(f"Precio Unitario Final Neto ($/{unidad_medicion})", min_value=0.0, value=15750.0, step=250.0)
    subtotal_mov_tierra = volumen_cobrar * pu_neto_mandante
elif tipo_oferta == "Definir por porcentaje de margen (%)":
    margen_pct = st.number_input("Margen Deseado (%)", min_value=0.0, value=13.5, step=0.5)
    costo_base = costo_interno_total + costo_poliza
    subtotal_mov_tierra = (costo_base / (1.0 - (margen_pct / 100.0))) if margen_pct < 100 else costo_base
    pu_neto_mandante = subtotal_mov_tierra / volumen_cobrar if volumen_cobrar > 0 else 0.0
else:
    subtotal_mov_tierra = st.number_input("Precio Final Neto Objetivo Movimiento Tierra ($)", min_value=0.0, value=45895500.0)
    pu_neto_mandante = subtotal_mov_tierra / volumen_cobrar if volumen_cobrar > 0 else 0.0

# Oferta Total Neto incluye Movimiento de Tierra + Demolición + Maquinaria Adicional
oferta_total_neto = subtotal_mov_tierra + costo_total_demolicion + costo_total_maq_adicional

iva_monto = oferta_total_neto * 0.19
total_bruto = oferta_total_neto + iva_monto
margen_monto = oferta_total_neto - costo_interno_total
margen_porcentaje = (margen_monto / oferta_total_neto * 100.0) if oferta_total_neto > 0 else 0.0

# ---------------------------------------------------------
# RESUMEN ECONÓMICO E IMPUESTOS
# ---------------------------------------------------------
st.subheader("📊 Resumen Económico e Impuestos")
col_r1, col_r2, col_r3, col_r4 = st.columns(4)
col_r1.metric("Costo Interno Total", f"${costo_interno_total:,.0f}".replace(",", "."))
col_r2.metric("Subtotal Neto Oferta", f"${oferta_total_neto:,.0f}".replace(",", "."), delta=f"Margen: {margen_porcentaje:.1f}%")
col_r3.metric("Monto IVA (19%)", f"${iva_monto:,.0f}".replace(",", "."))
col_r4.metric("Total Bruto", f"${total_bruto:,.0f}".replace(",", "."))

st.markdown("---")

# ---------------------------------------------------------
# VISTA PREVIA Y CLÁUSULAS
# ---------------------------------------------------------
st.subheader("📋 Vista Previa de la Propuesta Formal")

st.markdown("**PRESUPUESTO DE SERVICIO DE MOVIMIENTO DE TIERRAS Y OBRAS ANEXAS**")
st.markdown(f"- **Para:** {cliente_nombre}")
st.markdown(f"- **Atención:** {profesional_cliente}")
st.markdown(f"- **De:** EDOS SpA ({representante})")
st.markdown(f"- **Ubicación:** {ubicacion_obra}")
st.markdown(f"- **Plazo de Ejecución:** {duracion_dias} días de faena (Rendimiento: {m3_diarios_est:,.0f} m³/día)")
st.markdown(f"- **Validez de la Oferta:** {validez_oferta} días corridos")

items_tabla = []
if incluir_demolicion:
    items_tabla.append({
        "Descripción": f"Servicio de demolición de {tipo_demolicion.lower()}",
        "Cantidad Estimada": f"{volumen_demolicion:,.0f}",
        "P. Unitario Neto": f"${precio_unitario_demolicion:,.0f}".replace(",", "."),
        "Total Neto Estimado": f"${costo_total_demolicion:,.0f}".replace(",", ".")
    })

if incluir_maq_adicional:
    items_tabla.append({
        "Descripción": f"{nombre_maq_adicional} ({unidad_maq_adicional.lower()})",
        "Cantidad Estimada": f"{cantidad_maq_adicional:,.0f}",
        "P. Unitario Neto": f"${precio_unitario_maq_adicional:,.0f}".replace(",", "."),
        "Total Neto Estimado": f"${costo_total_maq_adicional:,.0f}".replace(",", ".")
    })

items_tabla.append({
    "Descripción": f"Servicio de retiro / excavación ({unidad_medicion})",
    "Cantidad Estimada": f"{volumen_cobrar:,.0f} m³".replace(",", "."),
    "P. Unitario Neto": f"${pu_neto_mandante:,.0f} / m³".replace(",", "."),
    "Total Neto Estimado": f"${subtotal_mov_tierra:,.0f}".replace(",", ".")
})

st.table(items_tabla)

col_t1, col_t2, col_t3 = st.columns(3)
col_t1.write(f"**Subtotal Neto:** ${oferta_total_neto:,.0f}".replace(",", "."))
col_t2.write(f"**IVA (19%):** ${iva_monto:,.0f}".replace(",", "."))
col_t3.write(f"**Total Bruto:** ${total_bruto:,.0f}".replace(",", "."))

st.markdown("#### Condiciones Comerciales y Legales")
st.markdown(f"- **Forma de Pago:** {condicion_pago}.")
st.markdown(f"- **Control de Volumen y Logística:** {texto_control_volumen}")
st.markdown(f"- **Mínimo Diario Garantizado:** Se establece un mínimo de {minimo_horas} horas/día por equipo contratado.")
st.markdown("- **Stand-by por Clima o Paralización Imputable:** En caso de paralización de la obra por causas ajenas a EDOS SpA o eventos meteorológicos, se facturará la tarifa de stand-by correspondiente al mínimo diario garantizado de los equipos en obra.")

st.caption(f"*{representante} - EDOS SpA*")

# ---------------------------------------------------------
# GENERADOR DE CORREO RÁPIDO
# ---------------------------------------------------------
with st.expander("✉️ Generar Texto para Correo Electrónico"):
    cuerpo_email = f"""Estimado/a {profesional_cliente},

Junto con saludar, adjunto la propuesta comercial de EDOS SpA para el servicio de retiro de escombros y movimiento de tierras en la obra ubicada en {ubicacion_obra}, correspondiente a {cliente_nombre}.

Resumen de la Oferta:
- Volumen Estimado: {volumen_cobrar:,.0f} {unidad_medicion}
- Plazo de Ejecución: {duracion_dias} días de faena
- Subtotal Neto Oferta: ${oferta_total_neto:,.0f} CLP
- Monto IVA (19%): ${iva_monto:,.0f} CLP
- Total Bruto (incl. IVA): ${total_bruto:,.0f} CLP

Quedamos atentos a sus comentarios para coordinar el inicio de las actividades en terreno.

Saludos cordiales,
{representante}
EDOS SpA
dos.oficinacv@gmail.com
""".replace(",", ".")
    st.code(cuerpo_email, language="markdown")


# ---------------------------------------------------------
# GENERACIÓN DE PDF Y JSON
# ---------------------------------------------------------
def generar_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    ancho_util = pdf.w - pdf.l_margin - pdf.r_margin

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(ancho_util, 8, limpiar_texto("PRESUPUESTO DE SERVICIO DE MOVIMIENTO DE TIERRAS Y OBRAS ANEXAS"), ln=True, align="C")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(ancho_util, 6, limpiar_texto(f"- Para: {cliente_nombre}"), ln=True)
    pdf.cell(ancho_util, 6, limpiar_texto(f"- Atención: {profesional_cliente}"), ln=True)
    pdf.cell(ancho_util, 6, limpiar_texto(f"- De: {representante} (EDOS SpA)"), ln=True)
    pdf.cell(ancho_util, 6, limpiar_texto(f"- Ubicación: {ubicacion_obra}"), ln=True)
    pdf.cell(ancho_util, 6, limpiar_texto(f"- Plazo de Ejecución: {duracion_dias} días de faena"), ln=True)
    pdf.cell(ancho_util, 6, limpiar_texto(f"- Validez de la Oferta: {validez_oferta} días corridos"), ln=True)
    pdf.ln(5)

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

    if incluir_maq_adicional:
        pdf.cell(90, 7, limpiar_texto(f"{nombre_maq_adicional} ({unidad_maq_adicional.lower()})"), 1)
        pdf.cell(30, 7, limpiar_texto(f"{cantidad_maq_adicional:,.0f}".replace(",", ".")), 1, 0, "C")
        pdf.cell(35, 7, limpiar_texto(f"${precio_unitario_maq_adicional:,.0f}".replace(",", ".")), 1, 0, "R")
        pdf.cell(35, 7, limpiar_texto(f"${costo_total_maq_adicional:,.0f}".replace(",", ".")), 1, 1, "R")

    pdf.cell(90, 7, limpiar_texto(f"Retiro / excavación ({criterio_medicion.lower()})"), 1)
    pdf.cell(30, 7, limpiar_texto(f"{volumen_cobrar:,.0f} m3".replace(",", ".")), 1, 0, "C")
    pdf.cell(35, 7, limpiar_texto(f"${pu_neto_mandante:,.0f}".replace(",", ".")), 1, 0, "R")
    pdf.cell(35, 7, limpiar_texto(f"${subtotal_mov_tierra:,.0f}".replace(",", ".")), 1, 1, "R")

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(155, 6, limpiar_texto("SUBTOTAL NETO"), 1, 0, "R")
    pdf.cell(35, 6, limpiar_texto(f"${oferta_total_neto:,.0f}".replace(",", ".")), 1, 1, "R")
    
    pdf.cell(155, 6, limpiar_texto("19% IVA"), 1, 0, "R")
    pdf.cell(35, 6, limpiar_texto(f"${iva_monto:,.0f}".replace(",", ".")), 1, 1, "R")

    pdf.cell(155, 7, limpiar_texto("TOTAL BRUTO"), 1, 0, "R")
    pdf.cell(35, 7, limpiar_texto(f"${total_bruto:,.0f}".replace(",", ".")), 1, 1, "R")

    pdf.ln(8)

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
    pdf.multi_cell(ancho_util, 5, limpiar_texto(f"- Mínimo Diario Garantizado: Se establece un mínimo de {minimo_horas} horas/día por equipo contratado."))
    pdf.ln(2)

    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(ancho_util, 5, limpiar_texto("- Stand-by por Clima o Paralización Imputable: En caso de paralización de la obra por causas ajenas a EDOS SpA o eventos meteorológicos, se facturará la tarifa de stand-by correspondiente al mínimo diario garantizado de los equipos en obra."))
    pdf.ln(10)

    pdf.set_font("Helvetica", "I", 10)
    pdf.set_x(pdf.l_margin)
    pdf.cell(ancho_util, 6, limpiar_texto(f"{representante} - EDOS SpA"), ln=True, align="R")

    return bytes(pdf.output())


col_bot1, col_bot2 = st.columns(2)

with col_bot1:
    st.download_button(
        label="📄 Descargar Presupuesto PDF",
        data=generar_pdf(),
        file_name=f"Presupuesto_EDOS_{cliente_nombre.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )

with col_bot2:
    datos_json = {
        "cliente": cliente_nombre,
        "profesional_cliente": profesional_cliente,
        "ubicacion": ubicacion_obra,
        "criterio_medicion": criterio_medicion,
        "volumen_banco": volumen_ingresado,
        "factor_esponjamiento": factor_esponjamiento if "Banco" in criterio_medicion else 1.0,
        "tipo_suelo": tipo_suelo,
        "volumen_cobrar": volumen_cobrar,
        "duracion_dias_faena": duracion_dias,
        "camiones_simultaneos": camiones_simultaneos,
        "costo_interno_total": costo_interno_total,
        "pu_neto_mandante": pu_neto_mandante,
        "oferta_total_neto": oferta_total_neto,
        "monto_iva": iva_monto,
        "total_bruto": total_bruto
    }
    st.download_button(
        label="💾 Guardar parámetros (JSON)",
        data=json.dumps(datos_json, indent=4),
        file_name="parametros_cotizacion.json",
        mime="application/json"
    )
