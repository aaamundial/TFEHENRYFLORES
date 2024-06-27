class DeclaracionIVA:
    def __init__(self, driver, mes):
        self.driver = driver
        self.mes = mes

    def descargar_facturas(self):
        raise NotImplementedError("Este método debe ser implementado por las subclases")

    def generar_reporte_y_declarar(self):
        raise NotImplementedError("Este método debe ser implementado por las subclases")
