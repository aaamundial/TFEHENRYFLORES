import base64
import asyncio
import logging
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12, pkcs7
from datetime import datetime, timezone
from lxml import etree
from requests import Session
from requests.auth import HTTPBasicAuth
from signxml import XMLSigner, methods
from zeep.helpers import serialize_object
from zeep.transports import AsyncTransport
import aiohttp
from zeep import Client, Transport, Settings
from datetime import datetime
import json
import base64
import requests
import xml.etree.ElementTree as ET
import asyncio
import logging
import urllib3
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import NameOID


import uuid
from cryptography.hazmat.primitives.hashes import SHA1
import warnings
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
import warnings
from datetime import datetime, timezone, timedelta
from cryptography import x509
from cryptography.hazmat.primitives.serialization.pkcs7 import load_der_pkcs7_certificates


# Ignorar las advertencias de seguridad para SHA1
warnings.filterwarnings("ignore", category=DeprecationWarning)
# Configurar explícitamente el uso de SHA1
hashes.SHA1()


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)




# Configuración del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def test_sri_connection(url):
    try:
        # En lugar de enviar un XML vacío, solo verificamos si podemos acceder al WSDL
        wsdl_url = f"{url}?wsdl"
        response = requests.get(wsdl_url, timeout=10, verify=False)
        
        if response.status_code == 200:
            logging.info(f"Conexión exitosa a {url}")
            return True
        else:
            logging.error(f"Error al conectar a {url}. Código de estado: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Error de conexión a {url}: {str(e)}")
        return False
    
def load_certificates(p12_path, p12_password, root_cert_path, intermediate_cert_path):
    # Cargar el certificado P12
    with open(p12_path, 'rb') as p12_file:
        p12_data = p12_file.read()
        private_key, p12_cert, _ = pkcs12.load_key_and_certificates(p12_data, p12_password.encode(), default_backend())

    # Cargar el certificado raíz (PKCS#7)
    with open(root_cert_path, 'rb') as root_cert_file:
        root_cert_data = root_cert_file.read()
        certs = load_der_pkcs7_certificates(root_cert_data)
        root_cert = certs[0]  # Asumimos que el primer certificado es el raíz

    # Cargar el certificado intermedio (PEM)
    with open(intermediate_cert_path, 'rb') as intermediate_cert_file:
        intermediate_cert_data = intermediate_cert_file.read()
        intermediate_cert = x509.load_pem_x509_certificate(intermediate_cert_data, default_backend())

    return private_key, p12_cert, root_cert, intermediate_cert

# Ignorar las advertencias de seguridad para SHA1
warnings.filterwarnings("ignore", category=DeprecationWarning)


