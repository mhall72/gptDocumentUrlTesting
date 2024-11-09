import openai
import requests

# Set your OpenAI API key
openai.api_key = "your_openai_api_key"

# Define the URL of the resume
resume_url = "https://example.com/path/to/resume.pdf"  # replace with actual resume URL

# Step 1: Download the file from the URL
def download_file(url):
    response = requests.get(url)
    if response.status_code == 200:
        filename = "resume.pdf"
        with open(filename, "wb") as file:
            file.write(response.content)
        return filename
    else:
        raise Exception("Failed to download file")

resume_file_path = download_file(resume_url)

# Step 2: Upload the file to OpenAI
def upload_file_to_openai(file_path):
    with open(file_path, "rb") as file:
        file_response = openai.File.create(
            file=file,
            purpose="answers"
        )
    return file_response["id"]

file_id = upload_file_to_openai(resume_file_path)

# Step 3: Ask questions about the uploaded resume file
def ask_question_about_file(file_id, question):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are analyzing a resume file."},
            {"role": "user", "content": question}
        ],
        file=file_id
    )
    return response.choices[0].message["content"]

# Test question
question = "Can you summarize the experience listed in this resume?"
answer = ask_question_about_file(file_id, question)

# Display the answer
print("Answer:", answer)
