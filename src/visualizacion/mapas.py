"""
Clase Mapas - visualización geográfica adicional (mapa mundial de turistas por país)
"""

import os
import unicodedata
import pandas as pd
import folium

# GeoJSON público con las fronteras de todos los países (código ISO-3 en 'id')
URL_GEOJSON_PAISES = "https://raw.githubusercontent.com/python-visualization/folium/main/examples/data/world-countries.json"


class Mapas:
    """Genera un mapa mundial interactivo (estilo Google Maps, con tiles
    reales de OpenStreetMap) coloreando el área completa de cada país
    según la cantidad de turistas, usando Folium Choropleth."""

    # Nombre de país (español, sin tildes) -> código ISO-3
    ISO3 = {
        "alemania": "DEU", "arabia saudita": "SAU", "argentina": "ARG",
        "australia": "AUS", "austria": "AUT", "bahamas": "BHS",
        "belgica": "BEL", "belice": "BLZ", "bermuda": "BMU",
        "bolivia": "BOL", "brasil": "BRA", "canada": "CAN",
        "chile": "CHL", "china": "CHN", "colombia": "COL",
        "corea del sur": "KOR", "cuba": "CUB", "dinamarca": "DNK",
        "ecuador": "ECU", "egipto": "EGY", "el salvador": "SLV",
        "emiratos arabes unidos": "ARE", "eslovaquia": "SVK",
        "espana": "ESP", "estados unidos": "USA", "filipinas": "PHL",
        "finlandia": "FIN", "francia": "FRA", "guatemala": "GTM",
        "guyana": "GUY", "haiti": "HTI", "honduras": "HND",
        "hungria": "HUN", "india": "IND", "irlanda": "IRL",
        "israel": "ISR", "italia": "ITA", "jamaica": "JAM",
        "japon": "JPN", "jordania": "JOR", "libano": "LBN",
        "marruecos": "MAR", "mexico": "MEX", "nicaragua": "NIC",
        "nigeria": "NGA", "noruega": "NOR", "nueva zelanda": "NZL",
        "panama": "PAN", "paraguay": "PRY", "paises bajos": "NLD",
        "peru": "PER", "polonia": "POL", "portugal": "PRT",
        "reino unido": "GBR", "republica checa": "CZE",
        "republica dominicana": "DOM", "rumania": "ROU", "rusia": "RUS",
        "sudafrica": "ZAF", "suecia": "SWE", "suiza": "CHE",
        "taiwan": "TWN", "trinidad y tobago": "TTO", "uruguay": "URY",
        "venezuela": "VEN", "surinam": "SUR", "puerto rico": "PRI",
        "rep. de corea (sur)": "KOR", "rep. dem. pop. corea (norte)": "PRK",
    }

    @staticmethod
    def _normalizar(texto: str) -> str:
        texto = texto.strip().lower()
        texto = unicodedata.normalize('NFKD', texto)
        return "".join(c for c in texto if not unicodedata.combining(c))

    def _agregar_iso3(self, df_pais: pd.DataFrame) -> pd.DataFrame:
        df_pais = df_pais.copy()
        df_pais["pais_normalizado"] = df_pais["pais"].apply(self._normalizar)
        df_pais["iso3"] = df_pais["pais_normalizado"].map(self.ISO3)

        no_mapeados = df_pais[df_pais["iso3"].isna()]["pais"].unique()
        if len(no_mapeados) > 0:
            print(f"Aviso: {len(no_mapeados)} entradas no se pudieron ubicar en el mapa "
                  f"(no son países individuales, son categorías agregadas de la fuente): "
                  f"{list(no_mapeados)}")

        return df_pais.dropna(subset=["iso3"])

    def generar_mapa_folium(self, df_turismo: pd.DataFrame) -> folium.Map:
        """Construye y devuelve un mapa Folium interactivo (tiles reales,
        zoom y paneo) con cada país completo coloreado según su cantidad
        de turistas (mapa coroplético sobre mapa real)."""
        df_pais = df_turismo.groupby("pais")["turistas"].sum().reset_index()
        df_pais = self._agregar_iso3(df_pais)

        mapa = folium.Map(location=[15, 0], zoom_start=2, tiles="CartoDB positron")

        folium.Choropleth(
            geo_data=URL_GEOJSON_PAISES,
            data=df_pais,
            columns=["iso3", "turistas"],
            key_on="feature.id",
            fill_color="YlOrRd",
            fill_opacity=0.75,
            line_opacity=0.3,
            line_color="white",
            legend_name="Turistas por país (2019-2025)",
            nan_fill_color="#f0f0f0",
            nan_fill_opacity=0.3,
        ).add_to(mapa)

        # Tooltips al pasar el mouse: nombre del país + cantidad de turistas
        pais_por_iso = dict(zip(df_pais["iso3"], df_pais["pais"]))
        turistas_por_iso = dict(zip(df_pais["iso3"], df_pais["turistas"]))

        import requests
        geojson_data = requests.get(URL_GEOJSON_PAISES).json()
        for feature in geojson_data["features"]:
            iso = feature["id"]
            if iso in turistas_por_iso:
                feature["properties"]["turistas_texto"] = (
                    f"{pais_por_iso[iso].title()}: {turistas_por_iso[iso]:,.0f} turistas"
                )
            else:
                feature["properties"]["turistas_texto"] = f"{feature['properties']['name']}: sin datos"

        folium.GeoJson(
            geojson_data,
            style_function=lambda x: {"fillOpacity": 0, "color": "transparent"},
            tooltip=folium.GeoJsonTooltip(fields=["turistas_texto"], labels=False),
        ).add_to(mapa)

        return mapa

    def generar_mapa_mundial(self, df_turismo: pd.DataFrame, ruta_salida: str):
        """Genera el mapa y lo guarda como HTML interactivo en disco."""
        mapa = self.generar_mapa_folium(df_turismo)
        os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
        mapa.save(ruta_salida)
        print(f"Mapa guardado en {ruta_salida}")
        return mapa