import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from utils.constants.environment_keys import EnvironmentKeys
from utils.environment.environment_manager import EnvironmentManager
from utils.logger.logger import logger


class EmailMissingKeysException(Exception):
    pass


class NotificationMessage:
    message: str
    subject: str

    def __init__(self, message: str, subject: str):
        self.message = message
        self.subject = subject


class OTPNotification(NotificationMessage):
    otp_code: str

    def __init__(self, message: str, subject: str, otp_code: str):
        super().__init__(message, subject)
        self.otp_code = otp_code


def send_email_notification(notification_identifier: str, data: OTPNotification):
    env_map = EnvironmentManager()
    if env_map.get_key(EnvironmentKeys.EMAIL.value) is None or env_map.get_key(
            EnvironmentKeys.EMAIL_PASSWORD.value) is None:
        logger.error("Email or password keys in environment are missing or are named wrongly")
        raise EmailMissingKeysException("Email server cannot be initialized")
    message = MIMEMultipart()
    message["To"] = notification_identifier
    message["From"] = env_map.get_key(EnvironmentKeys.EMAIL.value)
    message["Subject"] = 'Password Reset'
    title = '<h2> Your OTP Code </h2>'
    message_text = MIMEText(''' 
          <main> 
            <div>
              ''' + data.message + '''
            </div>
            <div>
              ''' + data.otp_code + '''
            </div>
          </main> 
       ''', 'html')
    message.attach(MIMEText(title, 'html'))
    message.attach(message_text)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
        smtp_server.login(
            env_map.get_key(EnvironmentKeys.EMAIL.value),
            env_map.get_key(EnvironmentKeys.EMAIL_PASSWORD.value)
        )
        smtp_server.sendmail(
            env_map.get_key(EnvironmentKeys.EMAIL.value),
            notification_identifier,
            message.as_string()
        )
    logger.info("Message sent!")
