import os
import pandas as pd
import re
import sys
from openai import OpenAI
from dotenv import load_dotenv
from difflib import SequenceMatcher

def evaluate_song_file(file_path, team_name, prompt):
    """
    Evaluates a song data Excel file based on user prompt and calculates a score.
    """
    load_dotenv()  # Load environment variables from .env file
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}", "status": "error"}
            
        # Read the Excel file
        df = pd.read_excel(file_path)
        
        # Check if required columns exist
        required_columns = ["Lyrics (4-8 lines, 50-100 words)", "Genre"]
        for col in required_columns:
            if col not in df.columns:
                return {"error": f"Required column '{col}' not found in the Excel file", "status": "error"}
        
        # Use song genre evaluation function
        evaluation_results = evaluate_song_genres(df, prompt)
        
        # Generate detailed feedback
        feedback = f"""# Prompt Engineering Score: {evaluation_results['score']}/100

## Summary
- **Correct Classifications**: {evaluation_results['correct_count']}/{evaluation_results['total_count']}
- **Accuracy**: {evaluation_results['score']}%
- **Prompt Used**: "{prompt}"

## Detailed Results

| Song | Expected Genre | Predicted Genre | Result |
|------|---------------|----------------|--------|
"""
        
        # Add first 5 results to feedback table
        for i, result in enumerate(evaluation_results['results'][:5]):
            feedback += f"| {i+1} | {result['Expected Genre']} | {result['Predicted Genre']} | {'✓' if result['Correct'] else '✗'} |\n"
        
        if len(evaluation_results['results']) > 5:
            feedback += f"\n*...and {len(evaluation_results['results'])-5} more songs*\n"
            
        feedback += f"""
## Analysis

Your prompt: "{prompt}"

### Strengths
- {evaluation_results['correct_count']} out of {evaluation_results['total_count']} songs were correctly classified
- Your prompt {'performed very well' if evaluation_results['score'] > 80 else 'performed moderately well' if evaluation_results['score'] > 50 else 'needs improvement'}

### Areas for Improvement
- {'Consider being more specific about musical elements and lyrical patterns' if evaluation_results['score'] < 90 else 'Minor refinements could achieve perfect accuracy'}
- {'Focus on distinguishing between similar genres' if evaluation_results['score'] < 80 else 'Your approach effectively distinguishes between genres'}
"""
        
        # Save results to leaderboard
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        excel_path = os.path.join(data_dir, 'leaderboard.xlsx')
        
        # Create or update leaderboard
        if os.path.exists(excel_path):
            leaderboard_df = pd.read_excel(excel_path)
        else:
            leaderboard_df = pd.DataFrame(columns=['name', 'score', 'last_updated'])
        
        # Update or add team
        if team_name in leaderboard_df['name'].values:
            leaderboard_df.loc[leaderboard_df['name'] == team_name, 'score'] = evaluation_results['score']
            leaderboard_df.loc[leaderboard_df['name'] == team_name, 'last_updated'] = pd.Timestamp.now().isoformat()
        else:
            new_row = pd.DataFrame({
                'name': [team_name],
                'score': [evaluation_results['score']],
                'last_updated': [pd.Timestamp.now().isoformat()]
            })
            leaderboard_df = pd.concat([leaderboard_df, new_row], ignore_index=True)
        
        # Sort and save leaderboard
        leaderboard_df = leaderboard_df.sort_values(by='score', ascending=False)
        leaderboard_df.to_excel(excel_path, index=False)
        
        # Save detailed evaluation
        evaluations_dir = os.path.join(data_dir, 'evaluations')
        if not os.path.exists(evaluations_dir):
            os.makedirs(evaluations_dir)
        
        eval_file = os.path.join(evaluations_dir, f"{team_name}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(eval_file, 'w') as f:
            f.write(f"Team: {team_name}\n")
            f.write(f"Score: {evaluation_results['score']}/100\n")
            f.write(f"Correct: {evaluation_results['correct_count']}/{evaluation_results['total_count']}\n")
            f.write(f"Prompt: {prompt}\n\n")
            f.write("Detailed Results:\n\n")
            
            for i, result in enumerate(evaluation_results['results']):
                f.write(f"Song {i+1}:\n")
                f.write(f"Lyrics: {result['Lyrics'][:100]}...\n")
                f.write(f"Expected Genre: {result['Expected Genre']}\n")
                f.write(f"Predicted Genre: {result['Predicted Genre']}\n")
                f.write(f"Correct: {'Yes' if result['Correct'] else 'No'}\n\n")
        
        return {
            "team": team_name,
            "score": evaluation_results['score'],
            "feedback": feedback,
            "correct": evaluation_results['correct_count'],
            "total": evaluation_results['total_count'],
            "status": "success"
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error evaluating file: {str(e)}")
        print(error_details)
        return {"error": str(e), "details": error_details, "status": "error"}

def calculate_similarity(a, b):
    """Calculate string similarity using SequenceMatcher."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def is_correct_genre(expected, predicted, match_method="contains"):
    """Check if the predicted genre matches the expected genre."""
    expected = expected.lower().strip()
    predicted = predicted.lower().strip()
    
    if match_method == "exact":
        return expected == predicted
    elif match_method == "contains":
        return expected in predicted or predicted in expected
    elif match_method == "fuzzy":
        # Consider it a match if similarity is at least 0.8
        return calculate_similarity(expected, predicted) >= 0.8
    else:
        return False

def evaluate_song_genres(df, prompt, model="gpt-4o-mini"):
    """Evaluate each song in the dataset using the provided prompt."""
    results = []
    correct_count = 0
    total_count = len(df)
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    for idx, row in df.iterrows():
        lyrics = row["Lyrics (4-8 lines, 50-100 words)"]
        expected_genre = row["Genre"]
        
        # Combine lyrics with the user prompt
        combined_text = f"{lyrics}\n\n{prompt}"
        
        try:
            # Call OpenAI API
            completion = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": combined_text}],
                temperature=0.0
            )
            
            # Extract the predicted genre
            predicted_genre = completion.choices[0].message.content.strip()
            
            # Check if prediction is correct (using contains method by default)
            is_correct = is_correct_genre(expected_genre, predicted_genre, "contains")
            if is_correct:
                correct_count += 1
                
            # Store result
            results.append({
                "Lyrics": lyrics,
                "Expected Genre": expected_genre,
                "Predicted Genre": predicted_genre,
                "Correct": is_correct
            })
            
        except Exception as e:
            print(f"Error processing song {idx+1}: {e}")
            results.append({
                "Lyrics": lyrics,
                "Expected Genre": expected_genre,
                "Predicted Genre": "ERROR",
                "Correct": False
            })
    
    # Calculate score
    score = int((correct_count / total_count) * 100) if total_count > 0 else 0
    
    return {
        "results": results,
        "score": score,
        "correct_count": correct_count,
        "total_count": total_count
    }

if __name__ == "__main__":
    # This script can be run directly from command line
    if len(sys.argv) < 3:
        print("Usage: python evaluate_submission.py <file_path> <team_name> [evaluation_prompt]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    team_name = sys.argv[2]
    prompt = sys.argv[3] if len(sys.argv) > 3 else ""
    
    result = evaluate_song_file(file_path, team_name, prompt)
    
    if result["status"] == "success":
        print(f"Evaluation complete for {team_name}!")
        print(f"Score: {result['score']}/100")
        print("\nFeedback Summary:")
        print(result['feedback'][:300] + "..." if len(result['feedback']) > 300 else result['feedback'])
        print(f"\nFull evaluation saved to data/evaluations/{team_name}_*.txt")
    else:
        print(f"Error: {result['error']}")