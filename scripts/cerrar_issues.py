"""
Paso 8 del flujo QA orquestado con IA
Lee reports/analisis_ia.json y cierra automáticamente los Issues abiertos
cuyo test correspondiente ha vuelto a pasar en la última ejecución
"""

import os
import sys
import json
import requests


# Ruta del análisis generado por el Paso 6
ANALISIS_JSON = "reports/analisis_ia.json"

# Prefijo que usan los Issues creados por crear_issues.py — debe coincidir exactamente
PREFIJO_BUG = "[BUG]"

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


def obtener_issues_abiertos(headers, owner, repo):
    """Devuelve un dict {titulo: numero} de todos los Issues abiertos del repositorio."""
    issues = {}
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
            # La API mezcla PRs con Issues — los PRs tienen 'pull_request'
            if "pull_request" not in issue:
                issues[issue["title"]] = issue["number"]

        # Menos de 100 resultados significa que no hay más páginas
        if len(items) < 100:
            break
        pagina += 1

    return issues


def extraer_modulo(suite):
    """Extrae el nombre del módulo desde la ruta de suite.
    Ej: 'tests/test_login.py' → 'test_login'
    """
    if not suite:
        return "desconocido"
    nombre_archivo = suite.split("/")[-1]   # 'test_login.py'
    return nombre_archivo.replace(".py", "")  # 'test_login'


def comentar_issue(headers, owner, repo, numero, texto):
    """Añade un comentario al Issue indicando que el test volvió a pasar."""
    url = f"{API_BASE}/repos/{owner}/{repo}/issues/{numero}/comments"
    resp = requests.post(url, headers=headers, json={"body": texto}, timeout=15)
    resp.raise_for_status()


def cerrar_issue(headers, owner, repo, numero):
    """Cierra el Issue vía PATCH estableciendo state=closed."""
    url = f"{API_BASE}/repos/{owner}/{repo}/issues/{numero}"
    resp = requests.patch(url, headers=headers, json={"state": "closed"}, timeout=15)
    resp.raise_for_status()


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

    # Filtrar solo los tests que han pasado en esta ejecución
    tests_pasados = [
        t for t in analisis.get("tests", [])
        if t.get("status") == "passed"
    ]

    if not tests_pasados:
        print("No hay tests pasados en el análisis. Terminando sin error.")
        sys.exit(0)

    print(f"Tests pasados en esta ejecución: {len(tests_pasados)}")

    # Obtener el mapa de Issues abiertos para buscar coincidencias por título
    print("Consultando Issues abiertos en el repositorio...")
    try:
        issues_abiertos = obtener_issues_abiertos(headers, owner, repo)
    except requests.HTTPError as e:
        print(f"ERROR al consultar Issues existentes: {e}")
        sys.exit(1)

    print(f"Issues abiertos encontrados: {len(issues_abiertos)}")

    cerrados = 0
    sin_issue = 0

    for test in tests_pasados:
        nombre_corto = test.get("nombre_corto") or test.get("nombre", "desconocido")
        modulo = extraer_modulo(test.get("suite", ""))

        # El título debe coincidir exactamente con el formato de crear_issues.py
        titulo = f"{PREFIJO_BUG} {nombre_corto} — {modulo}"

        if titulo not in issues_abiertos:
            # No existe un Issue abierto para este test — no hay nada que cerrar
            sin_issue += 1
            continue

        numero = issues_abiertos[titulo]
        print(f"  Cerrando Issue #{numero}: {titulo}")

        # Comentar primero para dejar trazabilidad antes de cerrar
        comentario = (
            f"✅ El test `{nombre_corto}` ha vuelto a pasar en la última ejecución del pipeline. "
            f"Cerrando automáticamente."
        )

        try:
            comentar_issue(headers, owner, repo, numero, comentario)
            cerrar_issue(headers, owner, repo, numero)
            print(f"  → Cerrado correctamente")
            cerrados += 1
        except requests.HTTPError as e:
            print(f"  ERROR al cerrar Issue #{numero}: {e}")

    print(f"\nResumen: {cerrados} Issue(s) cerrado(s), {sin_issue} test(s) pasados sin Issue abierto.")


if __name__ == "__main__":
    main()
