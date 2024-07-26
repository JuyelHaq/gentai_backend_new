
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
loginexpired_bp = Blueprint('login_expired', __name__)

@loginexpired_bp.route('/login_expired', methods=['POST'])
def login_expired():
    try:
        connection = get_database_connection()
        cursor = connection.cursor()
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            actual_token = token.split('Bearer ')[1]
            print("token"+actual_token)
            token_user = request.json.get('token')
            print("token="+token_user)
            check_token_query = f'SELECT user_token FROM {master_database}.Customers WHERE user_token = %s'
            cursor.execute(check_token_query, (token_user,))
        
            token_exists = cursor.fetchone()
            print(token_exists)
            token_exists=token_exists[0]

            if token_exists:
                # Token exists, return success message along with the token
                return jsonify({'message': 'Token exists', 'api_token': token_exists}), 200
            else:
                # Token does not exist
                return jsonify({'error': 'Invalid token'}), 401
        else:
            return jsonify({'error': 'Token missing or invalid'}), 401
    except Exception as e:
        send_error_email('login_expired', str(e))
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()
