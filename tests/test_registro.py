import pytest
from playwright.sync_api import expect
from faker import Faker
from pages.register_page import RegisterPage
import allure

# Instancia de Faker para generar datos falsos en cada ejecución
fake = Faker()

@allure.feature("Registro de usuario")
@allure.story("Carga de pagina")
@allure.severity(allure.severity_level.CRITICAL)
def test_carga_pagina(page):
    """
    escenario: El usuario navega a la página de registro de ParaBank.
    esperado: La página carga correctamente mostrando el formulario y el botón Register.
    impacto: Si falla, ningún usuario puede acceder al formulario de registro.
    accion: Verificar que la URL y los elementos principales estén disponibles.
    """ 
    # Crear instancia de la página de registro
    register = RegisterPage(page)

    # Navegar 
    register.goto()

    # Verificar mensaje de error
    expect(page.get_by_text("Signing up is easy!")).to_be_visible()
    expect(page.get_by_text("If you have an account with us you can sign-up for free instant online access. You will have to provide some personal information.")).to_be_visible()
    expect(register.register_button).to_be_visible()


@allure.feature("Registro de usuario")
@allure.story("Registro exitoso")
@allure.severity(allure.severity_level.CRITICAL)
def test_registro(page):
    """
    escenario: El usuario completa todos los campos del formulario con datos válidos.
    esperado: El sistema crea la cuenta y muestra el mensaje de bienvenida.
    impacto: Si falla, los usuarios no pueden registrarse en la plataforma.
    accion: Verificar que el formulario de registro funciona correctamente.
    """

    # Crear instancia de la página de registro
    register = RegisterPage(page)

    # Navegar 
    register.goto()

    # Verificar que los campos están vacíos
    expect(register.first_name).to_have_value("")
    expect(register.last_name).to_have_value("")
    expect(register.address).to_have_value("")
    expect(register.city).to_have_value("")
    expect(register.state).to_have_value("")
    expect(register.zip_code).to_have_value("")
    expect(register.phone).to_have_value("")
    expect(register.ssn).to_have_value("")
    expect(register.username).to_have_value("")
    expect(register.password).to_have_value("") 

    # Generar datos aleatorios
    first_name = fake.first_name()
    last_name = fake.last_name()
    address = fake.street_address()
    city = fake.city()
    state = fake.state()
    zip_code = fake.zipcode()
    phone = fake.phone_number()
    ssn = fake.ssn()
    username = fake.user_name()
    password = fake.password()

    # Registrar
    register.llenar_formulario(first_name, last_name, address, city, state, zip_code, phone, ssn, username, password)

    # Verificar que los campos aceptaron los datos
    expect(register.first_name).to_have_value(first_name)
    expect(register.last_name).to_have_value(last_name) 
    expect(register.address).to_have_value(address)
    expect(register.city).to_have_value(city)
    expect(register.state).to_have_value(state)
    expect(register.zip_code).to_have_value(zip_code)
    expect(register.phone).to_have_value(phone)
    expect(register.ssn).to_have_value(ssn)
    expect(register.username).to_have_value(username)
    expect(register.password).to_have_value(password)
    expect(register.repeated_password).to_have_value(password)

    # Enviar formulario
    register.enviar_formulario()

    # Verificar que el registro fue exitoso
    register.verificar_registro_exitoso()

@allure.feature("Registro de usuario")
@allure.story("Campos vacios")
@allure.severity(allure.severity_level.CRITICAL)
def test_campos_vacios(page):
    """
    escenario: El usuario hace clic en Register sin completar ningún campo.
    esperado: El sistema muestra mensajes de error en todos los campos obligatorios.
    impacto: Si falla, el formulario podría permitir registros sin datos.
    accion: Verificar que las validaciones de campos obligatorios funcionan.
    """

    # Crear instancia de la página de registro
    register = RegisterPage(page)

    # Navegar 
    register.goto()

    # Enviar formulario sin llenar campos
    register.enviar_formulario()

    expect(page.get_by_text("First name is required.")).to_be_visible()
    expect(page.get_by_text("Last name is required.")).to_be_visible()
    expect(page.get_by_text("Address is required.")).to_be_visible()
    expect(page.get_by_text("City is required.")).to_be_visible()
    expect(page.get_by_text("State is required.")).to_be_visible()
    expect(page.get_by_text("Zip Code is required.")).to_be_visible()
    expect(page.get_by_text("Social Security Number is required.")).to_be_visible()
    expect(page.get_by_text("Username is required.")).to_be_visible()
    expect(page.get_by_text("Password is required.")).to_be_visible()
    expect(page.get_by_text("Password confirmation is required.")).to_be_visible()


@allure.feature("Registro de usuario")
@allure.story("Campo vacio")
@allure.severity(allure.severity_level.CRITICAL)
def test_campo_vacio(page):
    """
    escenario: El usuario completa todos los campos excepto First Name.
    esperado: El sistema muestra el mensaje de error solo para First Name.
    impacto: Si falla, el formulario podría aceptar registros con datos incompletos.
    accion: Verificar que cada campo obligatorio se valida individualmente.
    """

    # Crear instancia de la página de registro
    register = RegisterPage(page)

    # Navegar 
    register.goto()
    
    # Generar datos aleatorios
    last_name = fake.last_name()
    address = fake.street_address()
    city = fake.city()
    state = fake.state()
    zip_code = fake.zipcode()
    phone = fake.phone_number()
    ssn = fake.ssn()
    username = fake.user_name()
    password = fake.password()

    # Registrar
    register.llenar_formulario("",last_name, address, city, state, zip_code, phone, ssn, username, password)

    # Enviar formulario
    register.enviar_formulario()

    expect(page.get_by_text("First name is required.")).to_be_visible()


