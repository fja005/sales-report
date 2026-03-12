import io
import os
import unicodedata
from uuid import uuid4

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from flask import Flask, render_template, request, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ventas.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

UPLOAD_FOLDER = "static/uploads"
CHART_FOLDER = "static/charts"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHART_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["CHART_FOLDER"] = CHART_FOLDER

db = SQLAlchemy(app)


class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    producto = db.Column(db.String(200), nullable=False)
    categoria = db.Column(db.String(200), nullable=False)
    cantidad = db.Column(db.Float, nullable=False)
    precio = db.Column(db.Float, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "fecha",
            "producto",
            "categoria",
            "cantidad",
            "precio",
            name="uq_venta_unica"
        ),
    )


with app.app_context():
    db.create_all()


def archivo_permitido(filename):
    extensiones_permitidas = {".xlsx", ".csv"}
    _, extension = os.path.splitext(filename.lower())
    return extension in extensiones_permitidas


def limpiar_nombre_columna(col):
    col = str(col).strip().lower()
    col = unicodedata.normalize("NFKD", col).encode("ascii", "ignore").decode("utf-8")
    col = col.replace("_", " ")
    col = " ".join(col.split())
    return col


def normalizar_nombres_columnas(df):
    df.columns = [limpiar_nombre_columna(col) for col in df.columns]

    equivalencias = {
        "categoría": "categoria",
        "fecha venta": "fecha",
        "fecha de venta": "fecha",
        "producto vendido": "producto",
        "precio unitario": "precio",
        "precio venta": "precio",
    }

    df.rename(columns=equivalencias, inplace=True)
    return df


def validar_columnas(df):
    columnas_esperadas = {"fecha", "producto", "categoria", "cantidad", "precio"}
    columnas_archivo = set(df.columns)
    faltantes = columnas_esperadas - columnas_archivo
    return faltantes


def normalizar_dataframe(df):
    df["producto"] = df["producto"].astype(str).str.strip()
    df["categoria"] = df["categoria"].astype(str).str.strip()

    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce")
    df["precio"] = pd.to_numeric(df["precio"], errors="coerce")

    df = df.dropna(subset=["fecha", "producto", "categoria", "cantidad", "precio"]).copy()
    df["total"] = df["cantidad"] * df["precio"]

    # Evitar duplicados dentro del mismo archivo
    df = df.drop_duplicates(subset=["fecha", "producto", "categoria", "cantidad", "precio"])

    return df


def leer_archivo(ruta_archivo):
    _, extension = os.path.splitext(ruta_archivo.lower())

    if extension == ".xlsx":
        return pd.read_excel(ruta_archivo, engine="openpyxl")

    if extension == ".csv":
        try:
            return pd.read_csv(ruta_archivo, sep=None, engine="python", encoding="utf-8-sig")
        except UnicodeDecodeError:
            try:
                return pd.read_csv(ruta_archivo, sep=None, engine="python", encoding="latin-1")
            except Exception as e:
                raise ValueError(
                    "No se pudo leer el archivo CSV. Revisa que sea un CSV válido y que use separador coma (,) o punto y coma (;)."
                ) from e
        except Exception as e:
            raise ValueError(
                "No se pudo leer el archivo CSV. Revisa que sea un CSV válido y que use separador coma (,) o punto y coma (;)."
            ) from e

    raise ValueError("Formato de archivo no soportado. Solo se permiten .xlsx y .csv.")


def generar_grafico_ventas_por_dia(df, filename):
    ventas_dia = df.groupby("fecha")["total"].sum().sort_index()

    plt.figure(figsize=(10, 5))
    ventas_dia.plot(kind="line", marker="o")
    plt.title("Ventas por día")
    plt.xlabel("Fecha")
    plt.ylabel("Ventas")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()


def generar_grafico_ventas_por_categoria(df, filename):
    ventas_categoria = df.groupby("categoria")["total"].sum().sort_values(ascending=False)

    plt.figure(figsize=(10, 5))
    ventas_categoria.plot(kind="bar")
    plt.title("Ventas por categoría")
    plt.xlabel("Categoría")
    plt.ylabel("Ventas")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()


def guardar_ventas_en_db(df):
    nuevas = 0
    duplicadas = 0

    for _, row in df.iterrows():
        fecha = row["fecha"].date()
        producto = row["producto"]
        categoria = row["categoria"]
        cantidad = float(row["cantidad"])
        precio = float(row["precio"])

        existe = Venta.query.filter_by(
            fecha=fecha,
            producto=producto,
            categoria=categoria,
            cantidad=cantidad,
            precio=precio
        ).first()

        if existe:
            duplicadas += 1
            continue

        venta = Venta(
            fecha=fecha,
            producto=producto,
            categoria=categoria,
            cantidad=cantidad,
            precio=precio,
        )
        db.session.add(venta)
        nuevas += 1

    db.session.commit()
    return nuevas, duplicadas


