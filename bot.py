import os
import traceback
import tempfile
import datetime
import base64
import time
import pytz
from datetime import timedelta
from pyrogram import Client, filters
from pyrogram.types import Message
from dotenv import load_dotenv
from flask import Flask

# Load environment variables from .env file
load_dotenv()

# Create a new Pyrogram client
app = Client(
    "my_bot",
    api_id=int(os.getenv("TELEGRAM_API_ID")),
    api_hash=os.getenv("TELEGRAM_API_HASH"),
    bot_token=os.getenv("TELEGRAM_BOT_TOKEN")
)

start_time = datetime.datetime.now()  # Store the start time
timezone = pytz.timezone("Asia/Kolkata")

@app.on_message(filters.command('start') & filters.private)
def start_command(bot, message):
    app.send_message(
        chat_id=message.chat.id,
        text="Hey bro!"
    )

def upload_to_github(file_path: str, target_path: str):
    # Read file contents as binary
    with open(file_path, "rb") as f:
        file_content = f.read()

    # Encode file content as Base64
    encoded_content = base64.b64encode(file_content).decode("utf-8")

    # Create a new file in the GitHub repository using HTTP request
    github_username = os.getenv("GITHUB_USERNAME")
    github_repo_name = os.getenv("GITHUB_REPO_NAME")
    github_access_token = os.getenv("GITHUB_ACCESS_TOKEN")
    tg_bot_name = os.getenv("TELEGRAM_BOT_NAME", "@Pyrgm_bot")

    url = f"https://api.github.com/repos/{github_username}/{github_repo_name}/contents/{target_path}"
    headers = {"Authorization": f"token {github_access_token}"}
    data = {
        "message": f"Upload {target_path} by Telegram bot {tg_bot_name}",
        "content": encoded_content
    }
    response = requests.put(url, json=data, headers=headers)

    if response.ok:
        print("File uploaded successfully!")
    else:
        print("Error uploading the file:")
        print(response.status_code, response.text)

@app.on_message(filters.document | filters.photo | filters.video | filters.audio | filters.sticker | filters.animation)
def handle_file_upload(client: Client, message: Message):
    # Get the file from the message
    file = message.document or message.photo or message.video or message.audio or message.sticker or message.animation

    # Download the file to a temporary location
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        client.download_media(file, file_name=tmp_file.name)

        # Upload the file to GitHub
        file_path = file.file_name        
        try:
            upload_to_github(tmp_file.name, file_path)
        except Exception as e:
            traceback.print_exc()  # Print the traceback information
            message.reply_text("An error occurred while uploading the file. Please try again later.")
            return

        # Generate the raw URL of the file
        raw_url = get_raw_github_url(file_path)

        # Send the raw URL back to the user
        message.reply_text(f"File uploaded!\n\nRaw URL: {raw_url}")

    # Delete the temporary file
    os.remove(tmp_file.name)

def get_raw_github_url(file_path: str) -> str:
    # Generate the raw URL of the file
    github_username = os.getenv("GITHUB_USERNAME")
    github_repo_name = os.getenv("GITHUB_REPO_NAME")
    raw_url = f"https://raw.githubusercontent.com/{github_username}/{github_repo_name}/main/{file_path}"
    return raw_url

@app.on_message(filters.command('uptime'))
def uptime_command(bot, message):
    current_time = datetime.datetime.now()
    uptime = current_time - start_time
    days = uptime.days + 1 if uptime.seconds >= 43200 else uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_text = f"{days} days, {hours:02d} hours, {minutes:02d} minutes, {seconds:02d} seconds"
    app.send_message(
        chat_id=message.chat.id,
        text=f"Bot has been running for {uptime_text}."
    )

@app.on_message(filters.command('starttime'))
def starttime_command(bot, message):
    now = datetime.datetime.now()
    formatted_time = now.astimezone(timezone).strftime("%A, %B %d, %Y %I:%M:%S %p")    
    app.send_message(
        chat_id=message.chat.id,
        text=f"The bot started at: {formatted_time}"
    )

# Create a Flask app
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    formatted_time = start_time.astimezone(timezone).strftime("%A, %B %d, %Y %I:%M:%S %p")
    uptime = datetime.datetime.now() - start_time
    days = uptime.days + 1 if uptime.seconds >= 43200 else uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_text = f"{days} days, {hours:02d} hours, {minutes:02d} minutes, {seconds:02d} seconds"
    return f"Bot started at: {formatted_time}<br>Bot runtime: {uptime_text}"

if __name__ == "__main__":
    print("Bot is running...")
    # Start the Flask app in a separate thread
    from threading import Thread
    t = Thread(target=flask_app.run)
    t.start()
    # Start the bot
    app.run()
