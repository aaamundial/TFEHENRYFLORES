# fastapi_app.py
from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse

app = FastAPI()

class DeclaracionRequest(BaseModel):
    url: str
    usuario: str
    contraseña: str
    orden: str
    api_key_recaptcha: str
    site_key_recaptcha: str
    aceptar: bool

@app.post("/api/declaracion")
async def declaracion(request: DeclaracionRequest):
    data = request.dict()
    # Aquí puedes llamar a la lógica existente de Flask para procesar la declaración
    # y devolver la respuesta correspondiente.
    return JSONResponse(content={"status": "success"})

class ChatbotRequest(BaseModel):
    pregunta: str

@app.post("/api/chatbot")
async def chatbot(request: ChatbotRequest):
    data = request.dict()
    # Aquí puedes llamar a la lógica existente de Flask para procesar el chatbot
    # y devolver la respuesta correspondiente.
    return JSONResponse(content={"respuesta": "respuesta de ejemplo"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
