"""
Clase ProcesadorEDA - análisis exploratorio de datos de turismo y clima
Va dentro de: src/eda/procesador_eda.py
"""

import pandas as pd


class ProcesadorEDA:
    def __init__(self, df_turismo: pd.DataFrame, df_clima: pd.DataFrame = None):
        self.df_turismo = df_turismo.copy()
        self.df_clima = df_clima.copy() if df_clima is not None else None

    # ---------- Resumen y calidad de datos ----------
    def resumen_general(self) -> dict:
        return {
            "filas": len(self.df_turismo),
            "paises": self.df_turismo["pais"].nunique(),
            "anio_min": int(self.df_turismo["anio"].min()),
            "anio_max": int(self.df_turismo["anio"].max()),
            "turistas_totales": int(self.df_turismo["turistas"].sum()),
            "promedio_mensual_por_pais": round(self.df_turismo["turistas"].mean(), 2),
        }

    def valores_nulos(self) -> pd.Series:
        nulos = self.df_turismo.isnull().sum()
        return nulos[nulos > 0]

    def detectar_duplicados(self) -> pd.DataFrame:
        claves = ["pais", "anio", "mes_numero"]
        return self.df_turismo[self.df_turismo.duplicated(subset=claves, keep=False)]

    def detectar_atipicos(self, columna: str = "turistas") -> pd.DataFrame:
        q1 = self.df_turismo[columna].quantile(0.25)
        q3 = self.df_turismo[columna].quantile(0.75)
        iqr = q3 - q1
        limite_inf = q1 - 1.5 * iqr
        limite_sup = q3 + 1.5 * iqr
        return self.df_turismo[
            (self.df_turismo[columna] < limite_inf) | (self.df_turismo[columna] > limite_sup)
        ]

    # ---------- Agregaciones ----------
    def turistas_por_mes(self) -> pd.DataFrame:
        return (
            self.df_turismo.groupby(["mes_numero", "mes_nombre"])["turistas"]
            .sum()
            .reset_index()
            .sort_values("mes_numero")
        )

    def turistas_por_anio(self) -> pd.DataFrame:
        return (
            self.df_turismo.groupby("anio")["turistas"]
            .sum()
            .reset_index()
            .sort_values("anio")
        )

    def top_paises(self, n: int = 10) -> pd.DataFrame:
        return (
            self.df_turismo.groupby("pais")["turistas"]
            .sum()
            .reset_index()
            .sort_values("turistas", ascending=False)
            .head(n)
        )

    def turistas_por_pais_anio(self, pais: str) -> pd.DataFrame:
        filtro = self.df_turismo["pais"].str.lower() == pais.lower()
        return (
            self.df_turismo[filtro]
            .groupby("anio")["turistas"]
            .sum()
            .reset_index()
            .sort_values("anio")
        )

    # ---------- Cruce con clima ----------
    def combinar_con_clima(self) -> pd.DataFrame:
        if self.df_clima is None:
            raise ValueError("No se cargó df_clima; pasalo al construir ProcesadorEDA.")
        turismo_mensual = (
            self.df_turismo.groupby(["anio", "mes_numero"])["turistas"]
            .sum()
            .reset_index()
        )
        return turismo_mensual.merge(self.df_clima, on=["anio", "mes_numero"], how="inner")

    def correlacion_turismo_clima(self) -> float:
        combinado = self.combinar_con_clima()
        return round(combinado["turistas"].corr(combinado["temp_promedio"]), 3)

    # ---------- Tabla para heatmap ----------
    def pivote_mes_anio(self) -> pd.DataFrame:
        """Tabla anio x mes con el total de turistas, lista para un heatmap."""
        pivote = self.df_turismo.pivot_table(
            index="anio", columns="mes_numero", values="turistas", aggfunc="sum"
        )
        pivote.columns = [
            ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"][c - 1]
            for c in pivote.columns
        ]
        return pivote