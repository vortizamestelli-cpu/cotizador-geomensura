import json
import math
from fpdf import FPDF
import streamlit as st

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Cotizador Profesional EDOS SpA",
    page_icon="🚜",
    layout="wide"
)

st.title("🚜 EDOS SpA - Generador Integral de Presupuestos")
st.caption(
    "Plataforma técnica-comercial para movimiento de tierras, geomensura y obras civiles."
)
st.markdown("---")

# ---------------------------------------------------------
# DATOS DE LA OBRA, MANDANTE Y REPRESENTANTE
# ---------------------------------------------------------
st.subheader("📄 Datos del Mandante, Ubicación y Representación")
col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    cliente_nombre = st.text_input("Para (Cliente / Constructora)", "Constructora Minimal")
with col_m2:
    ubicacion_obra = st.text_input("Ubicación de la Obra", "Avenida El Salto 2255, Recoleta")
with col_m3:
    representante_edos = st.text_input("Representante EDOS SpA", "Vicente Ortiz Amestelli")

st.markdown("---")

# ---------------------------------------------------------
# 1. CUBICACIÓN, SUELO Y LOGÍSTICA
# ---------------------------------------------------------
st.subheader("1. Cubicaciones, Caracterización de Suelo y Logística")

criterio_medicion = st.radio(
    "Criterio / Base de Medición de Volumen",
    ["Volumen Geométrico en Banco (Topografía)", "Volumen Esponjado (Sobre Camión)"],
    index=0
)

col_v1, col_v2, col_v3 = st.columns(3)
with col_v1:
    volumen_banco = st.number_input(
        "Volumen Geométrico en Banco (m³)",
        min_value=1.0,
        value=2914.00,
        step=10.0
    )
with col_v2:
    tipo_suelo = st.selectbox(
        "Clasificación del Terreno",
        [
            "Tierra Común / Limos (Dificultad Normal)",
            "Maicillo / Arcilla Densa (Dificultad Media)",
            "Escombros Masivos / Hormigón Armado (Alta Dificultad)",
            "Roca / Terreno Semi-Rocoso (Requiere Martillo/Insumos)"
        ]
    )

# Factor de corrección por tipo de suelo
factor_dificultad_suelo = 1.0
if "Media" in tipo_suelo:
    factor_dificultad_suelo = 0.90
elif "Escombros" in tipo_suelo:
    factor_dificultad_suelo = 0.75
elif "Roca" in tipo_suelo:
    factor_dificultad_suelo = 0.55

if criterio_medicion == "Volumen Geométrico en Banco (Topografía)":
    with col_v3:
        factor_esponjamiento = st.number_input(
            "Factor Esponjamiento",
            min_value=1.0,
            max_value=1.0,
            value=1.00,
            disabled=True
        )
    volumen_cobrar = volumen_banco
    unidad_medicion = "m³ geométricos (en banco / topografía)"
    texto_control_volumen = (
        "El volumen final será controlado y cubicado estrictamente mediante "
        "levantamiento topográfico de terreno en banco (cota inicial vs. cota final)."
    )
else:
    with col_v3:
        factor_esponjamiento = st.number_input(
            "Factor Esponjamiento",
            min_value=1.01,
            max_value=2.00,
            value=1.20,
            step=0.05
        )
    volumen_cobrar = volumen_banco * factor_esponjamiento
    unidad_medicion = "m³ esponjados (sobre camión)"
    texto_control_volumen = (
        "El volumen final acumulado queda sujeto a control estricto por parte del "
        "mandante mediante la emisión y firma de vales de carga o registro diario "
        "de salida de camiones en obra."
    )

# --- MÓDULO LOGÍSTICO Y CICLO DE CAMIONES ---
st.markdown("#### 🚛 Logística de Transporte y Botadero")
col_l1, col_l2, col_l3 = st.columns(3)
with col_l1:
    distancia_botadero_km = st.number_input("Distancia a Botadero (Km ida/vuelta)", min_value=1.0, value=35.0, step=5.0)
with col_l2:
    capacidad_camion = st.number_input("Capacidad del Camión (m³ tolva)", min_value=10.0, value=15.0, step=1.0)
with col_l3:
    tiempo_ciclo_min = st.number_input("Tiempo Estimado por Ciclo (minutos)", min_value=10, value=90, step=5, help="Tiempo total de carga, ida, descarga y retorno.")

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
    duracion_dias = math.ceil(volumen_cobrar / m3_diarios_est)
    with col_t2:
        st.number_input("Duración Calculada de Faena (días)", value=duracion_dias, disabled=True)
