import smtplib
import yaml

email_details = yaml.safe_load(open("./email_info,yaml"))
SERVER = email_details["server"]
FROM = email_details["from"]
TO = email_details["to"]  # must be a list

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


def success_notify(log, testbed):
    # Prepare actual message

    message = f"""From: {FROM}\r\nTo: {", ".join(TO)}\r\nSubject: {SUBJECT}\r\n\
    
    Successfully completed router backup for {testbed}
    {log}
    """

    # Send the mail
    server = smtplib.SMTP(SERVER)
    server.sendmail(FROM, TO, message)
    server.quit()
