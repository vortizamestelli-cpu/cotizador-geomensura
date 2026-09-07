import json
import math
from fpdf import FPDF
import streamlit as st

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Cotizador EDOS SpA", page_icon="🚜", layout="wide"
)

st.title("🚜 EDOS SpA - Generador de Presupuestos")
st.caption(
    "Cálculo operativo, tarifa por m³, condiciones comerciales y propuesta"
    " formal."
)
st.markdown("---")

# ---------------------------------------------------------
# DATOS DE LA OBRA Y MANDANTE
# ---------------------------------------------------------
st.subheader("📄 Datos del Mandante y Ubicación")
col_m1, col_m2 = st.columns(2)
with col_m1:
  cliente_nombre = st.text_input(
      "Para (Cliente / Constructora)", "Constructora Minimal"
  )
with col_m2:
  ubicacion_obra = st.text_input(
      "Ubicación de la Obra", "Avenida El Salto 2255, Recoleta"
  )

st.markdown("---")

# ---------------------------------------------------------
# 1. PARÁMETROS GENERALES, CUBICACIÓN Y TIEMPOS
# ---------------------------------------------------------
st.subheader("1. Parámetros Generales, Cubicaciones y Tiempos")

criterio_medicion = st.radio(
    "Criterio / Base de Medición de Volumen",
    [
        "Volumen Geométrico en Banco (Topografía)",
        "Volumen Esponjado (Sobre Camión)",
    ],
    index=0,
)

col_v1, col_v2 = st.columns(2)

with col_v1:
  volumen_banco = st.number_input(
      "Volumen Geométrico en Banco (m³)",
      min_value=1.0,
      value=2914.00,
      step=10.0,
  )

if criterio_medicion == "Volumen Geométrico en Banco (Topografía)":
  with col_v2:
    factor_esponjamiento = st.number_input(
        "Factor de Esponjamiento",
        min_value=1.0,
        max_value=1.0,
        value=1.00,
        disabled=True,
    )

  volumen_cobrar = volumen_banco
  unidad_medicion = "m³ geométricos (en banco / topografía)"
  texto_esponjamiento_nota = (
      "Cobro en base a volumen geométrico medido mediante topografía en banco"
      " (Factor 1.00)."
  )
  texto_control_volumen = (
      "El volumen final será controlado y cubicado strictly mediante"
      " levantamiento topográfico de terreno en banco (cota inicial vs. cota"
      " final)."
  )

else:
  with col_v2:
    factor_esponjamiento = st.number_input(
        "Factor de Esponjamiento",
        min_value=1.01,
        max_value=2.00,
        value=1.20,
        step=0.05,
    )

  volumen_cobrar = volumen_banco * factor_esponjamiento
  unidad_medicion = "m³ esponjados (sobre camión)"
  texto_esponjamiento_nota = (
      f"Cobro en base a volumen esponjado sobre camión (Factor"
      f" {factor_esponjamiento:.2f} -> {volumen_cobrar:,.0f} m³ a"
      " cobrar).".replace(",", ".")
  )
  texto_control_volumen = (
      "El volumen final acumulado queda sujeto a control estricto por parte del"
      " mandante mediante la emisión y firma de vales de carga o registro diario"
      " de control de salida de camiones en obra."
  )

st.markdown("#### ⏱️ Planificación de Tiempos y Rendimientos")

modo_tiempo = st.radio(
    "Definición de Plazo de Ejecución",
    [
        "Calcular días según rendimiento estimado (m³/día)",
        "Fijar días de faena impuestos por el Mandante (recalcula m³/día necesarios)",
    ],
    index=0,
)

col_t1, col_t2, col_t3 = st.columns(3)

if modo_tiempo == "Calcular días según rendimiento estimado (m³/día)":
  with col_t1:
    m3_diarios_est = st.number_input(
        f"Rendimiento Estimado ({unidad_medicion}/día)",
        min_value=10.0,
        value=350.0,
        step=25.0,
    )
  duracion_dias = math.ceil(volumen_cobrar / m3_diarios_est)
  with col_t2:
    st.number_input(
        "Duración Calculada de Faena (días)", value=duracion_dias, disabled=True
    )
else:
  with col_t2:
    duracion_dias = st.number_input(
        "Días de Faena Impuestos por Mandante", min_value=1, value=5, step=1
    )
  m3_diarios_est = volumen_cobrar / duracion_dias
  with col_t1:
    st.number_input(
        f"Rendimiento Requerido ({unidad_medicion}/día)",
        value=m3_diarios_est,
        disabled=True,
    )

