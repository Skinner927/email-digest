# Builds emails to be sent through the gmail api
# Derived from:
# https://developers.google.com/gmail/api/v1/reference/users/messages/send#try-it

import base64
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import mimetypes
import os

from apiclient import errors


def _safe_to(to):
    try:
        return ', '.join(to)
    except TypeError:
        return str(to)


def send_message(service, user_id, message):
    """Send an email message.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      message: Message to be sent.

    Returns:
      Sent Message. or None on error
    """

    # Google's example did not use urlsafe_b64encode when creating messages.
    # This hack originally fixed it but I've since modified everything here to
    # use urlsafe_b64encode, but I'm going to keep this just in case.
    # cleanup message: http://stackoverflow.com/a/26720528/721519
    if 'raw' in message:
        message_raw = message.get('raw', '')
        message_raw = message_raw.replace('+', '-').replace('/', '_').strip('=')
        message['raw'] = message_raw

    try:
        message = (service.users().messages().send(userId=user_id, body=message)
                   .execute())
        return message
    except errors.HttpError, error:
        print 'An error occurred: %s' % error
        return None


def create_message(sender, to, subject, message_text):
    """Create a message for an email.

    Args:
      sender: Email address of the sender.
      to: Email address of the receiver.
      subject: The subject of the email message.
      message_text: The text of the email message.

    Returns:
      An object containing a base64 encoded email object.
    """
    message = MIMEText(message_text)
    message['to'] = _safe_to(to)
    message['from'] = sender
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_string())}


def create_html_message(sender, to, subject, message_html, plaintext=None):
    """
    Creates a html body
    Args:
        sender:
        to:
        subject:
        message_html: HTML email content
        plaintext: Optional plaintext of the same html

    Returns:
        An object containing a base64 encoded email object.
    """
    message = MIMEMultipart('alternative')
    message['to'] = _safe_to(to)
    message['from'] = sender
    message['subject'] = subject

    if plaintext is not None:
        message.attach(MIMEText(plaintext))

    message.attach(MIMEText(message_html, 'html'))

    return {'raw': base64.urlsafe_b64encode(message.as_string())}


def CreateMessageWithAttachment(sender, to, subject, message_text, file_dir,
                                filename):
    """Create a message for an email.

    Args:
      sender: Email address of the sender.
      to: Email address of the receiver.
      subject: The subject of the email message.
      message_text: The text of the email message.
      file_dir: The directory containing the file to be attached.
      filename: The name of the file to be attached.

    Returns:
      An object containing a base64 encoded email object.
    """
    message = MIMEMultipart()
    message['to'] = _safe_to(to)
    message['from'] = sender
    message['subject'] = subject

    msg = MIMEText(message_text)
    message.attach(msg)

    path = os.path.join(file_dir, filename)
    content_type, encoding = mimetypes.guess_type(path)

    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    main_type, sub_type = content_type.split('/', 1)
    if main_type == 'text':
        fp = open(path, 'rb')
        msg = MIMEText(fp.read(), _subtype=sub_type)
        fp.close()
    elif main_type == 'image':
        fp = open(path, 'rb')
        msg = MIMEImage(fp.read(), _subtype=sub_type)
        fp.close()
    elif main_type == 'audio':
        fp = open(path, 'rb')
        msg = MIMEAudio(fp.read(), _subtype=sub_type)
        fp.close()
    else:
        fp = open(path, 'rb')
        msg = MIMEBase(main_type, sub_type)
        msg.set_payload(fp.read())
        fp.close()

    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    message.attach(msg)

    return {'raw': base64.urlsafe_b64encode(message.as_string())}
