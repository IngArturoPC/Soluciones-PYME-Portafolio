import unittest
import os
import sqlite3
import json
from panel_ventas import (
    inicializar_infraestructura_analitica,
    ejecutar_reporte_utilidad_y_margen,
    formatear_y_exportar_payload_api,
    DB_NAME
)

class TestPanelVentasAnalitica(unittest.TestCase):

    def setUp(self):
        """
        Arrange: Configura un entorno de pruebas limpio antes de cada test.
        """
        if os.path.exists(DB_NAME):
            os.remove(DB_NAME)
        inicializar_infraestructura_analitica()

    def tearDown(self):
        """
        Clean: Remueve los archivos y bases de datos temporales del test.
        """
        if os.path.exists(DB_NAME):
            try:
                os.remove(DB_NAME)
            except PermissionError:
                pass
        
        if os.path.exists("data_ventas.json"):
            os.remove("data_ventas.json")

    def test_precision_calculos_financieros(self):
        """
        Prueba que las operaciones matemáticas de utilidad y margen en SQL sean exactas.
        """
        # Act: Obtener los resultados del reporte analítico
        reporte = ejecutar_reporte_utilidad_y_margen()
        
        # Assert: Validar que existan datos cargados
        self.assertGreater(len(reporte), 0, "El reporte analítico no devolvió registros.")
        
        # Tomamos el primer producto (Laptop de Oficina) para auditar sus números
        # Mock de datos insertados: 10 unidades vendidas en total a $15,000 c/u (Costo: $9,500)
        # Ingresos esperados: 150,000 | Costos: 95,000 | Utilidad: 55,000 | Margen: 36.67%
        laptop_data = next((p for p in reporte if p["nombre_producto"] == "Laptop Oficina Standar"), None)
        
        self.assertIsNotNone(laptop_data, "No se encontró el producto de prueba en el reporte.")
        
        # Verificación del cálculo de Utilidad Neta
        utilidad_calculada = laptop_data["ingresos_totales"] - laptop_data["costos_totales"]
        self.assertEqual(laptop_data["utilidad_neta"], utilidad_calculada, "La utilidad neta reportada no coincide con Ingresos - Costos.")
        
        # Verificación matemática del Margen Porcentual
        margen_esperado = round((utilidad_calculada / laptop_data["ingresos_totales"]) * 100, 2)
        self.assertEqual(laptop_data["margen_porcentual"], margen_esperado, "El margen porcentual calculado por el motor SQL es incorrecto.")

    def test_estructura_y_consistencia_json(self):
        """
        Prueba que el pipeline de exportación genere un JSON válido con la estructura que el frontend espera.
        """
        # Act: Exportar el archivo
        json_string = formatear_y_exportar_payload_api()
        
        # Assert: Validar que el archivo físico se haya creado
        self.assertTrue(os.path.exists("data_ventas.json"), "El archivo de intercambio JSON no fue creado en el disco.")
        
        # Validar que el string sea un JSON válido mapeable
        try:
            payload = json.loads(json_string)
        except json.JSONDecodeError:
            self.fail("El pipeline devolvió una cadena de texto que no es un JSON válido.")
            
        # Validar la estructura corporativa del contrato de la API (Metadatos + Data)
        self.assertEqual(payload["status"], "success")
        self.assertIn("metadata", payload)
        self.assertIn("data", payload)
        self.assertEqual(payload["metadata"]["registros_totales"], len(payload["data"]))

if __name__ == "__main__":
    unittest.main()