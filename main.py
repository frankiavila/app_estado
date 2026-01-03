from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from datetime import datetime, date
from sqlalchemy import text
from datetime import date
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from starlette.middleware.sessions import SessionMiddleware
from fastapi import Depends

import logging
logging.basicConfig(level=logging.DEBUG)

# Modelos y DB
from models import Usuario, ControlAsistencia, IncidenciasAsistencia
from database import SessionLocal1, SessionLocal2

# LDAP
from ldap_auth import authenticate_user, get_informatica_members


app = FastAPI()

# Plantillas y estáticos
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")



# Configuración de sesiones
app.add_middleware(
    SessionMiddleware,
    secret_key="una_clave_super_segura_y_larga",
    session_cookie="mi_sesion",
    max_age=3600,
    same_site="lax",
    https_only=False
)

# 🔑 Definir require_role ANTES de usarlo
def require_role(role: str):
    def wrapper(request: Request):
        user = request.session.get("user")
        if not user or role not in user["groups"]:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        return user
    return wrapper


# -------------------------------
# Página principal
# -------------------------------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("index.html", {
        "request": request,
        "username": user["username"],
        "groups": user["groups"]
    })


# -------------------------------
# Actualizar estado de usuario
# -------------------------------
@app.post("/actualizar_estado")
def actualizar_estado(id: int = Form(...), conectado: bool = Form(...)):
    db = SessionLocal1()
    usuario_obj = db.query(Usuario).filter(Usuario.id == id).first()
    if usuario_obj:
        usuario_obj.conectado = conectado
        db.commit()
        db.refresh(usuario_obj)
        db.close()
        return {"mensaje": "Estado actualizado", "usuario": usuario_obj.nombre}
    db.close()
    return {"mensaje": "Usuario no encontrado"}

# -------------------------------
# Listado de usuarios
# -------------------------------

@app.get("/usuarios", response_class=HTMLResponse)

@app.get("/usuarios", response_class=HTMLResponse)
def usuarios_html(request: Request):
    db = SessionLocal1()
    usuarios = db.query(Usuario.id, Usuario.nombre, Usuario.apellidos, Usuario.conectado).all()
    db.close()
    return templates.TemplateResponse("usuarios.html", {"request": request, "usuarios": usuarios})

# -------------------------------
# Reporte de asistencia por fecha
# -------------------------------
@app.get("/reporte_asistencia", response_class=HTMLResponse)  
def reporte_asistencia(request: Request, fecha: str = None, area: str = None):

    if not fecha:
        fecha = date.today().strftime("%Y-%m-%d")

    db = SessionLocal2()
    sql = """
        SELECT personal.codigo,
               personal.num_tarjeta,
               personal.nombre,
               personal.apellidos,
               carea.nombre AS area_nombre,
               carea.codigo AS area_codigo,
               incidencias_asistencia.marca_entrada,
               incidencias_asistencia.fecha
        FROM personal
        INNER JOIN carea ON personal.carea_fk = carea.id
        INNER JOIN control_asistencia ON control_asistencia.id_person = personal.id
        INNER JOIN incidencias_asistencia ON incidencias_asistencia.control_asistencia_fk = control_asistencia.id
        WHERE incidencias_asistencia.fecha::date = :fecha
          AND incidencias_asistencia.marca_entrada IS NOT NULL
    """
    params = {"fecha": fecha}
    if area:
        sql += " AND carea.nombre = :area"
        params["area"] = area
    sql += " ORDER BY carea.nombre, personal.apellidos, personal.nombre"

    registros = db.execute(text(sql), params).fetchall()
    db.close()

    areas = {}
    for r in registros:
        area_nombre = r.area_nombre
        if area_nombre not in areas:
            areas[area_nombre] = {"trabajadores": [], "conteo": 0}
        areas[area_nombre]["trabajadores"].append(r)
        areas[area_nombre]["conteo"] += 1

    total = sum(area["conteo"] for area in areas.values())

    return templates.TemplateResponse("reporte_asistencia.html", {
        "request": request, "areas": areas, "fecha": fecha, "total": total, "area": area
    })