capacidad_camion = 15.0
viajes_camion_dia = math.ceil(
    (volumen_banco * factor_esponjamiento) / (duracion_dias * capacidad_camion)
)

with col_t3:
  st.number_input(
      "Flujo Estimado de Camiones (viajes/día)",
      value=viajes_camion_dia,
      disabled=True,
  )

st.info(
    f"💡 **Criterio Seleccionado:** {texto_esponjamiento_nota} | **Planificación:**"
    f" {duracion_dias} días de faena requerirán un retiro diario de"
    f" **{m3_diarios_est:,.0f} m³/día** (~**{viajes_camion_dia} viajes de"
    " camión/día**).".replace(",", ".")
)

st.markdown("---")

# ---------------------------------------------------------
# MODALIDAD DE OPERACIÓN E IMPUTACIÓN DE COSTOS
# ---------------------------------------------------------
modalidad_ejecucion = st.radio(
    "Modalidad de Operación Interna",
    [
        "Desglosada (Gestión propia de Maquinaria, Petróleo y Transporte)",
        "Subcontrato Completo / Todo Incluido (Tarifa cerrada por m³)",
    ],
    index=1,
)

costo_maquinaria = 0.0
costo_combustible = 0.0
costo_transporte = 0.0
costo_paleteros = 0.0
costo_aljibe = 0.0
costo_topografia = 0.0
costo_maquinaria_extra = 0.0
detalles_maq_extra = []

if (
    modalidad_ejecucion
    == "Subcontrato Completo / Todo Incluido (Tarifa cerrada por m³)"
):
  costo_subcontrato_m3 = st.number_input(
      f"Costo del Subcontrato por {unidad_medicion} ($/m³)",
      min_value=0.0,
      value=13875.0,
      step=100.0,
  )
  costo_interno_total = volumen_cobrar * costo_subcontrato_m3

