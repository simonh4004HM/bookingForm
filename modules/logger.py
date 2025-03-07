import os
import json
import pdb
import datetime

## Had to install this locally in shell using 'pip install openai'
import openai
import requests

import gspread
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials

# print("logger.py loaded")

class GoogleLog:
    ## Note self.data has blank entries and voicemail entries
    def __init__(self,sheetName="logs",tabName="test"):
        
        scope = [
          "https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"
        ]

        googleCredentials = os.getenv("GOOGLE_ACCESS")
        if not googleCredentials:
          raise ValueError("GOOGLE_ACCESS is not set in Replit Secrets!")

        credentials_dict = json.loads(googleCredentials)
        credentials = Credentials.from_service_account_info(credentials_dict, scopes=scope)
        self.client = gspread.authorize(credentials)
        sheet = self.client.open(sheetName)

        bookingFormSheet = sheet.worksheet(tabName)
        self.bookingFormSheet = bookingFormSheet; self.sheetName = sheetName; self.tabName = tabName
        self.data = bookingFormSheet.get_all_records()
        # print(f"googleAccess.init.self.data:{self.data}")

        # available_tabs = [ws.title for ws in sheet.worksheets()]
        # print(f"Available tabs: {available_tabs}")
        # bookingFormSheet.update(range_name="A1:B2", values=[[1, 2], ["three", 4]])

    def log(self, message, sheetName="logs", tabName="test"):
        logSheet = self.client.open(sheetName).worksheet(tabName)
        logSheet.append_row([datetime.datetime.now().strftime("%Y-%m-%d.%H:%M:%S"), message])

    def getAllRows(self, sheetName="logs", tabName="test"):
        logSheet = self.client.open(sheetName).worksheet(tabName)
        allRows = logSheet.get_all_records()
        return allRows

# =========
    
class LoggerPerm:
    def __init__(self):
        # ✅ Get Replit's writable log path
        self.log_file = os.getenv("PERMANENT_LOG_PATH")

        # 🚨 Handle missing PERMANENT_LOG_PATH (Replit might not set it)
        if not self.log_file:
            raise ValueError("❌ PERMANENT_LOG_PATH is not set! Add it in Replit Secrets.")

        # ✅ Ensure the directory exists (Replit provides a writable path)
        log_dir = os.path.dirname(self.log_file)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)  # Create only if it's missing

    def log(self, message):
        """Write a log message to the persistent log file."""
        try:
            with open(self.log_file, "a") as log:
                log.write(message + "\n")
            print(f" Log written to {self.log_file}: {message}")
        except OSError as e:
            print(f"❌ Failed to write to log file: {e}")

        print(f"✅ Log written to: {self.log_file}")



class PaperLog:

    def __init__(self):
        print("PaperLog init")
        PAPERTRAIL_HOST = "logs4.papertrailapp.com"
        PAPERTRAIL_PORT = 51480

        try:
            with socket.create_connection((PAPERTRAIL_HOST, PAPERTRAIL_PORT), timeout=5) as sock:
                print("✅ Successfully connected to Papertrail via TCP!")
        except Exception as e:
            print(f"❌ Failed to connect to Papertrail: {e}")

        log_message = "<22> Test log from Replit using TCP\n"

        try:
            sock = socket.create_connection((PAPERTRAIL_HOST, PAPERTRAIL_PORT))
            sock.sendall(log_message.encode("utf-8"))
            sock.close()
            print("✅ Log sent successfully via raw TCP!")
        except Exception as e:
            print(f"❌ Failed to send log: {e}")
        
        # Configure the logger
        logger = logging.getLogger("PapertrailLogger")
        logger.setLevel(logging.INFO)  # Set log level (INFO, WARNING, ERROR, DEBUG)

        # Create a SysLogHandler for UDP
        syslog_handler = logging.handlers.SysLogHandler(address=(PAPERTRAIL_HOST, PAPERTRAIL_PORT), socktype=socket.SOCK_DGRAM)

        # Format log messages
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        syslog_handler.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(syslog_handler)

        # Send log messages
        logger.info("Test log: call from playPython/callPapertrail.py")
        print("End paperLog init")

    
    def writePapertrailLog(self, message):
        # logger = logging.getLogger("PapertrailLogger")
        print("Called writePapertrailLog with {message}")
        # paperLogger.info(message)

class Logger:
    """
    Logger class to write log entries to a file with timestamp, severity, and message.
    Ensures that the logs directory and log file exist before writing.
    """
    LOG_DIR = "logs"
    LOG_FILE = os.path.join(LOG_DIR, "log.txt")

    def __init__(self):
        # Ensure the logs directory exists
        os.makedirs(self.LOG_DIR, exist_ok=True)

        # Ensure the log file exists
        if not os.path.isfile(self.LOG_FILE):
            with open(self.LOG_FILE, "w", encoding="utf-8") as log_file:
                log_file.write("Log File Created: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")

    def write_to_log(self, message, severity="Info"):
        """
        Write a log entry to the log file.

        :param message: The log message (mandatory).
        :param severity: The severity level ('Info', 'Warning', or 'Error'). Default is 'Info'.
        """
        if severity not in ["Info", "Warning", "Error"]:
            severity = "Info"  # Default if an invalid severity is given

        # Generate timestamp
        timestamp = datetime.datetime.now().strftime("%Y%b%d-%H:%M")  # e.g., "2025Jan29-15:07"

        # Format log entry
        log_entry = f"{timestamp} {severity}: {message}\n"

        # Write to file
        with open(self.LOG_FILE, "a", encoding="utf-8") as log_file:
            log_file.write(log_entry)

        return log_entry  # Useful for debugging or returning response in Flask

# Example Usage
#if __name__ == "__main__":
#    logger.write_to_log("Process started")  # Defaults to Info
#    logger.write_to_log("Missing data detected", "Warning")
#    logger = Logger()
#    logger.write_to_log("Critical failure occurred", "Error")
