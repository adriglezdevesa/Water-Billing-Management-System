import sqlite3
import os
import sys
import json
from datetime import datetime, timedelta
from fpdf import FPDF
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as mpatches

def obtener_ruta_base():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def conectar_bd():
    ruta_bd = os.path.join(obtener_ruta_base(), 'datos', 'facturacion.db')
    return sqlite3.connect(ruta_bd)

def carpeta_informes():
    # Carpeta donde se guardan las facturas en PDF y las gráficas temporales; se crea si no existe
    ruta = os.path.join(obtener_ruta_base(), 'informes')
    os.makedirs(ruta, exist_ok=True)
    return ruta

def obtener_ruta_config():
    return os.path.join(obtener_ruta_base(), 'datos', 'config_tarifas.json')

def cargar_configuracion():
    ruta = obtener_ruta_config()

    config_default = {
        "agua_domestico": {
            "cuota_fija": 5.00,
            "minimo_m3": 40,
            "precio_t1": 0.55,
            "limite_t2": 80,
            "precio_t2": 0.76,
            "precio_t3": 1.46
        },
        "agua_industrial": {
            "cuota_fija": 5.00,
            "minimo_m3": 40,
            "precio_t1": 0.57,
            "limite_t2": 80,
            "precio_t2": 0.76,  # Asumimos una progresión igual si se pasan, pero lo podrás cambiar
            "precio_t3": 1.46
        },
        "canon_auga": {
            "cuota_fija": 6.16,
            "limite_t1": 24,
            "precio_t1": 0.00,
            "limite_t2": 48,
            "precio_t2": 0.29,
            "limite_t3": 80,
            "precio_t3": 0.37,
            "precio_t4": 0.42
        },
        "impuestos": {
            "iva_agua": 0.10
        }
    }
    
    if not os.path.exists(ruta):
        guardar_configuracion(config_default)
        return config_default
    else:
        with open(ruta, 'r', encoding='utf-8') as f:
            return json.load(f)

def guardar_configuracion(config):
    ruta = obtener_ruta_config()
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def obtener_periodo_actual():
    fecha_actual = datetime.now()
    año = fecha_actual.year
    mes = fecha_actual.month
    if mes <= 4:
        cuatrimestre = "1C"
    elif mes <= 8:
        cuatrimestre = "2C"
    else:
        cuatrimestre = "3C"
    return f"{año}-{cuatrimestre}"

def buscar_cliente(texto_busqueda):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT c.*, IFNULL(MAX(f.lectura_actual), 0) as ultima_lectura 
        FROM clientes c
        LEFT JOIN facturas f ON c.num_contrato = f.num_contrato
        WHERE c.num_contrato = ? OR c.nif = ? OR c.titular LIKE ?
        GROUP BY c.num_contrato
    ''', (texto_busqueda, texto_busqueda, f"%{texto_busqueda}%"))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado 

# --- FUNCIONES DE DIBUJO ---
def draw_card_section(pdf, x, y, w, h, r, color, corners):
    pdf.set_fill_color(*color)
    pdf.rect(x+r, y, w-2*r, h, style='F')
    pdf.rect(x, y+r, w, h-2*r, style='F')
    
    tl, tr, bl, br = corners
    if tl: pdf.ellipse(x, y, 2*r, 2*r, style='F')
    else: pdf.rect(x, y, r, r, style='F')
    if tr: pdf.ellipse(x+w-2*r, y, 2*r, 2*r, style='F')
    else: pdf.rect(x+w-r, y, r, r, style='F')
    if bl: pdf.ellipse(x, y+h-2*r, 2*r, 2*r, style='F')
    else: pdf.rect(x, y+h-r, r, r, style='F')
    if br: pdf.ellipse(x+w-2*r, y+h-2*r, 2*r, 2*r, style='F')
    else: pdf.rect(x+w-r, y+h-r, r, r, style='F')

def draw_rounded_border(pdf, x, y, w, h, r, line_width, color):
    draw_card_section(pdf, x, y, w, h, r, color, (True, True, True, True))
    draw_card_section(pdf, x + line_width, y + line_width, w - 2*line_width, h - 2*line_width, r - line_width, (255, 255, 255), (True, True, True, True))

# --- GRÁFICAS ---
def generar_grafica_historial(num_contrato):
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT periodo, MAX(consumo_real) 
        FROM facturas 
        WHERE num_contrato = ? 
        GROUP BY periodo 
        ORDER BY MAX(id_factura) DESC 
        LIMIT 5
    ''', (num_contrato,))
    datos = cursor.fetchall()
    conexion.close()
    
    periodos = [d[0] for d in reversed(datos)]
    consumos = [d[1] for d in reversed(datos)]
    
    fig, ax = plt.subplots(figsize=(4.0, 2.3))
    ax.set_facecolor('white')
    ax.yaxis.grid(True, linestyle='-', alpha=0.5, color='gray')
    ax.set_axisbelow(True)
    
    barras = ax.bar(periodos, consumos, color='#00FFFF', width=0.5, edgecolor='black', linewidth=0.8)
    
    for barra in barras:
        yval = barra.get_height()
        if yval > 0:
            ax.text(barra.get_x() + barra.get_width()/2, yval/2, f'{int(yval)}', 
                    ha='center', va='center', fontsize=9, color='black')
            
    ax.set_xticks(range(len(periodos)))
    ax.set_xticklabels(periodos, fontsize=5)
    
    max_c = max(consumos) if consumos else 100
    if max_c <= 100:
        ax.set_ylim(0, 100)
        ax.set_yticks([0, 20, 40, 60, 80, 100])
    else:
        ax.set_ylim(0, max_c + (max_c * 0.2))
        
    ax.tick_params(axis='y', labelsize=7)
    
    for spine in ax.spines.values():
        spine.set_edgecolor('black')
        spine.set_linewidth(0.8)
        
    plt.tight_layout(pad=0.2)
    ruta_img = os.path.join(carpeta_informes(), f'historial_{num_contrato}.png')
    plt.savefig(ruta_img, dpi=200, bbox_inches='tight', transparent=True)
    plt.close()
    return ruta_img

