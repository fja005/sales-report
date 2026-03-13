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

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "sqlite:///ventas.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

UPLOAD_FOLDER = "static/uploads"
CHART_FOLDER = "static/charts"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHART_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["CHART_FOLDER"] = CHART_FOLDER

db = SQLAlchemy(app)


TRANSLATIONS = {
    "es": {
        "app_title": "Reporte de Ventas",
        "hero_title": "Convierte tu archivo en un reporte claro de ventas",
        "hero_subtitle": "Sube un Excel o CSV y obtén métricas, gráficos y un dashboard separado por negocio.",
        "sales_total": "Ventas totales",
        "sales_total_desc": "Mide rápido cuánto vendiste",
        "top_products": "Productos top",
        "top_products_desc": "Descubre qué impulsa tu negocio",
        "business_dashboard": "Dashboard por negocio",
        "business_dashboard_desc": "Cada negocio ve solo sus propios datos",
        "required_format": "Formato requerido del archivo:",
        "business_name": "Nombre del negocio",
        "business_placeholder": "Ejemplo: Cafetería Central",
        "file_label": "Archivo Excel o CSV (.xlsx o .csv)",
        "generate_report": "Generar reporte",
        "view_dashboard": "Ver dashboard acumulado",
        "view_business_dashboard": "Ver dashboard de un negocio",
        "write_business_name": "Escribe el nombre del negocio",
        "reset_business_data": "Reiniciar datos de un negocio",
        "reset_button": "Reiniciar datos del negocio",
        "back_home": "Volver al inicio",
        "go_dashboard": "Ir al dashboard",
        "report_result": "Resultado del reporte",
        "business": "Negocio",
        "new_records": "Registros nuevos guardados",
        "duplicate_records": "Registros duplicados omitidos",
        "file_sales_total": "Ventas totales del archivo",
        "avg_ticket": "Ticket promedio",
        "best_selling_product": "Producto más vendido",
        "sales_by_category": "Ventas por categoría",
        "chart_sales_by_day": "Gráfico: ventas por día",
        "chart_sales_by_category": "Gráfico: ventas por categoría",
        "dashboard_title": "Dashboard por negocio",
        "download_excel": "Descargar Excel",
        "no_data_business": "No hay ventas guardadas para el negocio:",
        "total_saved_records": "Registros guardados",
        "accumulated_sales_total": "Ventas totales acumuladas",
        "accumulated_avg_ticket": "Ticket promedio",
        "accumulated_chart_day": "Gráfico acumulado: ventas por día",
        "accumulated_chart_category": "Gráfico acumulado: ventas por categoría",
        "ask_business_name": "Debes indicar el nombre del negocio.",
        "no_file_sent": "No se envió ningún archivo.",
        "select_file": "Debes seleccionar un archivo.",
        "invalid_format": "Solo se permiten archivos .xlsx o .csv.",
        "csv_error": "No se pudo leer el archivo CSV. Revisa que sea un CSV válido y que use separador coma (,) o punto y coma (;).",
        "unsupported_format": "Formato de archivo no soportado. Solo se permiten .xlsx y .csv.",
        "missing_columns_prefix": "Faltan estas columnas en el archivo:",
        "missing_columns_suffix": "Revisa también si el CSV usa separador coma (,) o punto y coma (;).",
        "empty_after_clean": "El archivo no contiene datos válidos después de la limpieza.",
        "processing_error": "Ocurrió un error al procesar el archivo:",
        "deleted_business_data": "Se eliminaron todos los datos del negocio:",
        "must_indicate_business": "Debes indicar un negocio.",
        "no_data_export": "No hay datos para exportar.",
        "language": "Idioma",
    },
    "en": {
        "app_title": "Sales Report",
        "hero_title": "Turn your file into a clear sales report",
        "hero_subtitle": "Upload an Excel or CSV file and get metrics, charts, and a business-specific dashboard.",
        "sales_total": "Total sales",
        "sales_total_desc": "Quickly measure how much you sold",
        "top_products": "Top products",
        "top_products_desc": "See what drives your business",
        "business_dashboard": "Business dashboard",
        "business_dashboard_desc": "Each business sees only its own data",
        "required_format": "Required file format:",
        "business_name": "Business name",
        "business_placeholder": "Example: Central Coffee Shop",
        "file_label": "Excel or CSV file (.xlsx or .csv)",
        "generate_report": "Generate report",
        "view_dashboard": "View accumulated dashboard",
        "view_business_dashboard": "View a business dashboard",
        "write_business_name": "Type the business name",
        "reset_business_data": "Reset business data",
        "reset_button": "Reset business data",
        "back_home": "Back to home",
        "go_dashboard": "Go to dashboard",
        "report_result": "Report result",
        "business": "Business",
        "new_records": "New saved records",
        "duplicate_records": "Duplicate records skipped",
        "file_sales_total": "File total sales",
        "avg_ticket": "Average ticket",
        "best_selling_product": "Best-selling product",
        "sales_by_category": "Sales by category",
        "chart_sales_by_day": "Chart: sales by day",
        "chart_sales_by_category": "Chart: sales by category",
        "dashboard_title": "Business dashboard",
        "download_excel": "Download Excel",
        "no_data_business": "There are no saved sales for business:",
        "total_saved_records": "Saved records",
        "accumulated_sales_total": "Accumulated total sales",
        "accumulated_avg_ticket": "Average ticket",
        "accumulated_chart_day": "Accumulated chart: sales by day",
        "accumulated_chart_category": "Accumulated chart: sales by category",
        "ask_business_name": "You must enter the business name.",
        "no_file_sent": "No file was sent.",
        "select_file": "You must select a file.",
        "invalid_format": "Only .xlsx and .csv files are allowed.",
        "csv_error": "The CSV file could not be read. Make sure it is a valid CSV and uses comma (,) or semicolon (;) as separator.",
        "unsupported_format": "Unsupported file format. Only .xlsx and .csv are allowed.",
        "missing_columns_prefix": "These columns are missing in the file:",
        "missing_columns_suffix": "Also check whether the CSV uses comma (,) or semicolon (;) as separator.",
        "empty_after_clean": "The file contains no valid data after cleaning.",
        "processing_error": "An error occurred while processing the file:",
        "deleted_business_data": "All data was deleted for business:",
        "must_indicate_business": "You must specify a business.",
        "no_data_export": "There is no data to export.",
        "language": "Language",
    },
    "id": {
        "app_title": "Laporan Penjualan",
        "hero_title": "Ubah file Anda menjadi laporan penjualan yang jelas",
        "hero_subtitle": "Unggah file Excel atau CSV dan dapatkan metrik, grafik, serta dashboard khusus bisnis.",
        "sales_total": "Total penjualan",
        "sales_total_desc": "Lihat dengan cepat berapa banyak yang terjual",
        "top_products": "Produk teratas",
        "top_products_desc": "Lihat apa yang mendorong bisnis Anda",
        "business_dashboard": "Dashboard bisnis",
        "business_dashboard_desc": "Setiap bisnis hanya melihat datanya sendiri",
        "required_format": "Format file yang diperlukan:",
        "business_name": "Nama bisnis",
        "business_placeholder": "Contoh: Kafe Central",
        "file_label": "File Excel atau CSV (.xlsx atau .csv)",
        "generate_report": "Buat laporan",
        "view_dashboard": "Lihat dashboard terkumpul",
        "view_business_dashboard": "Lihat dashboard bisnis",
        "write_business_name": "Tulis nama bisnis",
        "reset_business_data": "Reset data bisnis",
        "reset_button": "Reset data bisnis",
        "back_home": "Kembali ke beranda",
        "go_dashboard": "Pergi ke dashboard",
        "report_result": "Hasil laporan",
        "business": "Bisnis",
        "new_records": "Data baru tersimpan",
        "duplicate_records": "Data duplikat diabaikan",
        "file_sales_total": "Total penjualan file",
        "avg_ticket": "Rata-rata tiket",
        "best_selling_product": "Produk terlaris",
        "sales_by_category": "Penjualan per kategori",
        "chart_sales_by_day": "Grafik: penjualan per hari",
        "chart_sales_by_category": "Grafik: penjualan per kategori",
        "dashboard_title": "Dashboard bisnis",
        "download_excel": "Unduh Excel",
        "no_data_business": "Belum ada data penjualan tersimpan untuk bisnis:",
        "total_saved_records": "Data tersimpan",
        "accumulated_sales_total": "Total penjualan terkumpul",
        "accumulated_avg_ticket": "Rata-rata tiket",
        "accumulated_chart_day": "Grafik terkumpul: penjualan per hari",
        "accumulated_chart_category": "Grafik terkumpul: penjualan per kategori",
        "ask_business_name": "Anda harus mengisi nama bisnis.",
        "no_file_sent": "Tidak ada file yang dikirim.",
        "select_file": "Anda harus memilih file.",
        "invalid_format": "Hanya file .xlsx dan .csv yang diperbolehkan.",
        "csv_error": "File CSV tidak dapat dibaca. Pastikan file valid dan menggunakan pemisah koma (,) atau titik koma (;).",
        "unsupported_format": "Format file tidak didukung. Hanya .xlsx dan .csv yang diperbolehkan.",
        "missing_columns_prefix": "Kolom berikut tidak ada dalam file:",
        "missing_columns_suffix": "Periksa juga apakah CSV menggunakan pemisah koma (,) atau titik koma (;).",
        "empty_after_clean": "File tidak memiliki data valid setelah pembersihan.",
        "processing_error": "Terjadi kesalahan saat memproses file:",
        "deleted_business_data": "Semua data bisnis telah dihapus:",
        "must_indicate_business": "Anda harus menentukan bisnis.",
        "no_data_export": "Tidak ada data untuk diekspor.",
        "language": "Bahasa",
    },
}


