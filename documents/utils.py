from cryptography.fernet import Fernet
from django.conf import settings
import os
import re
import qrcode
import io
import base64

DEFAULT_FERNET_KEY = 'tz8nR7y2G0d3X01_SmV1ZrV2L9cMh7Q11b4Ro0lQq7o='


def get_fernet_key():
    key = os.environ.get('FERNET_KEY', DEFAULT_FERNET_KEY)
    if not key:
        raise ValueError("FERNET_KEY not set in environment")
    return Fernet(key)

def encrypt_file(file_path):
    f = get_fernet_key()
    with open(file_path, 'rb') as file:
        file_data = file.read()
    encrypted_data = f.encrypt(file_data)
    with open(file_path, 'wb') as file:
        file.write(encrypted_data)

def decrypt_file(file_path):
    f = get_fernet_key()
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
    """
    Generates a QR code for the given URL and returns it as a base64
    string that can be embedded directly in an <img> tag.
    """
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