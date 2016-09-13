from __future__ import print_function
import httplib2
import datetime
from HTMLParser import HTMLParser
import htmlentitydefs
import time

from apiclient import discovery
import oauth2client
from oauth2client import tools

import config
import error_mail
import gmail_mailer

try:
    import argparse

    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# IPython debugger. call Tracer()() to break when using %run
try:
    from IPython.core.debugger import Tracer
except ImportError:
    pass


class MLStripper(HTMLParser):
    """
    Helper class for stripping HTML tags
    http://stackoverflow.com/a/7778368/721519
    """

    def __init__(self):
        HTMLParser.__init__(self)
        self.result = []

    def handle_data(self, d):
        self.result.append(d.strip(' \t'))

    def handle_charref(self, number):
        codepoint = int(number[1:], 16) if number[0] in (u'x', u'X') else int(
            number)
        self.result.append(unichr(codepoint))

    def handle_entityref(self, name):
        codepoint = htmlentitydefs.name2codepoint[name]
        self.result.append(unichr(codepoint))

    def get_text(self):
        return u''.join(self.result)


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential or None if none are stored.
    """
    store = oauth2client.file.Storage(config.STORED_CREDENTIALS_FILE)
    credentials = store.get()
    if not credentials or credentials.invalid:
        return None
    return credentials


def get_service():
    """Shows basic usage of the Gmail API.

    Creates a Gmail API service object and outputs a list of label names
    of the user's Gmail account.
    """
    credentials = get_credentials()
    if credentials is None:
        print('No credentials!')
        error_mail.send(
            'Invalid creds for %s! Use the login.py script to refresh.' % (
                config.APPLICATION_NAME),
            'Email Digest: No credentials')
        print('Error email sent.')
        exit(1)

    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

    return service


def wrap_html_label(val):
    return '<span style="background: #cccccc; border-radius: 4px; ' \
           'padding: 1px 2px; margin-right: 4px;">%s</span>' % val


def main():
    service = get_service()

    # Get labels that we defined as digest labels in config
    lbl_req = service.users().labels().list(userId='me').execute()
    lbls = lbl_req.get('labels', [])
    digest_labels = [l for l in lbls if l['name'] in config.DIGEST_LABELS]
    digest_label_ids = [l['id'] for l in digest_labels]

    if len(digest_label_ids) < 1:
        print('No digest labels.')
        exit(1)

    # get message threads
    threads = []
    resp = {'nextPageToken': None}
    while 'nextPageToken' in resp:
        resp = service.users().threads().list(
            userId='me',
            labelIds=digest_label_ids,
            q='is:unread',
            pageToken=resp['nextPageToken']).execute()

        if 'threads' in resp:
            threads.extend(resp['threads'])

    # Do we have anything to do?
    if len(threads) < 1:
        exit()

    # Create formatted thread objects
    # values will have id, snippet, date, subject
    # A thread here is an email thread.
    formatted_threads = {}

    def thread_batch_handler(request_id, response, exception):
        if exception is None:
            # get the newest message in the thread
            sorted_messages = sorted(
                response['messages'],
                key=lambda m: m['internalDate'])
            last = sorted_messages[0] if sorted_messages else None

            headers = last.get('payload', {}).get('headers', {})

            formatted_threads[request_id] = {
                'id': response['id'],
                'snippet': last['snippet'],
                'labels': [l['name'] for l in digest_labels if l['id'] in
                           last.get('labelIds')],
                'date': next(
                    (h['value'] for h in headers if h['name'] == 'Date'),
                    ''),
                'subject': next(
                    (h['value'] for h in headers if h['name'] == 'Subject'),
                    ''),
            }
        else:
            print(exception)

    # Get thread info via batch call using the handler defined above
    thread_batch = service.new_batch_http_request()
    for t in threads:
        thread_batch.add(
            service.users().threads().get(
                userId='me',
                id=t['id'],
                format='metadata',
                metadataHeaders=['Date', 'Subject']
            ),
            callback=thread_batch_handler
        )
    thread_batch.execute()

    # Debug dump
    # with open('subjects.json', 'w') as f:
    #   f.write(json.dumps(formatted_threads.values(), indent=2))

    # Build the email
    html_open = """\
  <html>
    <head></head>
    <body>
  """
    html_close = """\
    </body>
  </html>
  """

    labels_found = set()
    time_right_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    message_body = '<h2>Digest %s</h2>' % time_right_now
    message_body += '<p>The following labels are in this digest: %s</p>' % \
                    ' '.join(
                        [wrap_html_label(l['name']) for l in digest_labels])
    message_body += '<p>The following emails are in this digest:</p>'
    message_body += '<table style="border-collapse: collapse; width:100%">'

    for t in formatted_threads.values():
        formatted_labels = []
        for l in t['labels']:
            labels_found.add(l)
            formatted_labels.append(wrap_html_label(l))

        formatted_labels = ' '.join(formatted_labels)

        # Link with auth user
        # TODO: https://mail.google.com/mail/?authuser=your.email.address@gmail.com#all/138d85da096d2126
        message_body += """\
      <tr><td style="border: 1px solid black; padding: 5px;">
                                      <!-- ID & subject -->
        <a style="display:block;" href="#inbox/%s">%s</a>
        <!-- labels -->
        <div>%s</div>
        <div>
          <!-- date -->
          <small>%s</small>
        </div>
        <!-- snippet -->
        <p>%s</p>
      </td></tr>
    """ % (t['id'], t['subject'], formatted_labels, t['date'], t['snippet'])

    message_body += '</table>'

    message_body = html_open + message_body + html_close

    # Rip the HTML out of the HTML body
    stripper = MLStripper()
    stripper.feed(message_body)
    plain_body = stripper.get_text()

    # Debug dump email
    # with open('email.html', 'w') as f:
    #     f.write(message_body)

    subject = 'Digest %s for: [%s]' % (time_right_now, ', '.join(labels_found),)

    # Create and send the email
    msg = gmail_mailer.create_html_message('Email Digest',
                                           config.SEND_DIGEST_TO,
                                           subject, message_body,
                                           plain_body)

    result = gmail_mailer.send_message(service, 'me', msg)

    if result is None:
        print('Unknown error sending your email')
        exit(1)

    # Now let's get rid of those pesky emails
    labels_to_remove = set()

    if config.MARK_DIGESTED_THREADS_AS_READ:
        labels_to_remove.add('UNREAD')

    if config.ARCHIVE_DIGESTED_THREADS:
        labels_to_remove.add('INBOX')

    if len(labels_to_remove) < 1:
        # I guess we're done
        exit()

    labels_to_remove = list(labels_to_remove)

    # API tells us to cool our jets so, let's do that
    time.sleep(5) # seconds

    def thread_label_remove_handler(request_id, response, exception):
        if exception is not None:
            print(exception)

    # Remove those labels
    thread_batch = service.new_batch_http_request()
    for t in threads:
        thread_batch.add(
            service.users().threads().modify(
                userId='me',
                id=t['id'],
                body={
                    'removeLabelIds': labels_to_remove,
                    'addLabelIds': []
                }
            ),
            callback=thread_label_remove_handler
        )
    thread_batch.execute()


if __name__ == '__main__':
    main()
