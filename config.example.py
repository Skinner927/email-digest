CLIENT_SECRET_FILE = 'client_secret.json'
STORED_CREDENTIALS_FILE = '.stored_credentials.json'
APPLICATION_NAME = 'Email Digest'

DIGEST_LABLES = ['Code Review']

# Who are we to send the digest to
SEND_DIGEST_TO = ['foo@email.com']
# Set to true to mark digested thread as read
MARK_DIGESTED_THREADS_AS_READ = True
# Set to true to archive digested threads
ARCHIVE_DIGESTED_THREADS = True

# Used to send error emails & authentication links.
# You don't technically need this.
SMTP = {
    'server': 'smtp.gmail.com',
    'port': 587,
    'username': 'foo@email.com',
    'password': 'aasdasvasdf'
}
