import sqlite3
import logging
import json
import os

# Configuración del sistema de logs para auditoría de rendimiento
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler("analitica_ventas.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

DB_NAME = "paneles_pyme.db"

# ==========================================
# CAPA DE PERSISTENCIA (PASO 1 REPETIDO)
# ==========================================
def inicializar_infraestructura_analitica():
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                cliente_codigo TEXT PRIMARY KEY,
                segmento_mercado TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                producto_id TEXT PRIMARY KEY,
                nombre_producto TEXT NOT NULL,
                categoria TEXT NOT NULL,
                precio_venta REAL NOT NULL,
                costo_produccion REAL NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transacciones_ventas (
                transaccion_id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_venta TEXT NOT NULL,
                cliente_codigo TEXT,
                producto_id TEXT,
                cantidad INTEGER NOT NULL,
                FOREIGN KEY(cliente_codigo) REFERENCES clientes(cliente_codigo),
                FOREIGN KEY(producto_id) REFERENCES productos(producto_id)
            );
        """)
        cursor.execute("SELECT COUNT(*) FROM productos;")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("INSERT INTO clientes VALUES (?, ?);", [
                ("CLI-1001", "Mayorista"), ("CLI-1002", "Minorista"), ("CLI-1003", "Corporativo")
            ])
            cursor.executemany("INSERT INTO productos VALUES (?, ?, ?, ?, ?);", [
                ("PROD-01", "Laptop Oficina Standar", "Electrónica", 15000.0, 9500.0),
                ("PROD-02", "Monitor 24 Pulgadas", "Electrónica", 3500.0, 1800.0),
                ("PROD-03", "Silla Ergonómica Ejecutiva", "Mobiliario", 4500.0, 2100.0)
            ])
            cursor.executemany("""
                INSERT INTO transacciones_ventas (fecha_venta, cliente_codigo, producto_id, Residential_cantidad) 
                VALUES (?, ?, ?, ?);
            """, [
                ("2026-04-10", "CLI-1001", "PROD-01", 5),
                ("2026-04-15", "CLI-1002", "PROD-02", 3),
                ("2026-05-02", "CLI-1001", "PROD-01", 2),
                ("2026-05-18", "CLI-1003", "PROD-03", 10),
                ("2026-06-01", "CLI-1002", "PROD-02", 8),
                ("2026-06-12", "CLI-1003", "PROD-01", 3)
            ])
            conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error en inicialización: {e}")
    finally:
        if conn: conn.close()

def ejecutar_reporte_utilidad_y_margen():
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = """
            SELECT p.nombre_producto,
                   p.categoria,
                   SUM(v.cantidad) AS unidades_vendidas,
                   SUM(v.cantidad * p.precio_venta) AS ingresos_totales,
                   SUM(v.cantidad * p.costo_produccion) AS costos_totales,
                   SUM(v.cantidad * (p.precio_venta - p.costo_produccion)) AS utilidad_neta,
                   ROUND((SUM(v.cantidad * (p.precio_venta - p.costo_produccion)) / SUM(v.cantidad * p.precio_venta)) * 100, 2) AS margen_porcentual
            FROM transacciones_ventas v
            JOIN productos p ON v.producto_id = p.producto_id
            GROUP BY p.producto_id
            ORDER BY utilidad_neta DESC;
        """
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logging.error(f"Fallo al ejecutar reporte de margen: {e}")
        return []
    finally:
        if conn: conn.close()


# ==========================================
# NUEVA CAPA: TRANSFORMACIÓN Y SERIALIZACIÓN (PASO 2)
# ==========================================
def formatear_y_exportar_payload_api():
    """
    Toma los diccionarios nativos de la consulta SQL analítica, los estructura
    bajo un esquema JSON corporativo estandarizado y genera un archivo físico de intercambio.
    """
    try:
        logging.info("Extrayendo métricas de base de datos para serialización...")
        datos_crudos = ejecutar_reporte_utilidad_y_margen()
        
        if not datos_crudos:
            logging.warning("No se recuperaron datos de la consulta. Payload vacío.")
            return None

        # Estructuración corporativa del JSON (Metadatos de control + Datos de negocio)
        payload = {
            "status": "success",
            "metadata": {
                "version": "1.0.0",
                "fuente": "Sistema SQLite Transaccional",
                "registros_totales": len(datos_crudos)
            },
            "data": datos_crudos
        }

        # Convertir a cadena de texto estructurada en formato JSON indentado
        json_string = json.dumps(payload, indent=4, ensure_ascii=False)
        
        # Guardar en un archivo estático (simulando un endpoint de API o caché de datos)
        ruta_salida = "data_ventas.json"
        with open(ruta_salida, "w", encoding="utf-8") as archivo:
            archivo.write(json_string)
            
        logging.info(f"✔ Payload JSON comercial exportado exitosamente a: {ruta_salida}")
        return json_string

    except Exception as e:
        logging.error(f"Error catastrófico en la capa de transformación JSON: {e}")
        return None


# ==========================================
# ORQUESTACIÓN INTERNA ACTUALIZADA
# ==========================================
if __name__ == "__main__":
    print("--- INICIANDO PIPELINE DE EXTRACCIÓN Y TRANSFORMACIÓN (ETL) ---")
    inicializar_infraestructura_analitica()
    
    print("\n--- GENERANDO PAYLOAD DE INTERCAMBIO PARA EL DASHBOARD FRONTEND ---")
    json_resultado = formatear_y_exportar_payload_api()
    
    if json_resultado:
        print("\nVista previa del JSON generado de forma limpia y segura:")
        print(json_resultado[:350] + "\n\n... [Contenido truncado para visualización] ...")