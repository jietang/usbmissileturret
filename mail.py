import smtplib

from email.mime.text import MIMEText

import random

PORTAL_TURRET_SAYINGS = [
    "Are you still there?",
    "Get mad!",
    "Hello!",
    "Target acquired.",
    "Dispensing product.",
    "Firing.",
    "Hello, friend",
    "Gotcha!",
    "There you are!" ,
    "I see you!",
    "Could you come over here?",
    "Coming through!",
    "Excuse me!",
    "Sorry!",
    "My fault!",
    "Preparing to dispense product.",
    "Activated!",
    "There you are.",
    "Who's there?",
    "Sorry, we're closed.",
    "I don't blame you.",
    "I don't hate you.",
    "No hard feelings.",
    "Who are you?",
    "But I need to protect the humans!",
    "Goodbye.",
    "Your business is appreciated.",
    "Good night.",
    "Can I help you?",
    "Wheee!",
    "Come closer!",
    "What are you doing?",
    "Ow!",
    "I'm on fire.",
    "You've made your point.",
    "This is not good.",
    "Well done!",
    "You have excellent aim!",
    "I never liked her.",
    "These things happen.",
    "That was nobody's fault.",
    "She was provoking you.",
    "I blame myself.",
    "I probably deserved it.",
    "I saw it... it was an accident!",
    "She's probably ok.",
]

def send_mail_with_link(link=None):
    me = 'jie@dropbox.com'
    to = 'dropbox-turret@dropbox.com'
    random.shuffle(PORTAL_TURRET_SAYINGS)

    body = []
    body.append(PORTAL_TURRET_SAYINGS[0])
    if link:
        body.append(link)
    body.append('Love')
    body.append('Turret')

    msg = MIMEText('\n\n'.join(body))
    msg['Subject'] = PORTAL_TURRET_SAYINGS[1]
    msg['From'] = me
    msg['To'] = to
    s = smtplib.SMTP('localhost')
    s.sendmail(me, [to], msg.as_string())
    s.quit()

if __name__ == "__main__":
    send_mail()
