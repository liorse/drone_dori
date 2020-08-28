from cryptography.fernet import Fernet
new_encryption_key = Fernet.generate_key()
print(new_encryption_key)