else:
    with col_t2:
        duracion_dias = st.number_input("Días de Faena Impuestos por Mandante", min_value=1, value=5, step=1)
    m3_diarios_est = volumen_cobrar / duracion_dias
    with col_t1:
        st.number_input(f"Rendimiento Requerido ({unidad_medicion}/día)", value=m3_diarios_est, disabled=True)

# Flujo teórico de camiones por día
viajes_totales = math.ceil((volumen_banco * factor_esponjamiento) / capacidad_camion)
viajes_camion_dia = math.ceil(viajes_totales / duracion_dias)
camiones_simultaneos = math.ceil((viajes_camion_dia * (tiempo_ciclo_min / 60)) / 8)

with col_t3:
    st.number_input("Camiones Necesarios en Flota", value=camiones_simultaneos, disabled=True, help="Número recomendado de camiones operando simultáneamente.")

st.info(f"💡 **Rendimiento Ajustado por Suelo:** {m3_diarios_est:,.0f} m³/día | **Flota Estimada:** {camiones_simultaneos} camiones en rotación para cumplir {viajes_camion_dia} viajes/día.".replace(",", "."))

st.markdown("---")

# ---------------------------------------------------------
# OPERACIÓN E IMPUTACIÓN DE COSTOS
# ---------------------------------------------------------
modalidad_ejecucion = st.radio(
    "Modalidad de Operación Interna",
    [
        "Desglosada (Gestión propia de Maquinaria, Petróleo y Transporte)",
        "Subcontrato Completo / Todo Incluido (Tarifa cerrada por m³)"
    ],
    index=1
)

costo_maquinaria = 0.0
costo_combustible = 0.0
costo_transporte = 0.0
costo_paleteros = 0.0
costo_aljibe = 0.0
costo_topografia = 0.0
costo_movilizacion = 0.0
costo_prevencion_epp = 0.0
costo_maquinaria_extra = 0.0
detalles_maq_extra = []

if modalidad_ejecucion == "Subcontrato Completo / Todo Incluido (Tarifa cerrada por m³)":
    costo_subcontrato_m3 = st.number_input(f"Costo del Subcontrato por {unidad_medicion} ($/m³)", min_value=0.0, value=13875.0, step=100.0)
    costo_interno_total = volumen_cobrar * costo_subcontrato_m3
else:
    with st.expander("⚙️ Maquinaria Principal de Excavación y Carga", expanded=True):
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            num_excavadoras = st.number_input("N° Excavadoras", min_value=1, value=1, step=1)
        with col_m2:
            tarifa_excavadora_hr = st.number_input("Tarifa Hora Excavadora ($/hr)", min_value=0.0, value=48000.0, step=1000.0)
        with col_m3:
            precio_petroleo = st.number_input("Precio Petróleo ($/litro)", min_value=0.0, value=1150.0, step=10.0)
        with col_m4:
            consumo_l_hr = st.number_input("Consumo Excavadora (L/hr)", min_value=0.0, value=22.0, step=1.0)

        horas_diarias_est = st.number_input("Horas operativas estimadas por día", min_value=1, value=8, step=1)
        horas_totales_maquinaria = duracion_dias * horas_diarias_est * num_excavadoras
        costo_maquinaria = horas_totales_maquinaria * tarifa_excavadora_hr
        costo_combustible = horas_totales_maquinaria * consumo_l_hr * precio_petroleo

    with st.expander("🛠️ Equipos Adicionales Solicitados", expanded=False):
        incluye_extra = st.checkbox("¿Incluir maquinaria adicional?")
        if incluye_extra:
            num_equipos_extra = st.number_input("Tipos de equipos", min_value=1, max_value=5, value=1, step=1)
            for i in range(num_equipos_extra):
                col_e1, col_e2, col_e3, col_e4 = st.columns([2, 1.5, 1.5, 1.5])
                with col_e1:
                    nombre_eq = st.text_input(f"Equipo #{i+1}", "Retroexcavadora", key=f"eq_custom_{i}")
                with col_e2:
                    modalidad_tarifa = st.selectbox("Unidad", ["Valor por Hora", "Valor Diario"], key=f"eq_mod_{i}")
                with col_e3:
                    tarifa_eq = st.number_input("Tarifa ($)", value=35000.0, step=1000.0, key=f"eq_tar_{i}")
                with col_e4:
                    cant_tiempo = st.number_input("Cantidad", value=duracion_dias * 8, step=1, key=f"eq_cant_{i}")

                subtotal_eq = tarifa_eq * cant_tiempo
                costo_maquinaria_extra += subtotal_eq
                detalles_maq_extra.append({
                    "equipo": nombre_eq,
                    "modalidad": modalidad_tarifa,
                    "cantidad": cant_tiempo,
                    "subtotal": subtotal_eq
                })

    with st.expander("🚚 Traslado Cama Baja, Transporte y Botadero", expanded=True):
        col_tr1, col_tr2 = st.columns(2)
        with col_tr1:
            costo_movilizacion = st.number_input("Cama Baja (Movilización y Desmovilización) ($)", min_value=0.0, value=350000.0, step=25000.0)
        with col_tr2:
            tarifa_transporte_m3 = st.number_input(f"Tarifa transporte + botadero ($/{unidad_medicion})", min_value=0.0, value=3200.0, step=100.0)

        costo_transporte = volumen_cobrar * tarifa_transporte_m3

    with st.expander("🚧 Mitigaciones, Prevención de Riesgos y Topografía"):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            incluye_aljibe = st.checkbox("Camión Aljibe (Polución)")
            num_paleteros = st.number_input("N° Paleteros / Banderilleros", min_value=0, value=0, step=1)
            valor_dia_paletero = st.number_input("Costo diario paletero ($/día)", min_value=0.0, value=35000.0)
        with col_p2:
            costo_prevencion_epp = st.number_input("Gastos EPP y Señalética PR ($)", min_value=0.0, value=120000.0)
            incluye_topografia = st.checkbox("Topógrafo dedicado")
            costo_topografia_global = st.number_input("Costo topografía ($)", min_value=0.0, value=150000.0)

        if incluye_aljibe:
            costo_aljibe = duracion_dias * 120000.0
        if num_paleteros > 0:
            costo_paleteros = num_paleteros * duracion_dias * valor_dia_paletero
        if incluye_topografia:
            costo_topografia = costo_topografia_global

        costo_interno_total = (
            costo_maquinaria + costo_combustible + costo_transporte +
            costo_aljibe + costo_paleteros + costo_topografia +
            costo_movilizacion + costo_prevencion_epp + costo_maquinaria_extra
        )

