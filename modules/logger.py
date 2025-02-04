import os
import datetime

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
