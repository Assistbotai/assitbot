import os
import openai
import logging
import pyttsx3
from flask import Flask, request, jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load API Key from Environment Variables
openai.api_key = os.getenv("OPENAI_API_KEY")

# Email Settings (from Render environment variables)
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")  # Your email
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # Your app password

# Initialize Flask App
app = Flask(__name__)

# Initialize Text-to-Speech
engine = pyttsx3.init()
voice_enabled = False  # Voice is off by default
session_data = {"waiting_for_message": False, "agent_email": "", "customer_email": ""}

# Configure logging
logging.basicConfig(filename="assistbot_error.log", level=logging.DEBUG)

# FAQs and Order Tracking
faqs = {
    "return policy": "You can return items within 30 days.",
    "support hours": "9 AM to 5 PM, Monday to Friday.",
}
order_tracking = {
    "123": "Shipped",
    "124": "Processing",
}

# Handoff Trigger Keywords
handoff_triggers = ["human", "agent", "talk to human", "talk to agent", "speak to human", "speak to agent"]

# Function to Send Email to Business Owner
def send_handoff_email(user_message, customer_email):
    business_email = os.getenv("BUSINESS_OWNER_EMAIL")  # The email where customer service requests go

    try:
        subject = "Live Agent Request from Customer"
        body = f"Customer Email: {customer_email}\n\nMessage: {user_message}\n\nPlease respond promptly."
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USERNAME
        msg["To"] = business_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USERNAME, business_email, msg.as_string())
        server.quit()

        logging.info(f"Email sent to agent: {business_email}")
        return True
    except Exception as e:
        logging.error(f"Error sending email: {e}")
        return False

# Generate Bot Response
def generate_response(user_message):
    global session_data

    # Check for Handoff Keywords
    if any(trigger in user_message.lower() for trigger in handoff_triggers):
        session_data["waiting_for_message"] = True
        return "Sure! Please enter your email so an agent can contact you."

    # Capture Customer Email for Handoff
    if session_data["waiting_for_message"] and "@" in user_message:
        session_data["customer_email"] = user_message.strip()
        return "Got it! Now please type your message for the agent."

    # Handoff Message Logic
    if session_data["waiting_for_message"] and session_data["customer_email"]:
        sent = send_handoff_email(user_message, session_data["customer_email"])
        session_data["waiting_for_message"] = False
        return "Your message has been sent to the agent." if sent else "Failed to send your message."

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

# Terminal Chat
def terminal_chat():
    print("👋 Hi! I'm AssistBot. How can I assist you today?")
    while True:
        user_message = input("You: ")
        if user_message.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        response = generate_response(user_message)
        print(f"AssistBot: {response}")

# Run Chatbot
if __name__ == "__main__":
    print("👋 Welcome to AssistBot!")
    print("🎉 Server starting...")
    mode = input("Type '1' for terminal testing or '2' to host as a server: ")
    if mode == "1":
        terminal_chat()
    elif mode == "2":
        app.run(host="0.0.0.0", port=8080)  # Ensure it runs on Render











    