import openai
import os
import pymongo
import flask
from flask_cors import CORS
from datetime import datetime
from flask import request, jsonify
import pandas as pd
import re

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
        # Path to your Excel file
        excel_path = os.path.join(os.path.dirname(__file__), 'data', 'leaderboard.xlsx')
        
        # Check if file exists
        if not os.path.exists(excel_path):
            # Return sample data if file doesn't exist
            leaderboard_data = [
                {"name": "Team 1", "score": 100},
                {"name": "Team 2", "score": 90},
                {"name": "Team 3", "score": 80}
            ]
            return jsonify(leaderboard_data)
        
        # Read Excel file
        df = pd.read_excel(excel_path)
        
        # Sort by score descending
        df = df.sort_values(by='score', ascending=False)
        
        # Convert to list of dictionaries (JSON format)
        leaderboard_data = df.to_dict('records')
        
        return jsonify(leaderboard_data)
    except Exception as e:
        print(f"Leaderboard error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/score', methods=['POST'])
def update_score():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    data = request.get_json()
    
    # Check if required fields exist
    if 'name' not in data or 'score' not in data:
        return jsonify({"error": "name and score are required"}), 400
        
    team_name = data['name']
    new_score = data['score']
    
    try:
        # Path to your Excel file
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        excel_path = os.path.join(data_dir, 'leaderboard.xlsx')
        
        # Create data directory if it doesn't exist
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # Check if file exists, create it if it doesn't
        if not os.path.exists(excel_path):
            # Create a new DataFrame
            df = pd.DataFrame(columns=['name', 'score', 'last_updated'])
        else:
            # Read existing data
            df = pd.read_excel(excel_path)
        
        # Check if team already exists
        if team_name in df['name'].values:
            # Update existing team's score
            df.loc[df['name'] == team_name, 'score'] = new_score
            df.loc[df['name'] == team_name, 'last_updated'] = datetime.now().isoformat()
            message = "Score updated successfully"
        else:
            # Add new team
            new_row = pd.DataFrame({
                'name': [team_name],
                'score': [new_score],
                'last_updated': [datetime.now().isoformat()]
            })
            df = pd.concat([df, new_row], ignore_index=True)
            message = "Team added successfully"
        
        # Sort by score descending
        df = df.sort_values(by='score', ascending=False)
        
        # Save back to Excel
        df.to_excel(excel_path, index=False)
        
        return jsonify({
            "status": "success",
            "message": message
        }), 200
        
    except Exception as e:
        print(f"Score update error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/analyze', methods=['POST'])
async def analyze_submission():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    data = request.get_json()
    
    # Check for required fields
    if 'team_name' not in data or 'file_path' not in data:
        return jsonify({"error": "team_name and file_path are required"}), 400
    
    team_name = data['team_name']
    file_path = data['file_path']
    evaluation_criteria = data.get('criteria', "Evaluate the Excel file for data quality, insights, and presentation.")
    
    try:
        # Check if file exists and is Excel
        if not os.path.exists(file_path) or not file_path.endswith(('.xlsx', '.xls', '.csv')):
            return jsonify({"error": "File not found or not a valid Excel/CSV file"}), 404
        
        # Read the Excel file
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        # Get basic stats about the data
        data_stats = {
            'columns': list(df.columns),
            'rows': len(df),
            'missing_values': df.isna().sum().to_dict(),
            'sample': df.head(5).to_dict('records')
        }
        
        # Create a prompt for the AI to evaluate the file
        system_prompt = f"""You are an expert data scientist evaluating submissions for a hackathon.
        Evaluate the following Excel data based on these criteria:
        {evaluation_criteria}
        
        Provide:
        1. A score from 0-100
        2. Detailed feedback on strengths and weaknesses
        3. Suggestions for improvement
        """
        
        # Format the data stats as text for the AI
        data_description = f"""
        Dataset Summary:
        - File: {os.path.basename(file_path)}
        - Columns: {', '.join(data_stats['columns'])}
        - Rows: {data_stats['rows']}
        - Sample data: {str(data_stats['sample'])}
        """
        
        # Make the OpenAI request
        response = await asy_chat_in(
            input_text=data_description,
            system_prompt=system_prompt,
            model="gpt-4o"  # Using a more capable model for evaluation
        )
        
        # Extract score from the response (assuming the AI includes it in the format "Score: XX/100")
        score_match = re.search(r"score:?\s*(\d+)", response.lower())
        score = int(score_match.group(1)) if score_match else 70  # Default if not found
        
        # Update the team's score in the leaderboard
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        excel_path = os.path.join(data_dir, 'leaderboard.xlsx')
        
        # Create data directory if it doesn't exist
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # Read or create leaderboard file
        if not os.path.exists(excel_path):
            # Create a new DataFrame
            leaderboard_df = pd.DataFrame(columns=['name', 'score', 'last_updated'])
        else:
            # Read existing data
            leaderboard_df = pd.read_excel(excel_path)
        
        # Update or add team
        if team_name in leaderboard_df['name'].values:
            leaderboard_df.loc[leaderboard_df['name'] == team_name, 'score'] = score
            leaderboard_df.loc[leaderboard_df['name'] == team_name, 'last_updated'] = datetime.now().isoformat()
        else:
            new_row = pd.DataFrame({
                'name': [team_name],
                'score': [score],
                'last_updated': [datetime.now().isoformat()]
            })
            leaderboard_df = pd.concat([leaderboard_df, new_row], ignore_index=True)
        
        # Sort and save
        leaderboard_df = leaderboard_df.sort_values(by='score', ascending=False)
        leaderboard_df.to_excel(excel_path, index=False)
        
        # Save the evaluation for reference
        evaluations_dir = os.path.join(data_dir, 'evaluations')
        if not os.path.exists(evaluations_dir):
            os.makedirs(evaluations_dir)
        
        eval_file = os.path.join(evaluations_dir, f"{team_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(eval_file, 'w') as f:
            f.write(f"Team: {team_name}\n")
            f.write(f"Score: {score}\n")
            f.write(f"File: {file_path}\n")
            f.write(f"Evaluation:\n{response}\n")
        
        # Return the results
        return jsonify({
            "team": team_name,
            "score": score,
            "feedback": response,
            "status": "success"
        }), 200
        
    except Exception as e:
        print(f"Analysis error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


from evaluate_submission import evaluate_song_file

@app.route('/api/evaluate-songs', methods=['POST'])
def evaluate_songs():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415

    data = request.get_json()
    
    # Check for required fields
    if 'team_name' not in data or 'file_path' not in data:
        return jsonify({"error": "team_name and file_path are required"}), 400
    
    team_name = data['team_name']
    file_path = data['file_path']
    evaluation_prompt = data.get('prompt', "")
    
    # Call the evaluation function
    result = evaluate_song_file(file_path, team_name, evaluation_prompt)
    
    if result.get("status") == "error":
        return jsonify(result), 500
    
    return jsonify(result), 200


if __name__ == '__main__':
    app.run(debug=True)
