
import os
import shutil
import base64
import requests
from bs4 import BeautifulSoup
import pdfkit
from urllib.parse import urljoin, urlparse
import re
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS, Chroma
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI
from langchain.callbacks import get_openai_callback
import openai
import fitz  # PyMuPDF
import argparse
import sys
from flask_mail import Mail, Message
import stripe
import uuid
from flask_jwt_extended import jwt_required, get_jwt_identity, JWTManager
import secrets
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
import json
from langdetect import detect
from googletrans import Translator
import weasyprint
from zipfile import ZipFile
from PIL import Image
import pytesseract

from flask import Blueprint, request, jsonify
from utils import get_database_connection, generate_password_hash, secrets, send_email, send_error_email
login_bp = Blueprint('login', __name__)

@login_bp.route('/login', methods=['POST'])
def login():
    data = request.json

    email = data.get('email')
    password = data.get('password')

    # Check if required fields are present
    if not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        # Initialize cursor after establishing connection
        connection = get_database_connection()
        cursor = connection.cursor()

        # Check if the user with the given email exists
        check_email_query = f'SELECT user_id, password, first_name,verified FROM {master_database}.Customers WHERE email = %s'
        cursor.execute(check_email_query, (email,))
        user = cursor.fetchone()
        print(user[3])

        if not user:
            cursor.close()
            return jsonify({'error': 'Invalid email or password'}), 401

        user_id, hashed_password, first_name,verified = user
        database_name = f'{first_name}_{user_id}'

        

        # Check if the password is correct
        if not check_password_hash(hashed_password, password):
            cursor.close()
            return jsonify({'error': 'Invalid email or password'}), 401
        if not user[3]:  # Check if the email is verified
            return jsonify({'error': 'Email not verified'}), 403
        # Generate a unique api_token for the user
        api_token = secrets.token_hex(16)

        # Update the user with the generated api_token
        update_token_query = f'UPDATE {master_database}.Customers SET api_token = %s WHERE email = %s'
        cursor.execute(update_token_query, (api_token, email))
        connection.commit()

        # Retrieve the user's directory name from the Directory table
        get_directory_query = f'SELECT directory_name FROM {database_name}.Directory_{user_id} WHERE user_id = %s'
        cursor.execute(get_directory_query, (user_id,))
        directory_info = cursor.fetchone()
        user_token_query = f'SELECT user_token FROM {master_database}.Customers WHERE user_id = %s'
        cursor.execute(user_token_query, (user_id,))
        user_token = cursor.fetchone()

        if directory_info:
            directory_name = directory_info[0]
            user_directory_path = os.path.join(BASE_UPLOAD_FOLDER, directory_name)

            context_file_path = os.path.join(user_directory_path, CONTEXT_FILE)
            if os.path.exists(context_file_path):
                with open(context_file_path) as file:
                    context = json.load(file)

            # Load user-specific sources from the sources file
            sources_file_path = os.path.join(user_directory_path, SOURCES_FILE)
            if os.path.exists(sources_file_path):
                with open(sources_file_path) as sources_file:
                    context["sources"] = list(map(lambda e: e.strip(), sources_file.readlines()))
                    context["collection_exists"] = True


            cursor.close()
            connection.close()

            return jsonify({'api_token': api_token,'user_token':user_token, 'message': 'Login successful', 'redirect': False}), 200
        else:
            cursor.close()
            connection.close()
            return jsonify({'error': 'User directory not found'}), 404

    except Exception as e:
        #send_error_email('login', str(e))
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred while processing the request'}), 500
