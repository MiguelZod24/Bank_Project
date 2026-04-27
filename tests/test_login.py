from playwright.sync_api import expect
from pages.login_page import LoginPage 


def test_carga_pagina(page):
    """
    escenario: El usuario navega a la página de LogIn de ParaBank.
    esperado: La página carga correctamente mostrando los campos y el botón LogIn.
    impacto: Si falla, ningún usuario puede acceder a su cuenta.
    accion: Verificar que la URL y los elementos principales estén disponibles.
    """ 
    # Crear instancia de la página de logIn
    login = LoginPage(page)

    # Navegar 
    login.goto()

    # Verificar mensajes indicativos
    expect(page.get_by_text("Customer Login")).to_be_visible()
    expect(page.get_by_text("Username")).to_be_visible()
    expect(page.get_by_text("Password")).to_be_visible()
    expect(page.locator('input[value="Log In"]')).to_be_visible()


def test_login(page):
    """
    escenario: El usuario completa todos los campos del login con datos válidos.
    esperado: El sistema ingresa a la cuenta y muestra el mensaje de bienvenida.
    impacto: Si falla, los usuarios no pueden ingresar en la plataforma.
    accion: Verificar que el formulario de login funciona correctamente.
    conocido: Parabank es inestable — el test puede fallar por problemas del servidor.
    """

    # Crear instancia de la página de registro
    login = LoginPage(page)

    # Navegar 
    login.goto()

    # Verificar que los campos están vacíos
    expect(login.username).to_have_value("")
    expect(login.password).to_have_value("") 

    # Ingresar datos:
    login.username.fill("Poronga")
    login.password.fill("123456")

    # Verificar que los campos aceptaron los datos
    expect(login.username).to_have_value("Poronga")
    expect(login.password).to_have_value("123456")
    

    # Enviar formulario
    login.enviar_formulario()

    # DEBUG — ver qué hay en la página después del login
    print(f"\nURL: {page.url}")
    print(f"Contenido: {page.content()[:500]}")  # primeros 500 caracteres del HTML

    # Verificar que el registro fue exitoso
    login.verificar_login_exitoso()