def get_lang():
    lang = request.args.get("lang", "es").lower()
    if lang not in TRANSLATIONS:
        lang = "es"
    return lang


def tr(lang, key):
    return TRANSLATIONS.get(lang, TRANSLATIONS["es"]).get(key, key)


class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    negocio = db.Column(db.String(200), nullable=False, index=True)
    fecha = db.Column(db.Date, nullable=False)
    producto = db.Column(db.String(200), nullable=False)
    categoria = db.Column(db.String(200), nullable=False)
    cantidad = db.Column(db.Float, nullable=False)
    precio = db.Column(db.Float, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "negocio",
            "fecha",
            "producto",
            "categoria",
            "cantidad",
            "precio",
            name="uq_venta_unica_por_negocio"
        ),
    )


with app.app_context():
    db.create_all()


def archivo_permitido(filename):
    extensiones_permitidas = {".xlsx", ".csv"}
    _, extension = os.path.splitext(filename.lower())
    return extension in extensiones_permitidas


def limpiar_texto(valor):
    return str(valor).strip()


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

    df = df.drop_duplicates(subset=["fecha", "producto", "categoria", "cantidad", "precio"])

    return df


def leer_archivo(ruta_archivo, lang):
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
                raise ValueError(tr(lang, "csv_error")) from e
        except Exception as e:
            raise ValueError(tr(lang, "csv_error")) from e

    raise ValueError(tr(lang, "unsupported_format"))


