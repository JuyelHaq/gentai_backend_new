from flask import Blueprint, request, jsonify, session, current_app
from utils import get_database_connection, send_email
from extensions import mail
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

verify_bp = Blueprint('verify', __name__)


@app.route('/verify_token', methods=['POST'])

def verify_token():
    try:
        data = request.json
        token = data.get('api_token')

        if not token:
            return jsonify({'error': 'Missing token'}), 400

        # Establish database connection
        connection = get_database_connection()
        cursor = connection.cursor()

        check_token_query = f'SELECT user_id, first_name, last_name FROM {master_database}.Customers WHERE api_token = %s'
        cursor.execute(check_token_query, (token,))
        user_info = cursor.fetchone()

        if not user_info:
            cursor.close()
            connection.close()
            return jsonify({'error': 'Invalid token'}), 401

        user_id, first_name, last_name = user_info
        username = f"{first_name} {last_name}"
        
        database_name = f'{first_name}_{user_id}'

        
        session['user_id'] = user_id

        cursor.close()
        connection.close()

        user_id = session.get('user_id')
        print(user_id)

        return jsonify({'status': 'success', 'user_id': user_id, 'first_name': first_name, 'last_name': last_name}), 200

    except Exception as e:
        print(f"Error: {e}")
        send_error_email('verify_token', str(e))

        return jsonify({'error': 'An error occurred while processing the request'}), 500
