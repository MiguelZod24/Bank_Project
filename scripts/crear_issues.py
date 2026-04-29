"""
Paso 7 del flujo QA orquestado con IA
Lee el análisis de reports/analisis_ia.json y por cada test fallido
crea un Issue en GitHub si no existe ya uno abierto con el mismo título
"""

import os
import sys
import json
import requests


# Ruta del análisis generado por el Paso 6
ANALISIS_JSON = "reports/analisis_ia.json"

# Prefijo estándar para los títulos de los Issues de bug
PREFIJO_BUG = "[BUG]"

# Nombre del label que se asigna a todos los issues creados
LABEL_BUG = "bug"

# Base de la API REST de GitHub
API_BASE = "https://api.github.com"


def obtener_credenciales():
    """Lee y valida las variables de entorno necesarias para la API de GitHub."""
    token = os.environ.get("GH_TOKEN", "")
    repo_completo = os.environ.get("GITHUB_REPOSITORY", "")

    if not token:
        print("ERROR: La variable de entorno GH_TOKEN no está definida.")
        sys.exit(1)
    if not repo_completo:
        print("ERROR: La variable de entorno GITHUB_REPOSITORY no está definida.")
        sys.exit(1)
    if "/" not in repo_completo:
        print(f"ERROR: GITHUB_REPOSITORY tiene formato inesperado: '{repo_completo}'")
        sys.exit(1)

    owner, nombre_repo = repo_completo.split("/", 1)
    return token, owner, nombre_repo


def construir_headers(token):
    """Devuelve los headers estándar para la API REST de GitHub."""
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def asegurar_label_bug(headers, owner, repo):
    """Crea el label 'bug' en el repositorio si todavía no existe."""
    url = f"{API_BASE}/repos/{owner}/{repo}/labels/{LABEL_BUG}"
    resp = requests.get(url, headers=headers, timeout=15)

    if resp.status_code == 200:
        # El label ya existe, no hay nada que hacer
        return

    # El label no existe — crearlo con el color rojo estándar de GitHub
    print(f"  Creando label '{LABEL_BUG}' en el repositorio...")
    payload = {
        "name": LABEL_BUG,
        "color": "d73a4a",
        "description": "Fallo detectado automáticamente por el pipeline QA",
    }
    resp_crear = requests.post(
        f"{API_BASE}/repos/{owner}/{repo}/labels",
        headers=headers,
        json=payload,
        timeout=15,
    )
    # 422 significa que ya existe (race condition) — no es un error real
    if resp_crear.status_code not in (200, 201, 422):
        print(f"  Advertencia: no se pudo crear el label: {resp_crear.status_code}")


def obtener_titulos_issues_abiertos(headers, owner, repo):
    """Devuelve el conjunto de títulos de todos los Issues abiertos del repositorio."""
    titulos = set()
    pagina = 1

    while True:
        url = (
            f"{API_BASE}/repos/{owner}/{repo}/issues"
            f"?state=open&per_page=100&page={pagina}"
        )
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        items = resp.json()
        if not items:
            break

        for issue in items:
            # La API de GitHub mezcla PRs con Issues — los PRs tienen 'pull_request'
            if "pull_request" not in issue:
                titulos.add(issue["title"])

        # Menos de 100 resultados significa que ya no hay más páginas
        if len(items) < 100:
            break
        pagina += 1

    return titulos


def extraer_modulo(suite):
    """Extrae el nombre del módulo desde la ruta de suite.
    Ej: 'tests/test_login.py' → 'test_login'
    """
    if not suite:
        return "desconocido"
    nombre_archivo = suite.split("/")[-1]   # 'test_login.py'
    return nombre_archivo.replace(".py", "")  # 'test_login'


