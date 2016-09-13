# This file is indented to be run interactively
# It is used to re-login the user.
from __future__ import print_function

import oauth2client
from oauth2client import client
from oauth2client import tools

import config
from gmail_scopes import SCOPES

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    store = oauth2client.file.Storage(config.STORED_CREDENTIALS_FILE)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(config.CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = config.APPLICATION_NAME
        flags.noauth_local_webserver = True; # Enforce copy paste
        credentials = tools.run_flow(flow, store, flags)
        print('Storing credentials to ' + config.STORED_CREDENTIALS_FILE)
    return credentials  

if __name__ == '__main__':
    creds = get_credentials()
    if creds is not None:
        print('You should be good now, let the cronjob take it from here.')
    else:
        print('Something went wrong, try running this script again.')
