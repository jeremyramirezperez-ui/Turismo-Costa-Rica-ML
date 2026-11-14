#____Generamos el Streamlit con 4 pestañas y filtros____#

import os
import sys

# La ruta a src/ debe agregarse ANTES de las importaciones de los otros
# módulos del proyecto (eda, helpers, api) -- si no, Python no los encuentra
# al correr el archivo directamente con "streamlit run".
RAIZ_PROYECTO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUTA_SRC = os.path.join(RAIZ_PROYECTO, "src")
if RUTA_SRC not in sys.path:
    sys.path.insert(0, RUTA_SRC)

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from eda.procesador_eda import ProcesadorEDA
from helpers.utilidades import Utilidades
from api.cliente_api import ClienteAPI
from visualizacion.mapas import Mapas
from streamlit_folium import st_folium

RUTA_CSV = os.path.join(RAIZ_PROYECTO, "data", "processed", "turismo.csv")
RUTA_MODELO = os.path.join(RAIZ_PROYECTO, "modelos_guardados", "modelo_ml_entrenado.pkl")

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
          "julio", "agosto", "setiembre", "octubre", "noviembre", "diciembre"]


@st.cache_data
def _cargar_turismo() -> pd.DataFrame:
    return pd.read_csv(RUTA_CSV)


@st.cache_data
def _cargar_clima(anio_min: int, anio_max: int) -> pd.DataFrame:
    cliente_api = ClienteAPI()
    return cliente_api.obtener_clima_mensual(f"{anio_min}-01-01", f"{anio_max}-12-31")


@st.cache_resource
def _cargar_modelo():
    if not os.path.exists(RUTA_MODELO):
        return None
    return Utilidades.cargar_objeto(RUTA_MODELO)


