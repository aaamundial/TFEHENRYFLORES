import firebase_admin
from firebase_admin import credentials, firestore

# Ruta al archivo JSON de credenciales
cred = credentials.Certificate("asistente-tributario-con-ia-firebase-adminsdk-dpfka-2143c990c0.json")
firebase_admin.initialize_app(cred)

# Inicializa el cliente de Firestore
db = firestore.client()

def add_data_to_firestore():
    doc_ref = db.collection('declaraciones').document('data1')
    doc_ref.set({
        'tipo_impuesto': 'IVA',
        'deducciones': 100,
        'fecha_limite': '2024-06-30'
    })

def add_sample_data():
    db.collection('declaraciones').add({
        'tipo_impuesto': 'IVA',
        'deducciones': 100,
        'fecha_limite': '2024-06-30',
        'preguntas_frecuentes': [
            {"pregunta": "¿Qué es el IVA?", "respuesta": "El IVA es un impuesto al valor agregado."},
            {"pregunta": "¿Cómo declaro el IVA?", "respuesta": "Debes seguir los pasos indicados en la página del SRI."}
        ]
    })

    db.collection('declaraciones').add({
        'tipo_impuesto': 'Renta',
        'deducciones': 500,
        'fecha_limite': '2024-04-15',
        'preguntas_frecuentes': [
            {"pregunta": "¿Qué es el impuesto a la renta?", "respuesta": "Es un impuesto sobre los ingresos."},
            {"pregunta": "¿Cómo declaro el impuesto a la renta?", "respuesta": "Debes presentar tu declaración en el portal del SRI."}
        ]
    })

def setup_collections():
    # Colección para tipos de impuestos
    impuestos_ref = db.collection('tipos_de_impuestos')
    impuestos_ref.add({'nombre': 'IVA', 'descripcion': 'Impuesto al Valor Agregado'})
    impuestos_ref.add({'nombre': 'Renta', 'descripcion': 'Impuesto a la Renta'})

    # Colección para deducciones
    deducciones_ref = db.collection('deducciones')
    deducciones_ref.add({'tipo_impuesto': 'IVA', 'monto': 100})
    deducciones_ref.add({'tipo_impuesto': 'Renta', 'monto': 500})

    # Colección para fechas límites
    fechas_ref = db.collection('fechas_limites')
    fechas_ref.add({'tipo_impuesto': 'IVA', 'fecha': '2024-06-30'})
    fechas_ref.add({'tipo_impuesto': 'Renta', 'fecha': '2024-04-15'})
