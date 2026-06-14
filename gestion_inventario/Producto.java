package modelo;

public class Producto {
    private String productoId;
    private String nombre;
    private int stockActual;
    private int stockMinimoSeguridad; // Punto de reorden

    // Constructor estructurado
    public Producto(String productoId, String nombre, int stockActual, int stockMinimoSeguridad) {
        this.productoId = productoId;
        this.nombre = nombre;
        this.stockActual = stockActual;
        this.stockMinimoSeguridad = stockMinimoSeguridad;
    }

    // Getters y Setters para encapsulamiento seguro
    public String getProductoId() { return productoId; }
    public String getNombre() { return nombre; }
    
    public int getStockActual() { return stockActual; }
    public void setStockActual(int stockActual) { this.stockActual = stockActual; }

    public int getStockMinimoSeguridad() { return stockMinimoSeguridad; }
}