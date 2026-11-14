# Aquí se trabaja la clase "ModeloML" #
from helpers.utilidades import Utilidades
import pandas as pd
import numpy as np

from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.neighbors import KNeighborsRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV


class ModeloML:
    """Entrena, compara (benchmarking con GridSearchCV) y usa modelos de
    regresión (Regresión Lineal, KNN, Random Forest) para predecir la
    cantidad de turistas mensuales según país, mes y temperatura promedio.

    El target (turistas) se entrena en escala logarítmica (log1p) porque la
    distribución está muy sesgada (Estados Unidos vs. países pequeños), y se
    revierte (expm1) antes de calcular métricas o devolver predicciones."""

    def __init__(self):
        self.modelos_entrenados = {}
        self.mejor_modelo = None
        self.mejor_modelo_nombre = None

    # ____Combinamos los datos____ #
    def combinar_turismo_clima(self, df_turismo: pd.DataFrame, df_clima: pd.DataFrame) -> pd.DataFrame:
        Utilidades.validar_columnas(df_turismo, ["pais", "anio", "mes_numero", "turistas"])
        Utilidades.validar_columnas(df_clima, ["anio", "mes_numero", "temp_promedio"])

        df_combinado = df_turismo.merge(df_clima, on=["anio", "mes_numero"], how="inner")

        Utilidades.validar_sin_nulos(df_combinado)
        return df_combinado

    # ____Combinamos las columnas que necesitamos para el modelo____ #
    def preparar_datos(self, df_combinado: pd.DataFrame):
        df = df_combinado.copy()

        df["mes_sin"], df["mes_cos"] = zip(
            *df["mes_numero"].apply(Utilidades.codificar_mes_ciclico)
        )

        X = df[["pais", "mes_sin", "mes_cos", "temp_promedio"]]
        y = df["turistas"]
        y_log = np.log1p(y)  # log1p = log(1 + y), evita problemas si turistas=0

        return X, y_log

    # ____OneHotEncoder para convertir pais en 0/1____ #
    def crear_preprocesador(self) -> ColumnTransformer:
        preprocesador = ColumnTransformer(
            transformers=[
                ("pais_codificado", OneHotEncoder(handle_unknown="ignore"), ["pais"]),
            ],
            remainder="passthrough"
        )
        return preprocesador

    # ____División train/test____ #
    def dividir_datos(self, X, y):
        X_train, X_test, y_train, y_test = Utilidades.dividir_train_test(
            X, y, test_size=0.2, random_state=42
        )
        return X_train, X_test, y_train, y_test

    # ____Benchmarking de los modelos____ #
    # ____Regresion lineal____ #
    def crear_pipeline_regresion_lineal(self) -> Pipeline:
        pipeline = Pipeline(steps=[
            ("preprocesador", self.crear_preprocesador()),  # ____Aplica el metodo de OneHotEncoder____#
            ("modelo", LinearRegression())  # ____Recibe el resultado numerico y entrena el modelo____#
        ])
        return pipeline

    # ____KNN____ #
    # ____Realizamos estandarizacion de columnas numericas____ #
    def crear_pipeline_knn(self) -> Pipeline:
        pipeline = Pipeline(steps=[
            ("preprocesador", self.crear_preprocesador()),
            ("escalado", StandardScaler(with_mean=False)),
            ("modelo", KNeighborsRegressor())
        ])
        return pipeline

    # ____Definimos los parametros____ #
    def obtener_parametros_knn(self) -> dict:
        return {
            "modelo__n_neighbors": [3, 5, 7, 10, 15],
            "modelo__weights": ["uniform", "distance"],
        }

    # ____Random Forest____ #
    def crear_pipeline_random_forest(self) -> Pipeline:
        pipeline = Pipeline(steps=[
            ("preprocesador", self.crear_preprocesador()),
            ("modelo", RandomForestRegressor(random_state=42))
        ])
        return pipeline

    def obtener_parametros_random_forest(self) -> dict:
        return {
            "modelo__n_estimators": [100, 200, 300],
            "modelo__max_depth": [None, 10, 20, 30],
            "modelo__min_samples_leaf": [1, 2, 4],
        }

    # ____Benchmarking____ #
    def ejecutar_benchmarking(self, X_train, X_test, y_train, y_test) -> pd.DataFrame:
        """y_train/y_test entran en escala log1p (ver preparar_datos). Las
        predicciones y y_test se revierten con expm1 antes de medir métricas,
        para que MAE/RMSE queden en turistas reales, no en logaritmos."""
        resultados = []
        self.modelos_entrenados = {}

        # ____Regresion Lineal____ #
        pipeline_rl = self.crear_pipeline_regresion_lineal()
        pipeline_rl.fit(X_train, y_train)
        y_pred_rl = np.expm1(pipeline_rl.predict(X_test))
        metricas_rl = Utilidades.calcular_metricas_regresion(np.expm1(y_test), y_pred_rl)
        resultados.append({"modelo": "Regresión Lineal", **metricas_rl, "mejores_parametros": "N/A"})
        self.modelos_entrenados["Regresión Lineal"] = pipeline_rl

        # ____KNN____ #
        grid_knn = GridSearchCV(
            estimator=self.crear_pipeline_knn(),
            param_grid=self.obtener_parametros_knn(),
            cv=5,
            scoring="neg_mean_absolute_error",
            n_jobs=-1
        )
        grid_knn.fit(X_train, y_train)
        y_pred_knn = np.expm1(grid_knn.predict(X_test))
        metricas_knn = Utilidades.calcular_metricas_regresion(np.expm1(y_test), y_pred_knn)
        resultados.append({"modelo": "KNN", **metricas_knn, "mejores_parametros": grid_knn.best_params_})
        self.modelos_entrenados["KNN"] = grid_knn.best_estimator_

        # ____Random Forest____ #
        grid_rf = GridSearchCV(
            estimator=self.crear_pipeline_random_forest(),
            param_grid=self.obtener_parametros_random_forest(),
            cv=5,
            scoring="neg_mean_absolute_error",
            n_jobs=-1
        )
        grid_rf.fit(X_train, y_train)
        y_pred_rf = np.expm1(grid_rf.predict(X_test))
        metricas_rf = Utilidades.calcular_metricas_regresion(np.expm1(y_test), y_pred_rf)
        resultados.append({"modelo": "Random Forest", **metricas_rf, "mejores_parametros": grid_rf.best_params_})
        self.modelos_entrenados["Random Forest"] = grid_rf.best_estimator_

        # ____Tabla comparativa____ #
        # ____Tabla comparativa____ #
        df_resultados = pd.DataFrame(resultados).sort_values("MAE")
        self.mejor_modelo_nombre = df_resultados.iloc[0]["modelo"]
        self.mejor_modelo = self.modelos_entrenados[self.mejor_modelo_nombre]
        self.resultados_benchmarking = df_resultados  # ← AGREGAS ESTA LÍNEA

        return df_resultados

    # ____Realizamos la prediccion____ #
    def predecir(self, pais: str, mes_numero: int, temp_promedio: float) -> float:
        if self.mejor_modelo is None:
            raise ValueError("Todavía no se ha entrenado ningún modelo. Corre ejecutar_benchmarking() primero.")

        mes_sin, mes_cos = Utilidades.codificar_mes_ciclico(mes_numero)

        X_nuevo = pd.DataFrame([{
            "pais": pais,
            "mes_sin": mes_sin,
            "mes_cos": mes_cos,
            "temp_promedio": temp_promedio
        }])

        prediccion_log = self.mejor_modelo.predict(X_nuevo)
        prediccion_real = np.expm1(prediccion_log)
        return round(float(prediccion_real[0]), 0)