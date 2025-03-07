import os
import pandas as pd
import re
import sys
from openai import OpenAI
from dotenv import load_dotenv

def evaluate_song_file(file_path, team_name, prompt):
    """
    Evaluates a song data Excel file based on user prompt and calculates a score.
    
    Parameters:
        file_path (str): Path to the Excel file
        team_name (str): Name of the team being evaluated
        prompt (str): User prompt for evaluation criteria
    
    Returns:
        dict: Results including score, feedback, and status
    """
    load_dotenv()  # Load environment variables from .env file
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}", "status": "error"}
            
        # Read the Excel file
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
            
        # Get data statistics
        data_stats = {
            'columns': list(df.columns),
            'rows': len(df),
            'missing_values': df.isna().sum().to_dict(),
            'data_types': {col: str(df[col].dtype) for col in df.columns},
            'unique_values': {col: df[col].nunique() for col in df.columns}
        }
        
        # Generate sample insights from the data
        insights = []
        
        # Check for numeric columns to get basic stats
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            for col in numeric_cols[:3]:  # Limit to first 3 numeric columns
                insights.append(f"{col} - Min: {df[col].min()}, Max: {df[col].max()}, Mean: {df[col].mean():.2f}")
        
        # Check for categorical columns
        cat_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(cat_cols) > 0:
            for col in cat_cols[:3]:  # Limit to first 3 categorical columns
                top_values = df[col].value_counts().head(3).to_dict()
                insights.append(f"{col} - Top values: {top_values}")
        
        # Prepare system prompt for evaluation
        if not prompt or prompt.strip() == '':
            # Default prompt if none provided
            system_prompt = """You are an expert data scientist evaluating song data for a hackathon.
            Evaluate the Excel data based on data quality, insights, and presentation.
            
            Provide:
            1. A score from 0-100
            2. Detailed feedback on strengths and weaknesses
            3. Suggestions for improvement
            
            Start your response with "Score: XX/100" where XX is the numerical score."""
        else:
            system_prompt = f"""You are an expert data scientist evaluating song data for a hackathon.
            Evaluate the Excel data based on the following criteria:
            {prompt}
            
            Provide:
            1. A score from 0-100
            2. Detailed feedback on strengths and weaknesses
            3. Suggestions for improvement
            
            Start your response with "Score: XX/100" where XX is the numerical score."""
        
        # Sample data for the AI to evaluate
        sample_data = df.head(5).to_dict('records')
        
        # Format data description for the AI
        data_description = f"""
        Dataset Summary for {os.path.basename(file_path)} submitted by {team_name}:
        
        Overview:
        - Total rows: {data_stats['rows']}
        - Total columns: {len(data_stats['columns'])}
        - Column names: {', '.join(data_stats['columns'])}
        
        Data types:
        {'-' + '-'.join([f"{col}: {data_stats['data_types'][col]}" for col in list(data_stats['data_types'].keys())[:5]])}
        
        Unique values per column:
        {'-' + '-'.join([f"{col}: {data_stats['unique_values'][col]}" for col in list(data_stats['unique_values'].keys())[:5]])}
        
        Sample insights:
        {'-' + '-'.join(insights)}
        
        Sample data (first 5 rows):
        {sample_data}
        """
        
        # Make OpenAI API call
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": data_description}
            ]
        )
        
        feedback = response.choices[0].message.content
        
        # Extract score from feedback
        score_match = re.search(r"Score:\s*(\d+)", feedback)
        score = int(score_match.group(1)) if score_match else 70  # Default score if not found
        
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
            leaderboard_df.loc[leaderboard_df['name'] == team_name, 'score'] = score
            leaderboard_df.loc[leaderboard_df['name'] == team_name, 'last_updated'] = pd.Timestamp.now().isoformat()
        else:
            new_row = pd.DataFrame({
                'name': [team_name],
                'score': [score],
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
            f.write(f"Score: {score}/100\n")
            f.write(f"File: {file_path}\n\n")
            f.write(f"Evaluation:\n{feedback}\n")
        
        return {
            "team": team_name,
            "score": score,
            "feedback": feedback,
            "status": "success"
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error evaluating file: {str(e)}")
        print(error_details)
        return {"error": str(e), "details": error_details, "status": "error"}

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