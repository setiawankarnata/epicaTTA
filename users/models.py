import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.dispatch import receiver
from django.db.models.signals import post_save


class Department(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    name = models.CharField(max_length=100, blank=True, null=True, unique=True)
    description = models.CharField(max_length=100, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.name == "" or self.name is None:
            raise ValidationError(_("Name of department must be filled!"), code="invalid_name")

        if self.description == "" or self.description is None:
            raise ValidationError(_("Description of department must be filled!"), code="invalid_description")

    def __str__(self):
        return self.name


class Profile(models.Model):
    GENDER = [
        ('M', 'Male'),
        ('F', 'Female')
    ]
    BOD = [
        ('Y', 'Yes'),
        ('N', 'No')
    ]
    CPMD = [
        ('Y', 'Yes'),
        ('N', 'No')
    ]
    SECRETARY = [
        ('Y', 'Yes'),
        ('N', 'No')
    ]
    PIC = [
        ('Y', 'Yes'),
        ('N', 'No')
    ]
    PIC_EPICA = [
        ('Y', 'Yes'),
        ('N', 'No')
    ]
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    profile2user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True,
                                        related_name='user2profile')
    gender = models.CharField(max_length=1, choices=GENDER, blank=True, null=True)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    photo = models.ImageField(upload_to='photo_profile/', blank=True, null=True, default='user.png')
    bod = models.CharField(max_length=1, choices=BOD, blank=True, null=True)
    cpmd = models.CharField(max_length=1, choices=CPMD, blank=True, null=True, default="N")
    secretary = models.CharField(max_length=1, choices=SECRETARY, blank=True, null=True, default="N")
    pic = models.CharField(max_length=1, choices=PIC, blank=True, null=True, default="N")
    pic_epica = models.CharField(max_length=1, choices=PIC_EPICA, blank=True, null=True, default="N")
    profile2department = models.ForeignKey(Department, on_delete=models.SET_NULL, blank=True, null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    email_atasan = models.EmailField(max_length=100, blank=True, null=True)
    nama_atasan = models.CharField(max_length=100, blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(profile2user=instance)
