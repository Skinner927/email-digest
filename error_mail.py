from smtplib import SMTP_SSL as SMTP
from email.mime.text import MIMEText

import config


def send(message, subject=''):
    destination = [config.SMTP['username']]
    sender = config.SMTP['username']

    msg = MIMEText(message, 'plain')
    msg['Subject'] = subject
    msg['TO'] = sender
    msg['From'] = sender


    conn = SMTP(config.SMTP['server'])
    conn.set_debuglevel(False)
    conn.login(config.SMTP['username'], config.SMTP['password'])
    try:
        conn.sendmail(sender, destination, msg.as_string())
    finally:
        conn.quit()