def generar_grafico_ventas_por_dia(df, filename):
    ventas_dia = df.groupby("fecha")["total"].sum().sort_index()

    plt.figure(figsize=(10, 5))
    ventas_dia.plot(kind="line", marker="o")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()


def generar_grafico_ventas_por_categoria(df, filename):
    ventas_categoria = df.groupby("categoria")["total"].sum().sort_values(ascending=False)

    plt.figure(figsize=(10, 5))
    ventas_categoria.plot(kind="bar")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()


def guardar_ventas_en_db(df, negocio):
    nuevas = 0
    duplicadas = 0

    for _, row in df.iterrows():
        fecha = row["fecha"].date()
        producto = row["producto"]
        categoria = row["categoria"]
        cantidad = float(row["cantidad"])
        precio = float(row["precio"])

        existe = Venta.query.filter_by(
            negocio=negocio,
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
            negocio=negocio,
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


def obtener_dataframe_db(negocio):
    ventas = Venta.query.filter_by(negocio=negocio).all()

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
    lang = get_lang()
    return render_template("index.html", lang=lang, t=TRANSLATIONS[lang])


@app.route("/procesar", methods=["POST"])
def procesar():
    lang = get_lang()
    negocio = limpiar_texto(request.form.get("negocio", ""))

    if not negocio:
        return render_template("index.html", lang=lang, t=TRANSLATIONS[lang], error=tr(lang, "ask_business_name"))

    if "archivo" not in request.files:
        return render_template("index.html", lang=lang, t=TRANSLATIONS[lang], error=tr(lang, "no_file_sent"))

    archivo = request.files["archivo"]

    if archivo.filename == "":
        return render_template("index.html", lang=lang, t=TRANSLATIONS[lang], error=tr(lang, "select_file"))

    if not archivo_permitido(archivo.filename):
        return render_template("index.html", lang=lang, t=TRANSLATIONS[lang], error=tr(lang, "invalid_format"))

    unique_id = str(uuid4())
    _, extension = os.path.splitext(archivo.filename.lower())
    ruta_archivo = os.path.join(app.config["UPLOAD_FOLDER"], f"{unique_id}{extension}")
    archivo.save(ruta_archivo)

    try:
        df = leer_archivo(ruta_archivo, lang)
        df = normalizar_nombres_columnas(df)

        faltantes = validar_columnas(df)
        if faltantes:
            return render_template(
                "index.html",
                lang=lang,
                t=TRANSLATIONS[lang],
                error=(
                    f"{tr(lang, 'missing_columns_prefix')} "
                    + ", ".join(sorted(faltantes))
                    + f". {tr(lang, 'missing_columns_suffix')}"
                )
            )

        df = normalizar_dataframe(df)

        if df.empty:
            return render_template(
                "index.html",
                lang=lang,
                t=TRANSLATIONS[lang],
                error=tr(lang, "empty_after_clean")
            )

        nuevas, duplicadas = guardar_ventas_en_db(df, negocio)

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
            lang=lang,
            t=TRANSLATIONS[lang],
            negocio=negocio,
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
        return render_template(
            "index.html",
            lang=lang,
            t=TRANSLATIONS[lang],
            error=f"{tr(lang, 'processing_error')} {e}"
        )


@app.route("/dashboard", methods=["GET"])
def dashboard():
    lang = get_lang()
    negocio = limpiar_texto(request.args.get("negocio", ""))

    if not negocio:
        return render_template(
            "dashboard.html",
            lang=lang,
            t=TRANSLATIONS[lang],
            pedir_negocio=True,
            sin_datos=False
        )

    df = obtener_dataframe_db(negocio)

    if df.empty:
        return render_template(
            "dashboard.html",
            lang=lang,
            t=TRANSLATIONS[lang],
            pedir_negocio=False,
            sin_datos=True,
            negocio=negocio
        )

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
        lang=lang,
        t=TRANSLATIONS[lang],
        pedir_negocio=False,
        sin_datos=False,
        negocio=negocio,
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
    lang = get_lang()
    negocio = limpiar_texto(request.args.get("negocio", ""))

    if not negocio:
        return tr(lang, "must_indicate_business"), 400

    df = obtener_dataframe_db(negocio)

    if df.empty:
        return tr(lang, "no_data_export"), 400

    excel = generar_excel_reporte(df)

    return send_file(
        excel,
        download_name=f"reporte_ventas_{negocio}.xlsx",
        as_attachment=True
    )


@app.route("/reiniciar-datos", methods=["POST"])
def reiniciar_datos():
    lang = get_lang()
    negocio = limpiar_texto(request.form.get("negocio", ""))

    if not negocio:
        return render_template(
            "index.html",
            lang=lang,
            t=TRANSLATIONS[lang],
            error=tr(lang, "must_indicate_business")
        )

    db.session.query(Venta).filter_by(negocio=negocio).delete()
    db.session.commit()

    return render_template(
        "index.html",
        lang=lang,
        t=TRANSLATIONS[lang],
        mensaje=f"{tr(lang, 'deleted_business_data')} {negocio}."
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)