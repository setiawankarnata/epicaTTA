from celery import shared_task
from .models import Approval, Meeting, Topic, Approval, Lampiran, Forum, Profile
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.core.mail import EmailMessage, send_mail
from django.conf import settings
import datetime as dt
import requests


@shared_task()
def send_email_notif(id, link):
    meeting = Meeting.objects.get(id=id)
    topics = Topic.objects.filter(topic2meeting=meeting)
    email_subject = "Notification from ePica System (New PICA)"
    list_pic = []
    for topic in topics:
        pic_inputter = User.objects.filter(user2topic=topic).first()
        pic_pica = User.objects.filter(incharge2topic=topic).first()
        if pic_inputter:
            if pic_inputter not in list_pic:
                list_pic.append(pic_inputter)
        if pic_pica:
            if pic_pica not in list_pic:
                list_pic.append(pic_pica)
    for pic in list_pic:
        topics = Topic.objects.filter(topic2meeting=meeting)
        topics_pic = []
        for topic in topics:
            if topic.topic2user == pic or topic.topic2incharge == pic:
                topics_pic.append(topic)

        # Send email to all inputters
        email_recipient = pic.email
        context = {
            'meeting': meeting,
            'flag_inputter': True,
            'topics': topics_pic,
            'pic': pic,
            'link': link,
        }
        html_message = render_to_string('pica/email_notif.html', context)
        email = EmailMessage(
            subject=email_subject,
            body=html_message,
            from_email=settings.EMAIL_HOST_USER,
            to=[email_recipient],
        )
        email.content_subtype = "html"
        email.send(fail_silently=False)
    return None


@shared_task(bind=True)
def send_activity_duedate_notifications(self):
    topics = Topic.objects.filter(status__in=['O', 'P'])
    hari_ini = dt.date.today()
    h_plus_one = dt.timedelta(days=1)
    h_plus_six = dt.timedelta(days=6)
    notif_topics = []
    notif_users = []
    for topic in topics:
        due = topic.due_date
        if due == hari_ini + h_plus_one:
            notif_topics.append(topic)
            continue
        if due + h_plus_six == hari_ini:
            notif_topics.append(topic)
            continue
    for topic in notif_topics:
        if topic.topic2user not in notif_users:
            notif_users.append(topic.topic2user)
    email_subject = "Notification from ePica System (Reminder)"
    for notif_user in notif_users:
        topics = []
        for notif_topic in notif_topics:
            if notif_topic.topic2user == notif_user:
                topics.append(notif_topic)
                continue
        context = {
            'topics': topics,
        }
        email_recipient = notif_user.email
        html_message = render_to_string('pica/email_notif_pic_inputter.html', context)
        email = EmailMessage(
            subject=email_subject,
            body=html_message,
            from_email=settings.EMAIL_HOST_USER,
            to=[email_recipient],
        )
        email.content_subtype = "html"
        email.send(fail_silently=False)
    return None


@shared_task()
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