else:
  with st.expander("⚙️ Maquinaria Principal de Excavación y Carga", expanded=True):
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
      num_excavadoras = st.number_input(
          "N° Excavadoras", min_value=1, value=1, step=1
      )
    with col_m2:
      tarifa_excavadora_hr = st.number_input(
          "Tarifa Hora Excavadora ($/hr)",
          min_value=0.0,
          value=48000.0,
          step=1000.0,
      )
    with col_m3:
      precio_petroleo = st.number_input(
          "Precio Petróleo ($/litro)", min_value=0.0, value=1150.0, step=10.0
      )
    with col_m4:
      consumo_l_hr = st.number_input(
          "Consumo Excavadora (L/hr)", min_value=0.0, value=22.0, step=1.0
      )

    horas_diarias_est = st.number_input(
        "Horas operativas estimadas por día", min_value=1, value=8, step=1
    )

    horas_totales_maquinaria = (
        duracion_dias * horas_diarias_est * num_excavadoras
    )
    costo_maquinaria = horas_totales_maquinaria * tarifa_excavadora_hr
    costo_combustible = horas_totales_maquinaria * consumo_l_hr * precio_petroleo

  # --- SECCIÓN NUEVA: MAQUINARIA ADICIONAL / SOLICITADA POR MANDANTE ---
  with st.expander("🛠️ Maquinaria y Equipos Adicionales (Opcional / Requeridos)", expanded=False):
    st.caption("Agrega equipos solicitados expresamente por la obra (Retroexcavadora, Minicargador, Motoniveladora, Camión Interno, etc.)")
    
    incluye_extra = st.checkbox("¿Incluir maquinaria o equipos adicionales?")
    if incluye_extra:
      num_equipos_extra = st.number_input("Cantidad de tipos de equipos a agregar", min_value=1, max_value=5, value=1, step=1)
      
      for i in range(num_equipos_extra):
        st.markdown(f"**Equipo Extra N° {i+1}**")
        col_e1, col_e2, col_e3, col_e4, col_e5 = st.columns([2, 1.5, 1.5, 1.5, 1.5])
        
        with col_e1:
          nombre_eq = st.selectbox(
              f"Tipo de Equipo #{i+1}",
              ["Retroexcavadora", "Minicargador (Bobcat)", "Camión Tolva Interno", "Motoniveladora", "Rodillo Compactador", "Otro"],
              key=f"eq_nom_{i}"
          )
          if nombre_eq == "Otro":
            nombre_eq = st.text_input(f"Especificar equipo #{i+1}", "Equipo Especial", key=f"eq_custom_{i}")
            
        with col_e2:
          modalidad_tarifa = st.selectbox("Modalidad Cobro", ["Valor por Hora", "Valor Diario"], key=f"eq_mod_{i}")
          
        with col_e3:
          incluye_combustible = st.selectbox("Petróleo / Combustible", ["Incluido (Seco)", "No Incluido (Suma Petróleo)"], key=f"eq_pet_{i}")
          
        with col_e4:
          tarifa_eq = st.number_input(f"Tarifa ({modalidad_tarifa.split()[-1]}) ($)", min_value=0.0, value=35000.0 if "Hora" in modalidad_tarifa else 250000.0, step=5000.0, key=f"eq_tar_{i}")
          
        with col_e5:
          cant_tiempo = st.number_input(f"Cantidad ({'Horas Totales' if 'Hora' in modalidad_tarifa else 'Días Totales'})", min_value=1, value=duracion_dias * 8 if "Hora" in modalidad_tarifa else duracion_dias, step=1, key=f"eq_cant_{i}")

        subtotal_eq = tarifa_eq * cant_tiempo
        costo_petroleo_eq = 0.0

        if incluye_combustible == "No Incluido (Suma Petróleo)":
          col_p1, col_p2 = st.columns(2)
          with col_p1:
            consumo_eq_l = st.number_input(f"Consumo Estimado L/{'hr' if 'Hora' in modalidad_tarifa else 'día'}", min_value=0.0, value=12.0, step=1.0, key=f"eq_con_{i}")
          with col_p2:
            costo_petroleo_eq = consumo_eq_l * cant_tiempo * precio_petroleo
            st.caption(f"Costo Petróleo Adicional: ${costo_petroleo_eq:,.0f} CLP".replace(",", "."))

        subtotal_total_eq = subtotal_eq + costo_petroleo_eq
        costo_maquinaria_extra += subtotal_total_eq
        
        detalles_maq_extra.append({
            "equipo": nombre_eq,
            "modalidad": modalidad_tarifa,
            "combustible": incluye_combustible,
            "cantidad": cant_tiempo,
            "subtotal": subtotal_total_eq
        })
        st.divider()

  with st.expander("🚛 Transporte y Botadero", expanded=True):
    tarifa_transporte_m3 = st.number_input(
        f"Tarifa transporte + botadero autorizado ($/{unidad_medicion})",
        min_value=0.0,
        value=3200.0,
        step=100.0,
    )
    costo_transporte = volumen_cobrar * tarifa_transporte_m3

  with st.expander("🚧 Mitigaciones, Personal y Topografía"):
    col_p1, col_p2 = st.columns(2)
    with col_p1:
      incluye_aljibe = st.checkbox("Incluir Camión Aljibe (Polución)")
      num_paleteros = st.number_input(
          "N° Paleteros / Banderilleros", min_value=0, value=0, step=1
      )
      valor_dia_paletero = st.number_input(
          "Costo diario por paletero ($/día)",
          min_value=0.0,
          value=35000.0,
          step=1000.0,
      )
    with col_p2:
      incluye_topografia = st.checkbox("Incluir Topógrafo dedicado")
      costo_topografia_global = st.number_input(
          "Costo global de topografía ($)",
          min_value=0.0,
          value=150000.0,
          step=10000.0,
      )

    if incluye_aljibe:
      costo_aljibe = duracion_dias * 120000.0
    if num_paleteros > 0:
      costo_paleteros = num_paleteros * duracion_dias * valor_dia_paletero
    if incluye_topografia:
      costo_topografia = costo_topografia_global

  costo_interno_total = (
      costo_maquinaria
      + costo_combustible
      + costo_transporte
      + costo_aljibe
      + costo_paleteros
      + costo_topografia
      + costo_maquinaria_extra
  )

st.markdown("---")

# ---------------------------------------------------------
# CONDICIONES COMERCIALES
# ---------------------------------------------------------
st.subheader("📜 Condiciones Comerciales y Legales")
col_c1, col_c2, col_c3 = st.columns(3)
with col_c1:
  validez_oferta = st.number_input(
      "Validez de la Oferta (días)", min_value=1, value=15
  )
with col_c2:
  minimo_horas = st.number_input(
      "Mínimo de Horas Diarias Garantizadas", min_value=1, value=8
  )
with col_c3:
  condicion_pago = st.text_input(
      "Condición de Pago", "50% Anticipo - 50% al finalizar"
  )

