import json
import math
from fpdf import FPDF
import streamlit as st

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Cotizador Profesional EDOS SpA", page_icon="🚜", layout="wide"
)

st.title("🚜 EDOS SpA - Generador Integral de Presupuestos")
st.caption(
    "Plataforma técnica-comercial para movimiento de tierras, geomensura y"
    " obras civiles."
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
# 1. CUBICACIÓN, SUELO Y LOGÍSTICA
# ---------------------------------------------------------
st.subheader("1. Cubicaciones, Caracterización de Suelo y Logística")

criterio_medicion = st.radio(
    "Criterio / Base de Medición de Volumen",
    [
        "Volumen Geométrico en Banco (Topografía)",
        "Volumen Esponjado (Sobre Camión)",
    ],
    index=0,
)

col_v1, col_v2, col_v3 = st.columns(3)

with col_v1:
  volumen_banco = st.number_input(
      "Volumen Geométrico en Banco (m³)",
      min_value=1.0,
      value=2914.00,
      step=10.0,
  )

with col_v2:
  tipo_suelo = st.selectbox(
      "Clasificación del Terreno",
      [
          "Tierra Común / Limos (Dificultad Normal)",
          "Maicillo / Arcilla Densa (Dificultad Media)",
          "Escombros Masivos / Hormigón Armado (Alta Dificultad)",
          "Roca / Terreno Semi-Rocoso (Requiere Martillo/Insumos)",
      ],
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
        disabled=True,
    )
  volumen_cobrar = volumen_banco
  unidad_medicion = "m³ geométricos (en banco / topografía)"
  texto_control_volumen = (
      "El volumen final será controlado y cubicado estrictamente mediante"
      " levantamiento topográfico de terreno en banco (cota inicial vs. cota"
      " final)."
  )
else:
  with col_v3:
    factor_esponjamiento = st.number_input(
        "Factor Esponjamiento",
        min_value=1.01,
        max_value=2.00,
        value=1.20,
        step=0.05,
    )
  volumen_cobrar = volumen_banco * factor_esponjamiento
  unidad_medicion = "m³ esponjados (sobre camión)"
  texto_control_volumen = (
      "El volumen final acumulado queda sujeto a control estricto por parte del"
      " mandante mediante la emisión y firma de vales de carga o registro diario"
      " de salida de camiones en obra."
  )

# --- MÓDULO LOGÍSTICO Y CICLO DE CAMIONES ---
st.markdown("#### 🚛 Logística de Transporte y Botadero")
col_l1, col_l2, col_l3 = st.columns(3)
with col_l1:
  distancia_botadero_km = st.number_input(
      "Distancia a Botadero (Km ida/vuelta)",
      min_value=1.0,
      value=35.0,
      step=5.0,
  )
with col_l2:
  capacidad_camion = st.number_input(
      "Capacidad del Camión (m³ tolva)", min_value=10.0, value=15.0, step=1.0
  )
with col_l3:
  tiempo_ciclo_min = st.number_input(
      "Tiempo Estimado por Ciclo (minutos)",
      min_value=10,
      value=90,
      step=5,
      help="Tiempo total de carga, ida, descarga y retorno.",
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
    rendimiento_base = st.number_input(
        f"Rendimiento Base ({unidad_medicion}/día)",
        min_value=10.0,
        value=350.0,
        step=25.0,
    )
  m3_diarios_est = rendimiento_base * factor_dificultad_suelo
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

# Flujo teórico de camiones por día
viajes_totales = math.ceil(
    (volumen_banco * factor_esponjamiento) / capacidad_camion
)
viajes_camion_dia = math.ceil(viajes_totales / duracion_dias)
camiones_simultaneos = math.ceil(
    (viajes_camion_dia * (tiempo_ciclo_min / 60)) / 8
)

with col_t3:
  st.number_input(
      "Camiones Necesarios en Flota",
      value=camiones_simultaneos,
      disabled=True,
      help="Número recomendado de camiones operando simultáneamente.",
  )

st.info(
    f"💡 **Rendimiento Ajustado por Suelo:** {m3_diarios_est:,.0f} m³/día |"
    f" **Flota Estimada:** {camiones_simultaneos} camiones en rotación para"
    f" cumplir {viajes_camion_dia} viajes/día.".replace(",", ".")
)

st.markdown("---")

# ---------------------------------------------------------
# OPERACIÓN E IMPUTACIÓN DE COSTOS
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
costo_movilizacion = 0.0
costo_prevencion_epp = 0.0
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

  with st.expander("🛠️ Equipos Adicionales Solicitados", expanded=False):
    incluye_extra = st.checkbox("¿Incluir maquinaria adicional?")
    if incluye_extra:
      num_equipos_extra = st.number_input(
          "Tipos de equipos", min_value=1, max_value=5, value=1, step=1
      )
      for i in range(num_equipos_extra):
        col_e1, col_e2, col_e3, col_e4 = st.columns([2, 1.5, 1.5, 1.5])
        with col_e1:
          nombre_eq = st.text_input(
              f"Equipo #{i+1}", f"Retroexcavadora", key=f"eq_custom_{i}"
          )
        with col_e2:
          modalidad_tarifa = st.selectbox(
              "Unidad", ["Valor por Hora", "Valor Diario"], key=f"eq_mod_{i}"
          )
        with col_e3:
          tarifa_eq = st.number_input(
              "Tarifa ($)", value=35000.0, step=1000.0, key=f"eq_tar_{i}"
          )
        with col_e4:
          cant_tiempo = st.number_input(
              "Cantidad", value=duracion_dias * 8, step=1, key=f"eq_cant_{i}"
          )

        subtotal_eq = tarifa_eq * cant_tiempo
        costo_maquinaria_extra += subtotal_eq
        detalles_maq_extra.append({
            "equipo": nombre_eq,
            "modalidad": modalidad_tarifa,
            "cantidad": cant_tiempo,
            "subtotal": subtotal_eq,
        })

  with st.expander("🚚 Traslado Cama Baja, Transporte y Botadero", expanded=True):
    col_tr1, col_tr2 = st.columns(2)
    with col_tr1:
      costo_movilizacion = st.number_input(
          "Cama Baja (Movilización y Desmovilización) ($)",
          min_value=0.0,
          value=350000.0,
          step=25000.0,
      )
    with col_tr2:
      tarifa_transporte_m3 = st.number_input(
          f"Tarifa transporte + botadero ($/{unidad_medicion})",
          min_value=0.0,
          value=3200.0,
          step=100.0,
      )
    costo_transporte = volumen_cobrar * tarifa_transporte_m3

  with st.expander("🚧 Mitigaciones, Prevención de Riesgos y Topografía"):
    col_p1, col_p2 = st.columns(2)
    with col_p1:
      incluye_aljibe = st.checkbox("Camión Aljibe (Polución)")
      num_paleteros = st.number_input(
          "N° Paleteros / Banderilleros", min_value=0, value=0, step=1
      )
      valor_dia_paletero = st.number_input(
          "Costo diario paletero ($/día)", min_value=0.0, value=35000.0
      )
    with col_p2:
      costo_prevencion_epp = st.number_input(
          "Gastos EPP y Señalética PR ($)", min_value=0.0, value=120000.0
      )
      incluye_topografia = st.checkbox("Topógrafo dedicado")
      costo_topografia_global = st.number_input(
          "Costo topografía ($)", min_value=0.0, value=150000.0
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
      + costo_movilizacion
      + costo_prevencion_epp
      + costo_maquinaria_extra
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
  condicion_pago = st.text_input(
      "Condición de Pago", "A tratar según previo acuerdo"
  )

with st.expander("🏦 Garantías, Pólizas y Factoring"):
  col_f1, col_f2 = st.columns(2)
  with col_f1:
    incluye_poliza = st.checkbox("¿Exige Póliza de Fianza / Boleta Garantía?")
    costo_poliza = 0.0
    if incluye_poliza:
      costo_poliza = st.number_input(
          "Costo Póliza / Boleta ($)", min_value=0.0, value=180000.0
      )

  with col_f2:
    incluye_factoring = st.checkbox("¿Aplica Cobro Vía Factoring?")
    costo_factoring = 0.0
    if incluye_factoring:
      tasa_factoring_mensual = st.number_input(
          "Tasa mensual (%)", min_value=0.1, value=2.2
      )
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
      "Margen Deseado (%)", min_value=0.0, value=13.5, step=0.5
  )
  costo_base = costo_interno_total + costo_poliza
  oferta_total_neto = (
      costo_base / (1.0 - (margen_pct / 100.0)) if margen_pct < 100 else costo_base
  )
  pu_neto_mandante = (
      oferta_total_neto / volumen_cobrar if volumen_cobrar > 0 else 0.0
  )
else:
  oferta_total_neto = st.number_input(
      "Precio Final Neto Objetivo ($)", min_value=0.0, value=45895500.0
  )
  pu_neto_mandante = (
      oferta_total_neto / volumen_cobrar if volumen_cobrar > 0 else 0.0
  )

if incluye_factoring:
  tasa_diaria = (tasa_factoring_mensual / 100.0) / 30.0
  costo_factoring = oferta_total_neto * (tasa_diaria * dias_anticipo)

costo_interno_total += costo_poliza + costo_factoring
iva_monto = oferta_total_neto * 0.19
total_bruto = oferta_total_neto + iva_monto
margen_monto = oferta_total_neto - costo_interno_total
margen_porcentaje = (
    (margen_monto / oferta_total_neto * 100.0) if oferta_total_neto > 0 else 0.0
)

# ---------------------------------------------------------
# RESUMEN ECONÓMICO
# ---------------------------------------------------------
st.subheader("📊 Resumen Económico e Impuestos")
col_r1, col_r2, col_r3 = st.columns(3)
col_r1.metric(
    "Costo Interno Total", f"${costo_interno_total:,.0f}".replace(",", ".")
)
col_r2.metric(
    "Oferta Total Neto",
    f"${oferta_total_neto:,.0f}".replace(",", "."),
    delta=f"Margen: {margen_porcentaje:.1f}%",
)
col_r3.metric("Total Bruto (incl. IVA)", f"${total_bruto:,.0f}".replace(",", "."))

st.markdown("---")

# ---------------------------------------------------------
# VISTA PREVIA Y CLÁUSULAS
# ---------------------------------------------------------
st.subheader("📋 Vista Previa de la Propuesta Formal")

texto_descripcion_servicio = (
    f"Retiro de aproximadamente {volumen_cobrar:,.0f} m³ de material en terreno"
    f" tipo '{tipo_suelo}', medidos bajo criterio de {unidad_medicion}. El plazo"
    f" de ejecución es de {duracion_dias} días de faena con un retiro diario de"
    f" {m3_diarios_est:,.0f} m³/día (~{camiones_simultaneos} camiones en"
    " rotación). Incluye gestión operativa, equipos y transporte a botadero"
    " autorizado."
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
    "Total Neto Estimado": f"${oferta_total_neto:,.0f}".replace(",", "."),
}])

