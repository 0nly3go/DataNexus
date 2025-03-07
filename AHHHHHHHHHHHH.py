import pandas as pd
from openai import OpenAI
import time
import os
from difflib import SequenceMatcher

def openai_response(model, messages, **kwargs):
    """
    Generate a response using OpenAI API.
   
    Args:
        model (str): The OpenAI model to use (e.g., "gpt-4o-mini")
        messages (list): List of message dictionaries with role and content
        **kwargs: Additional parameters to pass to the OpenAI API (temperature, max_tokens, etc.)
       
    Returns:
        The completion object from OpenAI
    """
    client = OpenAI()
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        **kwargs
    )
    return completion

def load_song_data(file_path):
    """
    Load song data from Excel file.
    
    Args:
        file_path (str): Path to the Excel file
        
    Returns:
        DataFrame: Pandas DataFrame containing the song data
    """
    try:
        df = pd.read_excel(file_path)
        # Check if required columns exist
        required_columns = ["Lyrics (4-8 lines, 50-100 words)", "Genre"]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' not found in the Excel file")
        return df
    except Exception as e:
        print(f"Error loading song data: {e}")
        return None

def get_user_prompt():
    """
    Get the prompt from the user.
    
    Returns:
        str: The user's prompt
    """
    print("\n= Prompt Engineering Competition =")
    print("Enter your prompt that will be appended to song lyrics.")
    print("The goal is to make the AI correctly identify the genre of each song.")
    print("Your prompt should guide the AI to analyze the lyrics and determine the genre.\n")
    print("Example: 'Analyze these lyrics and provide only the music genre as a one-word answer.'\n")
    return input("Your prompt: ")

def calculate_similarity(a, b):
    """
    Calculate string similarity using SequenceMatcher.
    
    Args:
        a (str): First string
        b (str): Second string
        
    Returns:
        float: Similarity ratio (0.0 to 1.0)
    """
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def is_correct_genre(expected, predicted, match_method="exact"):
    """
    Check if the predicted genre matches the expected genre.
    
    Args:
        expected (str): Expected genre
        predicted (str): Predicted genre
        match_method (str): Matching method ('exact', 'contains', or 'fuzzy')
        
    Returns:
        bool: True if correct, False otherwise
    """
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

def evaluate_prompt(df, prompt, model="gpt-4o-mini", temperature=0.0, max_retries=3, retry_delay=2, match_method="contains"):
    """
    Evaluate a prompt against all songs in the dataset.
    
    Args:
        df (DataFrame): DataFrame containing song data
        prompt (str): User prompt to append to lyrics
        model (str): OpenAI model to use
        temperature (float): Temperature setting for OpenAI API
        max_retries (int): Maximum number of retries for failed API calls
        retry_delay (int): Delay between retries in seconds
        match_method (str): Method to match genres
        
    Returns:
        dict: Results of the evaluation
    """
    results = []
    correct_count = 0
    total_count = len(df)
    
    print(f"\nEvaluating prompt against {total_count} songs...\n")
    
    for idx, row in df.iterrows():
        lyrics = row["Lyrics (4-8 lines, 50-100 words)"]
        expected_genre = row["Genre"]
        
        # Combine lyrics with the user prompt
        combined_text = f"{lyrics}\n\n{prompt}"
        
        # Create messages for OpenAI API
        messages = [
            {"role": "user", "content": combined_text}
        ]
        
        # Call OpenAI API with retries
        retries = 0
        while retries <= max_retries:
            try:
                completion = openai_response(
                    model=model,
                    messages=messages,
                    temperature=temperature
                )
                
                # Extract the predicted genre
                predicted_genre = completion.choices[0].message.content.strip()
                
                # Check if prediction is correct
                is_correct = is_correct_genre(expected_genre, predicted_genre, match_method)
                if is_correct:
                    correct_count += 1
                    
                # Store result
                results.append({
                    "Lyrics": lyrics,
                    "Expected Genre": expected_genre,
                    "Predicted Genre": predicted_genre,
                    "Correct": is_correct
                })
                
                # Print progress
                print(f"Song {idx+1}/{total_count}: {'✓' if is_correct else '✗'} Expected: {expected_genre}, Predicted: {predicted_genre}")
                
                # Success, so break the retry loop
                break
                
            except Exception as e:
                retries += 1
                if retries <= max_retries:
                    print(f"Error processing song {idx+1}, retrying ({retries}/{max_retries}): {e}")
                    time.sleep(retry_delay)
                else:
                    print(f"Error processing song {idx+1} after {max_retries} retries: {e}")
                    results.append({
                        "Lyrics": lyrics,
                        "Expected Genre": expected_genre,
                        "Predicted Genre": "ERROR",
                        "Correct": False
                    })
        
        # Add a small delay to avoid rate limiting
        time.sleep(1)
    
    # Calculate score
    score = (correct_count / total_count) * 100 if total_count > 0 else 0
    
    return {
        "results": results,
        "score": score,
        "correct_count": correct_count,
        "total_count": total_count,
        "prompt": prompt,
        "model": model,
        "match_method": match_method
    }

