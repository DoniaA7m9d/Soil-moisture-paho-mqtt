"""
Soil Moisture Monitoring System

MQTT-based system that monitors soil moisture sensor data,
generates daily/monthly/yearly reports with graphs, 
and sends alerts via Telegram.
"""

import paho.mqtt.client as mqtt
import ssl
import csv
import os
import logging
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BROKER_HOST = os.getenv("BROKER_HOST")
BROKER_PORT = int(os.getenv("BROKER_PORT", 8883))
USERNAME = os.getenv("MQTT_USERNAME")
PASSWORD = os.getenv("MQTT_PASSWORD")
TOPIC = os.getenv("MQTT_TOPIC")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ALERT_THRESHOLD = int(os.getenv("ALERT_THRESHOLD", 700))
CSV_FILE = 'soil_data.csv'

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('system.log'), logging.StreamHandler()]
)

last_day = datetime.now().day
last_month = datetime.now().month
last_year = datetime.now().year

def send_telegram_message(text):
    """Send text message via Telegram Bot API"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        logging.error(f"Telegram message error: {e}")

def send_telegram_document(file_path, caption=""):
    """Send document via Telegram Bot API"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
        with open(file_path, 'rb') as doc:
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
                         files={'document': doc}, timeout=30)
        logging.info(f"Sent document: {file_path}")
    except Exception as e:
        logging.error(f"Telegram document error: {e}")

def save_to_csv(payload):
    """Append sensor reading to CSV file"""
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['date', 'timestamp', 'value'])
        writer.writerow([payload['date'], payload['timestamp'], payload['value']])

def generate_report(period_type):
    """Generate PDF report with chart for specified period"""
    logging.info(f"Generating {period_type} report")
    # هنا حطي كود generate_report كامل من النسخة القديمة بتاعتك
    # المهم تبدلي أي print بـ logging.info

def on_connect(client, userdata, flags, reason_code, properties):
    """MQTT on_connect callback"""
    if reason_code == 0:
        logging.info("Connected to MQTT broker")
        client.subscribe(TOPIC)
        send_telegram_message("🟢 System Online")
    else:
        logging.error(f"Failed to connect: {reason_code}")

def on_message(client, userdata, msg):
    """MQTT on_message callback"""
    global last_day, last_month, last_year
    try:
        raw = msg.payload.decode().strip()
        value = int(raw) if raw.isdigit() else float(raw)
        
        payload = {
            'value': value,
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'date': datetime.now().strftime("%Y-%m-%d")
        }
        
        logging.info(f"Received: {value}")
        save_to_csv(payload)

        if value > ALERT_THRESHOLD:
            send_telegram_message(f"🚨 Soil Dry Alert!\nValue: {value}")

        # Check for report generation
        now = datetime.now()
        if now.day != last_day:
            generate_report("Daily")
            last_day = now.day
        if now.month != last_month:
            generate_report("Monthly")
            last_month = now.month
        if now.year != last_year:
            generate_report("Yearly")
            last_year = now.year

    except Exception as e:
        logging.error(f"Error processing message: {e}")

if __name__ == "__main__":
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS_CLIENT)
    client.username_pw_set(USERNAME, PASSWORD)
    
    logging.info("Starting MQTT Client...")
    client.connect(BROKER_HOST, BROKER_PORT, 60)
    client.loop_forever()
