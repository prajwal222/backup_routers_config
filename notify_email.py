import smtplib

SERVER = "mailhost.corp.equinix.com"
FROM = "prthapa@equinix.com"
TO = ["prthapa@equinix.com", "afsmohammad@equinix.com", "tadas@equinix.com"]  # must be a list

SUBJECT = "Router Backup Failed"


def failed_notify(text):
    # Prepare actual message

    message = f"""From: {FROM}\r\nTo: {", ".join(TO)}\r\nSubject: {SUBJECT}\r\n\

    {text}
    """

    # Send the mail
    server = smtplib.SMTP(SERVER)
    server.sendmail(FROM, TO, message)
    server.quit()
