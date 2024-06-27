from audio_utils1 import record_audio_to_file
from speech_recognition import interpretar_orden_de_voz
from web_automation import iniciar_sesion, resolver_recaptcha, descargar_facturas, generar_reporte_y_declarar_iva
from selenium.webdriver.common.by import By
import re
import spacy

nlp = spacy.load("es_core_news_md")

# Lista de meses en español
MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]

def procesar_orden(orden):
    print(f"Procesando la orden: {orden}")
    doc = nlp(orden.lower())
    mes = None
    tipo_declaracion = None

    for token in doc:
        if token.text in MESES:
            mes = token.text
        if token.lemma_ in ["semestral", "semestre", "semestrales"]:
            tipo_declaracion = "semestral"
        elif token.lemma_ in ["mensual", "mes", "mensuales"]:
            tipo_declaracion = "mensual"
    
    if tipo_declaracion is None and mes is not None:
        tipo_declaracion = "mensual"
    
    if tipo_declaracion:
        print(f"Tipo de declaración extraído: {tipo_declaracion}")
    else:
        print("No se encontró un tipo de declaración en la orden.")

    if mes:
        print(f"Mes extraído: {mes}")
    else:
        print("No se encontró un mes en la orden.")

    return tipo_declaracion, mes

def automatizar_declaracion_iva(url, usuario, contraseña, orden, api_key_recaptcha, site_key_recaptcha):
    print(f"Automatizando declaración de IVA con la orden: {orden}")
    
    tipo_declaracion, mes = procesar_orden(orden)
    if tipo_declaracion:
        print(f"Iniciando sesión en la URL: {url}")
        driver = iniciar_sesion(url, usuario, contraseña, orden)  # Pasamos la orden completa
        
        if "recaptcha" in driver.page_source:
            print("Se encontró reCAPTCHA en la página.")
            token = resolver_recaptcha(api_key_recaptcha, site_key_recaptcha, url)
            print(f"Token reCAPTCHA obtenido: {token}")
            recaptcha_input = driver.find_element(By.ID, "g-recaptcha-response")
            driver.execute_script("arguments[0].style.display = 'block';", recaptcha_input)
            recaptcha_input.send_keys(token)
            driver.find_element(By.ID, "submit").click()
        
        print(f"Descargando facturas para el mes: {mes}")
        descargar_facturas(driver, mes)
        facturas_xml = []  # Lista de facturas descargadas
        print(f"Generando reporte y declarando IVA.")
        generar_reporte_y_declarar_iva(driver, facturas_xml)
        
        print("El navegador permanecerá abierto para inspección.")
        # driver.quit()  # Comentado para mantener el navegador abierto
    else:
        print("No se pudo entender la orden del usuario.")

if __name__ == "__main__":
    audio_file_path = 'audio_temp.wav'
    print("Grabando audio...")
    record_audio_to_file(audio_file_path, record_seconds=5)  # Graba 5 segundos de audio
    print("Grabación finalizada.")
    orden = interpretar_orden_de_voz(audio_file_path)
    print(f"Orden interpretada: {orden}")

    url = "https://srienlinea.sri.gob.ec/auth/realms/Internet/protocol/openid-connect/auth?client_id=app-sri-claves-angular&redirect_uri=https%3A%2F%2Fsrienlinea.sri.gob.ec%2Fsri-en-linea%2F%2Fcontribuyente%2Fperfil&state=923d6b7e-e718-4383-8e8b-42d1ac3d037c&nonce=8cd8d75d-a789-4f1d-b46c-ba21ed6ed04b&response_mode=fragment&response_type=code&scope=openid"
    usuario = "1718249749001"
    contraseña = "Mlies2023."
    api_key_recaptcha = "TU_API_KEY"
    site_key_recaptcha = "SITE_KEY_DEL_PORTAL"

    automatizar_declaracion_iva(url, usuario, contraseña, orden, api_key_recaptcha, site_key_recaptcha)
