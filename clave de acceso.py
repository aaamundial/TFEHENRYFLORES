import datetime
import random

def transformar_fecha(fecha):
    try:
        fecha_obj = datetime.datetime.strptime(fecha, '%d/%m/%Y')
        return fecha_obj.strftime('%d%m%Y')
    except ValueError:
        return None

def generar_codigo_numerico():
    return str(random.randint(10000000, 99999999))

def obtener_datos():
    datos = {}

    fecha_hoy = datetime.datetime.now().strftime('%d/%m/%Y')
    fecha_emision = fecha_hoy
    datos['fechaEmision'] = transformar_fecha(fecha_emision)

    datos['codDoc'] = "01"
    datos['ruc'] = "1718573387001"
    datos['ambiente'] = "1"
    datos['estab'] = "001"
    datos['ptoEmi'] = "101"

    try:
        with open('secuencial.txt', 'r+') as f:
            secuencial = int(f.read().strip()) + 1
            f.seek(0)
            f.write(f'{secuencial:09d}')
            f.truncate()
    except FileNotFoundError:
        secuencial = 1
        with open('secuencial.txt', 'w') as f:
            f.write(f'{secuencial:09d}')

    datos['secuencial'] = f'{secuencial:09d}'
    datos['codigoNumerico'] = generar_codigo_numerico()
    datos['tipoEmision'] = '1'

    return datos

def mostrar_elementos(datos):
    etiquetas = {
        'fechaEmision': 'Fecha de emisión',
        'codDoc': 'Tipo de comprobante',
        'ruc': 'Número de RUC',
        'ambiente': 'Tipo de ambiente',
        'estab': 'Establecimiento',
        'ptoEmi': 'Punto de emisión',
        'secuencial': 'Secuencial',
        'codigoNumerico': 'Código numérico',
        'tipoEmision': 'Tipo de emisión'
    }

    for tag, valor in datos.items():
        print(f"{etiquetas[tag]}: {valor}")

def generar_cadena(datos):
    cadena = (
        datos['fechaEmision'] +
        datos['codDoc'] +
        datos['ruc'] +
        datos['ambiente'] +
        datos['estab'] +
        datos['ptoEmi'] +
        datos['secuencial'] +
        datos['codigoNumerico'] +
        datos['tipoEmision']
    )
    return cadena

def calcular_digito_verificador(numero_base):
    digitos = [int(d) for d in str(numero_base)]
    digitos.reverse()
    
    multiplicadores = [2, 3, 4, 5, 6, 7]
    
    suma = 0
    for i, digito in enumerate(digitos):
        suma += digito * multiplicadores[i % len(multiplicadores)]
    
    residuo = suma % 11
    
    digito_verificador = 11 - residuo
    if digito_verificador == 10:
        digito_verificador = 1
    elif digito_verificador == 11:
        digito_verificador = 0
    
    return digito_verificador

# Ejemplo de uso
if __name__ == "__main__":
    elementos = obtener_datos()
    mostrar_elementos(elementos)
    cadena_base = generar_cadena(elementos)
    digito_verificador = calcular_digito_verificador(cadena_base)
    cadena_final = cadena_base + str(digito_verificador)
    print(f"Cadena generada: {cadena_final}")