def construir_cuerpo_issue(test):
    """Genera el cuerpo en Markdown del Issue a partir de los datos del test."""
    nombre_corto = test.get("nombre_corto") or test.get("nombre", "")
    full_name = test.get("nombre", "")
    suite = test.get("suite", "")
    status = test.get("status", "")
    duracion = test.get("duracion", 0)
    error = test.get("error", "")
    analisis = test.get("analisis", "")
    sugerencia = test.get("sugerencia_fix", "")
    impacto = test.get("impacto_negocio", "")
    accion = test.get("accion_recomendada", "")

    partes = []

    # Tabla resumen del test
    partes.append("## Información del test\n")
    partes.append("| Campo | Valor |")
    partes.append("|---|---|")
    partes.append(f"| **Nombre** | `{nombre_corto}` |")
    partes.append(f"| **Full name** | `{full_name}` |")
    partes.append(f"| **Módulo** | `{suite}` |")
    partes.append(f"| **Estado** | `{status}` |")
    partes.append(f"| **Duración** | {duracion}s |")
    partes.append("")

    # Traza del error (si la hay)
    if error:
        partes.append("## Detalle del error\n")
        partes.append(f"```\n{error}\n```\n")

    # Análisis de la IA
    if analisis:
        partes.append("## Análisis IA\n")
        partes.append(f"{analisis}\n")

    # Sugerencia de corrección
    if sugerencia:
        partes.append("## Sugerencia de fix\n")
        partes.append(f"{sugerencia}\n")

    # Impacto en el negocio
    if impacto:
        partes.append("## Impacto en el negocio\n")
        partes.append(f"{impacto}\n")

    # Acción recomendada
    if accion:
        partes.append("## Acción recomendada\n")
        partes.append(f"{accion}\n")

    partes.append("---")
    partes.append(
        "*Issue generado automáticamente por el pipeline QA "
        "— Paso 7 del flujo QA orquestado con IA*"
    )

    return "\n".join(partes)


def crear_issue(headers, owner, repo, titulo, cuerpo):
    """Envía la petición a la API para crear el Issue y devuelve su URL."""
    payload = {
        "title": titulo,
        "body": cuerpo,
        "labels": [LABEL_BUG],
    }
    resp = requests.post(
        f"{API_BASE}/repos/{owner}/{repo}/issues",
        headers=headers,
        json=payload,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("html_url", "")


def main():
    # Obtener credenciales de las variables de entorno
    token, owner, repo = obtener_credenciales()
    headers = construir_headers(token)

    # Verificar que el análisis JSON del Paso 6 existe
    if not os.path.exists(ANALISIS_JSON):
        print(f"No se encontró '{ANALISIS_JSON}'. Terminando sin error.")
        sys.exit(0)

    # Leer el análisis
    with open(ANALISIS_JSON, "r", encoding="utf-8") as f:
        analisis = json.load(f)

    # Filtrar solo los tests con estado fallido o broken
    tests_fallidos = [
        t for t in analisis.get("tests", [])
        if t.get("status") in ("failed", "broken")
    ]

    if not tests_fallidos:
        print("No hay tests fallidos en el análisis. No se crean Issues. Terminando sin error.")
        sys.exit(0)

    print(f"Tests fallidos detectados: {len(tests_fallidos)}")

    # Asegurar que el label 'bug' existe en el repo antes de crear los issues
    asegurar_label_bug(headers, owner, repo)

    # Obtener los títulos de issues ya abiertos para evitar duplicados
    print("Consultando Issues abiertos en el repositorio...")
    try:
        issues_abiertos = obtener_titulos_issues_abiertos(headers, owner, repo)
    except requests.HTTPError as e:
        print(f"ERROR al consultar Issues existentes: {e}")
        sys.exit(1)

    print(f"Issues abiertos encontrados: {len(issues_abiertos)}")

    # Crear un Issue por cada test fallido que no tenga ya uno abierto
    creados = 0
    omitidos = 0

    for test in tests_fallidos:
        nombre_corto = test.get("nombre_corto") or test.get("nombre", "desconocido")
        modulo = extraer_modulo(test.get("suite", ""))
        titulo = f"{PREFIJO_BUG} {nombre_corto} — {modulo}"

        if titulo in issues_abiertos:
            print(f"  Omitido (ya existe): {titulo}")
            omitidos += 1
            continue

        print(f"  Creando Issue: {titulo}")
        cuerpo = construir_cuerpo_issue(test)

        try:
            url_issue = crear_issue(headers, owner, repo, titulo, cuerpo)
            print(f"  → Creado: {url_issue}")
            creados += 1
        except requests.HTTPError as e:
            print(f"  ERROR al crear Issue '{titulo}': {e}")

    print(f"\nResumen: {creados} Issue(s) creado(s), {omitidos} omitido(s) por duplicado.")


if __name__ == "__main__":
    main()