def display_results(evaluation, show_details=True):
    """
    Display the evaluation results.
    
    Args:
        evaluation (dict): Evaluation results
        show_details (bool): Whether to show detailed results for each song
        
    Returns:
        tuple: (correct_count, total_count, score_percentage)
    """
    if show_details:
        print("\n= Evaluation Results =")
        print(f"Prompt: \"{evaluation['prompt']}\"")
        print(f"Model: {evaluation['model']}")
        print(f"Match Method: {evaluation['match_method']}")
        
        # Create a decorated score display
        score_display = "=" * 50
        score_display += f"\n  FINAL SCORE: {evaluation['correct_count']} / {evaluation['total_count']} CORRECT"
        score_display += f"  ({evaluation['score']:.2f}%)"
        score_display += f"\n" + "=" * 50
        print(score_display)
        
        print("\nDetailed Results:")
        for idx, result in enumerate(evaluation["results"]):
            print(f"\nSong {idx+1}:")
            print(f"Expected Genre: {result['Expected Genre']}")
            print(f"Predicted Genre: {result['Predicted Genre']}")
            print(f"Correct: {'Yes' if result['Correct'] else 'No'}")
            
        # Save results to a file
        save_results = input("\nSave results to a file? (y/n): ").lower()
        if save_results == 'y':
            filename = f"prompt_results_{int(time.time())}.txt"
            with open(filename, 'w') as f:
                f.write(f"= Prompt Engineering Competition Results =\n")
                f.write(f"Prompt: \"{evaluation['prompt']}\"\n")
                f.write(f"Model: {evaluation['model']}\n")
                f.write(f"Match Method: {evaluation['match_method']}\n")
                f.write(score_display + "\n\n")
                
                f.write("Detailed Results:\n")
                for idx, result in enumerate(evaluation["results"]):
                    f.write(f"\nSong {idx+1}:\n")
                    f.write(f"Lyrics: {result['Lyrics'][:100]}...\n")
                    f.write(f"Expected Genre: {result['Expected Genre']}\n")
                    f.write(f"Predicted Genre: {result['Predicted Genre']}\n")
                    f.write(f"Correct: {'Yes' if result['Correct'] else 'No'}\n")
                
            print(f"Results saved to {filename}")
    
    return (evaluation['correct_count'], evaluation['total_count'], evaluation['score'])

def get_model_choice():
    """
    Get the user's choice of model.
    
    Returns:
        str: The chosen model name
    """
    models = [
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-4-turbo",
        "gpt-3.5-turbo"
    ]
    
    print("\nAvailable models:")
    for idx, model in enumerate(models):
        print(f"{idx+1}. {model}")
    
    while True:
        try:
            choice = int(input("\nSelect a model (1-4, default is 1): ") or "1")
            if 1 <= choice <= len(models):
                return models[choice-1]
            else:
                print(f"Please enter a number between 1 and {len(models)}")
        except ValueError:
            print("Please enter a valid number")

def get_match_method():
    """
    Get the user's choice of genre matching method.
    
    Returns:
        str: The chosen matching method
    """
    methods = [
        "contains",
        "exact",
        "fuzzy"
    ]
    
    print("\nGenre matching methods:")
    print("1. contains - Expected genre appears anywhere in the response")
    print("2. exact - Response must exactly match the expected genre")
    print("3. fuzzy - Response is similar to the expected genre")
    
    while True:
        try:
            choice = int(input("\nSelect a matching method (1-3, default is 1): ") or "1")
            if 1 <= choice <= len(methods):
                return methods[choice-1]
            else:
                print(f"Please enter a number between 1 and {len(methods)}")
        except ValueError:
            print("Please enter a valid number")

def main():
    """
    Main function to run the prompt engineering competition.
    
    Returns:
        tuple: (correct_count, total_count, score_percentage) or None if error
    """
    # Check for API key
    if "OPENAI_API_KEY" not in os.environ:
        api_key = input("Enter your OpenAI API key: ")
        os.environ["OPENAI_API_KEY"] = api_key
    
    # Load song data
    file_path = "backends\data\Prompt Engineering Songs.xlsx"
    df = load_song_data(file_path)
    
    if df is None:
        print("Exiting due to error loading song data.")
        return None
    
    # Use gpt-4o-mini model
    model = "gpt-4o-mini"
    
    # Get match method
    match_method = get_match_method()
    
    # Get user prompt
    prompt = get_user_prompt()
    
    # Evaluate prompt
    evaluation = evaluate_prompt(df, prompt, model=model, match_method=match_method)
    
    # Display results and get score
    score_results = display_results(evaluation)
    
    # Ask if user wants to try another prompt
    try_again = input("\nTry another prompt? (y/n): ").lower()
    if try_again == 'y':
        return main()
    else:
        print("\nThank you for participating in the Prompt Engineering Competition!")
        return score_results

if __name__ == "__main__":
    try:
        score_results = main()
        if score_results:
            correct, total, percentage = score_results
            print(f"\n{correct}/{total}")
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting...")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")