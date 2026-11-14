"""
Clase Visualizador - gráficos de turismo y clima
Va dentro de: src/visualizacion/visualizador.py
"""

import os
import matplotlib.pyplot as plt
import pandas as pd


class Visualizador:
    def __init__(self, carpeta_salida: str = "reports/figures"):
        self.carpeta_salida = carpeta_salida
        os.makedirs(self.carpeta_salida, exist_ok=True)

    def _guardar_o_mostrar(self, fig, nombre_archivo: str, guardar: bool = True, mostrar: bool = False):
        if guardar:
            ruta = os.path.join(self.carpeta_salida, nombre_archivo)
            fig.savefig(ruta, bbox_inches="tight", dpi=150)
            print(f"Gráfico guardado en {ruta}")
        if mostrar:
            plt.show()
        plt.close(fig)

    def grafico_turistas_por_mes(self, df_mensual: pd.DataFrame, guardar: bool = True, mostrar: bool = False):
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.bar(df_mensual["mes_nombre"], df_mensual["turistas"], color="#2c7fb8")
        ax.set_title("Turistas totales por mes (2019-2025)")
        ax.set_xlabel("Mes")
        ax.set_ylabel("Turistas")
        plt.xticks(rotation=45)
        self._guardar_o_mostrar(fig, "turistas_por_mes.png", guardar, mostrar)

    def grafico_tendencia_anual(self, df_anual: pd.DataFrame, guardar: bool = True, mostrar: bool = False):
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.plot(df_anual["anio"], df_anual["turistas"], marker="o", color="#e34a33")
        ax.set_title("Tendencia de turistas por año")
        ax.set_xlabel("Año")
        ax.set_ylabel("Turistas")
        ax.grid(alpha=0.3)
        self._guardar_o_mostrar(fig, "tendencia_anual.png", guardar, mostrar)

    def grafico_top_paises(self, df_top: pd.DataFrame, guardar: bool = True, mostrar: bool = False):
        fig, ax = plt.subplots(figsize=(9, 6))
        df_ordenado = df_top.sort_values("turistas")
        ax.barh(df_ordenado["pais"], df_ordenado["turistas"], color="#31a354")
        ax.set_title(f"Top {len(df_top)} países emisores de turistas")
        ax.set_xlabel("Turistas")
        self._guardar_o_mostrar(fig, "top_paises.png", guardar, mostrar)

    def grafico_dispersion_clima(self, df_combinado: pd.DataFrame, guardar: bool = True, mostrar: bool = False):
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.scatter(df_combinado["temp_promedio"], df_combinado["turistas"], alpha=0.6, color="#756bb1")
        ax.set_title("Turistas mensuales vs. temperatura promedio")
        ax.set_xlabel("Temperatura promedio (°C)")
        ax.set_ylabel("Turistas")
        self._guardar_o_mostrar(fig, "dispersion_clima.png", guardar, mostrar)

    def grafico_heatmap_mes_anio(self, df_pivote: pd.DataFrame, guardar: bool = True, mostrar: bool = False):
        fig, ax = plt.subplots(figsize=(10, 6))
        im = ax.imshow(df_pivote.values, cmap="YlOrRd", aspect="auto")
        ax.set_xticks(range(len(df_pivote.columns)))
        ax.set_xticklabels(df_pivote.columns)
        ax.set_yticks(range(len(df_pivote.index)))
        ax.set_yticklabels(df_pivote.index)
        ax.set_title("Turistas por mes y año (heatmap)")
        ax.set_xlabel("Mes")
        ax.set_ylabel("Año")
        fig.colorbar(im, ax=ax, label="Turistas")
        self._guardar_o_mostrar(fig, "heatmap_mes_anio.png", guardar, mostrar)

    def grafico_boxplot_turistas(self, df_turismo: pd.DataFrame, columna: str = "turistas",
                                  guardar: bool = True, mostrar: bool = False):
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.boxplot(df_turismo[columna], vert=True, patch_artist=True,
                   boxprops=dict(facecolor="#a6bddb"))
        ax.set_title(f"Distribución de '{columna}' (detección de valores atípicos)")
        ax.set_ylabel(columna.capitalize())
        self._guardar_o_mostrar(fig, "boxplot_turistas.png", guardar, mostrar)