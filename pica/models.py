from django.core.validators import FileExtensionValidator
from django.db import models
from django.contrib.auth.models import User
from users.models import Department, Profile
import uuid

ext_validators = FileExtensionValidator(['pdf'])


class Company(models.Model):
    CHOICE_TYPE_COMPANY = [
        ('HC', 'Holding Company'),
        ('OW', 'Mining Owner'),
        ('TR', 'Coal Trading'),
        ('CR', 'Mining Contractor'),
        ('OT', 'Others')
    ]
    CHOICE_YES_NO = [
        ('Y', 'Active'),
        ('N', 'Not Active'),
    ]
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    name = models.CharField(max_length=100, null=True, blank=True)
    short_code = models.CharField(max_length=5, null=True, blank=True)
    logo = models.ImageField(upload_to='logo/', null=True, blank=True)
    status_active = models.CharField(max_length=1, choices=CHOICE_YES_NO)
    company_type = models.CharField(max_length=2, choices=CHOICE_TYPE_COMPANY)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        self.logo.delete()
        super().delete(*args, **kwargs)


class Forum(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    forum_name = models.CharField(max_length=50)
    description = models.CharField(max_length=100, blank=True, null=True)
    forum2user = models.ManyToManyField(User, related_name='user2forum')
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.forum_name


class Workflow(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    position = models.CharField(max_length=50, blank=True, null=True)
    sequence_no = models.IntegerField(blank=True, null=True)
    bod_name = models.CharField(max_length=100, blank=True, null=True)
    workflow2user = models.ManyToManyField(User,
                                           related_name='user2workflow')
    workflow2forum = models.ForeignKey(Forum, on_delete=models.CASCADE, blank=True, null=True,
                                       related_name='forum2workflow')
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.workflow2forum.forum_name


class Meeting(models.Model):
    CHOICE_CHECKED = [
        ('Y', 'Checked'),
        ('N', 'Not Checked'),
    ]
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    meeting_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    notulen = models.CharField(max_length=100, null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    ref_no = models.CharField(max_length=50, blank=True, null=True)
    meeting2forum = models.ForeignKey(Forum, on_delete=models.CASCADE, related_name="forum2meeting",
                                      blank=True, null=True,
                                      verbose_name="Forum")
    meeting2user = models.ManyToManyField(User, related_name='user2meeting',
                                          verbose_name="Peserta Internal")
    cpmd_checked = models.CharField(max_length=1, default="N", choices=CHOICE_CHECKED)
    complete_approval = models.CharField(max_length=1, default="N")
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Meeting {self.meeting2forum.forum_name}, {self.meeting_date}"


class Outside(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    fullname = models.CharField(max_length=100)
    email = models.EmailField(null=True, blank=True)
    company_from = models.CharField(max_length=100, null=True, blank=True)
    mobile = models.CharField(max_length=20, null=True, blank=True)
    outside2meeting = models.ManyToManyField(Meeting, verbose_name="Meeting",
                                             related_name="meeting2outside", blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.fullname


class Topic(models.Model):
    CHOICE_STATUS = [
        ('O', 'Open'),
        ('P', 'Progress'),
        ('C', 'Closed'),
        ('H', 'Hold')
    ]
    CHOICE_CATEGORY = [
        ('FU', 'Follow Up'),
        ('PJ', 'Project'),
        ('PL', 'Policy'),
        ('NT', 'Notes')
    ]
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    topic_name = models.CharField(max_length=100, null=True, blank=True)
    problem_info = models.TextField(blank=True, null=True)
    action = models.TextField(null=True, blank=True)
    due_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=1, choices=CHOICE_STATUS, default="O")
    category = models.CharField(max_length=2, choices=CHOICE_CATEGORY, default="FU")
    to_ref_no = models.CharField(max_length=50, blank=True, null=True, default='yyyy.mm.dd-BOD xxx')
    topic2department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name="Department",
                                         related_name="department2topic")
    topic2meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, verbose_name="Meeting",
                                      related_name="meeting2topic")
    topic2company = models.ForeignKey(Company, on_delete=models.CASCADE, blank=True, null=True,
                                      related_name="company2topic", verbose_name="Problem owner")
    topic2user = models.ForeignKey(User, verbose_name="PIC Inputter", related_name="user2topic",
                                   on_delete=models.SET_NULL,
                                   blank=True, null=True)
    topic2incharge = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='incharge2topic',
                                       verbose_name="PIC PICA", blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.topic_name


class Activity(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    activity_date = models.DateField(blank=True, null=True)
    action_description = models.TextField(null=True, blank=True)
    activity2topic = models.ForeignKey(Topic, on_delete=models.CASCADE, verbose_name="Related Topic",
                                       related_name="topic2activity")
    activity2user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Updated by",
                                      related_name="user2activity")
    having_attachments = models.CharField(max_length=1, default="N")
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.activity2user.username} - {self.activity_date}"


class Docimg(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    docimg2activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='activity2docimg')
    doc_image = models.ImageField(upload_to='activity/docimg/%Y/%m/%d/', blank=True, null=True)
    nama_file = models.CharField(max_length=100, blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.doc_image.name

    def delete(self, *args, **kwargs):
        self.doc_image.delete()
        super().delete(*args, **kwargs)


class Docpdf(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    docpdf2activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='activity2docpdf')
    doc_pdf = models.FileField(upload_to='activity/docpdf/%Y/%m/%d/', blank=True, null=True)
    nama_file = models.CharField(max_length=100, blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.doc_pdf.name

    def delete(self, *args, **kwargs):
        self.doc_pdf.delete()
        super().delete(*args, **kwargs)


class Approval(models.Model):
    CHOICE_EDITABLE = [
        ('Y', 'Editable'),
        ('N', 'Not Editable'),
    ]
    CHOICE_APPROVED = [
        ('Y', 'Approved'),
        ('N', 'Not Approved'),
    ]
    CHOICE_PRESENT = [
        ('P', 'Present'),
        ('N', 'Not Present'),
    ]
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    approval2meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, blank=True, null=True,
                                         related_name='meeting2approval')
    approval2user = models.ManyToManyField(User, verbose_name="BOD Approval", related_name='user2approval')
    bod_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    editable = models.CharField(max_length=1, default="N", choices=CHOICE_EDITABLE)
    present = models.CharField(max_length=1, default="N", choices=CHOICE_PRESENT)
    sequence_no = models.IntegerField()
    approved = models.CharField(max_length=1, default='N', choices=CHOICE_APPROVED)
    token_code = models.CharField(max_length=20, blank=True, null=True)
    date_approved = models.DateTimeField(auto_now=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bod_name} - {self.editable} - {self.approved}"


class Lampiran(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    lampiran2meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='meeting2lampiran')
    lampir = models.FileField(upload_to='lampiran/%Y/%m/%d', blank=True, null=True)
    nama_file = models.CharField(max_length=100, blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def delete(self, *args, **kwargs):
        self.lampir.delete()
        super().delete(*args, **kwargs)
