from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from models import Usuario, ControlAsistencia, IncidenciasAsistencia
from sqlalchemy.orm import Session
from database import SessionLocal1, SessionLocal2

from datetime import datetime

import logging
logging.basicConfig(level=logging.DEBUG)


app = FastAPI()

# Carpeta de plantillas
templates = Jinja2Templates(directory="templates")

# Carpeta de archivos estáticos (favicon, css, etc.)
# Si no tienes carpeta static, comenta esta línea
app.mount("/static", StaticFiles(directory="static"), name="static")

# -------------------------------
# Dependencia: obtener usuario actual
# (simplificado: se asume admin con id=1)
# -------------------------------
def get_current_user(user_id: int, db: Session):
    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

# -------------------------------
# Verificación de rol admin
# -------------------------------
def verificar_admin(usuario: Usuario):
    if usuario.rol != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado: se requiere rol admin")
    return usuario

# -------------------------------
# Página principal
# -------------------------------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})



# -------------------------------
# Actualizar estado de usuario (solo admin)
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
def usuarios_html(request: Request):
    db = SessionLocal1()
    # Incluimos también el id para poder desconectar
    usuarios = db.query(Usuario.id, Usuario.nombre, Usuario.apellidos, Usuario.conectado).all()
    db.close()
    return templates.TemplateResponse(
        "usuarios.html",
        {"request": request, "usuarios": usuarios}
    )


# -------------------------------
# Reporte de asistencia por fecha
# -----------------------------


from sqlalchemy import text
from fastapi.responses import HTMLResponse
from datetime import date

@app.get("/reporte_asistencia", response_class=HTMLResponse)
def reporte_asistencia(request: Request, fecha: str = None, area: str = None):
    db = SessionLocal2()

    # Si no se pasa fecha, usar la fecha actual
    if not fecha:
        fecha = date.today().strftime("%Y-%m-%d")

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

    # Si se pasa un área, añadir filtro
    if area:
        sql += " AND carea.nombre = :area"
        params["area"] = area

    sql += " ORDER BY carea.nombre, personal.apellidos, personal.nombre"

    registros = db.execute(text(sql), params).fetchall()
    db.close()

    # Agrupar por área y contar
    areas = {}
    for r in registros:
        area_nombre = r.area_nombre
        if area_nombre not in areas:
            areas[area_nombre] = {"trabajadores": [], "conteo": 0}
        areas[area_nombre]["trabajadores"].append(r)
        areas[area_nombre]["conteo"] += 1

    # Total general
    total = sum(area["conteo"] for area in areas.values())

    return templates.TemplateResponse(
        "reporte_asistencia.html",
        {"request": request, "areas": areas, "fecha": fecha, "total": total, "area": area}
    )




from fastapi.responses import StreamingResponse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from sqlalchemy import text

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

    # Agrupar por área
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
                data.append([
                    r.codigo, r.num_tarjeta, r.nombre, r.apellidos,
                    r.area_codigo, str(r.marca_entrada), str(r.fecha)
                ])

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

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=reporte_asistencia_{fecha}.pdf"}
    )



@app.get("/usuarios/desconectar/{usuario_id}", response_class=HTMLResponse)
def desconectar_usuario(usuario_id: int, request: Request):
    db = SessionLocal1()
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario and usuario.conectado:   # solo si está conectado
        usuario.conectado = False
        db.commit()
    usuarios = db.query(Usuario.id, Usuario.nombre, Usuario.apellidos, Usuario.conectado).all()
    db.close()
    return templates.TemplateResponse(
        "usuarios.html",
        {"request": request, "usuarios": usuarios}
    )







# -------------------------------
# Conteo de asistencia por fecha
# -------------------------------
@app.get("/conteo_asistencia", response_class=HTMLResponse)
def conteo_asistencia(request: Request, fecha: str):
    db = SessionLocal2()
    conteo = db.query(IncidenciasAsistencia).filter(IncidenciasAsistencia.fecha == fecha).count()
    return templates.TemplateResponse("conteo_asistencia.html", {"request": request, "conteo": conteo, "fecha": fecha})
