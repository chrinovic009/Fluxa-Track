import secrets
import os
from flask import send_from_directory, abort
from flask_login import login_required
import cloudinary
import cloudinary.uploader

def save_file(file, folder):
    """Sauvegarde un fichier avec un nom sécurisé et aléatoire"""
    ext = os.path.splitext(file.filename)[1].lower()  # ex: .pdf, .jpg
    filename = f"{secrets.token_hex(16)}{ext}"
    path = os.path.join(folder, filename)
    file.save(path)
    return filename

def save_file_to_cloudinary(file):
    result = cloudinary.uploader.upload(file)
    return result['secure_url']


