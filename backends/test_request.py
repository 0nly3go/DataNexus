import requests

url = "http://127.0.0.1:5000/chat"


input_text = """Summarize the following text:
    MLS Cup 1999 was the fourth edition of the MLS Cup, the championship match of Major League Soccer (MLS), the top-level soccer league of the United States. It took place on November 21, 1999, at Foxboro Stadium (pictured) in Foxborough, Massachusetts, and was contested by D.C. United and the Los Angeles Galaxy in a rematch of the inaugural 1996 final played at the same venue. Both teams finished atop their respective conferences during the regular season under new head coaches and advanced through the first two rounds of the playoffs. D.C. United won 2–0 with first-half goals from Jaime Moreno and Ben Olsen for their third MLS Cup victory in four years; Olsen was named the most valuable player of the match for his winning goal. The final was played in front of 44,910 spectators and drew 1.16 million viewers on its ABC television broadcast. It was also the first MLS match to be played with a standard game clock and without a tiebreaker shootout. (Full article...)

    and identify the important entities in the text.
    Return the summary and the important entities as markdown.
    # Summary

    # Important Entities
    """


data = {
    "input_text": input_text,
    "chatbot_name": "Summarizers",
    "interaction_id": "1234567890",
    "system_prompt": "You are a helpful assistant that summarizes text."
}

response = requests.post(url, json=data)

print(response.json())
