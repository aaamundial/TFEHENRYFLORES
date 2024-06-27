from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import json
import joblib

# Cargar datos de entrenamiento desde un archivo JSON
with open('train_data.json', 'r', encoding='utf-8') as f:
    train_data = json.load(f)

# Dividir los datos en características y etiquetas
X, y = zip(*train_data)

# Dividir los datos en conjuntos de entrenamiento y prueba
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Crear y entrenar el pipeline
pipeline = make_pipeline(TfidfVectorizer(), LogisticRegression())
pipeline.fit(X_train, y_train)

# Guardar el modelo entrenado
joblib.dump(pipeline, 'modelo_clasificacion.pkl')

print("Modelo entrenado y guardado exitosamente.")

# Función para verificar el modelo
def verificar_modelo():
    # Realizar algunas predicciones de prueba
    ejemplos_prueba = [
        "necesito hacer la declaración semestral del IVA",
        "puedes declarar el IVA mensual",
        "declarar IVA cada mes",
        "presentar declaración semestral"
    ]

    for ejemplo in ejemplos_prueba:
        prediccion = pipeline.predict([ejemplo])
        print(f"Texto: '{ejemplo}' - Predicción: {prediccion[0]}")

    # Evaluar el modelo en el conjunto de prueba
    y_pred = pipeline.predict(X_test)
    print("\nMétricas de evaluación en el conjunto de prueba:")
    print(classification_report(y_test, y_pred))
    print(f"Precisión: {accuracy_score(y_test, y_pred)}")
    print(f"Matriz de confusión:\n{confusion_matrix(y_test, y_pred)}")

    # Evaluar el modelo con validación cruzada
    scores = cross_val_score(pipeline, X, y, cv=5)
    print(f"\nPuntajes de validación cruzada: {scores}")
    print(f"Precisión media de validación cruzada: {scores.mean()}")

verificar_modelo()
