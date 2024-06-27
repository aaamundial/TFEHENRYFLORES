from flask import Flask, render_template, request, jsonify
from audio_utils import record_audio_to_file
from speech_recognition import interpretar_orden_de_voz
from web_automation import iniciar_sesion, resolver_recaptcha, descargar_facturas, generar_reporte_y_declarar_iva
from selenium.webdriver.common.by import By
import re
import spacy
from firebase_admin import credentials, firestore, initialize_app
from firebase_config import db
import nltk
from nltk.corpus import stopwords
from openai import OpenAI
import json
import os
from sklearn.pipeline import make_pipeline
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
import threading
import fitz  # PyMuPDF
import firebase_admin


# Configura tu clave de API de OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "sk-proj-1rDMiZiZxS1uJe1GIHp1T3BlbkFJKNTiJnITxQU9DT4YggB1"))

# Inicializar Firebase solo si no está ya inicializado
if not firebase_admin._apps:
    cred = credentials.Certificate("C:\\Users\\henry\\proyecto1\\eternal-trees-401903-1f41b5f4bd5b.json")
    firebase_admin.initialize_app(cred)


# Obtener referencia a la base de datos Firestore
db = firestore.client()

# Descargar los recursos necesarios de nltk
nltk.download('stopwords')

# Inicializar los componentes de procesamiento de texto
stop_words = set(stopwords.words('spanish'))
nlp = spacy.load("es_core_news_md")

# Lista de meses en español
MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]

flask_app = Flask(__name__)

def preprocess_text(text):
    print(f"Texto original: {text}")
    # Tokenización y eliminación de stop words
    tokens = [word for word in text.split() if word.lower() not in stop_words]
    print(f"Tokens después de eliminar stop words: {tokens}")
    return tokens

def procesar_orden(orden):
    print(f"Procesando la orden: {orden}")
    orden_preprocesada = " ".join(preprocess_text(orden))
    print(f"Orden preprocesada: {orden_preprocesada}")
    doc = nlp(orden_preprocesada.lower())
    mes = None
    tipo_declaracion = None  # Suponiendo que siempre es IVA para simplificar

    # Identificar mes o semestre
    for token in doc:
        print(f"Token: {token.text}, Lema: {token.lemma_}")
        if token.text in MESES:
            mes = token.text
            tipo_declaracion = "mensual"  # Asignamos tipo mensual si se menciona un mes específico
        if "semestre" in token.text:
            tipo_declaracion = "semestral"
            if "primero" in orden_preprocesada or "primer" in orden_preprocesada:
                mes = "primer semestre"
            elif "segundo" in orden_preprocesada:
                mes = "segundo semestre"
    
    print(f"Tipo de declaración clasificado: {tipo_declaracion}")
    if tipo_declaracion and mes:
        return tipo_declaracion, mes
    else:
        print("No se encontró un tipo de declaración o mes en la orden.")
        return None, None

def extraer_texto_desde_pdf(pdf_path):
    documento = fitz.open(pdf_path)
    texto_completo = ""
    for pagina in documento:
        texto_completo += pagina.get_text()
    return texto_completo

def generar_faqs_desde_texto(texto):
    prompt = f"Genera preguntas y respuestas frecuentes basadas en el siguiente texto:\n\n{texto}\n\nFAQs:"
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Eres un asistente de ayuda para generar preguntas frecuentes."},
            {"role": "user", "content": prompt}
        ]
    )
    faqs_texto = response.choices[0].message.content.strip()
    
    faqs = []
    for linea in faqs_texto.split('\n'):
        if 'Pregunta:' in linea and 'Respuesta:' in linea:
            pregunta, respuesta = linea.split('Respuesta:')
            pregunta = pregunta.replace('Pregunta:', '').strip()
            respuesta = respuesta.strip()
            faqs.append({'pregunta': pregunta, 'respuesta': respuesta})
    
    return faqs

def guardar_faqs_en_firestore(faqs):
    for faq in faqs:
        db.collection('faqs').add(faq)

def procesar_pdf_y_actualizar_faqs(pdf_path):
    texto_pdf = extraer_texto_desde_pdf(pdf_path)
    nuevas_faqs = generar_faqs_desde_texto(texto_pdf)
    guardar_faqs_en_firestore(nuevas_faqs)

def responder_con_chatgpt(pregunta):
    faqs = obtener_faqs()  # Obtener FAQs desde Firestore
    faq_prompt = "Aquí tienes algunas preguntas y respuestas frecuentes:\n\n"
    for faq in faqs:
        faq_prompt += f"Pregunta: {faq['pregunta']}\nRespuesta: {faq['respuesta']}\n\n"
    faq_prompt += f"Pregunta del usuario: {pregunta}\nRespuesta:"

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Eres un asistente de ayuda para preguntas frecuentes sobre IVA."},
            {"role": "user", "content": faq_prompt}
        ]
    )
    respuesta = response.choices[0].message.content.strip()
    print(f"Respuesta generada por ChatGPT: {respuesta}")
    return respuesta

