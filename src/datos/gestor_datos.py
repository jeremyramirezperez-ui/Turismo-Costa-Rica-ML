"""
Clase GestorDatos - carga, transforma y exporta los datos de turismo del ICT
Va dentro de: src/datos/gestor_datos.py

Extrae el "CUADRO 1" (Llegadas internacionales, todas las vías, según zonas
y países, por mes) de los Informes Semestrales del ICT en PDF, y los combina
en un único CSV: pais, anio, mes_numero, mes_nombre, turistas.

Fuente de los PDFs: https://www.ict.go.cr/es/estadisticas/informes-estadisticos.html
(sección "Informes Semestrales")
"""

import pdfplumber
import re
import csv
import glob
import os
from collections import defaultdict


class GestorDatos:
    """Encargada de cargar, transformar y exportar los datos de turismo
    del ICT a partir de los PDFs de informes semestrales."""

    MESES_I = ["enero", "febrero", "marzo", "abril", "mayo", "junio"]
    MESES_II = ["julio", "agosto", "setiembre", "octubre", "noviembre", "diciembre"]

    MESES_NOMBRES = {"Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                      "Julio", "Agosto", "Setiembre", "Octubre", "Noviembre", "Diciembre"}

    MESES_ORDEN = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
                   "julio": 7, "agosto": 8, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12}

    # Encabezados de zona/región que se deben ignorar (solo interesan los países)
    ZONAS = {"TOTAL", "AMÉRICA DEL NORTE", "AMÉRICA CENTRAL", "AMÉRICA DEL SUR", "CARIBE",
             "EUROPA", "ASIA Y EL PACÍFICO", "ÁFRICA", "ORIENTE MEDIO",
             "ASIA Y EL PACIFICO", "AFRICA"}

    # Fragmentos de texto que delatan líneas que no son datos de país
    EXCLUIR = ("CUADRO", "PAÍSES", "PAISES", "MES", "LLEGADAS", "SEMESTRE", "I-SEM", "II-SEM",
               "INSTITUTO", "DIRECCIÓN", "UNIDAD", "FUENTE", "NOTA", "GUYANA FRANCESA")

    # Algunos informes del ICT escriben ciertos países con tilde y otros sin ella
    # (inconsistencia de la fuente entre años). Se normalizan para que no
    # queden duplicados como si fueran países distintos.
    CORRECCIONES_PAIS = {
        "republica checa": "república checa",
        "taiwan": "taiwán",
    }

    def __init__(self, carpeta_pdfs, archivo_salida):
        self.carpeta_pdfs = carpeta_pdfs
        self.archivo_salida = archivo_salida
        self.filas = []  # resultado final, se llena al exportar()

    # ---------- utilidades internas ----------
    @staticmethod
    def _es_numero(tok):
        return bool(re.fullmatch(r"[\d]+", tok))

    @staticmethod
    def _limpiar_nombre(nombre):
        nombre = re.sub(r"\d+$", "", nombre).strip()  # quita dígito de nota al pie (ej. "Rico1")
        return nombre.rstrip(".,")

    def _parsear_pagina(self, page, meses):
        """Extrae (país, {mes: turistas}) de una página del Cuadro 1 usando la
        posición horizontal (x1, borde derecho) de cada número para ubicarlo en
        su columna de mes correcta -- los números están alineados a la derecha,
        por eso se usa x1 y no x0."""
        words = page.extract_words()

        header_mes = [w for w in words if w['text'] in self.MESES_NOMBRES]
        if not header_mes:
            return []
        header_mes.sort(key=lambda w: w['x1'])
        col_x1 = [w['x1'] for w in header_mes[:6]]

        total_words = [w for w in words if w['text'].startswith("I-Sem") or w['text'].startswith("II")
                       or (w['text'].isdigit() and len(w['text']) == 4 and w['top'] < 195)]
        col_x1.append(max(w['x1'] for w in total_words) if total_words else col_x1[-1] + 60)

        limites = [(col_x1[i] + col_x1[i + 1]) / 2 for i in range(len(col_x1) - 1)]

        def columna_de(x1):
            for i, lim in enumerate(limites):
                if x1 < lim:
                    return i
            return len(col_x1) - 1

        palabras = sorted(words, key=lambda w: (w['top'], w['x0']))
        filas, fila_actual, top_actual = [], [], None
        for w in palabras:
            if top_actual is None or abs(w['top'] - top_actual) <= 3:
                fila_actual.append(w)
                top_actual = top_actual if top_actual is not None else w['top']
            else:
                filas.append(fila_actual)
                fila_actual, top_actual = [w], w['top']
        if fila_actual:
            filas.append(fila_actual)

        resultados = []
        for fila in filas:
            fila = sorted(fila, key=lambda w: w['x0'])
            nombre_tokens, i = [], 0
            while i < len(fila) and not self._es_numero(fila[i]['text']):
                nombre_tokens.append(fila[i]['text'])
                i += 1
            if not nombre_tokens:
                continue
            nombre = self._limpiar_nombre(" ".join(nombre_tokens))
            if nombre == "" or nombre.upper() in self.ZONAS or any(e in nombre.upper() for e in self.EXCLUIR):
                continue

            numeros_por_col = defaultdict(list)
            while i < len(fila):
                tok = fila[i]
                if self._es_numero(tok['text']):
                    numeros_por_col[columna_de(tok['x1'])].append(tok['text'])
                i += 1
            if not numeros_por_col:
                continue

            valores = {mes: int("".join(numeros_por_col[c])) if c in numeros_por_col else 0
                       for c, mes in enumerate(meses)}
            resultados.append((nombre, valores))
        return resultados

    def _parsear_pdf(self, path, anio):
        """Extrae todas las filas país×mes de un PDF de informe semestral."""
        filas_totales = []
        with pdfplumber.open(path) as pdf:
            texto = pdf.pages[2].extract_text() or ""
            meses = self.MESES_II if ("II-Sem" in texto or "II SEMESTRE" in texto.upper()) else self.MESES_I

            # el Cuadro 1 ocupa las páginas 2 (América+Caribe) y 3 (resto del mundo)
            for pagina_idx in [2, 3]:
                for nombre, valores in self._parsear_pagina(pdf.pages[pagina_idx], meses):
                    for mes, turistas in valores.items():
                        filas_totales.append([nombre.lower(), anio, self.MESES_ORDEN[mes], mes, turistas])
        return filas_totales

    # ---------- interfaz pública (cargar, transformar, exportar) ----------
    def cargar(self):
        """Lee todos los PDFs de la carpeta configurada y extrae sus tablas
        país×mes. El nombre de cada PDF debe contener el año
        (ej. '2023_Informe_I_Semestre.pdf')."""
        todas_filas = []
        for path in sorted(glob.glob(os.path.join(self.carpeta_pdfs, "*.pdf"))):
            nombre_archivo = os.path.basename(path)
            match = re.search(r"(\d{4})", nombre_archivo)
            if not match:
                print(f"  Se omite '{nombre_archivo}': no se detectó el año en el nombre.")
                continue
            anio = int(match.group(1))
            filas = self._parsear_pdf(path, anio)
            print(f"  {nombre_archivo} -> {len(filas)} filas")
            todas_filas.extend(filas)
        return todas_filas

    def transformar(self, filas):
        """Normaliza nombres de país inconsistentes entre informes y combina
        filas duplicadas (mismo país+año+mes con distinta grafía)."""
        for fila in filas:
            fila[0] = self.CORRECCIONES_PAIS.get(fila[0], fila[0])

        combinado = defaultdict(int)
        orden = {}
        for pais, anio, mes_num, mes_nombre, turistas in filas:
            clave = (pais, anio, mes_num)
            combinado[clave] += turistas
            orden[clave] = (pais, anio, mes_num, mes_nombre)

        filas_unicas = [
            [pais, anio, mes_num, mes_nombre, turistas]
            for (pais, anio, mes_num), turistas in combinado.items()
            for (pais, anio, mes_num, mes_nombre) in [orden[(pais, anio, mes_num)]]
        ]
        filas_unicas.sort(key=lambda x: (x[0], x[1], x[2]))
        return filas_unicas

    def exportar(self):
        """Ejecuta cargar() + transformar() y guarda el CSV final. Devuelve
        la ruta del archivo generado."""
        filas = self.cargar()
        self.filas = self.transformar(filas)

        os.makedirs(os.path.dirname(self.archivo_salida), exist_ok=True)
        with open(self.archivo_salida, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["pais", "anio", "mes_numero", "mes_nombre", "turistas"])
            writer.writerows(self.filas)

        print(f"\nListo: {len(self.filas)} filas guardadas en {self.archivo_salida}")
        print(f"Años cubiertos: {sorted(set(f[1] for f in self.filas))}")
        print(f"Países únicos: {len(set(f[0] for f in self.filas))}")
        return self.archivo_salida