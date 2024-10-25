import streamlit as st
import openai
import os
import csv
import uuid
from difflib import SequenceMatcher
from st_audiorec import st_audiorec  # Ensure you have this module installed

# Initialize OpenAI client
def setup_openai_client(api_key):
    openai.api_key = api_key
    return openai

def transcribe_audio(file_path):
    with open(file_path, "rb") as audio_file:
        response = openai.Audio.transcribe(
            model="whisper-1",
            file=audio_file,
            language="en"
        )
    return response["text"]

def calculate_similarity(text1, text2):
    return SequenceMatcher(None, text1, text2).ratio()

def text_to_audio(client, text, audio_path):
    response = client.Audio.synthesize(model="tts-1", voice="echo", input=text)
    with open(audio_path, "wb") as f:
        f.write(response['data'])

# Initialize or update CSV
def initialize_or_update_csv(usernames, audio_file):
    # Get the user's desktop path
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "audio_samples.csv")
    
    # Check if the CSV exists. If not, create it with the correct header.
    file_exists = os.path.isfile(desktop_path)

    if not file_exists:
        # Create the header using actual usernames
        with open(desktop_path, mode='w', newline='') as f:
            writer = csv.writer(f)
            header = usernames  # Use the provided usernames
            writer.writerow(header)

    # Read existing content and update the appropriate user's column
    with open(desktop_path, mode='r') as f:
        reader = list(csv.reader(f))
        # Ensure the CSV has the correct number of columns.
        if len(reader[0]) != len(usernames):
            st.error("CSV structure does not match the required number of users.")
            return

    # Find the user's column index
    user_index = usernames.index(st.session_state.username)  # Find index based on username

    # Add the audio path to the appropriate row/column.
    if len(reader) < st.session_state.current_prompt + 1:
        # If a new row is needed, add it
        new_row = [""] * len(usernames)  # Initialize an empty row
        new_row[user_index] = os.path.abspath(audio_file)  # Insert the audio path for this user
        reader.append(new_row)
    else:
        # If the row exists, update the specific column for the user
        reader[st.session_state.current_prompt][user_index] = os.path.abspath(audio_file)

    # Write the updated content back to the CSV
    with open(desktop_path, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(reader)

# Main function
def main():
    st.sidebar.title("ECHO_GEN Credentials")
    
    # Initialize session state variables if they do not exist
    if "username" not in st.session_state:
        st.session_state.username = None  # Initialize username as None
    if "usernames" not in st.session_state:
        st.session_state.usernames = []  # Initialize the list for usernames
    if "current_prompt" not in st.session_state:
        st.session_state.current_prompt = 0  # Start with the first prompt

    api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")
    username = st.sidebar.text_input("Enter your Username (e.g., user1, user2, user3)")

    # Update the username in session state if provided
    if username:
        st.session_state.username = username
        if username not in st.session_state.usernames:
            st.session_state.usernames.append(username)  # Add username to session state

    st.title("💬 🎙️ Welcome to ECHO GEN...🎧")
    st.text(
        "This is an AI voice generating software.\n"
        "Please provide 5 voice samples by reading the given sentences."
    )

    prompts = [
        "Hello, welcome to ECHO GEN!",
        "Please record your voice to create a custom voice profile.",
        "This is the third sample sentence for the voice model.",
        "Almost there, just one more after this!",
        "Thank you for providing your voice samples."
    ]

    if api_key and st.session_state.username in st.session_state.usernames:
        client = setup_openai_client(api_key)
        audio_files = []

        if st.session_state.current_prompt < len(prompts):
            current_prompt = st.session_state.current_prompt
            prompt = prompts[current_prompt]
            st.write(f"Sample {current_prompt + 1}: {prompt}")

            unique_key = f"audio_recorder_{current_prompt}_{uuid.uuid4().hex}"
            wav_audio_data = st_audiorec()  # Record audio

            if wav_audio_data and len(wav_audio_data) > 0:
                audio_file = f"audio_sample_{current_prompt}_{unique_key}.wav"
                with open(audio_file, "wb") as f:
                    f.write(wav_audio_data)
                st.success(f"Sample {current_prompt + 1} recorded successfully!")

                try:
                    # Append to the list and CSV
                    audio_files.append(audio_file)
                    initialize_or_update_csv(st.session_state.usernames, audio_file)
                    st.success(f"Sample {current_prompt + 1} saved and logged in the database.")

                    # Move to the next prompt
                    st.session_state.current_prompt += 1

                except Exception as e:
                    st.error(f"An error occurred while logging to CSV: {e}")
            else:
                st.warning("No audio recorded. Please try again.")

        if len(audio_files) == 5 and st.session_state.current_prompt > 4:
            st.success("All 5 voice samples have been recorded.")
            st.text("Generating your custom voice model...")

            user_text = st.text_input("Enter the text you want to hear in your custom voice:")
            if user_text:
                response_audio_file = "generated_audio_response.wav"
                try:
                    text_to_audio(client, user_text, response_audio_file)
                    st.audio(response_audio_file)
                    st.success("Generated voice has been played and saved successfully!")
                except Exception as e:
                    st.error(f"An error occurred while generating voice: {e}")

if __name__ == "__main__":
    main()

