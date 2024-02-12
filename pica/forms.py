from django import forms
from .models import Company, Forum, Workflow, Meeting, Topic, Department, Outside, Activity
from django.core.exceptions import ValidationError


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ["activity_date", "action_description"]
        exclude = ["activity2topic", "activity2user"]


class UpdateActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ["action_description"]
        exclude = ["activity2topic", "activity2user", "activity_date"]


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ["topic_name", "problem_info", "action", "due_date", "status", "category", "topic2department",
                  "topic2company", "to_ref_no"]
        exclude = ["topic2meeting", "topic2user", "topic2incharge"]


class UpdateTopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ["topic_name", "problem_info", "action", "due_date", "status", "category", "topic2department",
                  "topic2company", "to_ref_no"]
        exclude = ["topic2meeting", "topic2user", "topic2incharge"]


class ReviewTopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ["problem_info", "action", "due_date"]
        exclude = ["topic2meeting", "topic2user", "topic2department", "status", "topic2company",
                   "topic_name"]


class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ["meeting_date", "start_time", "end_time", "notulen", "location", "meeting2forum"]


class UpdateMeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ["meeting_date", "start_time", "end_time", "notulen", "location"]


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ["name", "short_code", "logo", "status_active", "company_type"]


class OutsideForm(forms.ModelForm):
    class Meta:
        model = Outside
        fields = ["fullname", "email", "company_from", "mobile"]


class UpdateCompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ["short_code", "logo", "status_active", "company_type"]


class ForumForm(forms.ModelForm):
    class Meta:
        model = Forum
        fields = ["forum_name", "description"]


class UpdateForumForm(forms.ModelForm):
    class Meta:
        model = Forum
        fields = ["description"]


class WorkflowForm(forms.ModelForm):
    class Meta:
        model = Workflow
        fields = ["position", "workflow2user"]


class EditWorkflowForm(forms.ModelForm):
    class Meta:
        model = Workflow
        fields = ["position", "sequence_no"]


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class UploadFileForm(forms.Form):
    files = MultipleFileField(required=False)

    def clean_files(self):
        """Make sure only pdf can be uploaded."""
        files = self.files.getlist("files")
        for f in files:
            if f.content_type != "application/pdf":
                raise ValidationError('File not supported!')


class UploadAttachmentsForm(forms.Form):
    files1 = MultipleFileField(required=False)
    files2 = MultipleFileField(required=False)

    # def clean_files(self):
    #     # """Make sure only pdf can be uploaded."""
    #     files1 = self.files.getlist("files1")
    #     for f in files1:
    #         if f.content_type != "application/pdf":
    #             raise ValidationError('File must be in pdf format!')
    #
    #     # """Make sure only image file can be uploaded."""
    #     files2 = self.files.getlist("files2")
    #     for f in files2:
    #         if f.content_type not in ["image/jpeg", "image/jpg", "image/png"]:
    #             raise ValidationError('File must be in jpeg/jpg/png format!')
# class InChargeForm(forms.ModelForm):
#     class Meta:
#         model = InCharge
#         fields = ["full_name", "email"]
