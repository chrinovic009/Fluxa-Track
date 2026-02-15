import secrets
import string

# generation du mot de passe aleatoire
def generate_secure_password(length=8):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))