@allure.feature("Registro de usuario")
@allure.story("Passwords no coinciden")
@allure.severity(allure.severity_level.CRITICAL)
def test_passwords_no_coinciden(page):
    """
    escenario: El usuario ingresa contraseñas diferentes en Password y Confirm Password.
    esperado: El sistema muestra el mensaje Passwords did not match.
    impacto: Si falla, los usuarios podrían registrarse con contraseñas incorrectas.
    accion: Verificar que la validación de confirmación de contraseña funciona.
    """

    # Crear instancia de la página de registro
    register = RegisterPage(page)

    # Navegar 
    register.goto()

    # Generar datos aleatorios
    first_name = fake.first_name()
    last_name = fake.last_name()
    address = fake.street_address()
    city = fake.city()
    state = fake.state()
    zip_code = fake.zipcode()
    phone = fake.phone_number()
    ssn = fake.ssn()
    username = fake.user_name()
    password = fake.password()

    # Registrar
    register.llenar_formulario(first_name, last_name, address, city, state, zip_code, phone, ssn, username, password)

    # Sobreescribir confirm password con uno diferente
    register.repeated_password.fill("Password_Diferente123")
    
    # Enviar formulario
    register.enviar_formulario()

    # Verificar mensaje de error
    expect(page.get_by_text("Passwords did not match.")).to_be_visible()

@allure.feature("Registro de usuario")
@allure.story("Username existente")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.xfail(reason="Parabank es inestable — el servidor no siempre devuelve el mensaje de error")
def test_username_existente(page):
    """
    escenario: El usuario intenta registrarse con un username que ya existe en el sistema.
    esperado: El sistema muestra el mensaje This username already exists.
    impacto: Si falla, podrían crearse cuentas duplicadas en la plataforma.
    accion: Verificar que el sistema detecta usernames duplicados correctamente.
    """

    # Crear instancia de la página de registro
    register = RegisterPage(page)

    # Navegar 
    register.goto()

    # Generar datos aleatorios
    first_name = fake.first_name()
    last_name = fake.last_name()
    address = fake.street_address()
    city = fake.city()
    state = fake.state()
    zip_code = fake.zipcode()
    phone = fake.phone_number()
    ssn = fake.ssn()
    username = fake.user_name()
    password = fake.password()

    # Registrar
    register.llenar_formulario(first_name, last_name, address, city, state, zip_code, phone, ssn, username, password)
    
    # Sobreescribir username con uno que ya existe
    register.username.fill("Poronga")

     # Enviar formulario
    register.enviar_formulario()

    # Verificar mensaje de error
    expect(page.get_by_text("This username already exists.")).to_be_visible()

@allure.feature("Registro de usuario")
@allure.story("Letras en phone")
@allure.severity(allure.severity_level.CRITICAL)
def test_letras_en_phone(page):
    """
    escenario: El usuario ingresa letras en el campo Phone Number.
    esperado: El sistema acepta el registro ya que el campo no es obligatorio ni valida formato.
    impacto: BUG detectado — el campo Phone no valida que el valor sea numérico.
    accion: Agregar validación de formato numérico en el campo Phone Number.
    """

    # Crear instancia de la página de registro
    register = RegisterPage(page)

    # Navegar 
    register.goto()

    # Generar datos aleatorios
    first_name = fake.first_name()
    last_name = fake.last_name()
    address = fake.street_address()
    city = fake.city()
    state = fake.state()
    zip_code = fake.zipcode()
    phone = fake.phone_number()
    ssn = fake.ssn()
    username = fake.user_name()
    password = fake.password()

    # Registrar
    register.llenar_formulario(first_name, last_name, address, city, state, zip_code, phone, ssn, username, password)
    
    # Sobreescribir el Phone con letras
    register.phone.fill("miguel")

    # Enviar formulario
    register.enviar_formulario()

    # BUG: La aplicación no valida letras en Phone
    # Comportamiento esperado: mostrar mensaje de validación

    # Verificar que el registro fue exitoso
    register.verificar_registro_exitoso()

@allure.feature("Registro de usuario")
@allure.story("Letras en zip code")
@allure.severity(allure.severity_level.CRITICAL)
def test_letras_en_zipcode(page):
    """
    escenario: El usuario ingresa letras en el campo Zip Code.
    esperado: El sistema debería mostrar un error de validación de formato.
    impacto: BUG detectado — el campo Zip Code no valida que el valor sea numérico.
    accion: Agregar validación de formato numérico en el campo Zip Code.
    """
     
    # Crear instancia de la página de registro
    register = RegisterPage(page)

    # Navegar 
    register.goto()

    # Generar datos aleatorios
    first_name = fake.first_name()
    last_name = fake.last_name()
    address = fake.street_address()
    city = fake.city()
    state = fake.state()
    zip_code = fake.zipcode()
    phone = fake.phone_number()
    ssn = fake.ssn()
    username = fake.user_name()
    password = fake.password()

    # Registrar
    register.llenar_formulario(first_name, last_name, address, city, state, zip_code, phone, ssn, username, password)
    
    # Sobreescribir el Zip Code con letras
    register.zip_code.fill("miguelll")

    # Enviar formulario
    register.enviar_formulario()

    # Verificar mensaje de error
    expect(page.get_by_text("Your account was created successfully. You are now logged in.")).to_be_visible()

    # BUG: La aplicación no valida letras en Zip Code
    # A veces lanza error interno, otras veces acepta el registro

    # Comportamiento esperado: mostrar mensaje de validación
    register.verificar_registro_exitoso()