def sign_xml_with_xades(xml_tree, private_key, p12_cert):
    print("Firmando el XML con XAdES-BES...")

    ns = {
        'ds': 'http://www.w3.org/2000/09/xmldsig#',
        'etsi': 'http://uri.etsi.org/01903/v1.3.2#'
    }

    signature_id = f"Signature{uuid.uuid4().hex[:6]}"
    signed_props_id = f"{signature_id}-SignedProperties{uuid.uuid4().hex[:5]}"
    signed_info_id = f"Signature-SignedInfo{uuid.uuid4().hex[:6]}"
    signature_value_id = f"SignatureValue{uuid.uuid4().hex[:6]}"
    certificate_id = f"Certificate{uuid.uuid4().hex[:7]}"
    reference_id = f"Reference-ID-{uuid.uuid4().hex[:6]}"
    object_id = f"{signature_id}-Object{uuid.uuid4().hex[:6]}"

    signature = etree.Element(f"{{{ns['ds']}}}Signature", Id=signature_id, nsmap=ns)

    signed_info = etree.SubElement(signature, f"{{{ns['ds']}}}SignedInfo", Id=signed_info_id)
    etree.SubElement(signed_info, f"{{{ns['ds']}}}CanonicalizationMethod", Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")
    etree.SubElement(signed_info, f"{{{ns['ds']}}}SignatureMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1")

    reference_sp = etree.SubElement(signed_info, f"{{{ns['ds']}}}Reference", Id=f"SignedPropertiesID{uuid.uuid4().hex[:6]}", Type="http://uri.etsi.org/01903#SignedProperties", URI=f"#{signed_props_id}")
    etree.SubElement(reference_sp, f"{{{ns['ds']}}}DigestMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#sha1")
    etree.SubElement(reference_sp, f"{{{ns['ds']}}}DigestValue")

    reference_ki = etree.SubElement(signed_info, f"{{{ns['ds']}}}Reference", URI=f"#{certificate_id}")
    etree.SubElement(reference_ki, f"{{{ns['ds']}}}DigestMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#sha1")
    etree.SubElement(reference_ki, f"{{{ns['ds']}}}DigestValue")

    reference = etree.SubElement(signed_info, f"{{{ns['ds']}}}Reference", Id=reference_id, URI="#comprobante")
    transforms = etree.SubElement(reference, f"{{{ns['ds']}}}Transforms")
    etree.SubElement(transforms, f"{{{ns['ds']}}}Transform", Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature")
    etree.SubElement(reference, f"{{{ns['ds']}}}DigestMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#sha1")
    etree.SubElement(reference, f"{{{ns['ds']}}}DigestValue")

    signature_value = etree.SubElement(signature, f"{{{ns['ds']}}}SignatureValue", Id=signature_value_id)

    key_info = etree.SubElement(signature, f"{{{ns['ds']}}}KeyInfo", Id=certificate_id)
    x509_data = etree.SubElement(key_info, f"{{{ns['ds']}}}X509Data")
    etree.SubElement(x509_data, f"{{{ns['ds']}}}X509Certificate").text = base64.b64encode(p12_cert.public_bytes(serialization.Encoding.DER)).decode()

    object_node = etree.SubElement(signature, f"{{{ns['ds']}}}Object", Id=object_id)
    qualifying_properties = etree.SubElement(object_node, f"{{{ns['etsi']}}}QualifyingProperties", Target=f"#{signature_id}")
    signed_props = etree.SubElement(qualifying_properties, f"{{{ns['etsi']}}}SignedProperties", Id=signed_props_id)
    signed_sig_props = etree.SubElement(signed_props, f"{{{ns['etsi']}}}SignedSignatureProperties")
    
    etree.SubElement(signed_sig_props, f"{{{ns['etsi']}}}SigningTime").text = datetime.now(timezone(timedelta(hours=-5))).strftime("%Y-%m-%dT%H:%M:%S-05:00")

    signing_certificate = etree.SubElement(signed_sig_props, f"{{{ns['etsi']}}}SigningCertificate")
    cert = etree.SubElement(signing_certificate, f"{{{ns['etsi']}}}Cert")
    cert_digest = etree.SubElement(cert, f"{{{ns['etsi']}}}CertDigest")
    etree.SubElement(cert_digest, f"{{{ns['ds']}}}DigestMethod", Algorithm="http://www.w3.org/2000/09/xmldsig#sha1")
    cert_digest_value = hashes.Hash(hashes.SHA1())
    cert_digest_value.update(p12_cert.public_bytes(serialization.Encoding.DER))
    etree.SubElement(cert_digest, f"{{{ns['ds']}}}DigestValue").text = base64.b64encode(cert_digest_value.finalize()).decode()

    issuer_serial = etree.SubElement(cert, f"{{{ns['etsi']}}}IssuerSerial")
    x509_issuer_name = etree.SubElement(issuer_serial, f"{{{ns['ds']}}}X509IssuerName")
    
     # Modificación aquí: crear una lista ordenada de los atributos del emisor
    issuer_attrs = []
    for oid in [NameOID.COUNTRY_NAME, NameOID.ORGANIZATION_NAME, NameOID.ORGANIZATIONAL_UNIT_NAME, NameOID.LOCALITY_NAME, NameOID.COMMON_NAME]:
        attr = p12_cert.issuer.get_attributes_for_oid(oid)
        if attr:
            issuer_attrs.append(f"{attr[0].oid._name}={attr[0].value}")
    x509_issuer_name.text = ",".join(reversed(issuer_attrs))
    

    x509_serial_number = etree.SubElement(issuer_serial, f"{{{ns['ds']}}}X509SerialNumber")
    x509_serial_number.text = str(p12_cert.serial_number)

    signed_data_obj_props = etree.SubElement(signed_props, f"{{{ns['etsi']}}}SignedDataObjectProperties")
    data_object_format = etree.SubElement(signed_data_obj_props, f"{{{ns['etsi']}}}DataObjectFormat", ObjectReference=f"#{reference_id}")
    etree.SubElement(data_object_format, f"{{{ns['etsi']}}}Description").text = "contenido comprobante"
    etree.SubElement(data_object_format, f"{{{ns['etsi']}}}MimeType").text = "text/xml"

    # Calculate digest values
    canonicalized_signed_props = etree.tostring(signed_props, method='c14n', exclusive=False, with_comments=False)
    signed_props_digest = hashes.Hash(hashes.SHA1())
    signed_props_digest.update(canonicalized_signed_props)
    reference_sp.find(f"{{{ns['ds']}}}DigestValue").text = base64.b64encode(signed_props_digest.finalize()).decode()

    canonicalized_key_info = etree.tostring(key_info, method='c14n', exclusive=False, with_comments=False)
    key_info_digest = hashes.Hash(hashes.SHA1())
    key_info_digest.update(canonicalized_key_info)
    reference_ki.find(f"{{{ns['ds']}}}DigestValue").text = base64.b64encode(key_info_digest.finalize()).decode()

    canonicalized_document = etree.tostring(xml_tree, method='c14n', exclusive=False, with_comments=False)
    document_digest = hashes.Hash(hashes.SHA1())
    document_digest.update(canonicalized_document)
    reference.find(f"{{{ns['ds']}}}DigestValue").text = base64.b64encode(document_digest.finalize()).decode()

    # Sign the SignedInfo
    canonicalized_signed_info = etree.tostring(signed_info, method='c14n', exclusive=False, with_comments=False)
    signature_value_bytes = private_key.sign(
        canonicalized_signed_info,
        padding.PKCS1v15(),
        hashes.SHA1()
    )
    signature_value.text = base64.b64encode(signature_value_bytes).decode()

    # Append the signature to the XML
    xml_tree.getroot().append(signature)

    print("XML firmado con XAdES-BES correctamente.")
    return xml_tree

def save_signed_xml(signed_xml, output_file_path):
    print(f"Guardando el XML firmado en {output_file_path}...")
    xml_str = etree.tostring(signed_xml, pretty_print=True, xml_declaration=True, encoding='UTF-8').decode('utf-8')
    
    if xml_str.startswith("<?xml"):
        xml_str = xml_str.replace("<?xml version='1.0' encoding='UTF-8'?>", '<?xml version="1.0" encoding="utf-8"?>', 1)
    
    with open(output_file_path, 'wb') as signed_file:
        signed_file.write(xml_str.encode('utf-8'))
    print("XML firmado guardado correctamente.")

def validate_xml_against_xsd(xml_path, xsd_path):
    print("Validando el XML contra el XSD...")
    xmlschema_doc = etree.parse(xsd_path)
    xmlschema = etree.XMLSchema(xmlschema_doc)
    xml_doc = etree.parse(xml_path)
    validation_result = xmlschema.validate(xml_doc)
    if validation_result:
        print("El XML es válido según el XSD.")
    else:
        print("El XML no es válido según el XSD. Errores:")
        for error in xmlschema.error_log:
            print(error)



def handle_sri_response(response):
    response_dict = serialize_object(response)
    estado = response_dict.get('estado')
    if estado == "RECIBIDA":
        logging.info("Comprobante recibido correctamente.")
    elif estado == "DEVUELTA":
        logging.warning("Comprobante devuelto. Motivos:")
        comprobantes = response_dict.get('comprobantes')
        if isinstance(comprobantes, dict) and 'comprobante' in comprobantes:
            for comprobante in comprobantes['comprobante']:
                logging.warning("Clave de Acceso: %s", comprobante['claveAcceso'])
                for mensaje in comprobante['mensajes']['mensaje']:
                    logging.warning("Error %s: %s - %s", mensaje['identificador'], mensaje['mensaje'], mensaje['tipo'])
                    if 'informacionAdicional' in mensaje:
                        logging.warning("Información Adicional: %s", mensaje['informacionAdicional'])
        else:
            logging.error("El formato de response.comprobantes no es el esperado.")
    else:
        logging.error("Estado desconocido: %s", estado)

def document_reception(signed_xml: str, reception_url: str):
    base64_xml = base64.b64encode(signed_xml.encode()).decode()
    
    envelope = f"""
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ec="http://ec.gob.sri.ws.recepcion">
        <soapenv:Header/>
        <soapenv:Body>
            <ec:validarComprobante>
                <xml>{base64_xml}</xml>
            </ec:validarComprobante>
        </soapenv:Body>
    </soapenv:Envelope>
    """

    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "SOAPAction": ""
    }

    try:
        response = requests.post(reception_url, data=envelope, headers=headers, verify=False, timeout=30)
        logging.info(f"Código de estado: {response.status_code}")
        logging.info(f"Respuesta del servidor: {response.text}")
        
        if response.status_code == 200:
            # Eliminar el namespace para facilitar la búsqueda de elementos
            response_content = response.content.decode('utf-8')
            response_content = response_content.replace('ns2:', '')
            root = ET.fromstring(response_content)
            
            estado = root.find(".//estado")
            
            if estado is not None:
                estado_text = estado.text
                logging.info(f"Estado de recepción: {estado_text}")
                result = {"estado": estado_text}
            else:
                logging.warning("No se encontró el estado en la respuesta")
                result = {"estado": "DESCONOCIDO"}

            mensajes = root.findall(".//mensaje")
            if mensajes:
                result["mensajes"] = []
                for mensaje in mensajes:
                    msg = {}
                    for elem in mensaje:
                        msg[elem.tag] = elem.text
                    result["mensajes"].append(msg)
                    logging.warning(f"Mensaje: {msg}")

            return result
        else:
            logging.error(f"Error en la solicitud. Código de estado: {response.status_code}")
            return {"estado": "ERROR_SOLICITUD"}
    except Exception as e:
        logging.error(f"Error en la recepción del documento: {str(e)}")
        return {"estado": "ERROR_EXCEPCION"}

async def document_authorization(access_key: str, authorization_url: str):
    envelope = f"""
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ec="http://ec.gob.sri.ws.autorizacion">
        <soapenv:Header/>
        <soapenv:Body>
            <ec:autorizacionComprobante>
                <claveAccesoComprobante>{access_key}</claveAccesoComprobante>
            </ec:autorizacionComprobante>
        </soapenv:Body>
    </soapenv:Envelope>
    """

    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "SOAPAction": ""
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(authorization_url, data=envelope, headers=headers, ssl=False) as response:
                response_text = await response.text()
                logging.info(f"Código de estado de autorización: {response.status}")
                logging.info(f"Respuesta de autorización del servidor: {response_text}")
                
                # Guardar la respuesta del servidor en un archivo de texto
                with open('respuesta_servidor.txt', 'w', encoding='utf-8') as file:
                    file.write(response_text)

                if response.status == 200:
                    root = ET.fromstring(response_text)
                    numero_comprobantes = root.find(".//numeroComprobantes")
                    if numero_comprobantes is not None and numero_comprobantes.text != "0":
                        autorizaciones = root.findall(".//autorizacion")
                        for autorizacion in autorizaciones:
                            estado = autorizacion.find("estado")
                            if estado is not None:
                                estado_text = estado.text
                                logging.info(f"Estado de autorización: {estado_text}")
                                if estado_text == "AUTORIZADO":
                                    numero_autorizacion = autorizacion.find("numeroAutorizacion").text
                                    fecha_autorizacion = autorizacion.find("fechaAutorizacion").text
                                    return {
                                        "estado": estado_text,
                                        "numeroAutorizacion": numero_autorizacion,
                                        "fechaAutorizacion": fecha_autorizacion
                                    }
                                elif estado_text == "NO AUTORIZADO":
                                    mensajes = autorizacion.findall(".//mensaje")
                                    errores = []
                                    for mensaje in mensajes:
                                        error = {
                                            "identificador": mensaje.find("identificador").text,
                                            "mensaje": mensaje.find("mensaje").text,
                                            "tipo": mensaje.find("tipo").text
                                        }
                                        errores.append(error)
                                    return {"estado": estado_text, "errores": errores}
                    return {"estado": "EN_PROCESO"}
                else:
                    logging.error(f"Error en la solicitud de autorización. Código de estado: {response.status}")
                    return {"estado": "ERROR_SOLICITUD"}
    except Exception as e:
        logging.error(f"Error en la autorización del documento: {str(e)}")
        return {"estado": "ERROR_EXCEPCION"}

async def check_authorization(authorization_url: str, access_key: str, max_retries=12, initial_delay=60):
    logging.info(f"Esperando {initial_delay} segundos antes de iniciar las verificaciones.")
    await asyncio.sleep(initial_delay)

    wait_time = 5
    for attempt in range(max_retries):
        logging.info(f"Intento {attempt + 1} de {max_retries}. Esperando {wait_time} segundos.")
        try:
            result = await document_authorization(access_key, authorization_url)
            if result['estado'] == "AUTORIZADO":
                logging.info(f"Comprobante autorizado correctamente. Número de autorización: {result['numeroAutorizacion']}")
                return True
            elif result['estado'] == "EN_PROCESO":
                logging.info("Comprobante en proceso. Esperando...")
            elif result['estado'] == "NO AUTORIZADO":
                logging.error("Comprobante no autorizado.")
                for error in result.get('errores', []):
                    logging.error(f"Error: {error['mensaje']} (Identificador: {error['identificador']}, Tipo: {error['tipo']})")
                return False
            else:
                logging.warning(f"Estado de autorización desconocido: {result['estado']}")
        except Exception as e:
            logging.error(f"Error al verificar la autorización: {str(e)}")
        await asyncio.sleep(wait_time)
        wait_time = min(wait_time * 2, 300)  # Incremento exponencial del tiempo de espera, máximo 5 minutos
    
    logging.error("No se pudo obtener la autorización después de múltiples intentos.")
    return False



async def process_document(signed_xml: str, access_key: str, reception_url: str, authorization_url: str):
    try:
        reception_result = document_reception(signed_xml, reception_url)
        
        if reception_result.get('estado') in ["RECIBIDA", "DEVUELTA"]:
            if reception_result.get('estado') == "DEVUELTA":
                logging.warning("El comprobante fue devuelto. Revise los mensajes de error.")
                for mensaje in reception_result.get('mensajes', []):
                    logging.warning(f"Error: {mensaje.get('mensaje')} - Tipo: {mensaje.get('tipo')}")
                    logging.warning(f"Información adicional: {mensaje.get('informacionAdicional')}")
            
            logging.info("Procediendo con la autorización...")
            is_authorized = await check_authorization(authorization_url, access_key, initial_delay=10)
            if is_authorized:
                logging.info("Proceso completado con éxito.")
            else:
                logging.error("El comprobante no fue autorizado después de múltiples intentos.")
        else:
            logging.error(f"Estado de recepción inesperado: {reception_result.get('estado')}")
            if 'mensajes' in reception_result:
                for mensaje in reception_result['mensajes']:
                    logging.error(f"Mensaje: {mensaje}")
    except Exception as e:
        logging.error(f"Error en el procesamiento del documento: {str(e)}")
        raise


async def main():
    p12_file_path = r'firma.p12'
    p12_password = '12345678'
    xml_file_path = r'Factura sin firma.xml'
    output_file_path = r'archivo_firmado.xml'
    xsd_path = r'factura_V2.1.0.xsd'

    logging.info("Iniciando proceso de firma de XML...")

    try:
        # Cargar el certificado P12
        with open(p12_file_path, 'rb') as p12_file:
            p12_data = p12_file.read()
            private_key, p12_cert, _ = pkcs12.load_key_and_certificates(p12_data, p12_password.encode(), default_backend())

        # Cargar el XML
        xml_tree = etree.parse(xml_file_path)
        
        # Asegurarse de que el elemento raíz tenga el atributo id="comprobante"
        root = xml_tree.getroot()
        root.set('id', 'comprobante')

        # Firmar el XML
        signed_xml = sign_xml_with_xades(xml_tree, private_key, p12_cert)

        # Guardar el XML firmado
        save_signed_xml(signed_xml, output_file_path)
            
        logging.info("Proceso de firma de XML completado.")

        validate_xml_against_xsd(output_file_path, xsd_path)

        with open(output_file_path, 'r', encoding='utf-8') as file:
            signed_xml_content = file.read()

        wsdl_recepcion = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline'
        wsdl_autorizacion = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline'

        if not test_sri_connection(wsdl_recepcion):
            logging.error("No se pudo establecer conexión con el servidor del SRI. Por favor, verifica tu conexión a internet y la disponibilidad del servicio.")
            return

        clave_acceso = signed_xml.find('.//claveAcceso').text
        await process_document(signed_xml_content, clave_acceso, wsdl_recepcion, wsdl_autorizacion)

    except Exception as e:
        logging.error("Error en el proceso principal: %s", str(e))

if __name__ == "__main__":
    asyncio.run(main())