st.markdown("---")

# ---------------------------------------------------------
# FINANZAS, PÓLIZAS Y FACTORING
# ---------------------------------------------------------
st.subheader("📜 Condiciones Comercial, Garantías y Financiamiento")
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
        costo_poliza = 0.0
        if incluye_poliza:
            costo_poliza = st.number_input("Costo Póliza / Boleta ($)", min_value=0.0, value=180000.0)
    with col_f2:
        incluye_factoring = st.checkbox("¿Aplica Cobro Vía Factoring?")
        costo_factoring = 0.0
        if incluye_factoring:
            tasa_factoring_mensual = st.number_input("Tasa mensual (%)", min_value=0.1, value=2.2)
            dias_anticipo = st.number_input("Días anticipo", min_value=1, value=30)

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
    oferta_total_neto = volumen_cobrar * pu_neto_mandante
elif tipo_oferta == "Definir por porcentaje de margen (%)":
    margen_pct = st.number_input("Margen Deseado (%)", min_value=0.0, value=13.5, step=0.5)
    costo_base = costo_interno_total + costo_poliza
    oferta_total_neto = costo_base / (1.0 - (margen_pct / 100.0)) if margen_pct < 100 else costo_base
    pu_neto_mandante = oferta_total_neto / volumen_cobrar if volumen_cobrar > 0 else 0.0
else:
    oferta_total_neto = st.number_input("Precio Final Neto Objetivo ($)", min_value=0.0, value=45895500.0)
    pu_neto_mandante = oferta_total_neto / volumen_cobrar if volumen_cobrar > 0 else 0.0

if incluye_factoring:
    tasa_diaria = (tasa_factoring_mensual / 100.0) / 30.0
    costo_factoring = oferta_total_neto * (tasa_diaria * dias_anticipo)
    costo_interno_total += costo_poliza + costo_factoring

iva_monto = oferta_total_neto * 0.19
total_bruto = oferta_total_neto + iva_monto
margen_monto = oferta_total_neto - costo_interno_total
margen_porcentaje = (margen_monto / oferta_total_neto * 100.0) if oferta_total_neto > 0 else 0.0

# ---------------------------------------------------------
# RESUMEN ECONÓMICO
# ---------------------------------------------------------
st.subheader("📊 Resumen Económico e Impuestos")
col_r1, col_r2, col_r3 = st.columns(3)
col_r1.metric("Costo Interno Total", f"${costo_interno_total:,.0f}".replace(",", "."))
col_r2.metric("Oferta Total Neto", f"${oferta_total_neto:,.0f}".replace(",", "."), delta=f"Margen: {margen_porcentaje:.1f}%")
col_r3.metric("Total Bruto (incl. IVA)", f"${total_bruto:,.0f}".replace(",", "."))