st.markdown("#### Condiciones Comerciales y Legales")
st.markdown(f"- **Forma de Pago:** {condicion_pago}.")
st.markdown(f"- **Control de Volumen:** {texto_control_volumen}")
st.markdown(
    "- **Mínimo Diario Garantizado:** Se establece un mínimo de"
    f" {minimo_horas} horas/día por equipo contratado."
)
st.markdown(
    "- **Stand-by por Clima o Paralización Imputable:** En caso de"
    " paralización de la obra por causas ajenas a EDOS SpA o eventos"
    " meteorológicos, se facturará la tarifa de stand-by correspondiente al"
    " mínimo diario garantizado de los equipos en obra."
)

st.caption("*Vicente Ortiz Amestelli - EDOS SpA*")

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
- Total Neto: ${oferta_total_neto:,.0f} CLP
- Total Bruto (incl. IVA): ${total_bruto:,.0f} CLP

Quedamos atentos a sus comentarios para coordinar el inicio de las actividades en terreno.

Saludos cordiales,
Vicente Ortiz Amestelli
EDOS SpA
dos.oficinacv@gmail.com
""".replace(",", ".")
  st.code(cuerpo_email, language="markdown")


# ---------------------------------------------------------
# GENERACIÓN DE PDF Y JSON
# ---------------------------------------------------------
class PDFPresupuesto(FPDF):

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
  pdf = PDFPresupuesto("P", "mm", "A4")
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
  pdf.cell(0, 5, f"Validez Oferta: {validez_oferta} dias corridos", 0, 1)
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
  pdf.cell(0, 6, "2. Condiciones Comerciales y Legales", 0, 1)
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
      "tipo_suelo": tipo_suelo,
      "volumen_cobrar": volumen_cobrar,
      "duracion_dias_faena": duracion_dias,
      "camiones_simultaneos": camiones_simultaneos,
      "costo_interno_total": costo_interno_total,
      "pu_neto_mandante": pu_neto_mandante,
      "oferta_total_neto": oferta_total_neto,
      "total_bruto": total_bruto,
  }
  st.download_button(
      label="💾 Guardar parámetros (JSON)",
      data=json.dumps(datos_json, indent=4),
      file_name="parametros_cotizacion.json",
      mime="application/json",
  )
