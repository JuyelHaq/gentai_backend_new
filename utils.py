import mysql.connector
from flask import current_app
from flask_mail import Message
from extensions import mail

def get_database_connection():
    """Establish and return a database connection using configuration from Flask."""
    db_config = current_app.config['DB_CONFIG']
    return mysql.connector.connect(**db_config)

def send_email(subject, recipient, body):
    """Send an email notification."""
    message = Message(subject=subject, recipients=[recipient], body=body)
    mail.send(message)
