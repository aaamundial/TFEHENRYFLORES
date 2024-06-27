from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
import spacy

# Cargar el modelo de spaCy para español
nlp = spacy.load("es_core_news_md")

# Lista de meses en español
MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]

def click_unico_boton_en_dialogo(driver, dialog_id):
    try:
        print(f"Buscando el cuadro de diálogo con ID '{dialog_id}'...")
        dialogo = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, dialog_id))
        )
        print("Cuadro de diálogo encontrado.")
        # Encontrar el único botón dentro del cuadro de diálogo
        boton = dialogo.find_element(By.TAG_NAME, "button")
        print(f"Botón encontrado: {boton}")
        boton.click()
        print("Botón clickeado.")
    except TimeoutException:
        print(f"No se pudo encontrar el cuadro de diálogo con ID '{dialog_id}' o el botón dentro de él.")

def determinar_tipo_declaracion(orden):
    doc = nlp(orden.lower())
    for token in doc:
        if token.lemma_ in ["semestral", "semestre", "semestrales"]:
            return "semestral"
        elif token.lemma_ in ["mensual", "mes", "mensuales"]:
            return "mensual"
        elif token.text in MESES:
            return "mensual"
    return None

def seleccionar_opcion_declaracion(select_element, tipo_declaracion):
    if tipo_declaracion == "semestral":
        select_element.select_by_visible_text("2021 - DECLARACIÓN SEMESTRAL IVA")
        print("Opción '2021 - DECLARACIÓN SEMESTRAL IVA' seleccionada.")
    elif tipo_declaracion == "mensual":
        select_element.select_by_visible_text("2011 DECLARACION DE IVA")
        print("Opción '2011  DECLARACION DE IVA' seleccionada.")
    else:
        print("No se encontró una opción válida en la orden.")


def iniciar_sesion(url, usuario, contraseña, orden):
    print("Iniciando sesión...")
    driver = webdriver.Chrome()
    driver.get(url)
    
    time.sleep(2)  # Asegúrate de que la página se cargue completamente antes de buscar los elementos
    
    usuario_input = driver.find_element(By.ID, "usuario")
    contraseña_input = driver.find_element(By.ID, "password")  # Cambiado a 'password'
    
    usuario_input.send_keys(usuario)
    contraseña_input.send_keys(contraseña)
    
    # Encontrar y hacer clic en el botón de inicio de sesión
    login_button = driver.find_element(By.ID, "kc-login")
    login_button.click() 
    print("Sesión iniciada.")

    try:
        declaraciones_button = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "sri-menu"))
        )
        print("Sesión iniciada correctamente.")
    except TimeoutException:
        print("No se pudo iniciar sesión.")
        return None
    
    # Redirigir automáticamente a la página de declaración de IVA
    url_declaracion_iva = "https://srienlinea.sri.gob.ec/sri-declaraciones-web-internet/pages/recepcion/recibirDeclaracion.jsf?identificadorGrupoObligacion=IVA&contextoMPT=https://srienlinea.sri.gob.ec/tuportal-internet&pathMPT=&actualMPT=Formulario%20IVA%20&linkMPT=%2Fsri-declaraciones-web-internet%2Fpages%2Frecepcion%2FrecibirDeclaracion.jsf%3FidentificadorGrupoObligacion%3DIVA&esFavorito=S"
    driver.get(url_declaracion_iva)
    print("Redirigido a la página de declaración de IVA.")

    # Determinar el tipo de declaración
    tipo_declaracion = determinar_tipo_declaracion(orden)

    # Esperar a que el menú desplegable esté presente y visible
    try:
        retries = 3
        for i in range(retries):
            try:
                select_label = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.ID, "frmFlujoDeclaracion:somObligacion_label"))
                )
                select_label.click()  # Hacer clic en el label para desplegar las opciones
                
                # Esperar a que el menú desplegable esté disponible
                select_element = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.ID, "frmFlujoDeclaracion:somObligacion_input"))
                )
                # Crear una instancia de Select y seleccionar la opción "2021 - DECLARACIÓN SEMESTRAL IVA"
                select = Select(select_element)
                seleccionar_opcion_declaracion(select, tipo_declaracion)

                print("Opción 'DECLARACIÓN SEMESTRAL IVA' seleccionada.")
                break  # Salir del bucle si la selección fue exitosa
            except StaleElementReferenceException:
                if i < retries - 1:
                    print("Intentando de nuevo debido a StaleElementReferenceException...")
                    time.sleep(2)
                else:
                    print("No se pudo seleccionar la opción debido a StaleElementReferenceException.")
    except TimeoutException:
        print("No se pudo encontrar el menú desplegable.")
        
    # Manejar la ventana emergente "ESTAMOS EN REMISIÓN" si aparece
    retries = 3
    for i in range(retries):
        try:
            print("Buscando el cuadro de diálogo de mensajes personalizados...")
            aceptar_dialogo = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "frmFlujoDeclaracion:dialogoMensajesPersonalizados"))
            )
            print("Cuadro de diálogo encontrado.")
            time.sleep(2)  # Asegúrate de que el cuadro de diálogo esté completamente cargado
            click_unico_boton_en_dialogo(driver, "frmFlujoDeclaracion:dialogoMensajesPersonalizados")
            break
        except TimeoutException:
            print("No apareció la ventana emergente de remisión.")
            break
        except Exception as e:
            print(f"Error al buscar el cuadro de diálogo o hacer clic en el botón: {e}")




    return driver
    


def resolver_recaptcha(api_key, site_key, url):
    solver = recaptchaV2Proxyless()
    solver.set_verbose(1)
    solver.set_key(api_key)
    solver.set_website_url(url)
    solver.set_website_key(site_key)

    token = solver.solve_and_return_solution()
    if token != 0:
        print("Recaptcha resuelto: " + token)
        return token
    else:
        print("Error al resolver recaptcha: " + solver.error_code)
        return None

def descargar_facturas(driver, mes):
    # Aquí iría el código para navegar al mes deseado y descargar las facturas XML
    print(f"Descargando facturas del mes: {mes}")
    # Implementar la lógica para descargar las facturas
    pass

def generar_reporte_y_declarar_iva(driver, facturas_xml):
    # Aquí iría el código para generar el reporte y declarar el IVA
    print("Generando reporte y declarando IVA...")
    # Implementar la lógica para generar el reporte y declarar el IVA
    pass
