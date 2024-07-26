from flask import Blueprint, request, jsonify, current_app
from utils import get_database_connection, send_error_emai
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

smtp_bp = Blueprint('setup_smtp', __name__)

@smtp_bp.route('/setup_smtp', methods=['POST'])

def setup_smtp():
    connection = None
    cursor = None
    try:
        connection = get_database_connection()
        cursor = connection.cursor()

        # Retrieve token from headers
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({'error': 'Invalid token'}), 401

        actual_token = token.split('Bearer ')[1]

        # Retrieve user ID based on token
        get_user_id_query = f'SELECT user_id,first_name FROM {master_database}.Customers WHERE api_token = %s'
        cursor.execute(get_user_id_query, (actual_token,))
        user_id_result = cursor.fetchone()

        if not user_id_result:
            return jsonify({'error': 'User not found'}), 404

        user_id = user_id_result[0]
        first_name=user_id_result[1]
        database_name = f'{first_name}_{user_id}'

        # Retrieve SMTP details from request
        data = request.json
        print(data)
        port=data.get('port')
        smtp_server = data.get('smtp_server')
        email = data.get('email')
        password = data.get('password')

        # Upsert SMTP details for the user
        upsert_smtp_query = f"""
            INSERT INTO {database_name}.smtp_details_{user_id} (user_id,port, smtp_server, email, password)
            VALUES (%s, %s, %s, %s,%s)
            ON DUPLICATE KEY UPDATE smtp_server = VALUES(smtp_server), email = VALUES(email), password = VALUES(password),port=VALUES(port)
        """
        cursor.execute(upsert_smtp_query, (user_id, port, smtp_server, email, password))

        connection.commit()

        return jsonify({'message': 'SMTP server setup successful'}), 200

    except Exception as e:
        send_error_email('setup_smtp', str(e))
 
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