st.markdown("---")

# ---------------------------------------------------------
# OFERTA COMERCIAL AL MANDANTE
# ---------------------------------------------------------
st.subheader("7. Oferta Comercial al Mandante")

tipo_oferta = st.radio(
    "¿Cómo deseas definir la oferta?",
    [
        "Ingresar Precio Unitario Neto al Mandante ($/m³)",
        "Definir por porcentaje de margen (%)",
        "Ingresar Precio Final Neto Objetivo ($)",
    ],
)

if tipo_oferta == "Ingresar Precio Unitario Neto al Mandante ($/m³)":
  pu_neto_mandante = st.number_input(
      f"Precio Unitario Final Neto ($/{unidad_medicion})",
      min_value=0.0,
      value=15750.0,
      step=250.0,
  )
  oferta_total_neto = volumen_cobrar * pu_neto_mandante

elif tipo_oferta == "Definir por porcentaje de margen (%)":
  margen_pct = st.number_input(
      "Porcentaje de Margen Deseado (%)", min_value=0.0, value=13.5, step=0.5
  )
  if margen_pct < 100.0:
    oferta_total_neto = costo_interno_total / (1.0 - (margen_pct / 100.0))
  else:
    oferta_total_neto = costo_interno_total
  pu_neto_mandante = (
      oferta_total_neto / volumen_cobrar if volumen_cobrar > 0 else 0.0
  )

else:
  oferta_total_neto = st.number_input(
      "Precio Final Neto Objetivo ($)",
      min_value=0.0,
      value=45895500.0,
      step=100000.0,
  )
  pu_neto_mandante = (
      oferta_total_neto / volumen_cobrar if volumen_cobrar > 0 else 0.0
  )

# Cálculos Impuestos y Margen
iva_monto = oferta_total_neto * 0.19
total_bruto = oferta_total_neto + iva_monto
margen_monto = oferta_total_neto - costo_interno_total
margen_porcentaje = (
    (margen_monto / oferta_total_neto * 100.0) if oferta_total_neto > 0 else 0.0
)

st.markdown("---")

# ---------------------------------------------------------
# RESUMEN ECONÓMICO
# ---------------------------------------------------------
st.subheader("📊 Resumen Económico e Impuestos")
col_r1, col_r2, col_r3 = st.columns(3)

col_r1.metric(
    "Costo Interno (Ejecución)",
    f"${costo_interno_total:,.0f}".replace(",", "."),
)
col_r2.metric(
    "Oferta Total Neto",
    f"${oferta_total_neto:,.0f}".replace(",", "."),
    delta=f"Margen: {margen_porcentaje:.1f}%",
)
col_r3.metric("Total Bruto (incl. IVA)", f"${total_bruto:,.0f}".replace(",", "."))

st.info(
    f"💡 **Precio Unitario Neto:** ${pu_neto_mandante:,.0f} / m³ | **IVA"
    f" (19%):** ${iva_monto:,.0f} CLP".replace(",", ".")
)

st.markdown("---")

# ---------------------------------------------------------
# VISTA PREVIA
# ---------------------------------------------------------
st.subheader("📋 Vista Previa de la Propuesta Formal")

texto_descripcion_servicio = (
    f"Retiro de aproximadamente {volumen_cobrar:,.0f} m³ de material,"
    f" medidos bajo criterio de {unidad_medicion}. El tiempo de ejecución"
    f" acordado es de {duracion_dias} días corridos, lo que exige un rendimiento"
    f" medio de {m3_diarios_est:,.0f} m³/día (flujo estimado de"
    f" {viajes_camion_dia} viajes de camión/día). Incluye gestión operativa,"
    " maquinaria y transporte a botadero autorizado."
).replace(",", ".")

st.markdown("### PRESUPUESTO DE SERVICIO DE RETIRO Y MOVIMIENTO DE TIERRAS")
st.markdown(f"- **Para:** {cliente_nombre}")
st.markdown("- **De:** EDOS SpA")
st.markdown(f"- **Ubicación:** {ubicacion_obra}")
st.markdown(f"- **Plazo de Ejecución:** {duracion_dias} días de faena")
st.markdown(f"- **Validez de la Oferta:** {validez_oferta} días corridos")

st.markdown("#### 1. Detalle del Servicio y Valores")
st.write(texto_descripcion_servicio)

