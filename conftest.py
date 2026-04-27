import pytest
import base64
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
import pytest_html

# Lista global donde se van guardando los resultados de cada test
_test_results = []


def _parse_po_info(docstring):
    """
    Lee el docstring de cada test y extrae las claves:
    escenario, esperado, impacto, accion
    """
    if not docstring:
        return {}
    info = {}
    current_key = None
    current_lines = []
    for line in docstring.strip().splitlines():
        line = line.strip()
        matched = False
        for key in ['escenario', 'esperado', 'impacto', 'accion']:
            if line.lower().startswith(f'{key}:'):
                if current_key:
                    info[current_key] = ' '.join(current_lines).strip()
                current_key = key
                current_lines = [line[len(key) + 1:].strip()]
                matched = True
                break
        if not matched and current_key and line:
            current_lines.append(line)
    if current_key:
        info[current_key] = ' '.join(current_lines).strip()
    return info


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # Captura el resultado de cada test para usarlo después
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(scope="session")
def browser():
    # Abre el navegador una sola vez para toda la sesión
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(browser, request, extra):
    # Crea una página nueva para cada test
    page = browser.new_page()
    start = time.time()
    yield page

    duration = time.time() - start
    failed = hasattr(request.node, "rep_call") and request.node.rep_call.failed

    # Si el test falló, toma captura de pantalla
    screenshot_b64 = None
    if failed:
        screenshot_bytes = page.screenshot(full_page=True)
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        extra.append(pytest_html.extras.png(screenshot_bytes, name="Captura del error"))
        extra.append(pytest_html.extras.text(
            f"Test: {request.node.name}\nURL al momento del fallo: {page.url}",
            name="Detalles del error"
        ))

    # Guarda el log del error si existe
    error_log = ''
    if failed and hasattr(request.node, 'rep_call') and request.node.rep_call.longrepr:
        error_log = str(request.node.rep_call.longrepr)

    # Guarda el resultado del test en la lista global
    _test_results.append({
        'name': request.node.name,
        'nodeid': request.node.nodeid,
        'result': 'Fallido' if failed else 'Pasado',
        'duration': f'{duration:.1f}s',
        'error_log': error_log,
        'screenshot_b64': screenshot_b64,
        'url': page.url,
        'po_info': _parse_po_info(request.node.function.__doc__),
    })

    page.close()


def pytest_sessionfinish(session, exitstatus):
    # Al terminar todos los tests, genera el reporte HTML
    if _test_results:
        _generate_po_report()


