from .declaracion_iva import DeclaracionIVA

class DeclaracionIVAMensual(DeclaracionIVA):
    def descargar_facturas(self):
        print(f"Descargando facturas mensuales para el mes: {self.mes}")
        # Implementar la lógica específica para descargar facturas mensuales

    def generar_reporte_y_declarar(self):
        print("Generando reporte y declarando IVA mensual...")
        # Implementar la lógica específica para generar el reporte y declarar el IVA mensual
