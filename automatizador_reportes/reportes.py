import os
import sqlite3
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.encoders import encode_base64
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
# Cargar soporte para configuración segura
from dotenv import load_load, dotenv_values 
load_config = dotenv_values(".env")

# 1. Configuración del sistema de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] (%(filename)s:%(lineno)d) - %(message)s',
    handlers=[
        logging.FileHandler("sistema_reportes.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

DB_NAME = "sistema_pymes.db"
PLANTILLA_NAME = "plantilla.html"
CARPETA_SALIDA = "reportes_generados"

# ==========================================
# FUNCIONES DE CAPAS ANTERIORES (PASOS 1 y 2)
# ==========================================
def inicializar_base_de_datos():
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                cliente_codigo TEXT PRIMARY KEY,
                nombre_empresa TEXT NOT NULL,
                correo_contacto TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reportes_mensuales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_codigo TEXT,
                mes_periodo TEXT NOT NULL,
                monto_ejercido REAL DEFAULT 0,
                servicios_prestados INTEGER DEFAULT 0,
                estatus_pago TEXT NOT NULL,
                FOREIGN KEY(cliente_codigo) REFERENCES clientes(cliente_codigo)
            );
        """)
        cursor.execute("SELECT COUNT(*) FROM clientes;")
        if cursor.fetchone()[0] == 0:
            clientes_mock = [
                ("CLI-001", "Distribuidora del Centro S.A.", "contacto@distcentro.com"),
                ("CLI-002", "Consultores Asociados de México", "finanzas@conasoc.mx"),
                ("CLI-003", "Logística Rápida Local", "operaciones@loglocal.com")
            ]
            cursor.executemany("INSERT INTO clientes VALUES (?, ?, ?);", clientes_mock)
            reportes_mock = [
                ("CLI-001", "2026-05", 24500.50, 12, "Pagado"),
                ("CLI-002", "2026-05", 48000.00, 8, "Pendiente"),
                ("CLI-003", "2026-05", 15250.00, 22, "Pagado")
            ]
            cursor.executemany("INSERT INTO reportes_mensuales (cliente_codigo, mes_periodo, monto_ejercido, servicios_prestados, estatus_pago) VALUES (?, ?, ?, ?, ?);", reportes_mock)
            conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error en BD: {e}")
    finally:
        if conn: conn.close()

def obtener_datos_periodo(periodo):
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        query = """
            SELECT c.cliente_codigo, c.nombre_empresa, c.correo_contacto, 
                   r.mes_periodo, r.monto_ejercido, r.servicios_prestados, r.estatus_pago
            FROM reportes_mensuales r
            JOIN clientes c ON r.cliente_codigo = c.cliente_codigo
            WHERE r.mes_periodo = ?;
        """
        cursor.execute(query, (periodo,))
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logging.error(f"Error al consultar periodo {periodo}: {e}")
        return []
    finally:
        if conn: conn.close()

def generar_pdf_reporte(datos_cliente):
    try:
        os.makedirs(CARPETA_SALIDA, exist_ok=True)
        env = Environment(loader=FileSystemLoader('.'))
        plantilla = env.get_template(PLANTILLA_NAME)
        html_renderizado = plantilla.render(datos_cliente)

        nombre_archivo = f"Reporte_{datos_cliente['cliente_codigo']}_{datos_cliente['mes_periodo']}.pdf"
        ruta_completa = os.path.join(CARPETA_SALIDA, nombre_archivo)
        
        HTML(string=html_renderizado).write_pdf(ruta_completa)
        return ruta_completa
    except Exception as e:
        logging.error(f"Error generando PDF para {datos_cliente.get('cliente_codigo')}: {e}")
        return None


# ==========================================
# NUEVA CAPA: PIPELINE SMTP SEGURO (PASO 3)
# ==========================================
def enviar_correo_con_adjunto(datos_cliente, ruta_adjunto):
    """
    Se conecta de forma segura al servidor SMTP, estructura un correo multipart
    (HTML + Adjunto PDF) y lo despacha al destinatario.
    """
    # Extracción segura de variables de entorno cargadas desde el .env
    smtp_server = load_config.get("SMTP_SERVER")
    smtp_port = load_config.get("SMTP_PORT")
    smtp_user = load_config.get("SMTP_USER")
    smtp_password = load_config.get("SMTP_PASSWORD")

    if not all([smtp_server, smtp_port, smtp_user, smtp_password]):
        logging.error("Faltan configuraciones en el archivo .env. Envío abortado.")
        return False

    destinatario = datos_cliente["correo_contacto"]
    empresa = datos_cliente["nombre_empresa"]
    periodo = datos_cliente["mes_periodo"]

    try:
        # 1. Crear el contenedor del mensaje estructural (Multipart)
        mensaje = MIMEMultipart()
        mensaje["From"] = smtp_user
        mensaje["To"] = destinatario
        mensaje["Subject"] = f"Reporte de Actividades Mensual - {periodo} - {empresa}"

        # 2. Cuerpo del correo en formato HTML comercial
        cuerpo_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2 style="color: #1a365d;">Estimado equipo de {empresa},</h2>
                <p>Esperamos que se encuentren muy bien. Adjunto a este correo encontrarán su 
                <strong>Reporte de Actividades y Consumos</strong> correspondiente al periodo <strong>{periodo}</strong>.</p>
                <p>Este es un servicio automatizado de auditoría y transparencia para su comodidad.</p>
                <br>
                <p style="font-size: 10pt; color: #718096;">Por favor, no responda a este correo electrónico. 
                Si tiene dudas sobre los montos, contacte directamente a su asesor asignado asignando su código: {datos_cliente['cliente_codigo']}.</p>
            </body>
        </html>
        """
        mensaje.attach(MIMEText(cuerpo_html, "html"))

        # 3. Procesar y adjuntar el archivo PDF de forma binaria
        logging.info(f"Preparando adjunto: {ruta_adjunto}")
        with open(ruta_adjunto, "rb") as adjunto_archivo:
            parte_adjunto = MIMEBase("application", "octet-stream")
            parte_adjunto.set_payload(adjunto_archivo.read())
            
        encode_base64(parte_adjunto)
        parte_adjunto.add_header(
            "Content-Disposition",
            f"attachment; filename={os.path.basename(ruta_adjunto)}",
        )
        mensaje.attach(parte_adjunto)

        # 4. Conexión segura y cifrada al servidor SMTP
        logging.info(f"Estableciendo conexión SMTP con {smtp_server}:{smtp_port}...")
        with smtplib.SMTP(smtp_server, int(smtp_port)) as servidor:
            servidor.starttls()  # Cifrado TLS (Security-First)
            servidor.login(smtp_user, smtp_password)
            
            logging.info(f"Enviando correo a: {destinatario}...")
            servidor.send_mail(smtp_user, destinatario, mensaje.as_string())
            
        logging.info(f"✔ Correo enviado con éxito a {empresa} ({destinatario})")
        return True

    except Exception as e:
        logging.error(f"Fallo al enviar correo a {destinatario} para el cliente {datos_cliente['cliente_codigo']}: {e}")
        return False


# ==========================================
# ORQUESTACIÓN INTERNA ACTUALIZADA
# ==========================================
if __name__ == "__main__":
    print("--- INICIANDO PIPELINE DE AUTOMATIZACIÓN COMPLETA (DATOS -> PDF -> CORREO) ---")
    
    inicializar_base_de_datos()
    periodo_objetivo = "2026-05"
    
    lista_reportes = obtener_datos_periodo(periodo_objetivo)
    
    if not lista_reportes:
        logging.warning("No hay registros para este periodo.")
    else:
        logging.info(f"Procesando {len(lista_reportes)} clientes...")
        
        pdf_creados = 0
        correos_enviados = 0
        
        # Bucle de ejecución punta a punta
        for reporte in lista_reportes:
            # Paso 2: Generar el PDF
            ruta_pdf = generar_pdf_reporte(reporte)
            
            if ruta_pdf:
                pdf_creados += 1
                # Paso 3: Enviar el correo con el PDF recién hecho
                envio_exitoso = enviar_correo_con_adjunto(reporte, ruta_pdf)
                if envio_exitoso:
                    correos_enviados += 1
                
        print(f"\n--- INFORME FINAL DE EJECUCIÓN ---")
        print(f"Periodo evaluado: {periodo_objetivo}")
        print(f"PDFs generados con éxito: {pdf_creados}/{len(lista_reportes)}")
        print(f"Correos despachados con éxito: {correos_enviados}/{pdf_creados}")