def _generate_po_report():
    total = len(_test_results)
    failed_count = sum(1 for r in _test_results if r['result'] == 'Fallido')
    passed_count = total - failed_count
    now = datetime.now().strftime('%d-%b-%Y a las %H:%M:%S')

    css = """
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Helvetica, Arial, sans-serif; font-size: 14px; background: #f4f6f9; color: #333; padding: 30px; }
    h1 { font-size: 26px; color: #222; margin-bottom: 4px; }
    .subtitle { color: #888; font-size: 13px; margin-bottom: 30px; }
    .summary-bar { display: flex; gap: 16px; margin-bottom: 30px; }
    .summary-card { flex: 1; background: white; border-radius: 8px; padding: 18px 24px; border-left: 5px solid #ccc; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
    .summary-card.total { border-color: #555; }
    .summary-card.failed { border-color: #e53935; }
    .summary-card.passed { border-color: #43a047; }
    .summary-card .number { font-size: 36px; font-weight: bold; }
    .summary-card.failed .number { color: #e53935; }
    .summary-card.passed .number { color: #43a047; }
    .summary-card .label { font-size: 13px; color: #888; margin-top: 2px; }
    .test-card { background: white; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); margin-bottom: 24px; overflow: hidden; }
    .test-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid #eee; }
    .test-header .test-name { font-weight: bold; font-size: 15px; }
    .test-header .test-file { font-size: 12px; color: #999; margin-top: 3px; }
    .badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; color: white; }
    .badge.failed { background: #e53935; }
    .badge.passed { background: #43a047; }
    .test-body { display: grid; grid-template-columns: 1fr 1fr; gap: 0; }
    .technical { padding: 20px; border-right: 1px solid #eee; }
    .technical h3 { font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: #888; margin-bottom: 12px; }
    .meta-row { display: flex; gap: 8px; margin-bottom: 10px; font-size: 13px; }
    .meta-label { color: #999; min-width: 80px; }
    .log-box { background: #1e1e1e; color: #d4d4d4; border-radius: 6px; padding: 14px; font-family: "Courier New", Courier, monospace; font-size: 11.5px; line-height: 1.6; white-space: pre-wrap; overflow-x: auto; margin-top: 12px; }
    .error-line { color: #f48771; }
    .pointer-line { color: #569cd6; font-weight: bold; }
    .screenshot-section { margin-top: 16px; }
    .screenshot-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #888; margin-bottom: 8px; }
    .po-view { padding: 20px; background: #fafbfc; }
    .po-view h3 { font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: #888; margin-bottom: 12px; }
    .po-section { margin-bottom: 16px; }
    .po-label { font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.06em; color: #aaa; margin-bottom: 4px; }
    .po-section p { font-size: 13.5px; line-height: 1.6; color: #333; }
    .alert-box { background: #fff3e0; border-left: 4px solid #fb8c00; border-radius: 4px; padding: 12px 14px; font-size: 13px; line-height: 1.6; margin-top: 14px; color: #444; }
    .alert-box strong { color: #e65100; }
    .info-box { background: #e8f5e9; border-left: 4px solid #43a047; border-radius: 4px; padding: 12px 14px; font-size: 13px; line-height: 1.6; color: #444; }
    .duration-badge { font-size: 12px; color: #888; background: #f0f0f0; padding: 2px 8px; border-radius: 10px; }
    footer { text-align: center; color: #bbb; font-size: 12px; margin-top: 40px; }
    """

    cards = ''
    for r in _test_results:
        badge_class = 'failed' if r['result'] == 'Fallido' else 'passed'
        po = r['po_info']
        escenario = po.get('escenario', 'No especificado.')
        esperado = po.get('esperado', 'No especificado.')
        impacto = po.get('impacto', 'No especificado.')
        accion = po.get('accion', 'No especificado.')

        screenshot_html = ''
        if r['screenshot_b64']:
            screenshot_html = (
                '<div class="screenshot-section">'
                '<div class="screenshot-label">Captura del error</div>'
                f'<img src="data:image/png;base64,{r["screenshot_b64"]}" '
                'style="max-width:100%;border-radius:4px;border:1px solid #ddd;" />'
                '</div>'
            )

        error_html = ''
        if r['error_log']:
            escaped = (r['error_log']
                       .replace('&', '&amp;')
                       .replace('<', '&lt;')
                       .replace('>', '&gt;'))
            lines = []
            for line in escaped.splitlines():
                stripped = line.lstrip()
                if stripped.startswith('E ') or 'AssertionError' in stripped:
                    lines.append(f'<span class="error-line">{line}</span>')
                elif stripped.startswith('&gt;'):
                    lines.append(f'<span class="pointer-line">{line}</span>')
                else:
                    lines.append(line)
            error_html = '<div class="log-box">' + '<br>'.join(lines) + '</div>'

        impact_class = 'alert-box' if r['result'] == 'Fallido' else 'info-box'

        cards += f'''
        <div class="test-card">
          <div class="test-header">
            <div>
              <div class="test-name">{r["name"]}</div>
              <div class="test-file">{r["nodeid"]} &nbsp;·&nbsp; <span class="duration-badge">{r["duration"]}</span></div>
            </div>
            <span class="badge {badge_class}">{r["result"].upper()}</span>
          </div>
          <div class="test-body">
            <div class="technical">
              <h3>Detalle técnico</h3>
              <div class="meta-row"><span class="meta-label">Archivo:</span> {r["nodeid"]}</div>
              <div class="meta-row"><span class="meta-label">URL:</span> {r["url"]}</div>
              <div class="meta-row"><span class="meta-label">Duración:</span> {r["duration"]}</div>
              {error_html}
              {screenshot_html}
            </div>
            <div class="po-view">
              <h3>Explicación para el negocio</h3>
              <div class="po-section">
                <div class="po-label">¿Qué se estaba probando?</div>
                <p>{escenario}</p>
              </div>
              <div class="po-section">
                <div class="po-label">¿Qué se esperaba?</div>
                <p>{esperado}</p>
              </div>
              <div class="{impact_class}">
                <strong>Impacto en el negocio:</strong> {impacto}
              </div>
              <div class="info-box" style="margin-top:10px;">
                <strong>Acción recomendada:</strong> {accion}
              </div>
            </div>
          </div>
        </div>'''

    test_word = 'Test ejecutado' if total == 1 else 'Tests ejecutados'
    failed_word = 'Fallido' if failed_count == 1 else 'Fallidos'
    passed_word = 'Pasado' if passed_count == 1 else 'Pasados'

    html = f'''<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8"/>
  <title>Reporte de Pruebas — Vista PO</title>
  <style>{css}</style>
</head>
<body>
  <h1>Reporte de Pruebas Automatizadas</h1>
  <p class="subtitle">Generado el {now} &nbsp;·&nbsp; Aplicación: Registro — parabank.parasoft.com</p>
  <div class="summary-bar">
    <div class="summary-card total">
      <div class="number">{total}</div>
      <div class="label">{test_word}</div>
    </div>
    <div class="summary-card failed">
      <div class="number">{failed_count}</div>
      <div class="label">{failed_word}</div>
    </div>
    <div class="summary-card passed">
      <div class="number">{passed_count}</div>
      <div class="label">{passed_word}</div>
    </div>
  </div>
  {cards}
  <footer>Reporte generado automáticamente con pytest-playwright</footer>
</body>
</html>'''

    with open('reporte_po.html', 'w', encoding='utf-8') as f:
        f.write(html)