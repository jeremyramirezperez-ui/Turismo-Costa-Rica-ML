"""
Clase ClienteAPI - consulta la API histórica de clima de Open-Meteo
"""

import requests
import pandas as pd

class ClienteAPI:
    def __init__(self, latitude=9.93, longitude=-84.08):
        self.url = "https://archive-api.open-meteo.com/v1/archive"
        self.latitude = latitude
        self.longitude = longitude

    def obtener_clima_diario(self, fecha_inicio, fecha_fin):
        """Consulta la API y devuelve un DataFrame con temperatura diaria."""
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "start_date": fecha_inicio,
            "end_date": fecha_fin,
            "daily": "temperature_2m_mean",
            "timezone": "America/Costa_Rica",
        }
        respuesta = requests.get(self.url, params=params)
        respuesta.raise_for_status()
        datos = respuesta.json()

        df = pd.DataFrame({
            "fecha": datos["daily"]["time"],
            "temperatura": datos["daily"]["temperature_2m_mean"],
        })
        df["fecha"] = pd.to_datetime(df["fecha"])
        return df

    def obtener_clima_mensual(self, fecha_inicio, fecha_fin):
        """Devuelve el clima ya promediado por año y mes."""
        df = self.obtener_clima_diario(fecha_inicio, fecha_fin)
        df["anio"] = df["fecha"].dt.year
        df["mes_numero"] = df["fecha"].dt.month

        clima_mensual = (
            df.groupby(["anio", "mes_numero"])["temperatura"]
            .mean()
            .round(2)
            .reset_index()
            .rename(columns={"temperatura": "temp_promedio"})
        )
        return clima_mensual