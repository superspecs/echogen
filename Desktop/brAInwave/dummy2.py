import streamlit as st
import openai
import uuid
import csv
import os
from st_audiorec import st_audiorec

# Initialize OpenAI client
def setup_openai_client(api_key):
    openai.api_key = api_key
    return openai

# Initialize or update the CSV to store audio sample paths
def initialize_or_update_csv(username, audio_file):
    # Set the path to store the CSV on the Desktop
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    csv_file = os.path.join(desktop_path, "audio_samples.csv")

    # Check if the CSV exists; if not, create with a header row
    file_exists = os.path.isfile(csv_file)

    if not file_exists:
        # Initialize the CSV with the "Sample" column
        with open(csv_file, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Sample"])  # First column for sample names

    # Read the existing CSV content
    with open(csv_file, mode='r') as f:
        reader = list(csv.reader(f))
        header = reader[0]  # The first row (header)
        rows = reader[1:]  # All other rows (data)

    # If the username isn't in the header, add a new column for the user
    if username not in header:
        header.append(username)  # Add the new user to the header
        for row in rows:
            row.append("")  # Add an empty cell for the new user in each row

    # Determine how many samples this user has recorded so far
    user_index = header.index(username)
    user_samples = [row[user_index] for row in rows if row[user_index]]

    if len(user_samples) >= 5:
        st.warning(f"{username} has already recorded the maximum of 5 audio samples.")
        return False  # Stop further recording

    # Calculate the next sample name (audio_sample_1, audio_sample_2, ...)
    sample_index = len(user_samples) + 1  # Current sample number for this user
    sample_name = f"audio_sample_{sample_index}"

    # Check if this sample already exists; if not, create a new row
    existing_samples = [row[0] for row in rows]  # First column is sample names
    if sample_name not in existing_samples:
        new_row = [sample_name] + [""] * (len(header) - 1)  # Initialize with blanks
        rows.append(new_row)  # Add the new row

    # Update the specific user's column with the audio file path
    for row in rows:
        if row[0] == sample_name:  # Locate the correct row for the sample
            row[user_index] = os.path.abspath(audio_file)  # Store the audio file path

    # Write the updated content back to the CSV
    with open(csv_file, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)  # Write the header
        writer.writerows(rows)   # Write the data rows

    return True  # Successful update

# Main function for the Streamlit app
def main():
    st.sidebar.title("ECHO_GEN Credentials")
    api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")
    username = st.sidebar.text_input("Enter your Username (e.g., user1, user2)")

    st.title("💬 🎙️ Welcome to ECHO GEN...🎧")
    st.text("This is an AI voice generating software. Please provide your audio samples.")

    if "current_prompt" not in st.session_state:
        st.session_state.current_prompt = 0  # Start with the first prompt

    prompts = [
        "Hello, welcome to ECHO GEN!",
        "Please record your voice to create a custom voice profile.",
        "This is the third sample sentence for the voice model.",
        "Almost there, just one more after this!",
        "Thank you for providing your voice samples."
    ]

    if api_key:
        client = setup_openai_client(api_key)

        if username:
            # Read the existing CSV content to check how many samples this user has
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            csv_file = os.path.join(desktop_path, "audio_samples.csv")

            # Check if the CSV exists and read it
            if os.path.isfile(csv_file):
                with open(csv_file, mode='r') as f:
                    reader = list(csv.reader(f))
                    header = reader[0]  # The first row (header)
                    rows = reader[1:]  # All other rows (data)

                # Determine how many samples this user has recorded so far
                if username in header:
                    user_index = header.index(username)
                    user_samples = [row[user_index] for row in rows if row[user_index]]
                    if len(user_samples) >= 5:
                        st.warning(f"{username} has already recorded the maximum of 5 audio samples.")
                        st.text("All voice samples have been recorded.")
                        st.text("Generating your custom voice model...")
                        return  # Exit the main function
            else:
                # If the CSV doesn't exist, initialize it
                with open(csv_file, mode='w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Sample"])  # First column for sample names

            if st.session_state.current_prompt < len(prompts):
                current_prompt = st.session_state.current_prompt
                prompt = prompts[current_prompt]
                st.write(f"Sample {current_prompt + 1}: {prompt}")

                unique_key = f"audio_recorder_{current_prompt}_{uuid.uuid4().hex}"
                wav_audio_data = st_audiorec()  # Record audio

                if wav_audio_data and len(wav_audio_data) > 0:
                    audio_file = f"audio_sample_{current_prompt + 1}_{unique_key}.wav"
                    with open(audio_file, "wb") as f:
                        f.write(wav_audio_data)
                    st.success(f"Sample {current_prompt + 1} recorded successfully!")

                    try:
                        # Log the audio file path in the CSV
                        if initialize_or_update_csv(username, audio_file):
                            st.success(f"Sample {current_prompt + 1} saved for {username}.")
                            st.session_state.current_prompt += 1  # Move to the next prompt
                        else:
                            st.warning("Your response has been recorded, please enter another username to proceed.")
                            st.session_state.current_prompt = len(prompts)  # Exit loop for the current user
                    except Exception as e:
                        st.error(f"An error occurred while logging to CSV: {e}")
                else:
                    st.warning("No audio recorded. Please try again.")
            else:
                st.success("All voice samples have been recorded.")
                st.text("Generating your custom voice model...")

                user_text = st.text_input("Enter the text you want to hear in your custom voice:")
                if user_text:
                    response_audio_file = "generated_audio_response.wav"
                    try:
                        text_to_audio(client, user_text, response_audio_file)
                        st.audio(response_audio_file)
                        st.success("Generated voice played and saved successfully!")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
        else:
            st.warning("Please enter a username to proceed.")

if __name__ == "__main__":
    main()
