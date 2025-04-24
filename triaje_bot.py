
from flask import Flask, request
import openai
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
symptom_data = pd.read_csv("sintomas.csv")
symptom_data["sintoma"] = symptom_data["sintoma"].str.lower()

user_sessions = {}

flow = {
    "inicio": {
        "mensaje": "👋 ¡Hola! Soy tu asistente de salud. Vamos a evaluar tus síntomas paso a paso. ¿Estás listo? (responde sí/no)",
        "siguiente": "edad"
    },
    "edad": {
        "mensaje": "🧒 ¿Cuál es tu edad?",
        "siguiente": "genero"
    },
    "genero": {
        "mensaje": "👤 ¿Cuál es tu sexo asignado al nacer? (masculino/femenino)",
        "siguiente": "localizacion"
    },
    "localizacion": {
        "mensaje": "📍 ¿Dónde sientes el síntoma principal?\n- Cabeza\n- Pecho\n- Abdomen\n- Extremidades\n- Todo el cuerpo",
        "siguiente": "tipo_sintoma"
    },
    "tipo_sintoma": {
        "mensaje": "🩺 ¿Cuál es el síntoma principal que estás presentando?\n- Dolor\n- Fiebre\n- Mareo\n- Tos\n- Sangrado\n- Otro",
        "siguiente": "intensidad"
    },
    "intensidad": {
        "mensaje": "📊 ¿Qué tan intenso es el síntoma en una escala del 1 al 10?",
        "siguiente": "sintomas_alarma"
    },
    "sintomas_alarma": {
        "mensaje": "🚨 ¿Tienes alguno de estos síntomas? Responde sí o no a cada uno:\n- Pérdida del conocimiento\n- Dificultad para respirar\n- Dolor intenso en el pecho\n- Vómito con sangre\n- Convulsiones",
        "siguiente": "evaluacion"
    },
    "evaluacion": {
        "mensaje": "Gracias por tus respuestas. Estoy evaluando tu caso... ⏳",
        "siguiente": "recomendacion"
    },
    "recomendacion": {
        "mensaje": "🤖 Basado en tus respuestas, recibirás una recomendación sobre el nivel de atención necesario.",
        "siguiente": None
    }
}

@app.route("/whatsapp", methods=["POST"])
def whatsapp_bot():
    phone = request.form.get("From", "default").split(":")[-1]
    msg = request.form.get("Body", "").strip().lower()

    if phone not in user_sessions:
        user_sessions[phone] = {"etapa": "inicio", "respuestas": {}}
    etapa_actual = user_sessions[phone]["etapa"]
    siguiente = flow[etapa_actual]["siguiente"]

    if etapa_actual not in ["inicio", "evaluacion", "recomendacion"]:
        user_sessions[phone]["respuestas"][etapa_actual] = msg

    if etapa_actual == "evaluacion":
        datos = user_sessions[phone]["respuestas"]
        sintomas_texto = datos.get("tipo_sintoma", "")

        # 1. Buscar coincidencia exacta en base de síntomas
        coincidencia = symptom_data[symptom_data["sintoma"] == sintomas_texto]
        if not coincidencia.empty:
            row = coincidencia.iloc[0]
            respuesta = f"{row['clasificacion']}\n\n{row['recomendacion']}"
        else:
            # 2. Evaluación personalizada por lógica
            intensidad = int(datos.get("intensidad", "0")) if datos.get("intensidad", "0").isdigit() else 0
            alarma = "sí" in datos.get("sintomas_alarma", "")
            if intensidad > 7 or alarma:
                respuesta = "🚨 Atención de emergencia\n\nPor favor acude a un centro médico de inmediato."
            elif intensidad >= 4:
                respuesta = "⏳ Puede esperar\n\nAgenda una cita médica pronto."
            else:
                respuesta = "✅ No requiere atención médica inmediata\n\nMonitorea tus síntomas."

        user_sessions[phone]["etapa"] = "recomendacion"
        return respuesta + "\n\n*Este resultado no reemplaza una consulta médica presencial.*"

    respuesta = flow[etapa_actual]["mensaje"]
    user_sessions[phone]["etapa"] = siguiente if siguiente else "inicio"
    return respuesta

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

