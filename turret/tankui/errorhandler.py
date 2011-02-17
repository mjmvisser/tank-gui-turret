from PyQt4 import QtGui
import sys, traceback, os
from email.mime.text import MIMEText
from smtplib import SMTP
import socket

email = None

def excepthook(etype, value, tb):
    """
    Global function to catch unhandled exceptions.

    :param etype: exception type
    :param value: exception value
    :param tb: traceback object
    """

    notice = "An unhandled exception has occurred."
    if email is not None:
        notice += " An e-mail has been sent to %s." % email

    error_msg = ''.join(traceback.format_exception(etype, value, tb))

    print error_msg

    if email is not None:
        msg = MIMEText(error_msg)
        msg["Subject"] = "Error traceback"
        msg.set_payload(error_msg)

        author = os.environ["USER"]
        domainname = socket.getfqdn()

        s = SMTP("localhost")
        s.sendmail(author + "@" + domainname, [email], msg.as_string())

    errorbox = QtGui.QMessageBox()
    errorbox.setText('\n\n'.join((notice, error_msg)))
    errorbox.exec_()

sys.excepthook = excepthook
