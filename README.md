# 🏦 Bank_Project — QA Automation con IA Orquestada

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Playwright](https://img.shields.io/badge/Playwright-latest-green?logo=playwright)
![Pytest](https://img.shields.io/badge/Pytest-latest-orange?logo=pytest)
![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-blue?logo=githubactions)
![GitHub Issues](https://img.shields.io/badge/Issues%20automáticos-GitHub%20Models-blueviolet?logo=github)
[![Quality gate](https://sonarcloud.io/api/project_badges/quality_gate?project=MiguelZod24_Bank_Project)](https://sonarcloud.io/summary/new_code?id=MiguelZod24_Bank_Project)

> Proyecto de automatización QA sobre **[Parabank](https://parabank.parasoft.com/parabank/index.html)** aplicando un flujo completo de 8 pasos orquestado con Inteligencia Artificial. Desde la exploración automática hasta el cierre automático de bugs — todo integrado en un pipeline CI/CD.

---

## 📋 Descripción

Este proyecto implementa una metodología propia de QA con IA que cubre el ciclo de vida completo del testing:

- Planificación asistida por IA (historias de usuario, criterios de aceptación, casos de prueba)
- Automatización E2E con Playwright + Page Object Model
- Pipeline CI/CD con ejecución diaria automática
- Análisis inteligente de fallos con GitHub Models (GPT-4o)
- Creación y cierre automático de GitHub Issues cuando se detecta un bug real

**App bajo prueba:** [Parabank — Parasoft](https://parabank.parasoft.com/parabank/index.html)  
**Módulos cubiertos:** Login · Registro

---

## 🤖 Flujo QA Orquestado con IA — 8 Pasos

| Paso | Descripción | Herramienta IA |
|------|-------------|----------------|
| **0 — Exploración** | Análisis automático de la app: selectores, flujos y riesgos | Claude Code |
| **1 — Historia de usuario** | Definición del escenario con criterios de aceptación | Claude (chat) |
| **2 — Criterios de aceptación** | Escenarios Given/When/Then estructurados | Claude (chat) |
| **3 — Casos de prueba** | Casos funcionales, UI/UX y seguridad con datos incluidos | Claude (chat) |
| **4 — POM + Tests** | Page Object Model + tests con anotaciones Allure | Claude Code |
| **5 — CI/CD + SonarCloud** | Pipeline diario + Quality Gate de calidad de código | GitHub Actions |
| **6 — Análisis inteligente** | Reporte ejecutivo con causa raíz y sugerencias de fix | GitHub Models |
| **7 — Issues automáticos** | Creación automática de GitHub Issues cuando hay bug real | GitHub Models |
| **8 — Fix + Regresión** | Cierre automático del Issue tras fix verificado en pipeline | Claude Code + GitHub Actions |

---

## 🛠️ Stack Técnico

| Categoría | Herramientas |
|-----------|-------------|
| Automatización | Python · Playwright · Pytest |
| Reportes | Allure · HTML custom (`reporte_po.html`) · Reporte IA (`reporte_ia.html`) |
| CI/CD | GitHub Actions — ejecución diaria 6AM UTC (8AM España) |
| Calidad de código | SonarCloud — Quality Gate integrado en el pipeline |
| Análisis IA | GitHub Models (GPT-4o) via `scripts/analisis_ia.py` |
| Issues | GitHub Issues — creación y cierre automático via API |

---

## 📁 Estructura del Proyecto

```
Bank_Project/
├── .github/
│   └── workflows/
│       └── pipeline.yml        # CI/CD: tests + Allure + SonarCloud + análisis IA
├── pages/
│   ├── __init__.py
│   ├── login_page.py           # POM — módulo Login
│   └── registro_page.py        # POM — módulo Registro
├── scripts/
│   └── analisis_ia.py          # Análisis con GitHub Models + creación/cierre de Issues
├── tests/
│   ├── __init__.py
│   ├── test_login.py           # Tests módulo Login
│   └── test_registro.py        # Tests módulo Registro
├── conftest.py                 # Fixtures + reporte HTML custom
├── pytest.ini                  # Configuración Pytest + Allure
├── sonar-project.properties    # Configuración SonarCloud
└── requirements.txt
```

---

## 🚀 Cómo ejecutar localmente

### 1. Clonar el repositorio
```bash
git clone https://github.com/MiguelZod24/Bank_Project.git
cd Bank_Project
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Ejecutar los tests
```bash
pytest --alluredir=allure-results
```

### 4. Ver reporte Allure
```bash
allure serve allure-results
```

### 5. Ver reporte HTML custom
Abrir `reports/reporte_po.html` en el navegador.

---

## ⚙️ Pipeline CI/CD

El pipeline se ejecuta automáticamente cada día a las **6AM UTC (8AM España)** y también puede lanzarse manualmente desde GitHub Actions (`workflow_dispatch`).

**Pasos del pipeline:**
1. Instalación de dependencias y navegadores
2. Ejecución de todos los tests en modo headless
3. Generación de reporte Allure como artefacto descargable
4. Generación de reporte HTML custom como artefacto
5. Análisis de calidad con SonarCloud (Quality Gate)
6. Análisis inteligente de resultados con GitHub Models
7. Creación automática de Issues si se detectan bugs reales
8. Cierre automático de Issues si los tests pasan tras un fix

---

## 🐛 Gestión automática de bugs

Cuando el pipeline detecta un fallo, GitHub Models analiza la causa raíz y crea automáticamente un Issue con el siguiente formato:

- **Título:** `[BUG] nombre_del_test — módulo`
- **Contenido:** descripción del fallo, análisis IA, sugerencia de fix, impacto y acción recomendada
- **Label:** `bug` asignado automáticamente
- **Deduplicación:** no se crea un Issue si ya existe uno abierto igual

Cuando el bug se corrige y el test vuelve a pasar, el Issue se cierra automáticamente con un comentario de cierre.

📌 Ver historial de bugs detectados y resueltos: [Issues cerrados](https://github.com/MiguelZod24/Bank_Project/issues?q=is%3Aissue+is%3Aclosed)

---

## 📊 Resultados

- ✅ Pipeline en verde
- ✅ Issues creados y cerrados automáticamente
- ✅ Flujo completo de 8 pasos implementado y verificado

---

## 👤 Autor

**Miguel Barrientos**  
QA Automation Engineer — AI-Augmented QA  
[LinkedIn](https://www.linkedin.com/in/miguelbarrientosottolina/) · [GitHub](https://github.com/MiguelZod24)

---

*Proyecto desarrollado como parte de una investigación aplicada sobre integración de IA en el ciclo de vida completo del testing — Abril 2026*