def generar_grafica_quesito(num_contrato, imp_agua, imp_canon, imp_iva):
    imp_alcantarillado = 0
    total = imp_agua + imp_alcantarillado + imp_canon + imp_iva
    if total == 0: total = 1 
    
    tamanos = [imp_agua, imp_iva, imp_alcantarillado, imp_canon]
    nombres = ['Agua', 'IVA', 'Alcantarillado', 'Canon da Auga']
    colores = ['#00FFFF', '#FFFF00', '#00FF00', '#FF0000']
    
    tamanos_reales = []
    colores_reales = []
    for i, t in enumerate(tamanos):
        if t > 0:
            tamanos_reales.append(t)
            colores_reales.append(colores[i])
            
    fig, ax = plt.subplots(figsize=(3.5, 2.6)) 
    
    def fmt(x):
        pct = (x / total) * 100
        return f'{pct:.2f}%'.replace('.', ',')
        
    wedges, texts = ax.pie(tamanos_reales, colors=colores_reales, startangle=140)
    kw = dict(arrowprops=dict(arrowstyle="-", color="black", lw=0.8), zorder=0, va="center")
    
    for i, p in enumerate(wedges):
        ang = (p.theta2 - p.theta1)/2. + p.theta1
        y = np.sin(np.deg2rad(ang))
        x = np.cos(np.deg2rad(ang))
        horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
        connectionstyle = f"angle,angleA=0,angleB={ang}"
        kw["arrowprops"].update({"connectionstyle": connectionstyle})
        
        ax.annotate(fmt(tamanos_reales[i]), xy=(x, y), xytext=(1.1*np.sign(x), 1.15*y),
                    horizontalalignment=horizontalalignment, **kw, fontsize=8, fontweight='bold')
    
    handles = [mpatches.Patch(color=c, label=n) for c, n in zip(colores, nombres)]
    ax.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, -0.15), ncol=2, 
              fontsize=7.5, frameon=False, handlelength=1.2, handleheight=1.2, 
              columnspacing=1.0, labelspacing=0.3)
    
    ruta_img = os.path.join(carpeta_informes(), f'quesito_{num_contrato}.png')
    plt.savefig(ruta_img, dpi=200, bbox_inches='tight', transparent=True)
    plt.close()
    return ruta_img

