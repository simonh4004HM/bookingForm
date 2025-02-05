from flask import Flask, render_template, request, flash, redirect, url_for, send_from_directory, jsonify, send_file
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
from modules.logger import PaperLog   
from modules.logger import LoggerPerm
from replit import db        # installed with shell> pip install replit

from replit.object_storage import Client
client = Client()

#objects = client.list(prefix="forms/")
#print(f"file_names: {file_names}")
#tmp = jsonify({"stored_files": file_names})
#file_names = [obj.name.replace("forms/", "") for obj in objects if obj.name != "forms/"]

#listFiles = client.list(prefix="forms/")
#print(f"listFiles: {listFiles}")
#fileNames = [obj.name.replace("forms/", "") for obj in listFiles if obj.name != "forms/"]
#jsonD = jsonify({"stored_files": fileNames})
#print(f"jsonD: {jsonD}")

import pytesseract

app = Flask(__name__)
logger = Logger()
# paperLog = PaperLog()

# ✅ Create logger instance
loggerPerm = LoggerPerm()

# ✅ Use logger to write a log message
loggerPerm.log("🚀 loggerPerm Application started successfully!")


ALLOWED_EXTENSIONS = {'jpeg','jpg','pdf'}

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

STORAGE_DIR = "bookingForm/forms/"
os.makedirs(STORAGE_DIR, exist_ok=True)
app.config['STORAGE_DIR'] = STORAGE_DIR

TMP_DIR = "/tmp/"

#DOWNLOAD_DIR = "Downloads/"  # ✅ Local storage directory
#os.makedirs(DOWNLOAD_DIR, exist_ok=True)
#app.config['DOWNLOAD_DIR'] = DOWNLOAD_DIR


from replit import db
print(db.keys())  # ✅ See if "test.pdf" is stored
print(db.get("simpleBookingFormV2.pdf")) 

workingFilename = 'none'
displayFilename = 'none'
# openai.api_key = os.environ['OPENAI_API_KEY']
openai.api_key = os.getenv("OPENAI_API_KEY")
# print(f"API Key: {openai.api_key}")
openAIapi_url = "https://api.openai.com/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer " + f"{openai.api_key}"
}
# print(f"headers: {headers}")
# print("working directory" + os.getcwd())

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

def extract_data_from_image(filename):
    try:
        print(f"extract_data_from_image from: {filename}")
        # The file is now in /bookingForm/forms/filename 
        fullFilePath = os.path.join(app.config['STORAGE_DIR'], filename)
        base64_image = encode_image(fullFilePath)
        print(f"extract_data_from_image base64_image: base64_image too big to print")
        if os.path.exists(fullFilePath):
            print("extract_data_from_image File exists, proceeding to encode.")
        else:
            print(f"extract_data_from_image File not found at: {fullFilePath}")
            
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
        # print(f"extract_data_from_image response:{extractedData}")

        # return render_template('form_action.html', extracted_data=extractedData, filename=workingFilename)
        return extractedData["choices"][0]["message"]["content"]
        # data = {"one":"car"}
        # return data
    except Exception as e:
        return {"error": str(e)}

# Route for the home page
@app.route("/", methods=["GET", "POST"])
def home():
    # print("/home start")
    loggerPerm.log("/home start")
    # logger.write_to_log("/home start")
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
        loggerPerm.log(f"/home: file.filename: {file.filename} ")
        global displayFilename
        displayFilename = file.filename
        global workingFilename
        workingFilename = add_timestamp_to_filename(file.filename)
        ### file.save(os.path.join(app.config['UPLOAD_FOLDER'], workingFilename))
        loggerPerm.log(f"/home workingFilename: {workingFilename}")

        # ✅ Save the file to Replit's persistent storage
        # file_path = os.path.join(STORAGE_DIR, file.filename)
        ## cc from above file.save(os.path.join(app.config['UPLOAD_FOLDER'], workingFilename))
        file.seek(0)
        file_path = os.path.join(app.config['STORAGE_DIR'], workingFilename)
        file.save(file_path)
        print(f"Saved file to {file_path}")
        
        # ✅ Store the file path in Replit DB (simulating object storage)
        db[workingFilename] = file_path 
        # db[file.filename] = file_path  # Store file reference in Replit DB
        loggerPerm.log(f"Stored file path in Replit DB file_path:{file_path}, file.filename: {workingFilename} ")

        if file.filename.lower().endswith(".pdf"):
            print(f"/home endswith '.pdf' workingFilename:{workingFilename} ")
            # Convert PDF to JPG
            loggerPerm.log(f"Convert pdf {workingFilename}")
            filePDF_path = os.path.join(app.config['STORAGE_DIR'], workingFilename)
            name, ext = workingFilename.rsplit(".", 1)
            filenameJPG = f"{name}.jpg"
            fileJPG_path = os.path.join(app.config['STORAGE_DIR'], filenameJPG)
            outputFolder = os.path.join(app.config['STORAGE_DIR'])
            print(f"/home filePDF_path:{filePDF_path}, filenameJPG: {filenameJPG}, fileJPG_path:{fileJPG_path}, outputFolder:{outputFolder}")

            print(f"/home about to convert_from_path with filePDF_path:{filePDF_path} to filenameJPG: {filenameJPG}")
            fileJPG = convert_from_path(filePDF_path, output_folder= outputFolder, fmt="jpeg")
            generated_files = [os.path.join(outputFolder, f) for f in os.listdir(outputFolder) if f.endswith(".jpg")]

            print(f"Just converted with fileJPG:{fileJPG}, {dir(fileJPG)}, genfiles:{generated_files}")
            fileJPG[0].save(fileJPG_path)
            workingFilename = filenameJPG
            # store filepath/name in Replit DB (or lose track of it)
            db[workingFilename] = fileJPG_path
            print(f"Stored file path in Replit DB fileJPG_path:{fileJPG_path}")

            # loop thru generated_files, adding DB ref where it does not exist
            existing_files = set(db.keys()) 
            for filename in generated_files:
                fileJPG_path = os.path.join(outputFolder, filename)

                if filename not in existing_files:  # ✅ Check if the file is already in Replit DB
                    db[filename] = fileJPG_path  # ✅ Store new file reference
                    print(f"✅ Added {filename} to Replit DB.")
                else:
                    print(f"⚠️ {filename} already exists in Replit DB, skipping.")
        
        loggerPerm.log(f"About to exit /home, with workingFilename:{workingFilename}")
        print(f"About to exit /home, with workingFilename:{workingFilename}, displayFilename:{displayFilename}")
        return render_template("home.html", uploaded=f"File '{displayFilename}' uploaded successfully.", json_data=None)
    return render_template("home.html", uploaded=None, json_data=None)

