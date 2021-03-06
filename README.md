# Gmail Email Digester

We all know email digests from email lists. Changing a digest to once per day or 
per hour can really help keep an inbox tidy. But what about when you have tons 
of the same emails coming in and you have no ability to rate limit them?

This script is the answer.

## Setup

Create a filter for the messages you want to digest and assign a label to these 
messages. You should probably set them to skip the inbox but don't mark them as 
read.

Now new mails will come in, skip the inbox but still have the label attached to 
them. 

Next, clone this repo somewhere you can create a cron job or some other way of 
running a script at certain times of day. I like to have mine run every hour.  

```
0 * * * * /path/to/run.py
```

Or if you're using virtualenv:

```
0 * * * * /path/to/virtual/bin/python /path/to/run.py
```

Next step is to configure 

## Configuration

You will need to create an OAuth Client ID with Google's API and also configure 
the application locally.

### OAuth Client ID

Head over to [Google's API Manager](https://console.developers.google.com). You 
will want to create a new project, this is at the very top of the page. 

Once a project is created, head over to the "Credentials" tab. Here, create a 
new "OAuth client ID". Application type will be "other". Click "OK" on the modal 
that pops up with the secrets, don't bother noting them down. You should now 
see your new OAuth client ID listed in the table on this page. 

Click the download button at the far right of the row and save this file as 
`client_secret.json` and place it in the directory where you cloned the repo.

### Application Config

Copy `config.example.py` to `config.py`.

Open this file and you will find defaults and hopefully a description of what 
each setting does. Configure them to your liking and perform the initial oauth 
login.

`DIGEST_LABELS` is the magic here. In this list, add the human-readable labels 
you want to digest.

Ensure you put your email in `SEND_DIGEST_TO` or you won't get any 
notifications.

`SMTP` configuration is only for sending authentication errors. Basically, if 
for some reason your cached oauth login fails you will need to re-authenticate. 
Configure a SMTP server that will email the `username` email of the issue.

Config is now set up. Ensure you give this script access to your account with 
`login.py`.

Run `python login.py` to perform the login. This should present you with a link 
to open in a web browser, once visited, allow the app access to your account and 
copy the resulting code back into the login script. You can run `login.py` again 
to verify everything works.

Once you've done this, you're completely set up and the digets should work.

You may run `run.py` manually to test.


# License

Do whatever you want. Sell this; make millions. 