# --- CEREBRO CON PDF MILIMÉTRICO (MODIFICADO PARA TARIFAS DINÁMICAS) ---
def procesar_factura(datos_cliente, lectura_anterior, lectura_actual, periodo=None):
    if lectura_actual < lectura_anterior: return "❌ ERROR: Lectura actual menor que la anterior.", None
        
    if not periodo:
        periodo = obtener_periodo_actual()

    # Recogemos también el tipo_tarifa
    num_contrato, titular, nif, direccion, poblacion, num_contador, tipo_tarifa = datos_cliente
    consumo_real = lectura_actual - lectura_anterior
    
    conexion = conectar_bd()
    cursor = conexion.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO clientes (num_contrato, titular, nif, direccion, poblacion, num_contador, diametro_contador, tipo_tarifa)
        VALUES (?, ?, ?, ?, ?, ?, '13 mm', ?)
    ''', (num_contrato, titular, nif, direccion, poblacion, num_contador, tipo_tarifa))
    conexion.commit()

    # --- CARGAMOS LA CONFIGURACIÓN ---
    config = cargar_configuracion()
    if tipo_tarifa == "INDUSTRIAL":
        conf_agua = config["agua_industrial"]
    else:
        conf_agua = config["agua_domestico"]
        
    conf_canon = config["canon_auga"]
    conf_imp = config["impuestos"]

    # --- 1. SERVICIO DE AGUA (Cálculos dinámicos) ---
    consumo_facturado_agua = max(consumo_real, conf_agua["minimo_m3"])
    cuota_fija_agua = conf_agua["cuota_fija"]
    
    m3_agua_t1 = min(consumo_facturado_agua, conf_agua["minimo_m3"])
    m3_agua_t2 = max(0, min(consumo_facturado_agua - conf_agua["minimo_m3"], conf_agua["limite_t2"] - conf_agua["minimo_m3"]))
    m3_agua_t3 = max(0, consumo_facturado_agua - conf_agua["limite_t2"])
    
    coste_agua_t1 = m3_agua_t1 * conf_agua["precio_t1"]
    coste_agua_t2 = m3_agua_t2 * conf_agua["precio_t2"]
    coste_agua_t3 = m3_agua_t3 * conf_agua["precio_t3"]
    
    base_agua = cuota_fija_agua + coste_agua_t1 + coste_agua_t2 + coste_agua_t3
    iva_agua = base_agua * conf_imp["iva_agua"]
    
    # --- 2. CANON DA AUGA (Cálculos dinámicos) ---
    cuota_fija_canon = conf_canon["cuota_fija"]
    
    m3_canon_t1 = min(consumo_real, conf_canon["limite_t1"]) 
    m3_canon_t2 = max(0, min(consumo_real - conf_canon["limite_t1"], conf_canon["limite_t2"] - conf_canon["limite_t1"]))
    m3_canon_t3 = max(0, min(consumo_real - conf_canon["limite_t2"], conf_canon["limite_t3"] - conf_canon["limite_t2"]))
    m3_canon_t4 = max(0, consumo_real - conf_canon["limite_t3"])
    
    coste_canon_t1 = m3_canon_t1 * conf_canon["precio_t1"]
    coste_canon_t2 = m3_canon_t2 * conf_canon["precio_t2"]
    coste_canon_t3 = m3_canon_t3 * conf_canon["precio_t3"]
    coste_canon_t4 = m3_canon_t4 * conf_canon["precio_t4"]
    
    base_canon = cuota_fija_canon + coste_canon_t1 + coste_canon_t2 + coste_canon_t3 + coste_canon_t4
    total_factura = base_agua + iva_agua + base_canon

    # --- FECHAS Y REGISTRO ---
    fecha_emision_dt = datetime.now()
    fecha_emision = fecha_emision_dt.strftime('%d/%m/%Y')
    fecha_limite = (fecha_emision_dt + timedelta(days=7)).strftime('%d/%m/%Y')
    fecha_hasta = fecha_emision_dt.strftime('%d/%m/%y')
    fecha_desde = (fecha_emision_dt - timedelta(days=120)).strftime('%d/%m/%y')
    
    # El número de factura es correlativo (año + id de la factura en la base de datos),
    # así dos clientes distintos nunca comparten número ni se pisan los PDF.
    cursor.execute('''
        INSERT INTO facturas (num_factura, num_contrato, periodo, fecha_emision, lectura_anterior, lectura_actual, consumo_real, consumo_facturado, total_pagar)
        VALUES ('', ?, ?, DATE('now'), ?, ?, ?, ?, ?)
    ''', (num_contrato, periodo, lectura_anterior, lectura_actual, consumo_real, consumo_facturado_agua, total_factura))
    num_factura = f"{fecha_emision_dt.strftime('%y')}{cursor.lastrowid:05d}"
    cursor.execute("UPDATE facturas SET num_factura = ? WHERE id_factura = ?", (num_factura, cursor.lastrowid))
    conexion.commit()
    conexion.close()
    
    ruta_barras = generar_grafica_historial(num_contrato)
    ruta_queso = generar_grafica_quesito(num_contrato, base_agua, base_canon, iva_agua)
    
    pdf = FPDF()
    pdf.set_auto_page_break(False) 
    pdf.add_page()
    
    EURO = chr(128)
    def fmt_eur(val):
        return f"{val:.2f}".replace('.', ',') + f" {EURO}"

    ruta_logo = os.path.join(obtener_ruta_base(), 'datos', 'logo_concello.png')
    if os.path.exists(ruta_logo):
        pdf.image(ruta_logo, x=175, y=8, h=25) 
        
    pdf.set_font("helvetica", "B", 18)
    pdf.cell(0, 8, "Concello de Prueba", align="C", ln=1)
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 6, "SERVICIO MUNICIPAL DE AGUAS", align="C", ln=1)
    
    pdf.set_xy(10, 25)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 5, "CIF: P0000000A")  # CIF ficticio de ejemplo
    
    color_fondo_oscuro = (180, 225, 245) 
    color_fondo_claro = (210, 240, 252) 
    ancho_izq = 120 
    radio = 2.5 
    
    draw_card_section(pdf, 10, 32, ancho_izq, 8, radio, color_fondo_oscuro, (True, True, False, False))
    draw_card_section(pdf, 10, 40, ancho_izq, 45, radio, color_fondo_claro, (False, False, True, True))
    
    pdf.set_xy(10, 32)
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(ancho_izq, 8, " FACTURA", ln=1)
    
    pdf.set_xy(10, 40); pdf.set_font("helvetica", "B", 9); pdf.set_text_color(0, 0, 0); pdf.cell(35, 5, "Nº contrato:")
    pdf.set_font("helvetica", "", 9); pdf.set_text_color(100, 100, 100); pdf.cell(ancho_izq-35, 5, num_contrato, align="R", ln=1)
    
    pdf.set_xy(10, 45); pdf.set_font("helvetica", "B", 9); pdf.set_text_color(0, 0, 0); pdf.cell(35, 5, "Titular:")
    pdf.set_font("helvetica", "", 9); pdf.set_text_color(100, 100, 100); pdf.cell(ancho_izq-35, 5, titular, align="R", ln=1)
    
    pdf.set_xy(10, 50); pdf.set_font("helvetica", "B", 9); pdf.set_text_color(0, 0, 0); pdf.cell(35, 5, "NIF Titular:")
    pdf.set_font("helvetica", "", 9); pdf.set_text_color(100, 100, 100); pdf.cell(ancho_izq-35, 5, nif, align="R", ln=1)
    
    pdf.set_xy(10, 55); pdf.set_font("helvetica", "B", 9); pdf.set_text_color(0, 0, 0); pdf.cell(35, 5, "Dirección suministo:")
    pdf.set_font("helvetica", "", 8); pdf.set_text_color(100, 100, 100); pdf.cell(ancho_izq-35, 5, direccion, align="R", ln=1)
    
    pdf.set_xy(10, 60); pdf.set_font("helvetica", "B", 9); pdf.set_text_color(0, 0, 0); pdf.cell(35, 5, "")
    pdf.set_font("helvetica", "", 8); pdf.set_text_color(100, 100, 100); pdf.cell(ancho_izq-35, 5, poblacion, align="R", ln=1)
    
    pdf.set_xy(10, 65); pdf.set_font("helvetica", "B", 9); pdf.set_text_color(0, 0, 0); pdf.cell(35, 5, "Nº factura:")
    pdf.set_font("helvetica", "", 9); pdf.set_text_color(100, 100, 100); pdf.cell(ancho_izq-35, 5, num_factura, align="R", ln=1)
    
    pdf.set_xy(10, 70); pdf.set_font("helvetica", "B", 9); pdf.set_text_color(0, 0, 0); pdf.cell(35, 5, "Periodo facturación:")
    pdf.set_font("helvetica", "", 9); pdf.set_text_color(100, 100, 100); pdf.cell(ancho_izq-35, 5, periodo, align="R", ln=1)
    
    pdf.set_xy(10, 75); pdf.set_font("helvetica", "B", 9); pdf.set_text_color(0, 0, 0); pdf.cell(35, 5, "Fecha emisión:")
    pdf.set_font("helvetica", "", 9); pdf.set_text_color(100, 100, 100); pdf.cell(ancho_izq-35, 5, fecha_emision, align="R", ln=1)
    
    pdf.set_xy(10, 80); pdf.set_font("helvetica", "B", 9); pdf.set_text_color(0, 0, 0); pdf.cell(35, 5, "Fecha Límite pago:")
    pdf.set_font("helvetica", "", 9); pdf.set_text_color(100, 100, 100); pdf.cell(ancho_izq-35, 5, fecha_limite, align="R", ln=1)
    
    pdf.set_draw_color(0, 0, 0); pdf.set_line_width(0.1)
    for line_y in [45, 50, 55, 65, 70, 75, 80]:
        pdf.line(10, line_y, 130, line_y)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(142, 42)
    pdf.set_font("helvetica", "", 8)
    texto_dir_limpio = f"{titular.strip()}\n{direccion.strip()}\n{poblacion.strip()}\nPOBLACION PRUEBA"
    pdf.multi_cell(55, 4.2, texto_dir_limpio)
    
    pdf.set_draw_color(0, 0, 0); pdf.set_line_width(0.3)
    pdf.line(140, 40, 143, 40); pdf.line(140, 40, 140, 43) 
    pdf.line(197, 40, 200, 40); pdf.line(200, 40, 200, 43) 
    pdf.line(140, 65, 143, 65); pdf.line(140, 65, 140, 62) 
    pdf.line(197, 65, 200, 65); pdf.line(200, 65, 200, 62) 
    
    draw_card_section(pdf, 10, 87, ancho_izq, 8, radio, color_fondo_oscuro, (True, True, False, False))
    draw_card_section(pdf, 10, 95, ancho_izq, 20, radio, color_fondo_claro, (False, False, True, True))
    
    pdf.set_xy(10, 87)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(ancho_izq, 8, " Consumo del Periodo", ln=1)
    
    pdf.set_xy(10, 97)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(16, 5, "Contador"); pdf.cell(12, 5, "Diám."); pdf.cell(16, 5, "Desde"); pdf.cell(16, 5, "Hasta")
    pdf.cell(19, 5, "Lect. ant."); pdf.cell(19, 5, "Lect. act."); pdf.cell(22, 5, "Consumo", ln=1)
    
    pdf.set_draw_color(0, 0, 0); pdf.set_line_width(0.1)
    pdf.line(10, 102, 130, 102)

    pdf.set_xy(10, 102)
    pdf.set_font("helvetica", "", 8); pdf.set_text_color(100, 100, 100)
    pdf.cell(16, 5, num_contador); pdf.cell(12, 5, "13 mm"); pdf.cell(16, 5, fecha_desde); pdf.cell(16, 5, fecha_hasta)
    pdf.cell(19, 5, f"{int(lectura_anterior):,} m3".replace(',', '.')); 
    pdf.cell(19, 5, f"{int(lectura_actual):,} m3".replace(',', '.')); 
    pdf.cell(22, 5, f"{int(consumo_real):,} m3".replace(',', '.'), ln=1)
    
    pdf.set_draw_color(150, 150, 150); pdf.set_line_width(0.1)
    pdf.line(10, 108, 130, 108) 
    
    pdf.set_xy(10, 110); pdf.set_font("helvetica", "B", 8.5); pdf.set_text_color(0, 0, 0)
    pdf.cell(17, 5, "Imputado:", align="L")
    pdf.set_draw_color(0, 0, 0); pdf.rect(28, 111.5, 2.5, 2.5) 
    
    pdf.set_xy(42, 110)
    pdf.cell(17, 5, "Estimado:", align="L")
    pdf.rect(60, 111.5, 2.5, 2.5) 
    
    pdf.set_xy(75, 110)
    # AQUI CAMBIAMOS PARA QUE VISUALMENTE MUESTRE LO REAL, AUNQUE CUESTE EL MÍNIMO
    pdf.cell(53, 5, f"Consumo facturado:            {int(consumo_real):,} m3".replace(',', '.'), align="R") 
    
    # --- DIBUJADO INTELIGENTE DE TRAMOS ---
    draw_card_section(pdf, 10, 120, ancho_izq, 8, radio, color_fondo_oscuro, (True, True, False, False))
    draw_card_section(pdf, 10, 128, ancho_izq, 82, radio, color_fondo_claro, (False, False, True, True))
    
    pdf.set_xy(10, 120) 
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(ancho_izq, 8, " Conceptos a Facturar", ln=1)
    
    y_pos = 130
    pdf.set_xy(10, y_pos); pdf.set_font("helvetica", "B", 10)
    pdf.cell(ancho_izq, 5, " Servicio de Agua", ln=1) 
    
    y_pos += 5
    pdf.set_xy(10, y_pos); pdf.set_font("helvetica", "", 8)
    pdf.cell(50, 5, "Concepto"); pdf.cell(15, 5, "Cant.", align="R"); pdf.cell(25, 5, "Precio", align="R")
    pdf.cell(20, 5, "Subtotal", align="R"); pdf.cell(10, 5, "IVA", align="R", ln=1)
    
    y_pos += 5
    pdf.set_draw_color(150, 150, 150); pdf.set_line_width(0.1)
    pdf.line(10, y_pos, 130, y_pos) 
    
    # TEXTOS DINÁMICOS SEGÚN CONFIGURACIÓN Y TARIFA
    iva_txt = f"{int(conf_imp['iva_agua']*100)}%"
    if tipo_tarifa == "INDUSTRIAL":
        txt_cuota = "CUOTA ABASTECIMIENTO INDUSTRIAL"
    else:
        txt_cuota = "CUOTA ABASTECIMIENTO DOMÉSTICA"
        
    t1_mes = conf_agua["minimo_m3"] // 4
    t2_mes = conf_agua["limite_t2"] // 4
    txt_t1 = f"Consumo de 0 a {t1_mes} m3/mes(Mínimo)"
    txt_t2 = f"Consumo de {t1_mes+1} a {t2_mes} m3/mes"
    txt_t3 = f"Consumo exceso máis de {t2_mes} m3/mes"
    
    y_pos += 1
    pdf.set_xy(10, y_pos); pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0)
    pdf.cell(50, 5, txt_cuota)
    pdf.set_font("helvetica", "", 8); pdf.set_text_color(100, 100, 100)
    pdf.set_xy(60, y_pos)
    pdf.cell(15, 5, "", align="R"); pdf.cell(25, 5, f"{conf_agua['cuota_fija']:.2f} {EURO}".replace('.',','), align="R")
    pdf.cell(20, 5, fmt_eur(cuota_fija_agua), align="R"); pdf.cell(10, 5, iva_txt, align="R", ln=1)
    y_pos += 5; pdf.line(10, y_pos, 130, y_pos)
    
    pdf.set_xy(10, y_pos); pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0)
    pdf.cell(50, 5, txt_t1)
    pdf.set_font("helvetica", "", 8); pdf.set_text_color(100, 100, 100)
    pdf.set_xy(60, y_pos)
    pdf.cell(15, 5, f"{m3_agua_t1:.0f}m3 x", align="R"); pdf.cell(25, 5, f"{conf_agua['precio_t1']:.4f} {EURO}/m3 =".replace('.',','), align="R")
    pdf.cell(20, 5, fmt_eur(coste_agua_t1), align="R"); pdf.cell(10, 5, iva_txt, align="R", ln=1)
    y_pos += 5; pdf.line(10, y_pos, 130, y_pos)
    
    if m3_agua_t2 > 0:
        pdf.set_xy(10, y_pos); pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0)
        pdf.cell(50, 5, txt_t2)
        pdf.set_font("helvetica", "", 8); pdf.set_text_color(100, 100, 100)
        pdf.set_xy(60, y_pos)
        pdf.cell(15, 5, f"{m3_agua_t2:.0f}m3 x", align="R"); pdf.cell(25, 5, f"{conf_agua['precio_t2']:.4f} {EURO}/m3 =".replace('.',','), align="R")
        pdf.cell(20, 5, fmt_eur(coste_agua_t2), align="R"); pdf.cell(10, 5, iva_txt, align="R", ln=1)
        y_pos += 5; pdf.line(10, y_pos, 130, y_pos)
        
    if m3_agua_t3 > 0:
        pdf.set_xy(10, y_pos); pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0)
        pdf.cell(50, 5, txt_t3)
        pdf.set_font("helvetica", "", 8); pdf.set_text_color(100, 100, 100)
        pdf.set_xy(60, y_pos)
        pdf.cell(15, 5, f"{m3_agua_t3:.0f}m3 x", align="R"); pdf.cell(25, 5, f"{conf_agua['precio_t3']:.4f} {EURO}/m3 =".replace('.',','), align="R")
        pdf.cell(20, 5, fmt_eur(coste_agua_t3), align="R"); pdf.cell(10, 5, iva_txt, align="R", ln=1)
        y_pos += 5; pdf.line(10, y_pos, 130, y_pos)
        
    y_pos += 2 
    pdf.set_xy(10, y_pos); pdf.set_font("helvetica", "B", 10); pdf.set_text_color(0, 0, 0)
    pdf.cell(ancho_izq, 5, " Canon da Auga (AUGAS DE GALICIA - Q1500378C)", ln=1)
    
    y_pos += 5
    pdf.set_xy(10, y_pos); pdf.set_font("helvetica", "", 8)
    pdf.cell(50, 5, "Concepto"); pdf.cell(15, 5, "Cant.", align="R"); pdf.cell(25, 5, "Precio", align="R")
    pdf.cell(20, 5, "Subtotal", align="R"); pdf.cell(10, 5, "IVA", align="R", ln=1)
    
    y_pos += 5; pdf.line(10, y_pos, 130, y_pos)
    
    # Textos dinámicos canon
    ct1_mes = conf_canon["limite_t1"] // 4
    ct2_mes = conf_canon["limite_t2"] // 4
    ct3_mes = conf_canon["limite_t3"] // 4
    txt_c1 = f"Tramo 1 (0 - {ct1_mes}m3/mes)"
    txt_c2 = f"Tramo 2 ({ct1_mes+1} - {ct2_mes}m3/mes)"
    txt_c3 = f"Tramo 3 ({ct2_mes+1} - {ct3_mes}m3/mes)"
    txt_c4 = f"Tramo 4 (> {ct3_mes}m3/mes)"
    
    y_pos += 1
    pdf.set_xy(10, y_pos); pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0)
    pdf.cell(50, 5, "CANON AUGA CUOTA FIJA")
    pdf.set_font("helvetica", "", 8); pdf.set_text_color(100, 100, 100)
    pdf.set_xy(60, y_pos)
    pdf.cell(15, 5, "", align="R"); pdf.cell(25, 5, f"{conf_canon['cuota_fija']:.2f} {EURO}".replace('.',','), align="R")
    pdf.cell(20, 5, fmt_eur(cuota_fija_canon), align="R"); pdf.cell(10, 5, "0%", align="R", ln=1)
    y_pos += 5; pdf.line(10, y_pos, 130, y_pos)
    
    pdf.set_xy(10, y_pos); pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0)
    pdf.cell(50, 5, txt_c1)
    pdf.set_font("helvetica", "", 8); pdf.set_text_color(100, 100, 100)
    pdf.set_xy(60, y_pos)
    pdf.cell(15, 5, f"{m3_canon_t1:.0f}m3 x", align="R"); pdf.cell(25, 5, f"{conf_canon['precio_t1']:.4f} {EURO}/m3 =".replace('.',','), align="R")
    pdf.cell(20, 5, fmt_eur(coste_canon_t1), align="R"); pdf.cell(10, 5, "0%", align="R", ln=1)
    y_pos += 5; pdf.line(10, y_pos, 130, y_pos)
    
    if m3_canon_t2 > 0:
        pdf.set_xy(10, y_pos); pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0)
        pdf.cell(50, 5, txt_c2)
        pdf.set_font("helvetica", "", 8); pdf.set_text_color(100, 100, 100)
        pdf.set_xy(60, y_pos)
        pdf.cell(15, 5, f"{m3_canon_t2:.0f}m3 x", align="R"); pdf.cell(25, 5, f"{conf_canon['precio_t2']:.4f} {EURO}/m3 =".replace('.',','), align="R")
        pdf.cell(20, 5, fmt_eur(coste_canon_t2), align="R"); pdf.cell(10, 5, "0%", align="R", ln=1)
        y_pos += 5; pdf.line(10, y_pos, 130, y_pos) 
        
    if m3_canon_t3 > 0:
        pdf.set_xy(10, y_pos); pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0)
        pdf.cell(50, 5, txt_c3)
        pdf.set_font("helvetica", "", 8); pdf.set_text_color(100, 100, 100)
        pdf.set_xy(60, y_pos)
        pdf.cell(15, 5, f"{m3_canon_t3:.0f}m3 x", align="R"); pdf.cell(25, 5, f"{conf_canon['precio_t3']:.4f} {EURO}/m3 =".replace('.',','), align="R")
        pdf.cell(20, 5, fmt_eur(coste_canon_t3), align="R"); pdf.cell(10, 5, "0%", align="R", ln=1)
        y_pos += 5; pdf.line(10, y_pos, 130, y_pos) 
        
    if m3_canon_t4 > 0:
        pdf.set_xy(10, y_pos); pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0)
        pdf.cell(50, 5, txt_c4)
        pdf.set_font("helvetica", "", 8); pdf.set_text_color(100, 100, 100)
        pdf.set_xy(60, y_pos)
        pdf.cell(15, 5, f"{m3_canon_t4:.0f}m3 x", align="R"); pdf.cell(25, 5, f"{conf_canon['precio_t4']:.4f} {EURO}/m3 =".replace('.',','), align="R")
        pdf.cell(20, 5, fmt_eur(coste_canon_t4), align="R"); pdf.cell(10, 5, "0%", align="R", ln=1)
        y_pos += 5; pdf.line(10, y_pos, 130, y_pos) 

    # --- RESUMEN ECONÓMICO ---
    draw_card_section(pdf, 10, 213, ancho_izq, 8, radio, color_fondo_oscuro, (True, True, False, False))
    draw_card_section(pdf, 10, 221, ancho_izq, 32, radio, color_fondo_claro, (False, False, True, True))
    
    pdf.set_xy(10, 213) 
    pdf.set_font("helvetica", "B", 12); pdf.set_text_color(0, 0, 0)
    pdf.cell(ancho_izq, 8, " Resumen Económico", ln=1)
    
    total = base_agua + base_canon + iva_agua
    pct_agua = (base_agua/total)*100 if total else 0
    pct_canon = (base_canon/total)*100 if total else 0
    pct_iva = (iva_agua/total)*100 if total else 0

    def draw_resumen_row(y, label, val_eur, val_pct):
        pdf.set_xy(12, y)
        pdf.set_font("helvetica", "", 8.5) 
        pdf.cell(32, 5, label)  
        pdf.set_text_color(100, 100, 100)
        pdf.cell(14, 5, val_eur, align="R")
        pdf.set_font("helvetica", "B", 8); pdf.set_text_color(0, 0, 0)
        pdf.cell(14, 5, val_pct, align="R")

    draw_resumen_row(223, "Base imp. Agua:", fmt_eur(base_agua), f"{pct_agua:.2f}%".replace('.', ','))
    draw_resumen_row(228, "Base imp. Alcantar.:", f"0,00 {EURO}", "0,00%")
    draw_resumen_row(233, "Base imp. Canon Agua:", fmt_eur(base_canon), f"{pct_canon:.2f}%".replace('.', ','))
    draw_resumen_row(244, f"Total IVA ({iva_txt}):", fmt_eur(iva_agua), f"{pct_iva:.2f}%".replace('.', ','))
    
    pdf.set_font("helvetica", "", 8.5); pdf.set_text_color(0, 0, 0)
    pdf.set_xy(76, 223)
    pdf.cell(24, 5, f"Total Bases {iva_txt}:"); 
    pdf.set_text_color(100, 100, 100); pdf.cell(18, 5, fmt_eur(base_agua), align="R") 
    
    pdf.set_font("helvetica", "", 8.5); pdf.set_text_color(0, 0, 0)
    pdf.set_xy(76, 228)
    pdf.cell(24, 5, f"Total IVA {iva_txt}:"); 
    pdf.set_text_color(100, 100, 100); pdf.cell(18, 5, fmt_eur(iva_agua), align="R")
    
    pdf.set_font("helvetica", "", 8.5); pdf.set_text_color(0, 0, 0)
    pdf.set_xy(76, 233)
    pdf.cell(24, 5, "Total Gastos:"); 
    pdf.set_text_color(100, 100, 100); pdf.cell(18, 5, f"0,00 {EURO}", align="R")
    
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.6)
    pdf.rect(75, 240, 53, 10, style='D') 
    pdf.set_xy(77, 242)
    pdf.set_font("helvetica", "B", 10); pdf.set_text_color(0, 0, 0)
    pdf.cell(24, 6, "Total a pagar:")
    pdf.set_font("helvetica", "B", 13)
    pdf.cell(25, 6, fmt_eur(total_factura), align="R")
    pdf.set_line_width(0.2) 
    
    draw_rounded_border(pdf, 133, 80, 69, 53, radio, 0.5, color_fondo_oscuro)
    draw_rounded_border(pdf, 133, 137, 69, 58, radio, 0.5, color_fondo_oscuro)
    
    try:
        pdf.set_xy(135, 82)
        pdf.set_font("helvetica", "B", 11); pdf.set_text_color(0, 0, 0)
        pdf.cell(65, 5, "Historial de Consumo", ln=1)
        pdf.image(ruta_barras, x=135, y=88, w=65) 
        
        pdf.set_xy(135, 139) 
        pdf.set_font("helvetica", "B", 11); pdf.set_text_color(0, 0, 0)
        pdf.cell(65, 5, "Distribución del Gasto", ln=1)
        pdf.image(ruta_queso, x=136, y=143, w=61) 
    except: pass
    
    pdf.set_xy(135, 197) 
    pdf.set_font("helvetica", "", 7.5)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(50, 3.5, "En caso de estar empadronadas 4 o\nmás personas en una vivienda,\npueden beneficiarse de\nbonificaciones en el canon del agua.")
    
    pdf.set_fill_color(255, 0, 0)
    pdf.ellipse(186, 198, 11, 11, 'F')
    pdf.set_xy(186, 198)
    pdf.set_text_color(255, 255, 255); pdf.set_font("helvetica", "B", 18)
    pdf.cell(11, 11, "!", align="C")
    
    draw_card_section(pdf, 135, 213, 65, 8, radio, color_fondo_oscuro, (True, True, False, False))
    draw_card_section(pdf, 135, 221, 65, 32, radio, color_fondo_claro, (False, False, True, True))
    
    pdf.set_xy(135, 213) 
    pdf.set_font("helvetica", "B", 12); pdf.set_text_color(0, 0, 0)
    pdf.cell(65, 8, " Forma de Pago", ln=1)
    
    pdf.set_xy(137, 224)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(60, 5, "DOMICILIADO", ln=1)
    pdf.set_xy(137, 229)
    pdf.set_font("helvetica", "", 7.5) 
    pdf.multi_cell(61, 3.8, f"El importe de la factura le será domiciliado a partir del {fecha_limite} al nº de cuenta que ha facilitado.")

    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(10, 255)
    pdf.set_font("helvetica", "B", 10)
    
    pdf.cell(0, 5, "ATENCION AL CLIENTE 900 000 000 | FACTURACION 900 000 000 | Horario 9:00 a 14:00", align="C", ln=1)
    pdf.cell(0, 5, "info@concellodeprueba.gal", align="C", ln=1)
    
    pdf.set_y(265) 
    pdf.set_font("helvetica", "", 5.5) 
    
    texto_legal = "PROTECCIÓN DE DATOS: De conformidade co disposto no Regulamento (UE) 2016/679 de 27 de abril (GDPR) e na Lei Orgánica 3/2018 de 5 de decembro (LOPDGDD), informámoslle que os datos persoais solicitados serán tratados baixo a responsabilidade de CONCELLO DE PRUEBA para o envío de comunicacións sobre os seus trámites. Os datos non serán comunicados a terceiros, salvo obrigación legal. Pode exercer os dereitos de acceso, rectificación, portabilidade e supresión dos seus datos dirixíndose a Praza Maior, 1 - 00000 Concello de Prueba. Email: info@concellodeprueba.gal."
    
    pdf.multi_cell(0, 2.5, texto_legal, align="J")

    ruta_pdf = os.path.join(carpeta_informes(), f'Factura_{num_factura}.pdf')
    pdf.output(ruta_pdf)
    
    try:
        os.remove(ruta_barras)
        os.remove(ruta_queso)
    except: 
        pass
    
    return "✅ Factura generada con diseño oficial.", ruta_pdf