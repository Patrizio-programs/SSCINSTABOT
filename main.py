import os
from instagrapi import Client
from telebot import TeleBot
from telebot.types import Message
import requests

# Instagram login details
INSTAGRAM_USERNAME = 'simplyspanish@pgmja.com'
INSTAGRAM_PASSWORD = 'elpadrino111'

# Initialize Instagram Client
ig_client = Client()

def instagram_login():
    try:
        ig_client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        print("Logged into Instagram successfully!")
    except Exception as e:
        print(f"Failed to login to Instagram: {e}")

def instagram_upload(photo_path, caption):
    try:
        ig_client.photo_upload(photo_path, caption)
        print("Photo uploaded successfully!")
    except Exception as e:
        print(f"Failed to upload photo to Instagram: {e}")

# Initialize Telegram bot
bot_token = "7077730350:AAHKVELxGFnvHMPp_zT7s_kIPcTqQ7Xru5I"
bot = TeleBot(bot_token)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hi! Send me an image with a caption, and I'll post it on Instagram.")

@bot.message_handler(content_types=['photo'])
def handle_image(message: Message):
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

if __name__ == "__main__":
    instagram_login()
    bot.polling()
