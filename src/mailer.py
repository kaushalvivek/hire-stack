import smtplib
import pandas as pd
from jinja2 import Template
from tqdm import tqdm
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.config import EmailConfig

class Mailer:
    def __init__(self):
        self.config = EmailConfig()

    def _get_candidates(self, path):
        df = pd.read_csv(path)
        return df.to_dict(orient='records')
        
    def _send_email(self, receiver_name, receiver_email):
        # Create the email message
        message = MIMEMultipart("alternative")
        message["Subject"] = self.config.subject
        message["From"] = self.config.sender_email
        message["To"] = receiver_email
        template = Template(self.config.body)
        body = template.render(name=receiver_name)
        # Turn the body into a plain MIMEText object
        part = MIMEText(body, "plain")
        message.attach(part)
        # Send the email
        try:
            with smtplib.SMTP(self.config.smtp_server, self.config.port) as server:
                server.starttls()  # Secure the connection
                server.login(self.config.sender_email, self.config.app_password)
                server.sendmail(self.config.sender_email, receiver_email, message.as_string())
        except Exception as e:
            print(f"Error: {e}")

    def trigger(self, path):
        candidates = self._get_candidates(path)
        for candidate in tqdm(candidates):
            self._send_email(candidate["First Name"], candidate["Email address 1"])