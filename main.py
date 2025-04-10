# Redeploy trigger
print("Running AssistBot Flask App")
import os
import openai
import logging
import time
from flask import Flask, request, jsonify

# Load API Key from Environment Variables
openai.api_key = os.getenv("OPENAI_API_KEY")
print("API Key Loaded:", bool(openai.api_key))  # Should print True

# Flask App Initialization
app = Flask(__name__)

# Session data and in-memory storage
session_data = {
    "waiting_for_message": False,
    "customer_email": "",
    "customer_name": "",
    "last_message_time": time.time(),
    "team_member_emails": ["team1@business.com", "team2@business.com"],
    "welcome_displayed": False,
}
unresolved_issues = []  # Stored in memory

# Console logging only
logging.basicConfig(level=logging.DEBUG)

# FAQs and Order Tracking
faqs = {
    "return policy": "You can return items within 30 days.",
    "support hours": "Our support is available from 9 AM to 5 PM, Monday to Friday.",
}
order_tracking = {
    "123": "Shipped",
    "124": "Processing",
}

# Function to Save Issue
def save_issue_to_memory(customer_name, customer_email, message):
    unresolved_issues.append({
        "name": customer_name,
        "email": customer_email,
        "message": message,
        "timestamp": time.time(),
    })

# Generate Bot Response
def generate_response(user_message):
    global session_data
    session_data["last_message_time"] = time.time()

    # Handle built-in flows
    if "did i resolve your issue" in user_message.lower():
        return "Would you like me to message the conversation to a team member? (yes/no)"
    if user_message.lower() == "no":
        session_data["waiting_for_message"] = True
        return "Okay, please type your message for a team member."
    if user_message.lower() == "yes":
        return "Glad I could help! Is there anything else I can assist you with?"
    if session_data["waiting_for_message"]:
        save_issue_to_memory(
            session_data.get("customer_name", "Unknown"),
            session_data.get("customer_email", "N/A"),
            user_message,
        )
        session_data["waiting_for_message"] = False
        return "Your message has been saved for the team member. They will respond shortly."

    if "order status" in user_message.lower():
        order_id = user_message.split()[-1]
        return order_tracking.get(order_id, "Order not found.")

    faq_response = faqs.get(user_message.lower())
    if faq_response:
        return faq_response

    # Use OpenAI for general queries
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message},
            ],
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        # Show actual error in logs and response
        print("💥 OpenAI ERROR:", str(e))
        return f"Error from OpenAI: {str(e)}"

# Flask API Endpoint
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    return jsonify({"response": generate_response(data["message"])})

# Run Server
if __name__ == "__main__":
    print("Starting in server mode...")
    app.run(host="0.0.0.0", port=8080, debug=False)


