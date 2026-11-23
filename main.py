import os
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from peewee import Model, CharField, AutoField
from playhouse.db_url import connect

# Carga las variables del archivo .env si existe (para pruebas locales)
load_dotenv()

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("Falta la variable de entorno DATABASE_URL")

db = connect(DATABASE_URL)

class Tarea(Model):
    id = AutoField()
    titulo = CharField()

    class Meta:
        database = db
        table_name = "tareas"

# Conecta y crea la tabla en Supabase automáticamente si no existe
db.connect()
db.create_tables([Tarea], safe=True)
db.close()

@app.middleware("http")
async def db_session_middleware(request, call_next):
    if db.is_closed():
        db.connect()
    try:
        response = await call_next(request)
    finally:
        if not db.is_closed():
            db.close()
    return response

class TareaSchema(BaseModel):
    titulo: str

@app.get("/api/tareas")
def obtener_tareas():
    tareas = Tarea.select().order_by(Tarea.id.desc())
    return [{"id": t.id, "titulo": t.titulo} for t in tareas]

@app.post("/api/tareas")
def crear_tarea(tarea: TareaSchema):
    nueva = Tarea.create(titulo=tarea.titulo)
    return {"id": nueva.id, "titulo": nueva.titulo}