tabla_detalle = [{
    "Descripción": f"Servicio completo de retiro / excavación ({unidad_medicion})",
    "Cantidad Estimada": f"{volumen_cobrar:,.0f} m³".replace(",", "."),
    "P. Unitario Neto": f"${pu_neto_mandante:,.0f} / m³".replace(",", "."),
    "Total Neto Estimado": f"${oferta_total_neto:,.0f}".replace(",", "."),
}]

st.table(tabla_detalle)

if detalles_maq_extra:
  st.markdown("##### 🛠️ Equipamiento Adicional Solicitado")
  st.table(detalles_maq_extra)

st.markdown(
    f"* **Subtotal neto:** ${oferta_total_neto:,.0f} CLP".replace(",", ".")
)
st.markdown(f"* **IVA (19%):** ${iva_monto:,.0f} CLP".replace(",", "."))
st.markdown(f"* **Bruto total:** ${total_bruto:,.0f} CLP".replace(",", "."))

st.markdown("#### 2. Condiciones de Pago y Ajuste")
st.markdown(f"- **Forma de Pago:** {condicion_pago}.")
st.markdown(f"- **Control de Volumen:** {texto_control_volumen}")
st.markdown(
    "- **Stand-by / Mínimo Diario:** Se establece un mínimo de"
    f" {minimo_horas} horas diarias garantizadas por equipo contratado."
)

st.caption("*Vicente Ortiz Amestelli - EDOS SpA*")


# ---------------------------------------------------------
# GENERACIÓN DE PDF Y JSON
# ---------------------------------------------------------
class PDFPresupuesto(FPDF):

  def __init__(self):
    super().__init__(orientation="P", unit="mm", format="A4")

  def header(self):
    self.set_font("Arial", "B", 12)
    self.cell(
        0,
        7,
        "EDOS SpA - Servicios de Geomensura y Movimiento de Tierras",
        0,
        1,
        "C",
    )
    self.set_font("Arial", "I", 8)
    self.cell(0, 4, "Propuesta Tecnica y Comercial", 0, 1, "C")
    self.line(10, 21, 200, 21)
    self.ln(4)

  def footer(self):
    self.set_y(-15)
    self.set_font("Arial", "I", 8)
    self.cell(0, 10, f"Pagina {self.page_no()}", 0, 0, "C")


def clean_text(texto):
  replacements = {
      "á": "a",
      "é": "e",
      "í": "i",
      "ó": "o",
      "ú": "u",
      "Á": "A",
      "É": "E",
      "Í": "I",
      "Ó": "O",
      "Ú": "U",
      "ñ": "n",
      "Ñ": "N",
      "³": "3",
      "°": ".",
  }
  for orig, repl in replacements.items():
    texto = texto.replace(orig, repl)
  return texto.encode("latin-1", "replace").decode("latin-1")


