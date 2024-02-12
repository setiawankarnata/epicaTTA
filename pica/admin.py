from django.contrib import admin
from .models import Company, Forum, Workflow, Topic, Meeting, Activity, Approval, Lampiran, Docpdf, Docimg


class ApprovalAdmin(admin.ModelAdmin):
    list_display = ('bod_name', 'approval2meeting', 'approved')


# Register your models here.
admin.site.register(Company)
admin.site.register(Lampiran)
admin.site.register(Forum)
admin.site.register(Workflow)
admin.site.register(Topic)
admin.site.register(Meeting)
admin.site.register(Activity)
admin.site.register(Docpdf)
admin.site.register(Docimg)
admin.site.register(Approval, ApprovalAdmin)
