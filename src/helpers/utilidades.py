# Aquí se trabaja la clase "Utilidades" #

#Clase Utilidades y funciones auxiliares reutilizables#

import os
import unicodedata
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

class Utilidades:
    #____Validaciones____#
    @staticmethod
    def validar_columnas(df: pd.DataFrame, columnas_requeridas: list = None) -> None:
        #____Lanza un error si al DF le falta alguna columna esperada____#
        faltantes = [c for c in columnas_requeridas if c not in df.columns]
        if faltantes:
            raise ValueError(f"Faltan columnas requeridas en el dataset: {faltantes}")

    @staticmethod
    def validar_sin_nulos(df: pd.DataFrame, columnas: list = None) -> None:
        subconjutno = df[columnas] if columnas else df #____Filtramos para quedarnos solo con las columnas____#
        nulos = subconjutno.isnull().sum() #____Leemos los nulos en TRUE o FALSE y los sumamos____#
        nulos = nulos[nulos > 0]
        if not nulos.empty:
            raise ValueError(f"Se encontraron valores nulos en el dataset: {nulos}")


    #____Formateo____#
    @staticmethod
    def normalizar_texto(texto: str) -> str:
        #____Minusculas, sin espacios extra y sin tildes____#
        texto = texto.strip().lower()
        texto = unicodedata.normalize('NFKD', texto)
        return "".join(c for c in texto if not unicodedata.combining(c))

    @staticmethod
    def formatear_numero(numero: float) -> str:
        #____Tranforma numero pegados como 1234567 a 1,234,567____#
        return f"{numero:,.0f}"

    @staticmethod
    def codificar_mes_ciclico(mes_numero: int) -> tuple:
        #____Tranforman el mes en variables continuas que capturan la estacionalidad____#
        angulo = 2 * np.pi * mes_numero / 12
        return round(float(np.sin(angulo)), 4), round(float(np.cos(angulo)), 4)


    #____Machine Learning____#
    @staticmethod
    def dividir_train_test(X, y, test_size: float = 0.2, random_state: int = 42):
        #____Definimos los parametros para entrenar el modelo____#
        return train_test_split(X, y, test_size=test_size, random_state=random_state)

    @staticmethod
    def calcular_metricas_regresion(y_real, y_pred) -> dict:
        #____Metricas estandar para comparar modelos____#
        mae = mean_absolute_error(y_real, y_pred)
        rmse = mean_squared_error(y_real, y_pred)
        r2 = r2_score(y_real, y_pred)
        return {"MAE": round(mae, 2), "RMSE": round(rmse, 2), "R2": round(r2, 4)}



    #____Persistencia____#
    @staticmethod
    def asegurar_carpeta(ruta: str) -> None:
        #____Verifica si existe la carpeta, si no existe la crea____#
        os.makedirs(ruta, exist_ok=True)

    @staticmethod
    def guardar_objeto(objeto, ruta: str) -> None:
        #____Nos ayuda a guardar cualquier objeto de Python en el disco____#
        carpeta = os.path.dirname(ruta)
        if carpeta:
            Utilidades.asegurar_carpeta(carpeta)
        joblib.dump(objeto, ruta)
        print(f"Objeto guardado en {ruta}")

    @staticmethod
    def cargar_objeto(ruta: str):
        #____Cargamos los objetos____#
        if not os.path.exists(ruta):
            raise FileNotFoundError(f"No se encontró el archivo: {ruta}")
        return joblib.load(ruta)