from flask import Flask, render_template, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
from PIL import Image
import pytesseract

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

workingFilename = 'none'

def extract_data_from_image(file_path):
    try:
        print(f"extract_data_from_image from: {file_path}")
        # Extract text from the image using pytesseract
        #image = Image.open(file_path)
        #extracted_text = pytesseract.image_to_string(image)

        # Parse text into a dictionary using the given rules
        #data = {}
        #current_year = datetime.now().year
        #for line in extracted_text.splitlines():
        #    if ":" in line:
        #        key = key.strip()
        ##        key, value = line.split(":", 1)
        #        value = value.strip()

        #        if not value:
        #            value = "none"

                # Handle date formatting
        #        try:
        #            parsed_date = datetime.strptime(value, "%d/%m")
        #            value = parsed_date.replace(year=current_year).strftime("%d/%m/%Y")
        #        except ValueError:
        #            pass

        #        data[key] = value
        data = {"one":"car"}
        return data
    except Exception as e:
        return {"error": str(e)}

# Route for the home page
@app.route("/", methods=["GET", "POST"])
def home():
    print("/home start")
    if request.method == "POST":
        if "file" not in request.files:
            return render_template("home.html", uploaded=None, json_data=None)
        file = request.files["file"]
        if file.filename == "":
            return render_template("home.html", uploaded=None, json_data=None)

        # Save the uploaded file
        print(f"/home: file.filename: {file.filename} ")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        global workingFilename
        workingFilename = file.filename
        return render_template("home.html", uploaded=f"File '{workingFilename}' uploaded successfully!", json_data=None)
    return render_template("home.html", uploaded=None, json_data=None)

@app.route("/extract", methods=["POST"])
def extract_booking_data():
    print("/extract start")
    uploaded_files = os.listdir(app.config['UPLOAD_FOLDER'])
    if not uploaded_files:
        return render_template("home.html", uploaded="No uploaded files found!", json_data=None)

    # Assume the first uploaded file is the one to process
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], str(workingFilename))
    print(f"Processing file: {workingFilename}, path:{file_path}")
    extracted_data = extract_data_from_image(file_path)

    # Convert the extracted data to a JSON string
    json_data = json.dumps(extracted_data, indent=4)
    return render_template("home.html", uploaded=f"File '{workingFilename}' uploaded successfully!", json_data=json_data)


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000)
