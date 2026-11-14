"""
Clase GestorBaseDatos - conexión e integración con SQL Server
"""

import pyodbc
import pandas as pd


class GestorBaseDatos:
    def __init__(self, servidor="Gabriel", base_datos="TurismoCR"):
        self.servidor = servidor
        self.base_datos = base_datos
        self.conexion = None

    def conectar(self):
        cadena_conexion = (
            f"DRIVER={{SQL Server}};"
            f"SERVER={self.servidor};"
            f"DATABASE={self.base_datos};"
            f"Trusted_Connection=yes;"
        )
        self.conexion = pyodbc.connect(cadena_conexion)
        print(f"Conectado a {self.base_datos} en {self.servidor}")

    # ---------- Tabla turismo ----------
    def crear_tabla(self):
        cursor = self.conexion.cursor()
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='turismo' AND xtype='U')
            CREATE TABLE turismo (
                id INT IDENTITY(1,1) PRIMARY KEY,
                pais VARCHAR(60) NOT NULL,
                anio INT NOT NULL,
                mes_numero INT NOT NULL,
                mes_nombre VARCHAR(20) NOT NULL,
                turistas INT NOT NULL
            )
        """)
        self.conexion.commit()
        print("Tabla 'turismo' verificada/creada")

    def insertar_datos(self, df: pd.DataFrame):
        cursor = self.conexion.cursor()
        cursor.execute("TRUNCATE TABLE turismo")
        self.conexion.commit()
        filas_antes = self.consultar("SELECT COUNT(*) AS total FROM turismo")['total'][0]
        print(f"Tabla 'turismo' vaciada (filas antes de insertar: {filas_antes})")

        cursor.fast_executemany = True
        datos = list(
            df[["pais", "anio", "mes_numero", "mes_nombre", "turistas"]]
            .itertuples(index=False, name=None)
        )
        cursor.executemany(
            """
            INSERT INTO turismo (pais, anio, mes_numero, mes_nombre, turistas)
            VALUES (?, ?, ?, ?, ?)
            """,
            datos
        )
        self.conexion.commit()
        print(f"{len(df)} filas insertadas en la tabla 'turismo'")

    # ---------- Tabla clima ----------
    def crear_tabla_clima(self):
        cursor = self.conexion.cursor()
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='clima' AND xtype='U')
            CREATE TABLE clima (
                id INT IDENTITY(1,1) PRIMARY KEY,
                anio INT NOT NULL,
                mes_numero INT NOT NULL,
                temp_promedio DECIMAL(5,2) NULL
            )
        """)
        self.conexion.commit()
        print("Tabla 'clima' verificada/creada")

    def insertar_clima(self, df: pd.DataFrame):
        cursor = self.conexion.cursor()
        cursor.execute("TRUNCATE TABLE clima")
        self.conexion.commit()

        cursor.fast_executemany = True
        datos = list(
            df[["anio", "mes_numero", "temp_promedio"]]
            .itertuples(index=False, name=None)
        )
        cursor.executemany(
            "INSERT INTO clima (anio, mes_numero, temp_promedio) VALUES (?, ?, ?)",
            datos
        )
        self.conexion.commit()
        print(f"{len(df)} filas insertadas en la tabla 'clima'")

    # ---------- Utilidades ----------
    def consultar(self, query="SELECT * FROM turismo"):
        return pd.read_sql(query, self.conexion)

    def cerrar(self):
        if self.conexion:
            self.conexion.close()
            print("Conexión cerrada")