@app.route("/extract", methods=["POST"])
def extract_booking_data():
    loggerPerm.log("/extract start")
    uploaded_files = os.listdir(app.config['STORAGE_DIR'])
    if not uploaded_files:
        return render_template("home.html", uploaded="No uploaded files found!", json_data=None)

    file_path = os.path.join(app.config['STORAGE_DIR'], str(workingFilename))
    loggerPerm.log(f"/extract Processing file: {workingFilename}, path:{file_path}")
    extracted_data = extract_data_from_image(workingFilename)
    # print(f"/extract extracted_data: {extracted_data}")
    
    # Convert the extracted data to a JSON string. json_data has an odd structure, so
    # extract { ... } part then convert to dict
    json_data = json.dumps(extracted_data, indent=4)
    #print(f"/extract json_data: {json_data}")
    jsonStrConcat = re.search(r'\{.*\}', extracted_data, re.DOTALL)
    #print(f"/extract jsonStrConcat: {jsonStrConcat.group(0)}")
    jsonDict =  json.loads(jsonStrConcat.group(0))
    #print(f"type of jsonDict:{type(jsonDict)}")
    # logger.write_to_log(f"/extract_booking_data for {workingFilename}")
    return render_template("home.html", uploaded=f"File '{workingFilename}' uploaded successfully!", json_data=jsonDict)

@app.route("/scoreResult" , methods=["POST"])
def scoreResult():
    score = request.form.get("score")
    loggerPerm.log(f"/scoreResult for {workingFilename} score {score}")
    return render_template("home.html", user_score = score )

## don't use this, use downloadToLocal
@app.route("/download/<filename>")
def download_file(filename):
    # Serve the file from the 'templates' directory
    return send_from_directory(directory="templates", path=filename, as_attachment=True)

@app.route("/files", methods=["GET"])
def list_files():
    """List all uploaded files."""
    stored_files = list(db.keys())  # ✅ Retrieve file references from Replit DB
    return jsonify({"stored_files": stored_files})

@app.route("/downloadToLocal/<filename>")
def downloadToLocal(filename):
    """Serve uploaded files for download."""
    print(f"downloadToLocal called using STORAGE_DIR:{STORAGE_DIR}, filename:{filename}")
    if filename in db:
        # return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)
        # return send_from_directory(STORAGE_DIR, filename, as_attachment=True)
        db_file_path = db.get(filename)
        print(f"downloadToLocal db_file_path:{db_file_path}")
        if db_file_path and os.path.exists(db_file_path):
            return send_file(db_file_path, as_attachment=True)
        else:
            return abort(404, "❌ File not found in storage matey1")
            
    return "❌ File not found matey2", 404

# needs to be called by curl
# eg curl -X DELETE "https://tangobookingform.replit.app/delete/test225020511551561.jpg"
@app.route("/delete/<filename>", methods=["DELETE"])
def delete_file(filename):
    """Delete a file from storage and remove its reference in Replit DB."""
    if filename in db:
        file_path = db[filename]

        # ✅ Check if file exists before deleting
        if os.path.exists(file_path):
            print(f"about to remove:{file_path}")
            os.remove(file_path)  # ✅ Delete the file
            del db[filename]  # ✅ Remove reference from Replit DB
            return jsonify({"message": f"✅ {filename} deleted successfully!"})
        else:
            del db[filename]  # ✅ Remove stale entry from DB
            return jsonify({"error": "❌ File not found on disk, reference removed from DB"}), 404
    else:
        print(f"unable to remove:{filename}")
        return jsonify({"error": "❌ File not found in database"}), 404

@app.route("/tmpDownload/<filename>")
def tmpDownload(filename):
    """Serve a file from /tmp/ for download."""
    file_path = os.path.join(TMP_DIR, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({"error": "❌ File not found in /tmp/"}), 404

# needs to be called via curl
# eg curl -X DELETE "https://tangobookingform.replit.app/tmp-delete/log.txt
@app.route("/tmp-delete/<filename>", methods=["DELETE"])
def delete_tmp_file(filename):
    """Delete a file from /tmp/."""
    file_path = os.path.join(TMP_DIR, filename)

    if os.path.exists(file_path):
        os.remove(file_path)  # ✅ Delete the file
        return jsonify({"message": f"✅ {filename} deleted from /tmp/!"})
    else:
        return jsonify({"error": "❌ File not found in /tmp/"}), 404

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000)
