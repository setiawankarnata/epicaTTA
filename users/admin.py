from django.contrib import admin
from .models import Profile, Department
from django import forms

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'bod', 'cpmd', 'secretary', 'pic', 'pic_epica')
    search_fields = ('full_name',)
    list_filter = ('bod', 'cpmd', 'secretary', 'pic', 'pic_epica')

# Register your models here.
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Department)


class CsvImportForm(forms.Form):
    csv_upload = forms.FileField()
