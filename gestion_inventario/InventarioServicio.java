package servicio;

import modelo.Producto;
import java.util.ArrayList;
import java.util.List;

public class InventarioServicio {
    private List<Producto> bodega;

    public InventarioServicio() {
        this.bodega = new ArrayList<>();
    }

    public void registrarProducto(Producto producto) {
        this.bodega.add(producto);
    }

    /**
     * Lógica de Negocio: Reduce el stock tras una venta y evalúa la salud del inventario.
     * Maneja el control de excepciones lógicas si se intenta vender más de lo existente.
     */
    public void procesarSalida(String productoId, int cantidadVendida) throws IllegalArgumentException {
        for (Producto p : bodega) {
            if (p.getProductoId().equals(productoId)) {
                if (p.getStockActual() < cantidadVendida) {
                    throw new IllegalArgumentException("Error: Stock insuficiente para el producto: " + p.getNombre());
                }
                // Actualización segura
                int nuevoStock = p.getStockActual() - cantidadVendida;
                p.setStockActual(nuevoStock);
                return;
            }
        }
        throw new IllegalArgumentException("Error: El producto con ID " + productoId + " no existe en bodega.");
    }

    /**
     * Pipeline de Auditoría: Recorre el inventario y aísla los productos en desabasto.
     */
    public List<Producto> evaluarAlertasStock() {
        List<Producto> productosCriticos = new ArrayList<>();
        for (Producto p : bodega) {
            // Si el stock actual es igual o menor al mínimo de seguridad, se dispara alerta
            if (p.getStockActual() <= p.getStockMinimoSeguridad()) {
                productosCriticos.add(p);
            }
        }
        return productosCriticos;
    }

    public List<Producto> obtenerTodoElInventario() {
        return this.bodega;
    }
}