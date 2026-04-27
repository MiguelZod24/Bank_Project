from playwright.sync_api import expect

class RegisterPage:
    def __init__(self, page):
        self.page = page
        # Locators del formulario
        self.first_name = page.locator("#customer\\.firstName")
        self.last_name = page.locator("#customer\\.lastName")
        self.address = page.locator("#customer\\.address\\.street")
        self.city = page.locator("#customer\\.address\\.city")
        self.state = page.locator("#customer\\.address\\.state")
        self.zip_code = page.locator("#customer\\.address\\.zipCode")
        self.phone = page.locator("#customer\\.phoneNumber")
        self.ssn = page.locator("#customer\\.ssn")
        self.username = page.locator("#customer\\.username")
        self.password = page.locator("#customer\\.password")
        self.repeated_password = page.locator("#repeatedPassword")
        self.register_button = page.locator("input[value='Register']")

    # Método para navegar a la página de registro
    def goto(self):
        self.page.goto("https://parabank.parasoft.com/parabank/register.htm")

    # Método para llenar el formulario SIN hacer clic
    def llenar_formulario(self, first_name, last_name, address, city, state, zip_code, phone, ssn, username, password):
        self.first_name.fill(first_name)
        self.last_name.fill(last_name)
        self.address.fill(address)
        self.city.fill(city)
        self.state.fill(state)
        self.zip_code.fill(zip_code)
        self.phone.fill(phone)
        self.ssn.fill(ssn)
        self.username.fill(username)
        self.password.fill(password)
        self.repeated_password.fill(password)

    # Método para hacer clic en Register
    def enviar_formulario(self):
        self.register_button.click()

    # Método para verificar que el registro fue exitoso
    def verificar_registro_exitoso(self):
        expect(self.page.get_by_text("Your account was created successfully. You are now logged in.")).to_be_visible()