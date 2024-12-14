import os
from dotenv import load_dotenv
load_dotenv()

from instagrapi import Client
from telebot import TeleBot, types
from flask import Flask, request
import requests

# Instagram login details
INSTAGRAM_USERNAME = os.getenv('INSTA_USER')
INSTAGRAM_PASSWORD = os.getenv('INSTA_PASS')

# Initialize Instagram Client
ig_client = Client()

# Flask app for handling webhook
app = Flask(__name__)

# Function to handle Instagram login with session management
def instagram_login():
    session_path = "ig_session.json"  # File to store session data
    if os.path.exists(session_path):
        try:
            ig_client.load_settings(session_path)  # Load existing session
            ig_client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
            print("Logged into Instagram using saved session!")
            return
        except Exception as e:
            print(f"Failed to load saved session: {e}")

    # If no valid session, perform a fresh login
    try:
        ig_client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        ig_client.dump_settings(session_path)  # Save the session
        print("Logged into Instagram successfully and session saved!")
    except Exception as e:
        print(f"Login failed. Handling challenge: {e}")
        try:
            challenge_code = ig_client.challenge_resolve()
            print(f"Challenge resolved. Code sent to: {challenge_code}")
        except Exception as challenge_error:
            print(f"Failed to resolve challenge: {challenge_error}")

# Initialize Telegram bot
bot_token = os.getenv('TELEGRAM_TOKEN')
bot = TeleBot(bot_token)

@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    if request.headers.get('content-type') == 'application/json':
        json_data = request.get_json()
        update = types.Update.de_json(json_data)  # Parse the Telegram update
        bot.process_new_updates([update])
        return '', 200
    return '', 403

@app.route('/', methods=['GET'])
def bot_status():
    return "BOT IS RUNNING", 200

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hi! Send me an image with a caption, and I'll post it on Instagram.")

@bot.message_handler(content_types=['photo'])
def handle_image(message: types.Message):
    try:
        # Get the photo and save it locally
        file_info = bot.get_file(message.photo[-1].file_id)
        file_path = f"{message.from_user.id}_{message.date}.jpg"
        
        # Download the photo
        file = requests.get(f"https://api.telegram.org/file/bot{bot_token}/{file_info.file_path}")
        with open(file_path, 'wb') as f:
            f.write(file.content)

        # Upload to Instagram
        instagram_upload(file_path, message.caption or "No caption provided.")

        # Remove the saved file
        os.remove(file_path)

        bot.reply_to(message, "Your photo has been posted to Instagram!")
    except Exception as e:
        bot.reply_to(message, f"Failed to post photo: {e}")

def instagram_upload(photo_path, caption):
    try:
        ig_client.photo_upload(photo_path, caption)
        print("Photo uploaded successfully!")
    except Exception as e:
        print(f"Failed to upload photo to Instagram: {e}")

if __name__ == "__main__":
    # Login to Instagram
    instagram_login()
    
    # Set webhook URL for Telegram bot
    webhook_url = "https://sscinstabot.onrender.com/webhook"
    bot.remove_webhook()  # Remove existing webhook, if any
    bot.set_webhook(url=webhook_url)

    # Run Flask app
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))