def generar_pdf():
  pdf = PDFPresupuesto()
  pdf.add_page()
  pdf.set_auto_page_break(auto=True, margin=15)

  pdf.set_font("Arial", "B", 11)
  pdf.cell(0, 6, "PRESUPUESTO DE RETIRO Y MOVIMIENTO DE TIERRAS", 0, 1, "L")
  pdf.ln(2)

  pdf.set_font("Arial", "", 9)
  pdf.cell(0, 5, clean_text(f"Para: {cliente_nombre}"), 0, 1)
  pdf.cell(0, 5, "De: EDOS SpA", 0, 1)
  pdf.cell(0, 5, clean_text(f"Ubicacion: {ubicacion_obra}"), 0, 1)
  pdf.cell(
      0, 5, clean_text(f"Plazo Acordado: {duracion_dias} dias de faena"), 0, 1
  )
  pdf.cell(0, 5, f"Validez de la Oferta: {validez_oferta} dias corridos", 0, 1)
  pdf.ln(3)

  pdf.set_font("Arial", "B", 10)
  pdf.cell(0, 6, "1. Detalle del Servicio y Valores", 0, 1)
  pdf.set_font("Arial", "", 8)
  pdf.multi_cell(0, 4, clean_text(texto_descripcion_servicio))
  pdf.ln(2)

  pdf.set_font("Arial", "B", 8)
  pdf.cell(80, 6, "Descripcion", 1, 0, "C")
  pdf.cell(30, 6, "Cantidad", 1, 0, "C")
  pdf.cell(40, 6, "P. Unitario Neto", 1, 0, "C")
  pdf.cell(40, 6, "Total Neto", 1, 1, "C")

  pdf.set_font("Arial", "", 8)
  pdf.cell(80, 6, "Servicio completo de retiro / excavacion", 1, 0, "L")
  pdf.cell(30, 6, clean_text(f"{volumen_cobrar:,.0f} m3".replace(",", ".")), 1, 0, "C")
  pdf.cell(
      40,
      6,
      clean_text(f"${pu_neto_mandante:,.0f} / m3".replace(",", ".")),
      1,
      0,
      "R",
  )
  pdf.cell(
      40, 6, clean_text(f"${oferta_total_neto:,.0f}".replace(",", ".")), 1, 1, "R"
  )
  pdf.ln(3)

  if detalles_maq_extra:
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 5, "Equipamiento Adicional Solicitado:", 0, 1)
    pdf.set_font("Arial", "", 8)
    for eq in detalles_maq_extra:
      pdf.cell(
          0,
          4,
          clean_text(
              f"- {eq['equipo']} ({eq['modalidad']}): {eq['cantidad']}"
              f" unidades/horas - {eq['combustible']}"
          ),
          0,
          1,
      )
    pdf.ln(3)

  pdf.set_font("Arial", "", 9)
  pdf.cell(110, 5, "", 0, 0)
  pdf.cell(40, 5, "Subtotal Neto:", 0, 0, "R")
  pdf.cell(
      40,
      5,
      clean_text(f"${oferta_total_neto:,.0f} CLP".replace(",", ".")),
      0,
      1,
      "R",
  )

  pdf.cell(110, 5, "", 0, 0)
  pdf.cell(40, 5, "IVA (19%):", 0, 0, "R")
  pdf.cell(
      40, 5, clean_text(f"${iva_monto:,.0f} CLP".replace(",", ".")), 0, 1, "R"
  )

  pdf.set_font("Arial", "B", 9)
  pdf.cell(110, 5, "", 0, 0)
  pdf.cell(40, 5, "Total Bruto:", 0, 0, "R")
  pdf.cell(
      40, 5, clean_text(f"${total_bruto:,.0f} CLP".replace(",", ".")), 0, 1, "R"
  )
  pdf.ln(4)

  pdf.set_font("Arial", "B", 10)
  pdf.cell(0, 6, "2. Condiciones de Pago y Ajuste", 0, 1)
  pdf.set_font("Arial", "", 8)
  pdf.cell(0, 4, clean_text(f"- Forma de Pago: {condicion_pago}."), 0, 1)
  pdf.multi_cell(0, 4, clean_text(f"- Control de Volumen: {texto_control_volumen}"))
  pdf.cell(
      0,
      4,
      clean_text(
          f"- Stand-by / Minimo Diario: {minimo_horas} horas diarias"
          " garantizadas por equipo."
      ),
      0,
      1,
  )
  pdf.ln(8)

  pdf.set_font("Arial", "B", 9)
  pdf.cell(0, 5, "Vicente Ortiz Amestelli", 0, 1, "R")
  pdf.set_font("Arial", "", 8)
  pdf.cell(0, 4, "EDOS SpA", 0, 1, "R")

  pdf_output = pdf.output()
  if isinstance(pdf_output, str):
    return pdf_output.encode("latin-1", "replace")
  return bytes(pdf_output)


col_bot1, col_bot2 = st.columns(2)

with col_bot1:
  pdf_bytes = generar_pdf()
  st.download_button(
      label="📄 Descargar Presupuesto PDF",
      data=pdf_bytes,
      file_name=f"Presupuesto_EDOS_{cliente_nombre.replace(' ', '_')}.pdf",
      mime="application/pdf",
  )

with col_bot2:
  datos_json = {
      "cliente": cliente_nombre,
      "ubicacion": ubicacion_obra,
      "criterio_medicion": criterio_medicion,
      "volumen_banco": volumen_banco,
      "factor_esponjamiento": factor_esponjamiento,
      "volumen_cobrar": volumen_cobrar,
      "modo_tiempo": modo_tiempo,
      "m3_diarios_est": m3_diarios_est,
      "duracion_dias_faena": duracion_dias,
      "viajes_camion_dia_est": viajes_camion_dia,
      "costo_interno_total": costo_interno_total,
      "pu_neto_mandante": pu_neto_mandante,
      "oferta_total_neto": oferta_total_neto,
      "total_bruto": total_bruto,
      "equipos_adicionales": detalles_maq_extra,
  }
  st.download_button(
      label="💾 Guardar parámetros (JSON)",
      data=json.dumps(datos_json, indent=4),
      file_name="parametros_cotizacion.json",
      mime="application/json",
  )