# -------------------------------
# Reporte PDF
# -------------------------------
@app.get("/reporte_asistencia_pdf")
def reporte_asistencia_pdf(fecha: str, area: str = None):
    db = SessionLocal2()
    sql = """
        SELECT personal.codigo,
               personal.num_tarjeta,
               personal.nombre,
               personal.apellidos,
               carea.nombre AS area_nombre,
               carea.codigo AS area_codigo,
               incidencias_asistencia.marca_entrada,
               incidencias_asistencia.fecha
        FROM personal
        INNER JOIN carea ON personal.carea_fk = carea.id
        INNER JOIN control_asistencia ON control_asistencia.id_person = personal.id
        INNER JOIN incidencias_asistencia ON incidencias_asistencia.control_asistencia_fk = control_asistencia.id
        WHERE incidencias_asistencia.fecha::date = :fecha
          AND incidencias_asistencia.marca_entrada IS NOT NULL
    """
    params = {"fecha": fecha}
    if area:
        sql += " AND carea.nombre = :area"
        params["area"] = area
    sql += " ORDER BY carea.nombre, personal.apellidos, personal.nombre"

    registros = db.execute(text(sql), params).fetchall()
    db.close()

    areas = {}
    for r in registros:
        area_nombre = r.area_nombre
        if area_nombre not in areas:
            areas[area_nombre] = []
        areas[area_nombre].append(r)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    titulo = f"Reporte de Asistencia - {fecha}"
    if area:
        titulo += f" (Área: {area})"
    elements.append(Paragraph(titulo, styles['Title']))
    elements.append(Spacer(1, 12))

    if not registros:
        elements.append(Paragraph("No hay datos para los filtros seleccionados.", styles['Normal']))
    else:
        for area_nombre, trabajadores in areas.items():
            elements.append(Paragraph(f"Área: {area_nombre} ({len(trabajadores)} presentes)", styles['Heading2']))
            data = [["Código", "Tarjeta", "Nombre", "Apellidos", "Código Área", "Entrada", "Fecha"]]
            for r in trabajadores:
                data.append([r.codigo, r.num_tarjeta, r.nombre, r.apellidos,
                             r.area_codigo, str(r.marca_entrada), str(r.fecha)])
            table = Table(data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#003366")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 10),
                ('BOTTOMPADDING', (0,0), (-1,0), 8),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f2f2f2")),
                ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 20))

    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="application/pdf",
                             headers={"Content-Disposition": f"attachment; filename=reporte_asistencia_{fecha}.pdf"})

# -------------------------------
# Desconectar usuario
# -------------------------------
@app.get("/usuarios/desconectar/{usuario_id}", response_class=HTMLResponse)
def desconectar_usuario(usuario_id: int, request: Request):
    db = SessionLocal1()
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario and usuario.conectado:
        usuario.conectado = False
        db.commit()
    usuarios = db.query(Usuario.id, Usuario.nombre, Usuario.apellidos, Usuario.conectado).all()
    db.close()
    return templates.TemplateResponse("usuarios.html", {"request": request, "usuarios": usuarios})

# -------------------------------
# Conteo asistencia
# -------------------------------

@app.get("/conteo_asistencia", response_class=HTMLResponse)
def conteo_asistencia(request: Request, fecha: str = None):
    if fecha:
        try:
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usa YYYY-MM-DD")
    else:
        fecha_obj = date.today()  # 👈 usa la fecha actual si no se pasa parámetro

    db = SessionLocal2()
    conteo = db.query(IncidenciasAsistencia).filter(IncidenciasAsistencia.fecha == fecha_obj).count()
    db.close()

    return templates.TemplateResponse(
        "conteo_asistencia.html",
        {"request": request, "conteo": conteo, "fecha": fecha_obj}
    )





# -------------------------------
# Login LDAP
# -------------------------------
@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    # Renderiza el formulario vacío
    return templates.TemplateResponse("login.html", {"request": request})

from fastapi.responses import RedirectResponse

@app.post("/login")

def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = authenticate_user(username, password)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Credenciales inválidas"})
    
    # Guardar usuario en sesión
    request.session["user"] = {"username": user["username"], "groups": user["groups"]}
    
    # Redirigir al dashboard principal
    return RedirectResponse(url="/", status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login")




