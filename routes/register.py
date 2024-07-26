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
register_bp = Blueprint('register', __name__)

@register_bp.route('/register', methods=['POST'])
def register():
    print("Received a request to /register")

    data = request.json

    email = data.get('email')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    password = data.get('password')
    password_confirmation = data.get('password_confirmation')
    shopify=data.get('integration')

    # Check if required fields are present
    if not email or not first_name or not last_name or not password or not password_confirmation:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        # Establish database connection
        connection = get_database_connection()
        cursor = connection.cursor()

        # Check if the password and confirmation match
        if password != password_confirmation:
            return jsonify({'error': 'Password and confirmation do not match'}), 400

        # Check if the email is already registered
        

        # Check if the email is already registered
        check_email_query = f'SELECT user_id FROM {master_database}.Customers WHERE email = %s'
        cursor.execute(check_email_query, (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            return jsonify({'error': 'Email is already registered'}), 400

        # Hash the password before storing it
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        integration_value = json.dumps(shopify) if shopify is not None else None
        print(integration_value)


        # Insert the new user into the users table
        user_token = secrets.token_hex(16)
        insert_user_query = f'''
        INSERT INTO {master_database}.Customers (email, first_name, last_name, password,user_token,integration)
        VALUES (%s, %s, %s, %s,%s,%s)
        '''
        cursor.execute(insert_user_query, (email, first_name, last_name, hashed_password,user_token,integration_value))
        connection.commit()

        # Generate a unique api_token for the new user
        api_token = secrets.token_hex(16)

        # Update the user with the generated api_token
        update_token_query = f'UPDATE {master_database}.Customers SET api_token = %s WHERE email = %s'
        cursor.execute(update_token_query, (api_token, email))
        connection.commit()
        
        # Generate new api_token after 10 minutes
        
        # Create a user folder using the generated token
        user_id_query = f'SELECT user_id FROM {master_database}.Customers WHERE email = %s'
        cursor.execute(user_id_query, (email,))
        user_id = cursor.fetchone()[0]

        user_folder_name = f"{first_name}_{user_id}"
        database_name = f'{first_name}_{user_id}'

        
        create_database_query = f'CREATE DATABASE {database_name}'
        cursor.execute(create_database_query)
        use_database_query = f'USE {database_name}'
        cursor.execute(use_database_query)
        tables_creation_queries = [
    f'''
CREATE TABLE ChatLogs_{user_id} (
   user_id int DEFAULT NULL,
   question_id int NOT NULL AUTO_INCREMENT,
   question text,
   answer text,
   DateTimeColumn datetime DEFAULT NULL,
   PRIMARY KEY (question_id)) 
''',
   f'''CREATE TABLE Directory_{user_id} (
   directory_id int NOT NULL AUTO_INCREMENT,
   user_id int DEFAULT NULL,
   directory_name varchar(255) NOT NULL,
   PRIMARY KEY (directory_id),
   KEY user_id (user_id),
   FOREIGN KEY (user_id) REFERENCES {master_database}.Customers (user_id)
 ) ''',
    f''' CREATE TABLE FileLogs_{user_id} (
   upload_id int NOT NULL AUTO_INCREMENT,
   user_id int DEFAULT NULL,
   file_name varchar(255) NOT NULL,
   upload_date timestamp NULL DEFAULT CURRENT_TIMESTAMP,
   CreatedDateTimeColumn datetime DEFAULT CURRENT_TIMESTAMP,
   PRIMARY KEY (upload_id),
   UNIQUE KEY unique_file_name (file_name)
 ) ''',
 
 f''' CREATE TABLE PDF_setting_{user_id} (
   pdf_id int NOT NULL AUTO_INCREMENT,
   user_id int DEFAULT NULL,
   pdf1 blob,
   pdf2 blob,
   pdf3 blob,
   description1 text,
   description2 text,
   description3 text,
   PRIMARY KEY (pdf_id),
   UNIQUE KEY user_id (user_id),
   FOREIGN KEY (user_id) REFERENCES {master_database}.Customers (user_id)
 ) '''
   ,
   f'''CREATE TABLE PDF_settings_{user_id} (
   pdf_id int NOT NULL AUTO_INCREMENT,
   user_id int DEFAULT NULL,
   pdf_file1 text,
   pdf_file2 text,
   pdf_file3 text,
   title1 text,
   title2 text,
   title3 text,
   description1 text,
   description2 text,
   description3 text,
   PRIMARY KEY (pdf_id),
   UNIQUE KEY user_id (user_id)
 ) ''',
 
   f'''CREATE TABLE QuestionData_{user_id} (
   ID int NOT NULL AUTO_INCREMENT,
   PromptValue varchar(255) DEFAULT NULL,
   PromtId varchar(10) DEFAULT NULL,
   PromtQuery varchar(255) DEFAULT NULL,
   Score float DEFAULT NULL,
   SubmenuId varchar(10) DEFAULT NULL,
   Type varchar(50) DEFAULT NULL,
   user_id int DEFAULT NULL,
   unique_id varchar(30) DEFAULT NULL,
   CreationTime timestamp NULL DEFAULT CURRENT_TIMESTAMP,
   ModificationTime timestamp NULL DEFAULT CURRENT_TIMESTAMP,
   PRIMARY KEY (ID),
   UNIQUE KEY unique_id (unique_id)
 ) ''',
 f'''CREATE TABLE UserThemes_{user_id} (
   theme_id int NOT NULL AUTO_INCREMENT,
   user_id int DEFAULT NULL,
   theme_color varchar(50) DEFAULT 'light',
   created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
   updated_at timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
   PRIMARY KEY (theme_id),
   UNIQUE KEY user_id (user_id)
 ) ''',
 f'''CREATE TABLE WebURLlog_{user_id} (
   url_id int NOT NULL AUTO_INCREMENT,
   user_id int DEFAULT NULL,
   url varchar(255) NOT NULL,
   log_date timestamp NULL DEFAULT CURRENT_TIMESTAMP,
   PRIMARY KEY (url_id),
   UNIQUE KEY unique_url (url),
   KEY user_id (user_id),
   FOREIGN KEY (user_id) REFERENCES {master_database}.Customers (user_id) 
 ) '''
    ,
    f'''CREATE TABLE chatbot_name_{user_id} (
   chatbot_id int NOT NULL AUTO_INCREMENT,
   chatbot_name text,
   user_id int DEFAULT NULL,
   PRIMARY KEY (chatbot_id),
   UNIQUE KEY user_id (user_id)
 ) ''',
    f'''CREATE TABLE chats_customer_{user_id} (
   customer_id int NOT NULL AUTO_INCREMENT,
   customer_username varchar(255) DEFAULT NULL,
   customer_email varchar(255) DEFAULT NULL,
   customer_phone_no varchar(20) DEFAULT NULL,
   user_id varchar(255) DEFAULT NULL,
   created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
   PRIMARY KEY (customer_id)
 ) '''
,
 f'''CREATE TABLE cookies_{user_id} (
   id int NOT NULL AUTO_INCREMENT,
   user_id int DEFAULT NULL,
   cookies_data text,
   created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
   PRIMARY KEY (id),
   KEY user_id (user_id),
   FOREIGN KEY (user_id) REFERENCES {master_database}.Customers (user_id)
 ) ''',
 f'''CREATE TABLE delete_reports_{user_id} (
   file_id int NOT NULL AUTO_INCREMENT,
   user_id int DEFAULT NULL,
   uploaded_date datetime DEFAULT NULL,
   uploaded varchar(3) DEFAULT NULL,
   type varchar(50) DEFAULT NULL,
   trained_date datetime DEFAULT NULL,
   trained varchar(3) DEFAULT NULL,
   submenuname varchar(255) DEFAULT NULL,
   submenu_id varchar(3) DEFAULT NULL,
   status varchar(50) DEFAULT NULL,
   file_name varchar(255) NOT NULL,
   extracted_prompt varchar(3) DEFAULT NULL,
   extract_prompt_date datetime DEFAULT NULL,
   deleted_date datetime DEFAULT NULL,
   deleted varchar(3) DEFAULT NULL,
   PRIMARY KEY (file_id)
 ) ''',
    f'''CREATE TABLE documents_{user_id} (
   id int NOT NULL AUTO_INCREMENT,
   pdf_id int DEFAULT NULL,
   title varchar(255) DEFAULT NULL,
   description text,
   file_name varchar(255) DEFAULT NULL,
   user_id int DEFAULT NULL,
   PRIMARY KEY (id),
   UNIQUE KEY pdf_id (pdf_id,user_id)
 ) ''',
    f'''CREATE TABLE events_data_{user_id} (
   id int NOT NULL AUTO_INCREMENT,
   image_id int DEFAULT NULL,
   title varchar(255) DEFAULT NULL,
   description text,
   file_name varchar(255) DEFAULT NULL,
   url varchar(255) DEFAULT NULL,
   user_id int DEFAULT NULL,
   PRIMARY KEY (id),
   UNIQUE KEY image_id (image_id,user_id)
 ) ''',
    f'''CREATE TABLE header_text_{user_id} (
   header_text_id int NOT NULL AUTO_INCREMENT,
   header_text1 text,
   header_text2 text,
   user_id int DEFAULT NULL,
   PRIMARY KEY (header_text_id),
   UNIQUE KEY user_id (user_id)
 ) ''',
   f'''CREATE TABLE introductions_{user_id} (
   introduction_id int NOT NULL AUTO_INCREMENT,
   introduction text,
   descriptions text,
   user_id int DEFAULT NULL,
   PRIMARY KEY (introduction_id),
   UNIQUE KEY user_id (user_id)
 ) ''',
 f''' CREATE TABLE qna_{user_id} (
   qna_id int NOT NULL AUTO_INCREMENT,
   user_id int DEFAULT NULL,
   question_1 text,
   question_2 text,
   question_3 text,
   answer_1 text,
   answer_2 text,
   answer_3 text,
   PRIMARY KEY (qna_id),
   KEY user_id (user_id),
   FOREIGN KEY (user_id) REFERENCES {master_database}.Customers (user_id) 
 ) '''
    ,
    f'''CREATE TABLE reports_{user_id} (
   file_id int NOT NULL AUTO_INCREMENT,
   file_name varchar(255) NOT NULL,
   type varchar(50) DEFAULT NULL,
   uploaded_date datetime DEFAULT NULL,
   deleted_date datetime DEFAULT NULL,
   trained_date datetime DEFAULT NULL,
   extract_prompt_date datetime DEFAULT NULL,
   trained varchar(3) DEFAULT NULL,
   extracted_prompt varchar(3) DEFAULT NULL,
   status varchar(50) DEFAULT NULL,
   user_id int DEFAULT NULL,
   submenu_id varchar(3) DEFAULT NULL,
   deleted varchar(3) DEFAULT NULL,
   uploaded varchar(3) DEFAULT NULL,
   submenuname varchar(255) DEFAULT NULL,
   PRIMARY KEY (file_id),
   UNIQUE KEY unique_user (file_name,user_id,submenu_id)
 ) '''
,
 f'''CREATE TABLE setting_urls_{user_id} (
   url_id int NOT NULL AUTO_INCREMENT,
   user_id int DEFAULT NULL,
   url1 text,
   url2 text,
   url3 text,
   description1 text,
   description2 text,
   description3 text,
   Title1 text,
   Title2 text,
   Title3 text,
   PRIMARY KEY (url_id),
   UNIQUE KEY unique_user_id (user_id),
   FOREIGN KEY (user_id) REFERENCES {master_database}.Customers (user_id)) '''

    ,
   f'''CREATE TABLE smtp_details_{user_id} (
   smtp_id int NOT NULL AUTO_INCREMENT,
   user_id varchar(50) DEFAULT NULL,
   smtp_server varchar(255) DEFAULT NULL,
   email varchar(255) DEFAULT NULL,
   password varchar(255) DEFAULT NULL,
   port varchar(255) DEFAULT NULL,
   PRIMARY KEY (smtp_id),
   UNIQUE KEY user_id (user_id)
 ) ''',
    f'''CREATE TABLE tokens_{user_id} (
   token_id int NOT NULL AUTO_INCREMENT,
   token varchar(255) NOT NULL,
   user_id int NOT NULL,
   PRIMARY KEY (token_id),
   UNIQUE KEY user_id (user_id)
 ) ''',
    
 f'''CREATE TABLE url_reports_{user_id} (
   url_id int NOT NULL AUTO_INCREMENT,
   url varchar(255) NOT NULL,
   type varchar(50) DEFAULT NULL,
   uploaded_date datetime DEFAULT NULL,
   deleted_date datetime DEFAULT NULL,
   trained_date datetime DEFAULT NULL,
   extract_prompt_date datetime DEFAULT NULL,
   trained varchar(3) DEFAULT NULL,
   extracted_prompt varchar(3) DEFAULT NULL,
   status varchar(50) DEFAULT NULL,
   user_id int DEFAULT NULL,
   submenu_id varchar(3) DEFAULT NULL,
   uploaded varchar(3) DEFAULT NULL,
   deleted varchar(3) DEFAULT NULL,
   submenuname varchar(255) DEFAULT NULL,
   PRIMARY KEY (url_id),
   UNIQUE KEY (url,user_id,submenu_id)
 ) '''

 
]
        for query in tables_creation_queries:
            cursor.execute(query)

        connection.commit()


        user_folder_path = os.path.join(BASE_UPLOAD_FOLDER, user_folder_name)
        subprocess.run(['sudo', 'useradd', '-m', '-d', user_folder_path, user_folder_name])
        subprocess.run(['sudo', 'chpasswd'], input=f"{user_folder_name}:{user_folder_name}", text=True)

        if not os.path.exists(user_folder_path):
            os.makedirs(user_folder_path)
        upload_folder_path = os.path.join(user_folder_path, UPLOAD_FOLDER)
        if not os.path.exists(upload_folder_path):
            os.makedirs(upload_folder_path)

        # Insert directory information into the database
        insert_directory_query = f'''
        INSERT INTO {database_name}.Directory_{user_id} (user_id, directory_name)
        VALUES (%s, %s)
        '''
        cursor.execute(insert_directory_query, (user_id, user_folder_name))
        connection.commit()
        user_token_query = f'SELECT user_token FROM {master_database}.Customers WHERE user_id = %s'
        cursor.execute(user_token_query, (user_id,))
        usertoken = cursor.fetchone()[0]


        token_date = f'SELECT registration_date FROM {master_database}.Customers WHERE user_id = %s'
        cursor.execute(token_date, (user_id,))
        user_date = cursor.fetchone()

        if not user_date:
            return jsonify({'error': 'User not found'}), 404

        registration_date = user_date[0]
        print(registration_date)
       
        registration_date = registration_date.date()
        current_date = datetime.now().date()
        days_registered = (current_date - registration_date).days
        if days_registered >= 7:
    # Generate a new user token
           new_user_token = secrets.token_hex(16)

    # Update the user token in the database
           update_token_query = f'UPDATE {master_database}.Customers SET user_token = %s WHERE user_id = %s'
           cursor.execute(update_token_query, (new_user_token, user_id))
           connection.commit()


        # Send registration email
        send_email(email,api_token,usertoken)

        # Close cursor and connection
        cursor.close()
        connection.close()

        return jsonify({'api_token': api_token, 'message': 'Registration and login successful'}), 200

    except Exception as e:
        print(f"Error: {e}")
       # send_error_email('register', str(e)) 
        return jsonify({'error': 'An error occurred while processing the request'}), 500

def generate_confirmation_email_body(vtoken,ctoken):
    body = f"""\
Dear Sir/Madam,

A warm welcome to you from our entire family at InstaMart.ai!

You have two important pieces of information in this email:
   1. To get started with ChatBot, please enter the following code on the confirmation screen:
        Verification Token: {vtoken}

   2. Please save this token safely. You will require it as your personal key for your AI ChatBot:
        Client Token: {ctoken}

Please save this token safely. IMPORTANT!

If you didn’t sign up for an AI Chatbot at https://chatbot.instamart.ai, please check further. 

Have a wonderful day ahead! Don’t hesitate to reach out to us for anything at apara@instamart.ai.

Regards,
AI Chatbot Team
At InstaMart.AI Inc.
"""
    return body

def send_email(recipient, verification_token, usertoken):
    verification_link = "https://gentai.instamart.ai/verify"
    code = "886798"  # Generate or retrieve the confirmation code dynamically
    
    subject = "Welcome! Thank you for signing up to AI Chatbot!"
    msg = Message(subject, recipients=[recipient])
    msg.body = generate_confirmation_email_body(verification_token,usertoken)

    mail.send(msg)

