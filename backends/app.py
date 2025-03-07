import openai
import os
import pymongo
import flask
from flask_cors import CORS
from datetime import datetime
from flask import request, jsonify

from chat import chat_in
from database import write_to_db

from async_chat import asy_chat_in
from async_database import asy_write_to_db

from dotenv import load_dotenv
load_dotenv()  # This loads the variables from .env

app = flask.Flask(__name__)
CORS(app)  # Enable CORS for all routes


@app.route('/chat', methods=['POST'])
def handle_chat():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    data = request.get_json()

    # Check if required field exists
    if 'input_text' not in data:
        return jsonify({"error": "input_text is required"}), 400

    # Extract fields from JSON
    input_text = data['input_text']
    system_prompt = data.get('system_prompt')  # Optional
    model = data.get('model', 'gpt-4o-mini')  # Optional with default
    interaction_id = data.get('interaction_id')  # Optional
    chatbot_name = data.get('chatbot_name')  # Optional

    try:
        response = chat_in(
            input_text=input_text,
            system_prompt=system_prompt,
            model=model)

        interaction_date = datetime.now()
        write_to_db(texts=[input_text, response],
                    interaction_id=interaction_id,
                    chatbot_name=chatbot_name,
                    interaction_date=interaction_date)

        # Added response to return value
        return jsonify({"response": response, "status": "success"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/async_chat', methods=['POST'])
async def async_handle_chat():
    print("Async chat received")
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    data = request.get_json()

    # Check if required field exists
    if 'input_text' not in data:
        return jsonify({"error": "input_text is required"}), 400

    # Extract fields from JSON
    input_text = data['input_text']
    system_prompt = data.get('system_prompt')  # Optional
    model = data.get('model', 'gpt-4o-mini')  # Optional with default
    interaction_id = data.get('interaction_id')  # Optional
    chatbot_name = data.get('chatbot_name')  # Optional

    try:
        response = await asy_chat_in(
            input_text=input_text,
            system_prompt=system_prompt,
            model=model)

        interaction_date = datetime.now()
        await asy_write_to_db(texts=[input_text, response],
                              interaction_id=interaction_id,
                              chatbot_name=chatbot_name,
                              interaction_date=interaction_date)

        # Added response to return value
        return jsonify({"response": response, "status": "success"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    try:
        # Add your leaderboard logic here
        # For now, returning sample data
        leaderboard_data = [
            {"name": "Team 1", "score": 100},
            {"name": "Team 2", "score": 90},
            {"name": "Team 3", "score": 80}
        ]
        return jsonify(leaderboard_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
