import os
import sqlite3
import unittest
from unittest.mock import patch, MagicMock

# Importamos las funciones de nuestro script principal
from reportes import (
    inicializar_base_de_datos,
    obtener_datos_periodo,
    generar_pdf_reporte,
    enviar_correo_con_adjunto,
    DB_NAME,
    CARPETA_SALIDA
)

class TestAutomatizadorReportes(unittest.TestCase):

    def setUp(self):
        """
        Configuración del entorno antes de CADA prueba (Arrange).
        Crea una base de datos de pruebas limpia y efímera.
        """
        # Forzar un entorno limpio eliminando la BD de pruebas previa si existe
        if os.path.exists(DB_NAME):
            os.remove(DB_NAME)
        
        # Inicializamos la base de datos con los datos mock integrados
        inicializar_base_de_datos()

    def tearDown(self):
        """
        Limpieza del entorno después de CADA prueba (TearDown).
        Borra la base de datos y remueve archivos PDF generados en los tests.
        """
        # Cerrar conexiones residuales si las hubiera y eliminar BD de prueba
        if os.path.exists(DB_NAME):
            try:
                os.remove(DB_NAME)
            except PermissionError:
                pass # Evita que falle el test si el archivo sigue retenido momentáneamente
        
        # Limpiar PDFs de prueba específicos para no saturar el disco
        archivo_prueba = os.path.join(CARPETA_SALIDA, "Reporte_CLI-001_2026-05.pdf")
        if os.path.exists(archivo_prueba):
            os.remove(archivo_prueba)

    # ---------------------------------------------------------
    # PRUEBAS UNITARIAS
    # ---------------------------------------------------------

    def test_inicializacion_y_join_de_datos(self):
        """
        Prueba que la extracción por periodos funcione y realice el JOIN correctamente.
        """
        # Act: Extraemos los datos del periodo mock insertado
        periodo = "2026-05"
        resultados = obtener_datos_periodo(periodo)
        
        # Assert: Validamos que devuelva los 3 registros esperados
        self.assertEqual(len(resultados), 3)
        
        # Validamos que los campos del JOIN existan y no vengan vacíos
        primer_registro = resultados[0]
        self.assertIn("cliente_codigo", primer_registro)
        self.assertIn("nombre_empresa", primer_registro)
        self.assertIn("correo_contacto", primer_registro)
        self.assertEqual(primer_registro["cliente_codigo"], "CLI-001")

    def test_generacion_fisica_de_pdf(self):
        """
        Prueba que la capa de renderizado HTML y compilación de PDF cree el archivo en disco.
        """
        # Arrange: Datos simulados de un cliente
        datos_mock = {
            "cliente_codigo": "CLI-001",
            "nombre_empresa": "Empresa Test S.A.",
            "correo_contacto": "test@empresa.com",
            "mes_periodo": "2026-05",
            "monto_ejercido": 15000.00,
            "servicios_prestados": 5,
            "estatus_pago": "Pagado"
        }
        
        # Act: Ejecutamos la generación
        ruta_resultado = generar_pdf_reporte(datos_mock)
        
        # Assert: Verificaciones cruciales
        self.assertIsNotNone(ruta_resultado, "La ruta del PDF no debería ser None.")
        # Validación con aserción booleana nativa (tal como lo vimos en el cuestionario)
        self.assertTrue(os.path.exists(ruta_resultado), "El archivo PDF no se creó físicamente en el disco.")

    @patch('smtplib.SMTP')
    def test_envio_correo_seguro_con_mock(self, mock_smtp):
        """
        Prueba el pipeline de envío de correo aislando el servidor SMTP real mediante un Mock.
        """
        # Arrange: Configurar el comportamiento simulado del servidor de correo
        instancia_smtp = MagicMock()
        mock_smtp.return_value.__enter__.return_value = instancia_smtp
        
        datos_mock = {
            "cliente_codigo": "CLI-001",
            "nombre_empresa": "Empresa Test S.A.",
            "correo_contacto": "test@empresa.com",
            "mes_periodo": "2026-05"
        }
        
        # Creamos un archivo temporal vacío para simular el PDF adjunto
        ruta_pdf_falso = os.path.join(CARPETA_SALIDA, "Reporte_CLI-001_2026-05.pdf")
        os.makedirs(CARPETA_SALIDA, exist_ok=True)
        with open(ruta_pdf_falso, "w") as f:
            f.write("Contenido simulado de PDF")

        # Act: Intentamos enviar el correo
        # Forzamos temporalmente que lea variables de entorno mock si el archivo .env no existiera
        with patch('reportes.load_config', {
            "SMTP_SERVER": "smtp.test.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "user@test.com",
            "SMTP_PASSWORD": "password123"
        }):
            exito = enviar_correo_con_adjunto(datos_mock, ruta_pdf_falso)

        # Assert: Validaciones de comportamiento seguro
        self.assertTrue(exito, "El método de envío reportó un fallo.")
        
        # Verificamos que nuestro código haya llamado a los métodos de seguridad SMTP correctos
        instancia_smtp.starttls.assert_called_once() # Cifrado TLS obligatorio
        instancia_smtp.login.assert_called_once_with("user@test.com", "password123") # Autenticación
        instancia_smtp.send_mail.assert_called_once() # Despacho final

if __name__ == "__main__":
    unittest.main()