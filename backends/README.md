DataNexus Song Classification Hackathon
A web-based tool for evaluating prompts against a song genre classification dataset, designed for hackathon competitions. This will be an iframe displayed on their page deployed through azure.

Overview
interactive web application that allows participants to:

  1. Submit classification prompts that will be tested against a dataset of song lyrics
  2. Receive immediate feedback on how well their prompts perform
  3. View their score on a real-time leaderboard
  4. Share the competition via QR codes
The application evaluates how effectively a prompt can guide an AI model to correctly classify songs by genre.

Project Structure

    DataNexus/
    ├── backends/
    │   ├── app.py                  # Flask backend server
    │   ├── chat.py                 # OpenAI API integration
    │   ├── database.py             # Database interactions
    │   ├── async_chat.py           # Async OpenAI API integration
    │   ├── async_database.py       # Async database interactions
    │   ├── evaluate_submission.py  # Song classification evaluation
    │   ├── data/
    │   │   ├── leaderboard.xlsx    # Leaderboard data storage
    │   │   ├── Prompt Engineering Songs.xlsx  # Song dataset
    │   │   └── evaluations/        # Stored evaluation results
    │   └── requirements.txt        # Python dependencies
    ├── datanexus.js                # Frontend JavaScript
    ├── dataNexus.html              # Main HTML interface
    ├── styles.css                  # Styling for the interface
    └── .env                        # Environment variables (API keys)

Features
  Real-time Prompt Evaluation: Tests prompts against a dataset of song lyrics and genres
  Scoring System: Calculates scores based on correct genre classifications
  Detailed Feedback: Provides comprehensive analysis of prompt performance
  Leaderboard: Displays team rankings based on evaluation scores
  QR Code Sharing: Generates shareable QR codes for the competition
  Responsive Design: Works on both desktop and mobile devices

Technology Stack
  Frontend: HTML5, CSS3, JavaScript
  Backend: Python, Flask
  APIs: OpenAI API for text classification
  Data Storage: Excel files for simple data persistence
  Libraries:
     marked.js for Markdown rendering
     QRCode.js for QR code generation
     pandas for data manipulation

Installation

Prerequisites
  Python 3.8+
  Node.js (for development)
  OpenAI API key (set in system environmental variables)

Backend Setup
  pip install -r requirements.txt
  run: python app.py
  Open dataNexus.html in a web browser