st.markdown("---")

# ---------------------------------------------------------
# VISTA PREVIA Y CLÁUSULAS
# ---------------------------------------------------------
st.subheader("📋 Vista Previa de la Propuesta Formal")

texto_descripcion_servicio = (
    f"Retiro de aproximadamente {volumen_cobrar:,.0f} m³ de material en terreno tipo '{tipo_suelo}', "
    f"medidos bajo criterio de {unidad_medicion}. El plazo de ejecución es de {duracion_dias} días "
    f"de faena con un retiro diario de {m3_diarios_est:,.0f} m³/día (~{camiones_simultaneos} camiones en rotación). "
    f"Incluye gestión operativa, equipos y transporte a botadero autorizado."
).replace(",", ".")

st.markdown("### PRESUPUESTO DE SERVICIO DE RETIRO Y MOVIMIENTO DE TIERRAS")
st.markdown(f"- **Para:** {cliente_nombre}")
st.markdown("- **De:** EDOS SpA")
st.markdown(f"- **Ubicación:** {ubicacion_obra}")
st.markdown(f"- **Plazo de Ejecución:** {duracion_dias} días de faena")
st.markdown(f"- **Validez de la Oferta:** {validez_oferta} días corridos")

st.table([{
    "Descripción": f"Servicio de retiro / excavación ({unidad_medicion})",
    "Cantidad Estimada": f"{volumen_cobrar:,.0f} m³".replace(",", "."),
    "P. Unitario Neto": f"${pu_neto_mandante:,.0f} / m³".replace(",", "."),
    "Total Neto Estimado": f"${oferta_total_neto:,.0f}".replace(",", ".")
}])

st.markdown("#### Condiciones Comerciales y Legales")
st.markdown(f"- **Forma de Pago:** {condicion_pago}.")
st.markdown(f"- **Control de Volumen:** {texto_control_volumen}")
st.markdown(f"- **Mínimo Diario Garantizado:** Se establece un mínimo de {minimo_horas} horas/día por equipo contratado.")
st.markdown("- **Stand-by por Clima o Paralización Imputable:** En caso de paralización de la obra por causas ajenas a EDOS SpA o eventos meteorológicos, se facturará la tarifa de stand-by correspondiente al mínimo diario garantizado de los equipos en obra.")

st.caption(f"*{representante_edos} - EDOS SpA*")

# ---------------------------------------------------------
# GENERADOR DE CORREO RÁPIDO
# ---------------------------------------------------------
with st.expander("✉️ Generar Texto para Correo Electrónico"):
    cuerpo_email = f"""Estimados {cliente_nombre},

Junto con saludar, adjunto la propuesta comercial de EDOS SpA para el servicio de retiro de escombros y movimiento de tierras en la obra ubicada en {ubicacion_obra}.

Resumen de la Oferta:
- Volumen Estimado: {volumen_cobrar:,.0f} {unidad_medicion}
- Plazo de Ejecución: {duracion_dias} días de faena
- Precio Unitario Neto: ${pu_neto_mandante:,.0f} / m³
- Total Neto Estimado: ${oferta_total_neto:,.0f} + IVA

Condiciones Principales:
- Forma de Pago: {condicion_pago}
- Validez de la propuesta: {validez_oferta} días.

Quedamos atentos a sus comentarios para coordinar inicio de faenas.

Atentamente,
{representante_edos}
EDOS SpA
""".replace(",", ".")

    st.text_area("Copiar cuerpo del correo:", cuerpo_email, height=280)

# ---------------------------------------------------------
# EXPORTACIÓN PDF CON FPDF
# ---------------------------------------------------------
def limpiar_texto(texto):
    reemplazos = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U",
        "ñ": "n", "Ñ": "N", "°": ".", "º": "."
    }
    for original, reemplazo in reemplazos.items():
        texto = texto.replace(original, reemplazo)
    return texto.encode("latin-1", "replace").decode("latin-1")

