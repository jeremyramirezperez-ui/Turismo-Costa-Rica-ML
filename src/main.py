"""
Punto de entrada del proyecto: Análisis y Predicción del Turismo en Costa Rica
Curso BD-143 - Programación II
"""

import os
import pandas as pd
from datos.gestor_datos import GestorDatos
from api.cliente_api import ClienteAPI
from basedatos.gestor_basedatos import GestorBaseDatos
from eda.procesador_eda import ProcesadorEDA
from visualizacion.visualizador import Visualizador
from modelos.modelo_ml import ModeloML
from helpers.utilidades import Utilidades

RAIZ_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_PDFS = os.path.join(RAIZ_PROYECTO, "data", "raw", "informes_ict")
RUTA_CSV = os.path.join(RAIZ_PROYECTO, "data", "processed", "turismo.csv")
RUTA_MODELO = os.path.join(RAIZ_PROYECTO, "modelos_guardados", "modelo_ml_entrenado.pkl")

def main():
    # ---------- 1) Extraer los datos de los PDFs del ICT y generar el CSV ----------
    if not os.path.exists(RUTA_CSV):
        print("No se encontró el CSV, extrayendo datos de los PDFs...")
        gestor_datos = GestorDatos(carpeta_pdfs=RUTA_PDFS, archivo_salida=RUTA_CSV)
        gestor_datos.exportar()

    # ---------- 2) Cargar el CSV de turismo ya procesado ----------
    df_turismo = pd.read_csv(RUTA_CSV)
    print(f"CSV cargado: {len(df_turismo)} filas, {df_turismo['pais'].nunique()} países")

    # ---------- 3) Consultar el clima histórico mensual (API Open-Meteo) ----------
    anio_min = df_turismo["anio"].min()
    anio_max = df_turismo["anio"].max()
    print(f"Consultando clima de {anio_min}-01-01 a {anio_max}-12-31...")

    cliente_api = ClienteAPI()
    df_clima = cliente_api.obtener_clima_mensual(
        fecha_inicio=f"{anio_min}-01-01",
        fecha_fin=f"{anio_max}-12-31"
    )
    print(f"Clima cargado: {len(df_clima)} filas mensuales")

    # ---------- 4) Conectar a SQL Server y cargar ambas tablas ----------
    gestor_bd = GestorBaseDatos()
    gestor_bd.conectar()

    gestor_bd.crear_tabla()
    gestor_bd.insertar_datos(df_turismo)

    gestor_bd.crear_tabla_clima()
    gestor_bd.insertar_clima(df_clima)

    # ---------- 5) Verificar con una consulta que une ambas tablas ----------
    resultado = gestor_bd.consultar("""
        SELECT TOP 10 t.pais, t.anio, t.mes_nombre, t.turistas, c.temp_promedio
        FROM turismo t
        JOIN clima c ON t.anio = c.anio AND t.mes_numero = c.mes_numero
        ORDER BY t.anio, t.mes_numero
    """)
    print("\nMuestra de turismo + clima combinados:")
    print(resultado)

    gestor_bd.cerrar()

    # ---------- 6) Análisis exploratorio (EDA) ----------
    eda = ProcesadorEDA(df_turismo, df_clima)
    print("\nResumen general:", eda.resumen_general())
    print("Correlación turismo-clima:", eda.correlacion_turismo_clima())

    df_mensual = eda.turistas_por_mes()
    df_anual = eda.turistas_por_anio()
    df_top = eda.top_paises(n=10)
    df_combinado = eda.combinar_con_clima()
    df_pivote = eda.pivote_mes_anio()

    # ---------- 7) Visualización ----------
    visualizador = Visualizador()
    visualizador.grafico_turistas_por_mes(df_mensual)
    visualizador.grafico_tendencia_anual(df_anual)
    visualizador.grafico_top_paises(df_top)
    visualizador.grafico_dispersion_clima(df_combinado)
    visualizador.grafico_heatmap_mes_anio(df_pivote)
    visualizador.grafico_boxplot_turistas(df_turismo)

    # ---------- 8) Machine Learning: entrenar o cargar el modelo ----------
    if os.path.exists(RUTA_MODELO):
        print("\nModelo ya entrenado encontrado, cargando desde disco...")
        modelo_ml = Utilidades.cargar_objeto(RUTA_MODELO)
        print(f"Mejor modelo cargado: {modelo_ml.mejor_modelo_nombre}")
    else:
        print("\nNo hay modelo guardado, entrenando y comparando modelos (puede tardar unos minutos)...")
        modelo_ml = ModeloML()
        df_combinado_ml = modelo_ml.combinar_turismo_clima(df_turismo, df_clima)
        X, y_log = modelo_ml.preparar_datos(df_combinado_ml)
        X_train, X_test, y_train, y_test = modelo_ml.dividir_datos(X, y_log)

        resultados_ml = modelo_ml.ejecutar_benchmarking(X_train, X_test, y_train, y_test)
        print("\nResultados del benchmarking:")
        print(resultados_ml.to_string(index=False))
        print(f"\nMejor modelo: {modelo_ml.mejor_modelo_nombre}")

        Utilidades.guardar_objeto(modelo_ml, RUTA_MODELO)

    # ---------- 9) Predicción de ejemplo con el modelo ya entrenado/cargado ----------
    prediccion_ejemplo = modelo_ml.predecir("alemania", 1, 21.5)
    print("\nPredicción de ejemplo (Alemania, enero, 21.5°C):", prediccion_ejemplo)

if __name__ == "__main__":
    main()