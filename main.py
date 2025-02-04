from flask import Flask, render_template, request, flash, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os
import json
import re
import base64
from datetime import datetime
from PIL import Image
import openai
import requests
from pdf2image import convert_from_path
from modules.logger import Logger

import pytesseract

app = Flask(__name__)
logger = Logger()

ALLOWED_EXTENSIONS = {'jpeg','jpg','pdf'}

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

workingFilename = 'none'
displayFilename = 'none'
openai.api_key = os.environ['OPENAI_API_KEY']
openAIapi_url = "https://api.openai.com/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer " + os.environ['OPENAI_API_KEY']
}
print(f"headers: {headers}")
print("working directory" + os.getcwd())

# add timestamp to filename ie tmp.txt --> tmp25012816362713.txt
def add_timestamp_to_filename(filename):
    timestamp = datetime.now().strftime("%y%m%d%H%M%S%f")[:-4]  # Remove last 4 digits of microseconds
    name, ext = filename.rsplit(".", 1)
    new_filename = f"{name}{timestamp}.{ext}"
    return new_filename

# check file extension is within ALLOWED_EXTENSIONS
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def extract_data_from_image(file_path):
    try:
        print(f"extract_data_from_image from: {file_path}")
        #filename = request.form['filename']
        #file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        #print(f"extract_data_from_image file_path: {file_path}")
        base64_image = encode_image(file_path)
        print(f"extract_data_from_image base64_image: base64_image too big to print")
        if os.path.exists(file_path):
            print("extract_data_from_image File exists, proceeding to encode.")
        else:
            print(f"extract_data_from_image File not found at: {file_path}")
            
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            'text': "Convert the image file into a JSON string. extract the data from the attached form into Json data. Use the left hand column as the key for the data itself. If the data is blank insert value 'none' as data. If a date field is missing the year, put the current year into that date. Where the data is a date, convert to british numeric format ie dd/mm/yyyy. Return just the json data, no preamble so the first character is '{'."
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                        },
                    ],
                }
            ],
        } # EO payload
        response = requests.post(openAIapi_url, headers=headers, json=payload)
        extractedData = response.json()
        print(f"extract_data_from_image response:")

        # return render_template('form_action.html', extracted_data=extractedData, filename=workingFilename)
        return extractedData["choices"][0]["message"]["content"]
        # data = {"one":"car"}
        # return data
    except Exception as e:
        return {"error": str(e)}

# Route for the home page
@app.route("/", methods=["GET", "POST"])
def home():
    print("/home start")
    logger.write_to_log("/home start")
    if request.method == "POST":
        if "file" not in request.files:
            return render_template("home.html", uploaded=None, json_data=None)
        file = request.files["file"]
        if file.filename == "":
            return render_template("home.html", uploaded=None, json_data=None)

        # Validate the file type
        valid = allowed_file(file.filename)
        print(f"/home valid: {valid}")
        if not valid:
            return render_template("home.html", uploaded=None, json_data=None, error="Invalid file type. Only JPEG and PDF are allowed.")

        # Save the uploaded file
        print(f"/home: file.filename: {file.filename} ")
        global displayFilename
        displayFilename = file.filename
        global workingFilename
        workingFilename = add_timestamp_to_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], workingFilename))
        print(f"/home workingFilename: {workingFilename}")
        
        if file.filename.lower().endswith(".pdf"):
            print(f"/home file.filename.lower().endswith('.pdf'): {file.filename.lower().endswith}")
            # Convert PDF to JPG
            filePDF_path = os.path.join(app.config['UPLOAD_FOLDER'], workingFilename)
            name, ext = workingFilename.rsplit(".", 1)
            filenameJPG = f"{name}.jpg"
            fileJPG_path = os.path.join(app.config['UPLOAD_FOLDER'], filenameJPG)
            outputFolder = os.path.join(app.config['UPLOAD_FOLDER'])
            print(f"/home filePDF_path:{filePDF_path}, filenameJPG: {filenameJPG}, fileJPG_path:{fileJPG_path}, outputFolder:{outputFolder}")
            
            print(f"/home about to convert_from_path with filePDF_path:{filePDF_path} to filenameJPG: {filenameJPG}")
            fileJPG = convert_from_path(filePDF_path, output_folder= outputFolder, fmt="jpeg")
            fileJPG[0].save(fileJPG_path)
            workingFilename = filenameJPG
            print(f"About to exit /home, with workingFilename:{workingFilename}")
        return render_template("home.html", uploaded=f"File '{displayFilename}' uploaded successfully.", json_data=None)
    return render_template("home.html", uploaded=None, json_data=None)

@app.route("/extract", methods=["POST"])
def extract_booking_data():
    print("/extract start")
    uploaded_files = os.listdir(app.config['UPLOAD_FOLDER'])
    if not uploaded_files:
        return render_template("home.html", uploaded="No uploaded files found!", json_data=None)

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], str(workingFilename))
    print(f"/extract Processing file: {workingFilename}, path:{file_path}")
    extracted_data = extract_data_from_image(file_path)
    print(f"/extract extracted_data: {extracted_data}")
    
    # Convert the extracted data to a JSON string. json_data has an odd structure, so
    # extract { ... } part then convert to dict
    json_data = json.dumps(extracted_data, indent=4)
    print(f"/extract json_data: {json_data}")
    jsonStrConcat = re.search(r'\{.*\}', extracted_data, re.DOTALL)
    print(f"/extract jsonStrConcat: {jsonStrConcat.group(0)}")
    jsonDict =  json.loads(jsonStrConcat.group(0))
    print(f"type of jsonDict:{type(jsonDict)}")
    logger.write_to_log(f"/extract_booking_data for {workingFilename}")
    return render_template("home.html", uploaded=f"File '{workingFilename}' uploaded successfully!", json_data=jsonDict)

@app.route("/scoreResult" , methods=["POST"])
def scoreResult():
    score = request.form.get("score")
    print(f"/scoreResult start: score:{score}")
    logger.write_to_log(f"/scoreResult for {workingFilename} score {score}")
    return render_template("home.html", user_score = score )

@app.route("/download/<filename>")
def download_file(filename):
    # Serve the file from the 'templates' directory
    return send_from_directory(directory="templates", path=filename, as_attachment=True)

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000)