def obtener_faqs():
    faqs_ref = db.collection('faqs')
    faqs = []
    for doc in faqs_ref.stream():
        faqs.append(doc.to_dict())
    return faqs

@flask_app.route("/")
def index():
    return render_template("index.html")

@flask_app.route("/api/voice-command", methods=["POST"])
def voice_command():
    audio_file_path = 'audio_temp.wav'
    record_audio_to_file(audio_file_path, record_seconds=5)  # Graba 5 segundos de audio
    orden = interpretar_orden_de_voz(audio_file_path)
    print(f"Orden interpretada: {orden}")
    return jsonify({"orden": orden})

@flask_app.route("/api/declaracion", methods=["POST"])
def declaracion():
    data = request.json
    url = data.get("url")
    usuario = data.get("usuario")
    contraseña = data.get("contraseña")
    orden = data.get("orden")
    api_key_recaptcha = data.get("api_key_recaptcha")
    site_key_recaptcha = data.get("site_key_recaptcha")
    aceptar = data.get("aceptar")

    tipo_declaracion, mes = procesar_orden(orden)
    
    # Almacenar la orden y su interpretación en Firebase
    db.collection('ordenes').add({
        'usuario': usuario,
        'orden_original': orden,
        'tipo_declaracion': tipo_declaracion,
        'mes': mes,
        'aceptar': aceptar,
        'timestamp': firestore.SERVER_TIMESTAMP
    })

    if aceptar:
        nuevas_ordenes = [(orden, tipo_declaracion)]
        entrenar_modelo_con_nuevas_ordenes(nuevas_ordenes)

        automatizar_declaracion_iva(url, usuario, contraseña, orden, api_key_recaptcha, site_key_recaptcha)
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "orden rechazada"})

@flask_app.route("/api/chatbot", methods=["POST"])
def chatbot():
    data = request.json
    pregunta = data.get("pregunta")
    print(f"Pregunta recibida: {pregunta}")  # Depuración
    
    # Obtener respuesta de ChatGPT utilizando tus FAQs
    respuesta = responder_con_chatgpt(pregunta)
    print(f"Respuesta enviada: {respuesta}")  # Depuración
    return jsonify({"respuesta": respuesta})

@flask_app.route('/admin/faqs', methods=['GET', 'POST'])
def admin_faqs():
    if request.method == 'POST':
        pdf_file = request.files.get('pdf_file')
        if pdf_file:
            try:
                # Crear el directorio 'uploads' si no existe
                uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
                os.makedirs(uploads_dir, exist_ok=True)
                
                pdf_path = os.path.join(uploads_dir, pdf_file.filename)
                pdf_file.save(pdf_path)
                procesar_pdf_y_actualizar_faqs(pdf_path)
                return jsonify({"status": "success", "message": "PDF procesado y FAQs actualizadas"})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)})
    
    faqs = obtener_faqs()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"faqs": faqs})
    return render_template('admin_faqs.html', faqs=faqs)

def cargar_modelo():
    return joblib.load('modelo_clasificacion.pkl')

def guardar_modelo(modelo):
    joblib.dump(modelo, 'modelo_clasificacion.pkl')

def entrenar_modelo_con_nuevas_ordenes(nuevas_ordenes):
    # Cargar datos de entrenamiento existentes
    with open('train_data.json', 'r', encoding='utf-8') as f:
        train_data = json.load(f)
    
    # Añadir nuevas órdenes al conjunto de datos
    train_data.extend(nuevas_ordenes)
    
    # Dividir los datos en características y etiquetas
    X_train, y_train = zip(*train_data)
    
    # Crear y entrenar el pipeline
    pipeline = make_pipeline(TfidfVectorizer(), LogisticRegression())
    pipeline.fit(X_train, y_train)
    
    # Guardar el nuevo modelo entrenado
    guardar_modelo(pipeline)
    
    # Guardar el conjunto de datos actualizado
    with open('train_data.json', 'w', encoding='utf-8') as f:
        json.dump(train_data, f)

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
        
        print(f"Descargando facturas para el mes o semestre: {mes}")
        descargar_facturas(driver, mes)
        facturas_xml = []  # Lista de facturas descargadas
        print(f"Generando reporte y declarando IVA.")
        generar_reporte_y_declarar_iva(driver, facturas_xml)

        # Almacenar la declaración en Firebase
        db.collection('declaraciones').add({
            'usuario': usuario,
            'tipo_declaracion': tipo_declaracion,
            'mes': mes,
            'estado': 'completado',
            'orden_original': orden,
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        
        print("El navegador permanecerá abierto para inspección.")
        # driver.quit()  # Comentado para mantener el navegador abierto
    else:
        print("No se pudo entender la orden del usuario.")

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(debug=True, use_reloader=False, host="0.0.0.0", port=port)

if __name__ == "__main__":
    nlp = spacy.load("es_core_news_md")
    threading.Thread(target=run_flask).start()
