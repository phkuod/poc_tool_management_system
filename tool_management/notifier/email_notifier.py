import smtplib
from email.mime.text import MIMEText
from collections import defaultdict
import os

def send_notifications(failures):
    """
    Sends email notifications for the given failures.

    Args:
        failures (list): A list of failure dictionaries.
    """
    grouped_failures = defaultdict(list)
    for failure in failures:
        grouped_failures[failure["Responsible User"]].append(failure)

    for user, user_failures in grouped_failures.items():
        send_email(user, user_failures)

def send_email(user, failures):
    """
    Sends a single email with all the failures for a given user.

    Args:
        user (str): The email address of the user.
        failures (list): A list of failure dictionaries for the user.
    """
    sender_email = os.environ.get("SENDER_EMAIL")
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = os.environ.get("SMTP_PORT")
    
    if not all([sender_email, smtp_server, smtp_port]):
        print("Email configuration is missing. Skipping email notification.")
        return

    subject = "Outsourcing QC Failures"
    body = "The following outsourcing QC checks have failed:\n\n"
    for failure in failures:
        body += f"- Tool: {failure['Tool_Number']}, Project: {failure['Project']}, Reason: {failure['Fail Reason']}\n"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = user

    with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
        server.send_message(msg)
    
    print(f"Email sent to {user}")