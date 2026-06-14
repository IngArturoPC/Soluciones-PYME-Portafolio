import modelo.Producto;
import servicio.InventarioServicio;
import java.util.List;

public class Main {
    public static void main(String[] args) {
        System.out.println("--- SISTEMA DE GESTIÓN DE INVENTARIOS ENTERPRISE (JAVA) ---");
        
        InventarioServicio servicio = new InventarioServicio();

        // 1. Carga inicial de datos de prueba
        servicio.registrarProducto(new Producto("PROD-101", "Silla Ejecutiva Premium", 15, 5));
        servicio.registrarProducto(new Producto("PROD-102", "Monitor Gamer 27'", 3, 4)); // Inicia bajo en stock
        servicio.registrarProducto(new Producto("PROD-103", "Teclado Mecánico RGB", 25, 8));

        // 2. Simulación de una venta operativa
        try {
            System.out.println("\n[Venta] Procesando la salida de 12 Sillas Ejecutivas...");
            servicio.procesarSalida("PROD-101", 12); // Quedarán 3 unidades (Abajo del mínimo que es 5)
            System.out.println("✔ Venta procesada correctamente.");
        } catch (IllegalArgumentException e) {
            System.err.println(e.getMessage());
        }

        // 3. Ejecución del sistema de alertas en tiempo real
        System.out.println("\n--- EJECUTANDO AUDITORÍA AUTOMÁTICA DE STOCK MINIMO ---");
        List<Producto> alertas = servicio.evaluarAlertasStock();

        if (alertas.isEmpty()) {
            System.out.println("✔ Todo en orden. Los niveles de stock son saludables.");
        } else {
            System.out.println("⚠️ ALERTA DE REORDEN: Los siguientes productos requieren abastecimiento inmediato:");
            for (Producto p : alertas) {
                System.out.println("  • [ID: " + p.getProductoId() + "] " + p.getNombre() 
                        + " | Stock Actual: " + p.getStockActual() 
                        + " | Mínimo Requerido: " + p.getStockMinimoSeguridad());
            }
        }
    }
}