def generar_pdf():
    pdf = FPDF("P", "mm", "A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Encabezado
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, limpiar_texto("EDOS SpA - GEOMENSURA Y MOVIMIENTO DE TIERRAS"), 0, 1, "C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, limpiar_texto("Propuesta Técnica y Comercial"), 0, 1, "C")
    pdf.ln(5)

    # Datos Generales
    pdf.set_font("Arial", "B", 10)
    pdf.cell(35, 6, limpiar_texto("Cliente:"), 0, 0)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, limpiar_texto(cliente_nombre), 0, 1)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(35, 6, limpiar_texto("Ubicación:"), 0, 0)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, limpiar_texto(ubicacion_obra), 0, 1)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(35, 6, limpiar_texto("Representante:"), 0, 0)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, limpiar_texto(representante_edos), 0, 1)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(35, 6, limpiar_texto("Plazo Faena:"), 0, 0)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, limpiar_texto(f"{duracion_dias} días corridos/hábiles"), 0, 1)

    pdf.set_font("Arial", "B", 10)
    pdf.cell(35, 6, limpiar_texto("Validez Oferta:"), 0, 0)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, limpiar_texto(f"{validez_oferta} días"), 0, 1)
    pdf.ln(5)

    # Alcance del Servicio
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 6, limpiar_texto("1. Descripción del Servicio"), 0, 1)
    pdf.set_font("Arial", "", 9)
    pdf.multi_cell(0, 5, limpiar_texto(texto_descripcion_servicio))
    pdf.ln(4)

    # Cuadro Económico
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 6, limpiar_texto("2. Resumen Económico"), 0, 1)

    pdf.set_font("Arial", "B", 9)
    pdf.cell(100, 6, limpiar_texto("Item / Concepto"), 1, 0, "C")
    pdf.cell(30, 6, limpiar_texto("Cantidad"), 1, 0, "C")
    pdf.cell(30, 6, limpiar_texto("P. Unitario"), 1, 0, "C")
    pdf.cell(30, 6, limpiar_texto("Total Neto"), 1, 1, "C")

    pdf.set_font("Arial", "", 9)
    pdf.cell(100, 6, limpiar_texto(f"Retiro de Material ({unidad_medicion})"), 1, 0)
    pdf.cell(30, 6, limpiar_texto(f"{volumen_cobrar:,.0f} m³".replace(",", ".")), 1, 0, "C")
    pdf.cell(30, 6, limpiar_texto(f"${pu_neto_mandante:,.0f}".replace(",", ".")), 1, 0, "R")
    pdf.cell(30, 6, limpiar_texto(f"${oferta_total_neto:,.0f}".replace(",", ".")), 1, 1, "R")

    # Totales
    pdf.cell(160, 6, limpiar_texto("Subtotal Neto"), 1, 0, "R")
    pdf.cell(30, 6, limpiar_texto(f"${oferta_total_neto:,.0f}".replace(",", ".")), 1, 1, "R")
    pdf.cell(160, 6, limpiar_texto("IVA (19%)"), 1, 0, "R")
    pdf.cell(30, 6, limpiar_texto(f"${iva_monto:,.0f}".replace(",", ".")), 1, 1, "R")
    pdf.set_font("Arial", "B", 9)
    pdf.cell(160, 6, limpiar_texto("Total Bruto"), 1, 0, "R")
    pdf.cell(30, 6, limpiar_texto(f"${total_bruto:,.0f}".replace(",", ".")), 1, 1, "R")
    pdf.ln(6)

    # Condiciones Comerciales y Cláusulas
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 6, limpiar_texto("3. Condiciones Comerciales y Operativas"), 0, 1)

    pdf.set_font("Arial", "", 8)
    pdf.multi_cell(0, 4, limpiar_texto(f"- Forma de Pago: {condicion_pago}."))
    pdf.multi_cell(0, 4, limpiar_texto(f"- Control de Volumen: {texto_control_volumen}"))
    pdf.multi_cell(0, 4, limpiar_texto(f"- Mínimo Garantizado: {minimo_horas} horas/día por equipo operando en terreno."))
    pdf.multi_cell(0, 4, limpiar_texto("- Paralizaciones / Stand-by: Cualquier paralización no imputable a EDOS SpA será facturada a razón del mínimo diario garantizado."))
    pdf.ln(15)

    # Firma
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 5, limpiar_texto("__________________________________________"), 0, 1, "C")
    pdf.cell(0, 5, limpiar_texto(f"{representante_edos}"), 0, 1, "C")
    pdf.cell(0, 5, limpiar_texto("Representante Legal / EDOS SpA"), 0, 1, "C")

    return bytes(pdf.output())

# Botón para descargar el PDF generado
st.download_button(
    label="📄 Descargar Presupuesto Formal (PDF)",
    data=generar_pdf(),
    file_name=f"Presupuesto_EDOS_{cliente_nombre.replace(' ', '_')}.pdf",
    mime="application/pdf"
)
