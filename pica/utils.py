from .models import Meeting, Approval, Lampiran, Forum
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.conf import settings
import requests


def send_email_approve(id, html_message, bod, first_attach):
    meeting = Meeting.objects.get(id=id)
    lampirans = Lampiran.objects.filter(lampiran2meeting=meeting)
    approval = Approval.objects.filter(approval2meeting=meeting, editable="Y").order_by('sequence_no').first()
    email_recipient = approval.email
    forum = Forum.objects.get(forum2meeting=meeting)
    secretaries = User.objects.get(user2profile__secretary="Y", user2forum=forum)
    cpmds = User.objects.filter(user2profile__cpmd="Y", user2forum=forum)
    cc_email_recipient = []
    cc_email_recipient.append(secretaries.email)
    for cpmd in cpmds:
        cc_email_recipient.append(cpmd.email)
    if bod:
        email = EmailMessage(
            subject="Please approve the following MoM",
            body=html_message,
            from_email=settings.EMAIL_HOST_USER,
            to=[email_recipient],
        )
        for lampiran in lampirans:
            response = requests.get(lampiran.lampir.url)
            email.attach(lampiran.lampir.name, response.content, mimetype="application/pdf")
    else:
        email = EmailMessage(
            subject="Status workflow approval BOD",
            body=html_message,
            from_email=settings.EMAIL_HOST_USER,
            to=cc_email_recipient,
        )
        if first_attach:
            for lampiran in lampirans:
                response = requests.get(lampiran.lampir.url)
                email.attach(lampiran.lampir.name, response.content, mimetype="application/pdf")
    email.content_subtype = "html"
    email.send(fail_silently=False)
    return None