class Dashboard:
    #____Generamos el streamlit interactivo____#
    def __init__(self):
        self.df_turismo = _cargar_turismo()
        anio_min = int(self.df_turismo["anio"].min())
        anio_max = int(self.df_turismo["anio"].max())
        self.df_clima = _cargar_clima(anio_min, anio_max)
        self.eda = ProcesadorEDA(self.df_turismo, self.df_clima)
        self.modelo_ml = _cargar_modelo()
        self.mapas = Mapas()

    # ---------- Punto de entrada ----------
    def ejecutar(self):
        st.set_page_config(page_title="Turismo Costa Rica", page_icon="🌴", layout="wide")
        st.title("🌴 Análisis y Predicción del Turismo en Costa Rica")

        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["Panorama general", "Clima", "Países", "Predicción", "Mapa mundial"]
        )
        with tab1:
            self.mostrar_panorama_general()
        with tab2:
            self.mostrar_clima()
        with tab3:
            self.mostrar_paises()
        with tab4:
            self.mostrar_prediccion()
        with tab5:
            self.mostrar_mapa()

    # ---------- Pestaña 1: Panorama general ----------
    def mostrar_panorama_general(self):
        paises = sorted(self.df_turismo["pais"].unique())
        anio_min = int(self.df_turismo["anio"].min())
        anio_max = int(self.df_turismo["anio"].max())

        col_f1, col_f2 = st.columns(2)
        pais = col_f1.selectbox("País", paises, index=paises.index("estados unidos") if "estados unidos" in paises else 0)
        rango_anios = col_f2.slider("Rango de años", anio_min, anio_max, (anio_min, anio_max))

        df_filtrado = self.df_turismo[
            (self.df_turismo["pais"] == pais) &
            (self.df_turismo["anio"].between(rango_anios[0], rango_anios[1]))
        ]

        resumen = self.eda.resumen_general()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Turistas totales (histórico, todos los países)", Utilidades.formatear_numero(resumen["turistas_totales"]))
        c2.metric("Países registrados", resumen["paises"])
        c3.metric("Turistas de este país (rango filtrado)", Utilidades.formatear_numero(df_filtrado["turistas"].sum()))
        c4.metric("Correlación turismo-clima (global)", self.eda.correlacion_turismo_clima())

        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader(f"Turistas por mes — {pais.title()}")
            df_mes = (
                df_filtrado.groupby(["mes_numero", "mes_nombre"])["turistas"]
                .sum().reset_index().sort_values("mes_numero")
            )
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.bar(df_mes["mes_nombre"], df_mes["turistas"], color="#2c7fb8")
            plt.xticks(rotation=45)
            ax.set_ylabel("Turistas")
            st.pyplot(fig)

        with col_g2:
            st.subheader(f"Tendencia anual — {pais.title()}")
            df_anio = df_filtrado.groupby("anio")["turistas"].sum().reset_index()
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.plot(df_anio["anio"], df_anio["turistas"], marker="o", color="#e34a33")
            ax.grid(alpha=0.3)
            ax.set_ylabel("Turistas")
            st.pyplot(fig)

    # ---------- Pestaña 2: Clima ----------
    def mostrar_clima(self):
        anio_min = int(self.df_turismo["anio"].min())
        anio_max = int(self.df_turismo["anio"].max())
        rango_anios = st.slider("Rango de años", anio_min, anio_max, (anio_min, anio_max), key="clima_anios")

        df_combinado = self.eda.combinar_con_clima()
        df_filtrado = df_combinado[df_combinado["anio"].between(rango_anios[0], rango_anios[1])]

        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader("Turistas mensuales vs. temperatura promedio")
            fig, ax = plt.subplots(figsize=(6, 5))
            ax.scatter(df_filtrado["temp_promedio"], df_filtrado["turistas"], alpha=0.6, color="#756bb1")
            ax.set_xlabel("Temperatura promedio (°C)")
            ax.set_ylabel("Turistas")
            st.pyplot(fig)

        with col_g2:
            st.subheader("Turistas promedio según rango de temperatura")
            df_filtrado = df_filtrado.copy()
            df_filtrado["rango_temp"] = pd.cut(df_filtrado["temp_promedio"], bins=5)
            df_filtrado["rango_temp"] = df_filtrado["rango_temp"].astype(str)
            agg = df_filtrado.groupby("rango_temp")["turistas"].mean().reset_index()
            fig, ax = plt.subplots(figsize=(6, 5))
            ax.bar(agg["rango_temp"], agg["turistas"], color="#31a354")
            plt.xticks(rotation=30)
            ax.set_ylabel("Turistas promedio")
            st.pyplot(fig)

        correlacion = round(df_filtrado["turistas"].corr(df_filtrado["temp_promedio"]), 3)
        if abs(correlacion) < 0.3:
            interpretacion = "correlación débil"
        elif abs(correlacion) < 0.6:
            interpretacion = "correlación moderada"
        else:
            interpretacion = "correlación fuerte"
        st.info(f"Correlación turismo-clima en el rango seleccionado: **{correlacion}** ({interpretacion})")

    # ---------- Pestaña 3: Países ----------
    def mostrar_paises(self):
        top_n = st.slider("Cantidad de países en el top", 5, 20, 10, key="paises_top_n")

        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader(f"Top {top_n} países emisores de turistas")
            df_top = self.eda.top_paises(n=top_n)
            fig, ax = plt.subplots(figsize=(6, 6))
            df_ordenado = df_top.sort_values("turistas")
            ax.barh(df_ordenado["pais"], df_ordenado["turistas"], color="#31a354")
            ax.set_xlabel("Turistas")
            st.pyplot(fig)

        with col_g2:
            st.subheader("Turistas por mes y año (heatmap)")
            df_pivote = self.eda.pivote_mes_anio()
            fig, ax = plt.subplots(figsize=(6, 6))
            im = ax.imshow(df_pivote.values, cmap="YlOrRd", aspect="auto")
            ax.set_xticks(range(len(df_pivote.columns)))
            ax.set_xticklabels(df_pivote.columns)
            ax.set_yticks(range(len(df_pivote.index)))
            ax.set_yticklabels(df_pivote.index)
            fig.colorbar(im, ax=ax, label="Turistas")
            st.pyplot(fig)

        st.subheader("Distribución de turistas (detección de valores atípicos)")
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.boxplot(self.df_turismo["turistas"], vert=False, patch_artist=True,
                   boxprops=dict(facecolor="#a6bddb"))
        ax.set_xlabel("Turistas")
        st.pyplot(fig)
        st.caption(
            "Los puntos alejados a la derecha no son errores de datos: corresponden principalmente "
            "a Estados Unidos, que por su volumen se comporta como un valor atípico estructural "
            "frente al resto de los 72 países."
        )

    # ---------- Pestaña 4: Predicción ----------
    def mostrar_prediccion(self):
        if self.modelo_ml is None:
            st.warning(
                "No se encontró un modelo entrenado en `modelos_guardados/modelo_ml_entrenado.pkl`. "
                "Corre `main.py` primero para entrenar y guardar el modelo."
            )
            return

        st.subheader("Predecir cantidad de turistas")
        paises = sorted(self.df_turismo["pais"].unique())

        col1, col2, col3 = st.columns(3)
        pais = col1.selectbox("País", paises, key="pred_pais")
        mes_nombre = col2.selectbox("Mes", MESES, key="pred_mes")
        temp = col3.number_input("Temperatura promedio esperada (°C)", min_value=15.0, max_value=30.0, value=20.0, step=0.1)

        mes_numero = MESES.index(mes_nombre) + 1

        if st.button("Predecir", type="primary"):
            prediccion = self.modelo_ml.predecir(pais, mes_numero, temp)
            st.success(f"Predicción: **{Utilidades.formatear_numero(prediccion)} turistas** "
                       f"({pais.title()}, {mes_nombre}, {temp}°C)")
            st.caption(f"Modelo usado: {self.modelo_ml.mejor_modelo_nombre}")

        st.divider()
        st.subheader("Comparación de modelos (benchmarking)")
        if hasattr(self.modelo_ml, "resultados_benchmarking"):
            st.dataframe(self.modelo_ml.resultados_benchmarking, use_container_width=True)
        else:
            st.caption(
                "La tabla comparativa no quedó guardada en el modelo. "
                "Agrega `self.resultados_benchmarking = df_resultados` antes del `return` "
                "en `ejecutar_benchmarking()` (en modelo_ml.py) y vuelve a entrenar."
            )


    # ---------- Pestaña 5: Mapa mundial ----------
    def mostrar_mapa(self):
        st.subheader("Distribución mundial de turistas por país de origen")
        st.caption("Pasa el mouse o haz clic sobre cada círculo para ver el detalle del país.")
        mapa = self.mapas.generar_mapa_folium(self.df_turismo)
        st_folium(mapa, use_container_width=True, height=550, returned_objects=[])
        st.caption(
            "Suma histórica de turistas por país, 2019-2025. El tamaño y color del círculo "
            "reflejan la cantidad de turistas. Algunas categorías agregadas del ICT "
            "(ej. 'Otros Caribe', 'Otros Europa') no corresponden a un país individual "
            "y no aparecen en el mapa."
        )


if __name__ == "__main__":
    Dashboard().ejecutar()
