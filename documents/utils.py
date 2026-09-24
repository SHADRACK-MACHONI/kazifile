from cryptography.fernet import Fernet
from django.conf import settings
import os
import re
import qrcode
import io
import base64

from django.conf import settings
from cryptography.fernet import Fernet

def get_master_key():
    key = settings.FERNET_KEY
    if not key:
        raise ValueError("FERNET_KEY not set in environment")
    return Fernet(key)


def generate_file_key():
    """Generates a brand new random key, unique to a single file."""
    return Fernet.generate_key()


def encrypt_file_key(file_key):
    """Encrypts a file's unique key using the master key, for safe storage in the database."""
    master = get_master_key()
    encrypted = master.encrypt(file_key)
    return encrypted.decode()


def decrypt_file_key(encrypted_file_key):
    """Decrypts a file's unique key using the master key."""
    master = get_master_key()
    file_key = master.decrypt(encrypted_file_key.encode())
    return file_key


def encrypt_file(file_path, file_key):
    """Encrypts a file's contents using its own unique key (not the master key)."""
    f = Fernet(file_key)
    with open(file_path, 'rb') as file:
        file_data = file.read()
    encrypted_data = f.encrypt(file_data)
    with open(file_path, 'wb') as file:
        file.write(encrypted_data)


def decrypt_file(file_path, file_key):
    """Decrypts a file's contents using its own unique key."""
    f = Fernet(file_key)
    with open(file_path, 'rb') as file:
        encrypted_data = file.read()
    decrypted_data = f.decrypt(encrypted_data)
    return decrypted_data


CATEGORY_KEYWORDS = {
    'id': ['id', 'national id', 'passport', 'identity', 'birth certificate'],
    'academic': ['transcript', 'academic', 'result slip', 'kcse', 'kcpe', 'degree'],
    'certificate': ['certificate', 'certification', 'award', 'cert'],
    'cv': ['cv', 'resume', 'curriculum vitae'],
    'reference': ['reference', 'recommendation', 'referee'],
}

def guess_category(filename):
    name = filename.lower()
    name = re.sub(r'[_\-\.]', ' ', name)
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in name:
                return category
    return 'other'


def generate_qr_code_base64(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=8,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"
import hashlib

def compute_file_hash(file_obj):
    """Computes a SHA-256 hash of a file's raw content, before encryption."""
    sha256 = hashlib.sha256()
    for chunk in file_obj.chunks():
        sha256.update(chunk)
    file_obj.seek(0)  # reset pointer so the file can still be saved/encrypted afterward
    return sha256.hexdigest()