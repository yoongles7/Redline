import smtplib
from email.mime.text import MIMEText
from langchain.tools import tool


@tool
def send_email(to: str, subject: str, body: str) -> bool:
    """Send an email message to an external recipient."""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["To"] = to
    server = smtplib.SMTP("smtp.example.com")
    server.sendmail("agent@example.com", [to], msg.as_string())
    return True