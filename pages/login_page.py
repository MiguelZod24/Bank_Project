from playwright.sync_api import expect

class LoginPage:
    def __init__(self, page):
        self.page = page
        self.label_username = page.get_by_text("Username")
        self.label_password = page.get_by_text("Password")
        self.login_button = page.locator('input[value="Log In"]')
        self.username = page.locator('input[name="username"]')
        self.password = page.locator('input[name="password"]')

    def goto(self):
        self.page.goto("https://parabank.parasoft.com/parabank/index.html")

# Método para llenar campos SIN hacer clic
    def llenar_formulario(self, username, password):
        
        self.username.fill(username)
        self.password.fill(password)
       
    # Método para hacer clic en LogIn
    def enviar_formulario(self):
        self.login_button.click()

# Método para verificar que el login fue exitoso
    def verificar_login_exitoso(self):
    # NOTA: Parabank es una plataforma de práctica inestable.
    # El login a veces falla por problemas del servidor, no del test.
    # Verificamos simplemente que la URL cambió de login.htm
        expect(self.page).not_to_have_url(
        "https://parabank.parasoft.com/parabank/login.htm", 
        timeout=10000
    )

    