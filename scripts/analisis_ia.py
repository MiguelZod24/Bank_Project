"""
Paso 6 del flujo QA orquestado con IA
Lee los resultados de Allure, los analiza con GitHub Models (GPT-4o)
y genera un reporte HTML bilingüe (vista técnica + vista negocio)
"""

import os
import sys
import json
import glob
import requests
from datetime import datetime


# Directorio de resultados de Allure y ruta del reporte de salida
ALLURE_DIR = "reports/allure-results"
OUTPUT_HTML = "reports/reporte_ia.html"

# Configuración de GitHub Models
ENDPOINT = "https://models.inference.ai.azure.com"
MODELO = "openai/gpt-4o"


def leer_resultados():
    """Lee todos los *-result.json de Allure y extrae los datos relevantes de cada test."""
    archivos = glob.glob(f"{ALLURE_DIR}/*-result.json")

    if not archivos:
        return []

    resultados = []
    for archivo in archivos:
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                dato = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Advertencia: no se pudo leer {archivo}: {e}")
            continue

        # Ignorar archivos sin campo 'status' (son containers, no resultados de test)
        if "status" not in dato:
            continue

        # Calcular duración en segundos a partir de los timestamps en milisegundos
        duracion_ms = dato.get("stop", 0) - dato.get("start", 0)
        duracion_s = round(max(duracion_ms, 0) / 1000, 2)

        # Extraer mensaje de error si el test falló o rompió
        error_msg = ""
        detalles = dato.get("statusDetails", {})
        if detalles:
            raw_error = detalles.get("message", "") or detalles.get("trace", "")
            # Truncar errores muy largos para no saturar el prompt de la IA
            if raw_error and len(raw_error) > 800:
                error_msg = raw_error[:800] + "... [truncado]"
            else:
                error_msg = raw_error or ""

        # Derivar el archivo de suite a partir del fullName (ej: "tests.test_login#test_x")
        full_name = dato.get("fullName", "")
        suite = ""
        if "#" in full_name:
            modulo = full_name.split("#")[0]            # ej: "tests.test_login"
            suite = modulo.replace(".", "/") + ".py"   # ej: "tests/test_login.py"

        resultados.append({
            "nombre": dato.get("name", "desconocido"),
            "full_name": full_name,
            "status": dato.get("status", "unknown"),
            "duracion": duracion_s,
            "suite": suite,
            "error": error_msg,
        })

    # Ordenar: primero los fallidos para que la IA los analice con prioridad
    resultados.sort(
        key=lambda x: (0 if x["status"] in ("failed", "broken") else 1, x["nombre"])
    )
    return resultados


def llamar_ia(token, resultados):
    """Envía los datos de los tests a GitHub Models (GPT-4o) y devuelve el análisis como dict."""
    # Construir el resumen de tests para el prompt
    lineas_prompt = []
    for r in resultados:
        linea = (
            f"- full_name: {r['full_name']}"
            f" | nombre: {r['nombre']}"
            f" | suite: {r['suite']}"
            f" | status: {r['status']}"
            f" | duración: {r['duracion']}s"
        )
        if r["error"]:
            linea += f"\n  error: {r['error']}"
        lineas_prompt.append(linea)

    resumen_tests = "\n".join(lineas_prompt)

    prompt = f"""Eres un experto QA analizando resultados de pruebas automatizadas de la aplicación web ParaBank (parabank.parasoft.com). Los módulos testeados son Login y Registro.

Resultados de los tests:
{resumen_tests}

Responde ÚNICAMENTE con un JSON válido con esta estructura exacta (sin bloques markdown, sin texto adicional):
{{
  "resumen_ejecutivo": "Párrafo en español para el Product Owner resumiendo el estado de calidad, riesgos para el negocio y recomendaciones clave.",
  "estado_general": "VERDE",
  "code_review_general": "Observaciones sobre la suite de tests: cobertura, casos edge no cubiertos, calidad de los tests.",
  "tests": [
    {{
      "nombre": "full_name exacto del test tal como aparece en los datos recibidos",
      "analisis": "Para tests fallidos: qué falló y por qué. Para tests pasados: cadena vacía.",
      "sugerencia_fix": "Para tests fallidos: cómo corregirlo en el código de test o en la app. Para tests pasados: cadena vacía.",
      "impacto_negocio": "Qué significa este resultado para el negocio en 1-2 frases.",
      "accion_recomendada": "Próximo paso concreto para el equipo."
    }}
  ]
}}

Reglas:
- estado_general debe ser exactamente "VERDE", "AMARILLO" o "ROJO" según la proporción de tests fallidos.
- Para tests pasados: analisis y sugerencia_fix deben ser "" (cadena vacía).
- Para tests fallidos o broken: dar análisis detallado basado en el mensaje de error.
- El campo nombre en la lista tests debe contener el full_name exacto para identificar cada test.
- Todo el texto de respuesta en español."""

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODELO,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 3500,
    }

    respuesta = requests.post(
        f"{ENDPOINT}/chat/completions",
        headers=headers,
        json=payload,
        timeout=90,
    )
    respuesta.raise_for_status()

    contenido = respuesta.json()["choices"][0]["message"]["content"].strip()

    # Limpiar posibles bloques de código markdown que la IA pudiera añadir
    if contenido.startswith("```"):
        lineas_resp = contenido.split("\n")
        contenido = "\n".join(lineas_resp[1:-1])

    return json.loads(contenido)


