from dotenv import load_dotenv
import os

load_dotenv()

class CredenciaisVonix:
    def __init__(self):
        self.usuario=os.getenv("LOGIN_VONIX")
        self.senha=os.getenv("SENHA_VONIX")


        