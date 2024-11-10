from flask import Flask, request, jsonify
import requests
import mimetypes
import os
from docx import Document
import fitz  # PyMuPDF
import html2text
from io import BytesIO
from PIL import Image
import pytesseract
import tempfile

app = Flask(__name__)

# Helper function to download the document
def download_document(url):
    print("Starting document download...")
    response = requests.get(url)
    if response.status_code == 200:
        file_name = url.split('/')[-1]
        file_data = BytesIO(response.content)
        print(f"Document downloaded successfully: {file_name}")
        return file_name, file_data
    else:
        print("Failed to download document.")
        raise Exception("Could not download file")

# Helper functions to handle different document conversions
def convert_pdf_to_text(file_data):
    print("Converting PDF to text...")
    text = ""
    with fitz.open(stream=file_data, filetype="pdf") as pdf:
        for page in pdf:
            text += page.get_text()
    print("PDF conversion completed.")
    return text

def convert_docx_to_text(file_data):
    print("Converting DOCX to text...")
    doc = Document(file_data)
    print("DOCX conversion completed.")
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])

def convert_html_to_text(file_data):
    print("Converting HTML to text...")
    html_content = file_data.read().decode('utf-8')
    print("HTML conversion completed.")
    return html2text.html2text(html_content)

def convert_image_to_text(file_data):
    print("Converting image to text using OCR...")
    image = Image.open(file_data)
    text = pytesseract.image_to_string(image)
    print("Image OCR conversion completed.")
    return text

# Main function to detect file type and convert to text
def convert_to_text(file_name, file_data):
    file_extension = os.path.splitext(file_name)[1].lower()
    print(f"Detected file extension: {file_extension}")

    if file_extension == ".pdf":
        return convert_pdf_to_text(file_data)
    elif file_extension == ".docx":
        return convert_docx_to_text(file_data)
    elif file_extension == ".html":
        return convert_html_to_text(file_data)
    elif file_extension == ".txt":
        print("Reading plain text file...")
        return file_data.read().decode('utf-8')
    elif file_extension in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
        return convert_image_to_text(file_data)
    else:
        print("Unsupported file format.")
        return "Unsupported file format"

# Function to send resume data to the external endpoint
def send_resume_data(resume_data):
    endpoint_url = "https://rps-test-586746141603.us-central1.run.app/add_resumes"
    print("Sending data to external endpoint...")
    response = requests.post(endpoint_url, json=resume_data)
    response.raise_for_status()  # Raises an error if the request fails
    print("Data sent successfully.")
    return response.json()

@app.route('/submit-resumes', methods=['POST'])
def submit_resumes():
    data = request.json
    
    # Extracting fields from the request body
    company_name = data.get("companyName")
    posting_id = data.get("postingId")
    posting_name = data.get("postingName", "N/A")  # Default if postingName is missing
    source = data.get("source")
    resume_url = data.get("resumeUrl")
    batch_id = data.get("batchId")
    sheet_name = data.get("sheetName", "N/A")  # Default if sheetName is missing

    # Basic validation for required fields
    if not all([company_name, posting_id, source, resume_url, batch_id]):
        print("Error: Missing required fields.")
        return jsonify({"error": "Missing required fields in the request body"}), 400

    try:
        # Step 1: Download the document
        file_name, file_data = download_document(resume_url)

        # Step 2: Convert document to text
        text_content = convert_to_text(file_name, file_data)

        # Step 3: Create resume_dict to send to external endpoint
        resume_dict = {
            "company_name": company_name,
            "posting_id": posting_id,
            "posting_name": posting_name,
            "source": source,
            "file_name": resume_url,  # Including the resume URL as file_name
            "file_id": resume_url,  # Including the resume URL as file_id
            "sheet_name": sheet_name,
            "resume_content": text_content
        }
        print(f"Prepared resume data: {resume_dict}")

        # Step 4: Send data to external endpoint
        external_response = send_resume_data(resume_dict)

        # Return the result as JSON, including external endpoint response
        return jsonify({
            "postingId": posting_id,
            "resumeText": text_content,
            "externalResponse": external_response
        })
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask server on port 5000...")
    app.run(port=8080)