def html_escape(texto):
    """Escapa los caracteres especiales HTML para evitar XSS en el reporte."""
    if not texto:
        return ""
    return (
        str(texto)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def generar_html(resultados, analisis_ia):
    """Genera el reporte HTML con el mismo estilo visual que reporte_po.html."""
    ahora = datetime.now().strftime("%d-%b-%Y a las %H:%M:%S")

    total = len(resultados)
    pasados = sum(1 for r in resultados if r["status"] == "passed")
    fallidos = sum(1 for r in resultados if r["status"] in ("failed", "broken"))

    # Color del indicador de estado general según semáforo
    estado = analisis_ia.get("estado_general", "VERDE")
    color_estado = {"VERDE": "#43a047", "AMARILLO": "#fb8c00", "ROJO": "#e53935"}.get(
        estado, "#555"
    )

    # Indexar el análisis de la IA por full_name para búsqueda O(1)
    mapa_ia = {t["nombre"]: t for t in analisis_ia.get("tests", [])}

    # Generar las tarjetas de cada test
    tarjetas = []
    for r in resultados:
        ia = mapa_ia.get(r["full_name"], {})

        # Clase e ícono del badge según status
        if r["status"] == "passed":
            badge_class, badge_texto = "passed", "PASADO"
        elif r["status"] in ("failed", "broken"):
            badge_class, badge_texto = "failed", "FALLIDO"
        else:
            badge_class, badge_texto = "skipped", "OMITIDO"

        # Bloque de traza de error técnico (solo si hay error)
        bloque_error = ""
        if r["error"]:
            bloque_error = (
                '<div class="log-box">'
                f'<span class="error-line">{html_escape(r["error"])}</span>'
                "</div>"
            )

        # Bloques del análisis de la IA para la columna de negocio
        analisis_texto = ia.get("analisis", "")
        sugerencia = ia.get("sugerencia_fix", "")
        impacto = ia.get("impacto_negocio", "")
        accion = ia.get("accion_recomendada", "Ninguna acción requerida.")

        box_ia = ""
        if analisis_texto:
            box_ia += (
                '<div class="alert-box">'
                f"<strong>Análisis IA:</strong> {html_escape(analisis_texto)}"
                "</div>"
            )
        if sugerencia:
            box_ia += (
                '<div class="alert-box" style="margin-top:8px;">'
                f"<strong>Sugerencia de fix:</strong> {html_escape(sugerencia)}"
                "</div>"
            )

        tarjeta = f"""
        <div class="test-card">
          <div class="test-header">
            <div>
              <div class="test-name">{html_escape(r["nombre"])}</div>
              <div class="test-file">{html_escape(r["suite"])} &nbsp;·&nbsp; <span class="duration-badge">{r["duracion"]}s</span></div>
            </div>
            <span class="badge {badge_class}">{badge_texto}</span>
          </div>
          <div class="test-body">
            <div class="technical">
              <h3>Detalle técnico</h3>
              <div class="meta-row"><span class="meta-label">Test:</span> {html_escape(r["full_name"])}</div>
              <div class="meta-row"><span class="meta-label">Estado:</span> {html_escape(r["status"])}</div>
              <div class="meta-row"><span class="meta-label">Duración:</span> {r["duracion"]}s</div>
              {bloque_error}
            </div>
            <div class="po-view">
              <h3>Análisis IA — Vista negocio</h3>
              <div class="po-section">
                <div class="po-label">Impacto en el negocio</div>
                <p>{html_escape(impacto) or "Sin impacto identificado."}</p>
              </div>
              {box_ia}
              <div class="info-box" style="margin-top:10px;">
                <strong>Acción recomendada:</strong> {html_escape(accion)}
              </div>
            </div>
          </div>
        </div>"""
        tarjetas.append(tarjeta)

    resumen_ejecutivo = html_escape(
        analisis_ia.get("resumen_ejecutivo", "Sin análisis disponible.")
    )
    code_review = html_escape(analisis_ia.get("code_review_general", ""))

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8"/>
  <title>Reporte IA — Análisis QA</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: Helvetica, Arial, sans-serif; font-size: 14px; background: #f4f6f9; color: #333; padding: 30px; }}
    h1 {{ font-size: 26px; color: #222; margin-bottom: 4px; }}
    .subtitle {{ color: #888; font-size: 13px; margin-bottom: 30px; }}
    .summary-bar {{ display: flex; gap: 16px; margin-bottom: 24px; }}
    .summary-card {{ flex: 1; background: white; border-radius: 8px; padding: 18px 24px; border-left: 5px solid #ccc; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
    .summary-card.total {{ border-color: #555; }}
    .summary-card.failed {{ border-color: #e53935; }}
    .summary-card.passed {{ border-color: #43a047; }}
    .summary-card.estado {{ border-color: {color_estado}; }}
    .summary-card .number {{ font-size: 36px; font-weight: bold; }}
    .summary-card.failed .number {{ color: #e53935; }}
    .summary-card.passed .number {{ color: #43a047; }}
    .summary-card .label {{ font-size: 13px; color: #888; margin-top: 2px; }}
    .executive-summary {{ background: white; border-radius: 8px; padding: 20px 24px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); margin-bottom: 24px; border-left: 5px solid {color_estado}; }}
    .executive-summary h2 {{ font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; color: #888; margin-bottom: 10px; }}
    .executive-summary p {{ font-size: 14px; line-height: 1.7; color: #333; }}
    .code-review {{ background: white; border-radius: 8px; padding: 20px 24px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); margin-bottom: 24px; border-left: 5px solid #7b1fa2; }}
    .code-review h2 {{ font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; color: #888; margin-bottom: 10px; }}
    .code-review p {{ font-size: 14px; line-height: 1.7; color: #333; }}
    .test-card {{ background: white; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); margin-bottom: 24px; overflow: hidden; }}
    .test-header {{ display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid #eee; }}
    .test-header .test-name {{ font-weight: bold; font-size: 15px; }}
    .test-header .test-file {{ font-size: 12px; color: #999; margin-top: 3px; }}
    .badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; color: white; }}
    .badge.failed {{ background: #e53935; }}
    .badge.passed {{ background: #43a047; }}
    .badge.skipped {{ background: #888; }}
    .test-body {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0; }}
    .technical {{ padding: 20px; border-right: 1px solid #eee; }}
    .technical h3 {{ font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: #888; margin-bottom: 12px; }}
    .meta-row {{ display: flex; gap: 8px; margin-bottom: 10px; font-size: 13px; }}
    .meta-label {{ color: #999; min-width: 80px; }}
    .log-box {{ background: #1e1e1e; color: #d4d4d4; border-radius: 6px; padding: 14px; font-family: "Courier New", Courier, monospace; font-size: 11.5px; line-height: 1.6; white-space: pre-wrap; overflow-x: auto; margin-top: 12px; }}
    .error-line {{ color: #f48771; }}
    .po-view {{ padding: 20px; background: #fafbfc; }}
    .po-view h3 {{ font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: #888; margin-bottom: 12px; }}
    .po-section {{ margin-bottom: 16px; }}
    .po-label {{ font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.06em; color: #aaa; margin-bottom: 4px; }}
    .po-section p {{ font-size: 13.5px; line-height: 1.6; color: #333; }}
    .alert-box {{ background: #fff3e0; border-left: 4px solid #fb8c00; border-radius: 4px; padding: 12px 14px; font-size: 13px; line-height: 1.6; margin-top: 14px; color: #444; }}
    .alert-box strong {{ color: #e65100; }}
    .info-box {{ background: #e8f5e9; border-left: 4px solid #43a047; border-radius: 4px; padding: 12px 14px; font-size: 13px; line-height: 1.6; color: #444; }}
    .duration-badge {{ font-size: 12px; color: #888; background: #f0f0f0; padding: 2px 8px; border-radius: 10px; }}
    footer {{ text-align: center; color: #bbb; font-size: 12px; margin-top: 40px; }}
    .ia-badge {{ display: inline-block; background: #7b1fa2; color: white; font-size: 11px; padding: 2px 8px; border-radius: 10px; margin-left: 8px; vertical-align: middle; }}
  </style>
</head>
<body>
  <h1>Reporte IA — Análisis QA <span class="ia-badge">GPT-4o</span></h1>
  <p class="subtitle">Generado el {ahora} &nbsp;·&nbsp; Aplicación: ParaBank — parabank.parasoft.com</p>

  <div class="summary-bar">
    <div class="summary-card total">
      <div class="number">{total}</div>
      <div class="label">Tests ejecutados</div>
    </div>
    <div class="summary-card failed">
      <div class="number">{fallidos}</div>
      <div class="label">Fallidos</div>
    </div>
    <div class="summary-card passed">
      <div class="number">{pasados}</div>
      <div class="label">Pasados</div>
    </div>
    <div class="summary-card estado">
      <div class="number" style="font-size:24px; color:{color_estado};">{estado}</div>
      <div class="label">Estado general</div>
    </div>
  </div>

  <div class="executive-summary">
    <h2>Resumen ejecutivo — Product Owner</h2>
    <p>{resumen_ejecutivo}</p>
  </div>

  <div class="code-review">
    <h2>Code Review — Suite de tests</h2>
    <p>{code_review}</p>
  </div>

  {"".join(tarjetas)}

  <footer>Análisis generado con GitHub Models (GPT-4o) · Paso 6 del flujo QA orquestado · {ahora}</footer>
</body>
</html>"""

    return html


def main():
    # Verificar que el token de GitHub está disponible en el entorno
    token = os.environ.get("GH_TOKEN", "")
    if not token:
        print("ERROR: La variable de entorno GH_TOKEN no está definida.")
        sys.exit(1)

    # Leer los resultados de Allure
    print(f"Leyendo resultados de Allure en '{ALLURE_DIR}'...")
    resultados = leer_resultados()

    # Si no hay resultados no es un error, simplemente no hay nada que analizar
    if not resultados:
        print("No se encontraron archivos de resultado en allure-results. Terminando sin error.")
        sys.exit(0)

    print(f"Tests encontrados: {len(resultados)}")
    for r in resultados:
        print(f"  {r['status']:8s} | {r['full_name']}")

    # Llamar a GitHub Models para obtener el análisis
    print(f"\nEnviando datos a GitHub Models ({MODELO})...")
    try:
        analisis_ia = llamar_ia(token, resultados)
    except requests.HTTPError as e:
        print(f"ERROR HTTP al llamar a GitHub Models: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR al parsear la respuesta JSON de la IA: {e}")
        sys.exit(1)
    except requests.RequestException as e:
        print(f"ERROR de red al llamar a GitHub Models: {e}")
        sys.exit(1)

    # Generar el reporte HTML
    print(f"\nGenerando reporte en '{OUTPUT_HTML}'...")
    os.makedirs("reports", exist_ok=True)
    html_content = generar_html(resultados, analisis_ia)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Reporte generado correctamente: {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
