import os
import openai
import logging
import pyttsx3
import time
import threading
import json
from flask import Flask, request, jsonify

# Load API Key from Environment Variables
openai.api_key = os.getenv("OPENAI_API_KEY")

# Flask App Initialization
app = Flask(__name__)

# Text-to-Speech Setup
engine = pyttsx3.init()
voice_enabled = False
session_data = {
    "waiting_for_message": False,
    "customer_email": "",
    "customer_name": "",
    "last_message_time": time.time(),  # Track last message timestamp
    "team_member_emails": ["team1@business.com", "team2@business.com"],  # List of team members
    "welcome_displayed": False,  # Track if welcome message has been displayed
}

# Configure Logging
logging.basicConfig(filename="assistbot_error.log", level=logging.DEBUG)

# FAQs and Order Tracking Data
faqs = {
    "return policy": "You can return items within 30 days.",
    "support hours": "Our support is available from 9 AM to 5 PM, Monday to Friday.",
}
order_tracking = {
    "123": "Shipped",
    "124": "Processing",
}

# File to store unresolved issues (simple database alternative)
MESSAGE_STORAGE_FILE = "unresolved_issues.json"

# Initialize the unresolved issues storage file
if not os.path.exists(MESSAGE_STORAGE_FILE):
    with open(MESSAGE_STORAGE_FILE, "w") as f:
        json.dump([], f)

# Function to Save Issues to File
def save_issue_to_file(customer_name, customer_email, message):
    issue = {
        "name": customer_name,
        "email": customer_email,
        "message": message,
        "timestamp": time.time(),
    }
    with open(MESSAGE_STORAGE_FILE, "r+") as f:
        data = json.load(f)
        data.append(issue)
        f.seek(0)
        json.dump(data, f)

# Background Task to Check Inactivity
def check_inactivity():
    while True:
        time.sleep(10)  # Runs every 10 seconds
        if time.time() - session_data["last_message_time"] >= 300:  # 5 minutes (300 seconds)
            if not session_data["waiting_for_message"]:
                session_data["waiting_for_message"] = True
                print("Chatbot: Did I resolve your issue? (yes/no)")

# Start background thread for inactivity tracking
t = threading.Thread(target=check_inactivity, daemon=True)
t.start()

# Function to Generate Bot Response
def generate_response(user_message):
    global session_data

    # Update last message time
    session_data["last_message_time"] = time.time()

    # "Did I resolve your issue?" Logic
    if "did i resolve your issue" in user_message.lower():
        return "Would you like me to message the conversation to a team member? (yes/no)"

    if user_message.lower() == "no":
        session_data["waiting_for_message"] = True
        return "Okay, please type your message for a team member."

    if user_message.lower() == "yes":
        return "Glad I could help! Is there anything else I can assist you with?"

    if session_data["waiting_for_message"]:
        save_issue_to_file(
            session_data.get("customer_name", "Unknown"),
            session_data.get("customer_email", "N/A"),
            user_message,
        )
        session_data["waiting_for_message"] = False
        return "Your message has been saved for the team member. They will respond shortly."

    # Order Tracking
    if "order status" in user_message.lower():
        order_id = user_message.split()[-1]
        return order_tracking.get(order_id, "Order not found.")

    # FAQs
    faq_response = faqs.get(user_message.lower())
    if faq_response:
        return faq_response

    # Fallback to OpenAI GPT Response
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are a helpful assistant."},
                      {"role": "user", "content": user_message}],
        )["choices"][0]["message"]["content"]
        return response
    except Exception as e:
        logging.error(f"OpenAI API error: {e}")
        return "Sorry, I encountered an issue processing your request."

# Flask API Endpoint
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    return jsonify({"response": generate_response(data["message"])})

# Run Chatbot
if __name__ == "__main__":
    print("\U0001F44B Welcome to AssistBot!")
    print("\U0001F389 Server starting...")
    mode = input("Type '1' for terminal testing or '2' to host as a server: ")
    if mode == "1":
        print("AssistBot: Welcome to AssistBot. How can I help you today?")
        session_data["welcome_displayed"] = True  # Ensure welcome is shown only once
        while True:
            user_message = input("You: ")
            if user_message.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
            print(f"AssistBot: {generate_response(user_message)}")
    elif mode == "2":
        app.run(host="0.0.0.0", port=8080)  # Ensure it runs on a hosting platform.











    