def generar_excel_reporte(df):
    output = io.BytesIO()

    ventas_categoria = (
        df.groupby("categoria")["total"]
        .sum()
        .sort_values(ascending=False)
        .round(2)
        .reset_index()
    )

    top_productos = (
        df.groupby("producto")["cantidad"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )

    ventas_dia = (
        df.groupby("fecha")["total"]
        .sum()
        .sort_index()
        .round(2)
        .reset_index()
    )

    resumen = pd.DataFrame({
        "metrica": ["Ventas Totales", "Ticket Promedio", "Cantidad de registros"],
        "valor": [
            round(df["total"].sum(), 2),
            round(df["total"].mean(), 2),
            len(df)
        ]
    })

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Datos")
        ventas_categoria.to_excel(writer, index=False, sheet_name="Ventas por categoria")
        top_productos.to_excel(writer, index=False, sheet_name="Top productos")
        ventas_dia.to_excel(writer, index=False, sheet_name="Ventas por dia")
        resumen.to_excel(writer, index=False, sheet_name="Resumen")

    output.seek(0)
    return output


def obtener_dataframe_db():
    ventas = Venta.query.all()

    if not ventas:
        return pd.DataFrame(columns=["fecha", "producto", "categoria", "cantidad", "precio", "total"])

    data = [{
        "fecha": venta.fecha,
        "producto": venta.producto,
        "categoria": venta.categoria,
        "cantidad": venta.cantidad,
        "precio": venta.precio,
    } for venta in ventas]

    df = pd.DataFrame(data)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["total"] = df["cantidad"] * df["precio"]
    return df


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/procesar", methods=["POST"])
def procesar():
    if "archivo" not in request.files:
        return render_template("index.html", error="No se envió ningún archivo.")

    archivo = request.files["archivo"]

    if archivo.filename == "":
        return render_template("index.html", error="Debes seleccionar un archivo.")

    if not archivo_permitido(archivo.filename):
        return render_template("index.html", error="Solo se permiten archivos .xlsx o .csv.")

    unique_id = str(uuid4())
    _, extension = os.path.splitext(archivo.filename.lower())
    ruta_archivo = os.path.join(app.config["UPLOAD_FOLDER"], f"{unique_id}{extension}")
    archivo.save(ruta_archivo)

    try:
        df = leer_archivo(ruta_archivo)
        df = normalizar_nombres_columnas(df)

        faltantes = validar_columnas(df)
        if faltantes:
            return render_template(
                "index.html",
                error=(
                    "Faltan estas columnas en el archivo: "
                    + ", ".join(sorted(faltantes))
                    + ". Revisa también si el CSV usa separador coma (,) o punto y coma (;)."
                )
            )

        df = normalizar_dataframe(df)

        if df.empty:
            return render_template(
                "index.html",
                error="El archivo no contiene datos válidos después de la limpieza."
            )

        nuevas, duplicadas = guardar_ventas_en_db(df)

        ventas_totales = round(df["total"].sum(), 2)
        ticket_promedio = round(df["total"].mean(), 2)

        producto_top = (
            df.groupby("producto")["cantidad"]
            .sum()
            .sort_values(ascending=False)
            .index[0]
        )

        ventas_por_categoria = (
            df.groupby("categoria")["total"]
            .sum()
            .sort_values(ascending=False)
            .round(2)
            .to_dict()
        )

        top_productos = (
            df.groupby("producto")["cantidad"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
            .to_dict()
        )

        chart_dia = f"charts/ventas_dia_{unique_id}.png"
        chart_categoria = f"charts/ventas_categoria_{unique_id}.png"

        generar_grafico_ventas_por_dia(df, os.path.join("static", chart_dia))
        generar_grafico_ventas_por_categoria(df, os.path.join("static", chart_categoria))

        return render_template(
            "result.html",
            ventas_totales=ventas_totales,
            ticket_promedio=ticket_promedio,
            producto_top=producto_top,
            ventas_por_categoria=ventas_por_categoria,
            top_productos=top_productos,
            chart_dia=chart_dia,
            chart_categoria=chart_categoria,
            nuevas=nuevas,
            duplicadas=duplicadas
        )

    except Exception as e:
        return render_template("index.html", error=f"Ocurrió un error al procesar el archivo: {e}")


@app.route("/dashboard", methods=["GET"])
def dashboard():
    df = obtener_dataframe_db()

    if df.empty:
        return render_template("dashboard.html", sin_datos=True)

    ventas_totales = round(df["total"].sum(), 2)
    ticket_promedio = round(df["total"].mean(), 2)

    producto_top = (
        df.groupby("producto")["cantidad"]
        .sum()
        .sort_values(ascending=False)
        .index[0]
    )

    ventas_por_categoria = (
        df.groupby("categoria")["total"]
        .sum()
        .sort_values(ascending=False)
        .round(2)
        .to_dict()
    )

    top_productos = (
        df.groupby("producto")["cantidad"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .to_dict()
    )

    total_registros = len(df)

    unique_id = str(uuid4())
    chart_dia = f"charts/dashboard_ventas_dia_{unique_id}.png"
    chart_categoria = f"charts/dashboard_ventas_categoria_{unique_id}.png"

    generar_grafico_ventas_por_dia(df, os.path.join("static", chart_dia))
    generar_grafico_ventas_por_categoria(df, os.path.join("static", chart_categoria))

    return render_template(
        "dashboard.html",
        sin_datos=False,
        ventas_totales=ventas_totales,
        ticket_promedio=ticket_promedio,
        producto_top=producto_top,
        ventas_por_categoria=ventas_por_categoria,
        top_productos=top_productos,
        total_registros=total_registros,
        chart_dia=chart_dia,
        chart_categoria=chart_categoria
    )


@app.route("/descargar-dashboard", methods=["GET"])
def descargar_dashboard():
    df = obtener_dataframe_db()

    if df.empty:
        return "No hay datos para exportar.", 400

    excel = generar_excel_reporte(df)

    return send_file(
        excel,
        download_name="reporte_ventas_dashboard.xlsx",
        as_attachment=True
    )


@app.route("/reiniciar-datos", methods=["POST"])
def reiniciar_datos():
    db.session.query(Venta).delete()
    db.session.commit()
    return render_template("index.html", mensaje="Se eliminaron todos los datos del dashboard.")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)