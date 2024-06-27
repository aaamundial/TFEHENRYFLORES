import base64
import asyncio
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from lxml import etree
from signxml import XMLVerifier
import tkinter as tk
from tkinter import filedialog

def cargar_certificado_y_clave_p12(ruta_archivo, contrasena):
    with open(ruta_archivo, 'rb') as archivo_p12:
        contenido_p12 = archivo_p12.read()
    return pkcs12.load_key_and_certificates(
        contenido_p12,
        password=contrasena.encode(),
        backend=default_backend()
    )

def verificar_firma_xml(xml_data, certificado):
    try:
        doc = etree.fromstring(xml_data)
        XMLVerifier().verify(doc, x509_cert=certificado.public_bytes(serialization.Encoding.DER))
        print("La firma del XML es válida.")
    except Exception as e:
        print(f"La firma del XML es inválida: {e}")

def seleccionar_archivo_xml():
    root = tk.Tk()
    root.withdraw()  # Ocultar la ventana principal de tkinter
    ruta_archivo = filedialog.askopenfilename(
        title="Selecciona el archivo XML firmado",
        filetypes=[("Archivos XML", "*.xml"), ("Todos los archivos", "*.*")]
    )
    root.destroy()  # Cerrar la ventana de tkinter
    return ruta_archivo

def cargar_archivo_xml(ruta_archivo):
    with open(ruta_archivo, 'rb') as archivo:
        return archivo.read()

async def main():
    ruta_p12 = 'firma_1718249749.p12'  # Cambia esto por la ruta real de tu archivo .p12
    password = 'Mli09mli#'          # Cambia esto por la contraseña real de tu archivo .p12

    # Cargar el certificado y la clave privada desde el archivo .p12
    clave_privada, certificado, cadena_certificados = cargar_certificado_y_clave_p12(ruta_p12, password)

    # Permitir al usuario seleccionar el archivo XML
    ruta_xml = seleccionar_archivo_xml()
    if not ruta_xml:
        print("No se seleccionó ningún archivo XML.")
        return

    # Cargar los datos del archivo XML
    xml_data = cargar_archivo_xml(ruta_xml)

    # Verificar la firma del XML usando el certificado cargado
    verificar_firma_xml(xml_data, certificado)

if __name__ == "__main__":
    asyncio.run(main())
