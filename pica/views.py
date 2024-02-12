from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views import View
from .forms import CompanyForm, ForumForm, UpdateForumForm, UpdateCompanyForm, EditWorkflowForm, MeetingForm, \
    UpdateMeetingForm, TopicForm, UpdateTopicForm, OutsideForm, ActivityForm, UpdateActivityForm, ReviewTopicForm, \
    UploadFileForm, UploadAttachmentsForm
from .models import Company, Forum, Workflow, Meeting, Topic, Outside, Activity, Approval, Department, Lampiran, Docpdf, \
    Docimg
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.postgres.search import SearchQuery, SearchVector
from django.http import HttpResponse, Http404
from weasyprint import HTML
import tempfile, random
from django.conf import settings
from datetime import date
from .tasks import send_email_notif, send_email_approve
from django.contrib.sites.shortcuts import get_current_site
from openpyxl.workbook import Workbook
from openpyxl.styles import Font


def create_pdf(request, id):
    meeting = Meeting.objects.get(id=id)
    topics = Topic.objects.filter(topic2meeting=meeting)
    participants = User.objects.filter(user2meeting=meeting)
    forum_name = meeting.meeting2forum.forum_name
    # Setting BOD Signed
    forum = Forum.objects.get(forum2meeting=meeting)
    current_workflow = Workflow.objects.filter(workflow2forum=forum).order_by('sequence_no')
    tahun = meeting.meeting_date.year
    bulan = meeting.meeting_date.month
    tanggal = meeting.meeting_date.day
    format_bulan = str(100 + bulan)[1:]
    dtos = str(tahun) + format_bulan + str(tanggal)
    format_file = dtos + '_TTA_MoM'
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; attachment; filename=' + format_file + '.pdf'
    response['Context-Transfer-Encoding'] = 'binary'
    context = {
        'meeting': meeting,
        'topics': topics,
        'forum_name': forum_name,
        'participants': participants,
        'current_workflow': current_workflow,
    }
    html_string = render_to_string('pica/mom.html', context)
    result = HTML(string=html_string, base_url=request.build_absolute_uri()).render(stylesheets=[
        settings.STATIC_ROOT / 'BS5/css/bootstrap.min.css', ]).write_pdf()

    with tempfile.NamedTemporaryFile(delete=True) as output:
        output.write(result)
        output.flush()
        output = open(output.name, 'rb')
        response.write(output.read())
    return response


def is_valid_queryparam(param):
    return param != '' and param is not None


def search_incharge(request, id, op, tpk):
    meeting = Meeting.objects.get(id=id)
    topic = Topic.objects.get(id=tpk)
    all_users = User.objects.filter(is_superuser=False)
    all_users = all_users.filter(user2profile__bod="N", user2profile__secretary="N", user2profile__cpmd="N")
    user_in_topic = User.objects.filter(user2topic=topic)
    user_in_incharge = User.objects.filter(incharge2topic=topic)
    user_not_in_topic = all_users.exclude(user2topic=topic)
    user_not_in_topic = user_not_in_topic.exclude(incharge2topic=topic)
    q_all = request.GET.get('q_all')
    available_user = user_not_in_topic
    # Filter by Topic Name, Problem Info, Action
    if is_valid_queryparam(q_all):
        vector = SearchVector('first_name', 'last_name')
        query = SearchQuery(q_all)
        available_user = user_not_in_topic.annotate(search=vector).filter(search=query)
    available_user = available_user.order_by('first_name')
    # paginator = Paginator(available_user, 10)
    # page_number = request.GET.get('page')
    # page = paginator.get_page(page_number)
    # page_range = page.paginator.page_range
    context = {
        'available_user': available_user,
        'user_in_topic': user_in_topic,
        'user_in_incharge': user_in_incharge,
        # 'page_range': page_range,
        'topic': topic,
        'meeting': meeting,
        'op': op,
    }
    return render(request, 'pica/search_incharge.html', context)


def add_inputter_to_topic(request, id, op, tpk, usr, st):
    meeting = Meeting.objects.get(id=id)
    topic = Topic.objects.get(id=tpk)
    total_user = User.objects.filter(user2topic=topic).count()
    if total_user > 0:
        messages.error(request, "PICA Inputter only 1 person! No more.")
        return redirect('pica:search_incharge', meeting.id, op, topic.id)
    new_pic = User.objects.get(id=usr)
    topic.topic2user = new_pic
    topic.save()
    if st == "B":
        return redirect('pica:add_incharge_to_topic', meeting.id, op, topic.id, new_pic.id)
    else:
        return redirect('pica:search_incharge', meeting.id, op, topic.id)


def add_incharge_to_topic(request, id, op, tpk, usr):
    meeting = Meeting.objects.get(id=id)
    topic = Topic.objects.get(id=tpk)
    total_user = User.objects.filter(incharge2topic=topic).count()
    if total_user > 0:
        messages.error(request, "PICA Inputter only 1 person! No more.")
        return redirect('pica:search_incharge', meeting.id, op, topic.id)
    new_pic = User.objects.get(id=usr)
    topic.topic2incharge = new_pic
    topic.save()
    return redirect('pica:search_incharge', meeting.id, op, topic.id)


def delete_inputter_from_topic(request, id, op, tpk, usr):
    meeting = Meeting.objects.get(id=id)
    topic = Topic.objects.get(id=tpk, topic2user=usr)
    topic.topic2user = None
    topic.save()
    return redirect('pica:search_incharge', meeting.id, op, topic.id)


def delete_incharge_from_topic(request, id, op, tpk, usr):
    meeting = Meeting.objects.get(id=id)
    topic = Topic.objects.get(id=tpk, topic2incharge=usr)
    topic.topic2incharge = None
    topic.save()
    return redirect('pica:search_incharge', meeting.id, op, topic.id)


# Search Zone
def search_all(request):
    topics = Topic.objects.all()
    q_all = request.GET.get('q_all')
    forums = Forum.objects.all()
    departments = Department.objects.all()
    companies = Company.objects.all()
    bulan = request.GET.get('bulan')
    tahun = request.GET.get('tahun')
    forum_id = request.GET.get('forum_id')
    department_id = request.GET.get('department_id')
    company_id = request.GET.get('company_id')
    category = request.GET.get('category')
    status = request.GET.get('status')
    pic_inputter = request.GET.get('pic_inputter')
    pic_pica = request.GET.get('pic_pica')
    obj_forum = None
    obj_department = None
    obj_company = None
    categories = [('FU', 'Follow Up'), ('PJ', 'Project'), ('PL', 'Policy'), ('NT', 'Notes')]
    statuss = [('O', 'Open'),
               ('P', 'Progress'),
               ('C', 'Closed'),
               ('H', 'Hold')]
    bulans = [(1, "January"), (2, "February"), (3, "March"), (4, "April"), (5, "May"), (6, "June"),
              (7, "July"), (8, "August"), (9, "September"), (10, "October"), (11, "November"), (12, "December"), ]
    # Filter by Topic Name, Problem Info, Action
    if is_valid_queryparam(q_all):
        vector = SearchVector('topic_name', 'problem_info', 'action')
        query = SearchQuery(q_all)
        topics = Topic.objects.annotate(search=vector).filter(search=query)
    # Filter by Forum name
    if is_valid_queryparam(forum_id) and forum_id != 'Choose...':
        obj_forum = Forum.objects.get(id=forum_id)
        topics = topics.filter(topic2meeting__meeting2forum=obj_forum)
    # Filter by Category
    if is_valid_queryparam(category) and category != 'Choose...':
        topics = topics.filter(category=category)
    # Filter by Status
    if is_valid_queryparam(status) and status != 'Choose...':
        topics = topics.filter(status=status)
    # Filter by Department
    if is_valid_queryparam(department_id) and department_id != 'Choose...':
        obj_department = Department.objects.get(id=department_id)
        topics = topics.filter(topic2department=obj_department)
    # Filter by Company
    if is_valid_queryparam(company_id) and company_id != 'Choose...':
        obj_company = Company.objects.get(id=company_id)
        topics = topics.filter(topic2company=obj_company)

    if is_valid_queryparam(bulan) and bulan != 'Choose...':
        topics = topics.filter(topic2meeting__meeting_date__month=int(bulan))

    if is_valid_queryparam(tahun) and tahun != 'Choose...':
        topics = topics.filter(topic2meeting__meeting_date__year=int(tahun))

    if is_valid_queryparam(pic_inputter):
        topics = topics.filter(topic2user__user2profile__full_name__icontains=pic_inputter)

    if is_valid_queryparam(pic_pica):
        topics = topics.filter(topic2incharge__user2profile__full_name__icontains=pic_pica)
    topics = topics.order_by('topic2meeting__meeting2forum__forum_name', '-topic2meeting__meeting_date')
    if q_all is None:
        q_all = ''
    if bulan is not None and bulan != "Choose...":
        bulan = int(bulan)
    if tahun is not None and tahun != "":
        tahun = int(tahun)
    if pic_inputter is None:
        pic_inputter = ''
    if pic_pica is None:
        pic_pica = ''
    context = {
        'topics': topics,
        'forums': forums,
        'departments': departments,
        'companies': companies,
        'q_all': q_all,
        'category': category,
        'categories': categories,
        'status': status,
        'statuss': statuss,
        'obj_forum': obj_forum,
        'obj_department': obj_department,
        'obj_company': obj_company,
        'bulan': bulan,
        'bulans': bulans,
        'tahun': tahun,
        'pic_inputter': pic_inputter,
        'pic_pica': pic_pica,
    }
    return render(request, 'pica/search_topics.html', context)


# Homepage
def home(request):
    return render(request, 'users/home.html')


# Dashboard Zone
@login_required()
def dashboard(request):
    user = request.user
    total_topics = Topic.objects.filter(topic2user=user, status__in=['O', 'P']).count()
    total_approval = Approval.objects.filter(approval2user=user, editable="Y").count()
    context = {
        'total_topics': total_topics,
        'total_approval': total_approval,
    }
    return render(request, 'pica/dashboard.html', context)


# Meeting Approved Zone
def list_meeting_pending(request):
    user = request.user
    approvals = Approval.objects.filter(approval2user=user, editable="Y")
    context = {
        'approvals': approvals,
        'user': user,
    }
    return render(request, 'pica/list_pending_approved.html', context)


def list_topic_review(request, id):
    approval = Approval.objects.get(id=id)
    meeting = Meeting.objects.get(meeting2approval=approval)
    topics = Topic.objects.filter(topic2meeting=meeting)
    context = {
        'approval': approval,
        'topics': topics,
        'meeting': meeting,
    }
    return render(request, 'pica/list_topic_review.html', context)


class ReviewTopicView(View):
    def get(self, request, tpk, apr):
        topic = Topic.objects.get(id=tpk)
        approval = Approval.objects.get(id=apr)
        form = ReviewTopicForm(instance=topic)
        context = {
            'form': form,
            'topic': topic,
            'approval': approval,
        }
        return render(request, 'pica/review_topic.html', context)

    def post(self, request, tpk, apr):
        topic = Topic.objects.get(id=tpk)
        approval = Approval.objects.get(id=apr)
        form = ReviewTopicForm(request.POST, instance=topic)
        if form.is_valid():
            form.save()
            messages.success(request, "Data Topic has been updated!")
            return redirect('pica:list_topic_review', id=approval.id)
        else:
            messages.error(request, "Data Topic is invalid! Please try again.")
            form = UpdateTopicForm(instance=topic)
            context = {
                'form': form,
                'topic': topic,
                'approval': approval,
            }
            return render(request, 'pica/review_topic.html', context)


class ApproveMeetingView(View):
    def get(self, request, id):
        approval = Approval.objects.get(id=id)
        meeting = Meeting.objects.get(meeting2approval=approval)
        approvals = Approval.objects.filter(approval2meeting=meeting).order_by('sequence_no')
        context = {
            'meeting': meeting,
            'approval': approval,
            'approvals': approvals,
        }
        return render(request, 'pica/approve_meeting.html', context)

    def post(self, request, id):
        approval = Approval.objects.get(id=id)
        meeting = Meeting.objects.get(meeting2approval=approval)
        topics = Topic.objects.filter(topic2meeting=meeting)
        approval.approved = "Y"
        approval.editable = "N"
        approval.save()
        approvals = Approval.objects.filter(approval2meeting=meeting).order_by('sequence_no')
        next_bod = True
        for approval in approvals:
            if approval.approved == "Y":
                continue
            if approval.present == "N":
                continue
            if next_bod:
                approval.editable = "Y"
                approval.save()
                next_bod = False
        # Check if this is last approval
        total_bod = approvals.count()
        bod_absent = approvals.filter(present="N").count()
        bod_approve = approvals.filter(approved="Y").count()
        if total_bod == bod_approve + bod_absent:  # this is the last approval
            meeting.complete_approval = "Y"
            meeting.save()
            send_email_notif.delay(meeting.id)  # Using Celery to send email notifications
        messages.success(request, "Minutes of Meeting has been approved.")
        return redirect('pica:list_meeting_pending')
        #


# Finish Check
def list_finish_check(request):
    meetings = Meeting.objects.filter(cpmd_checked="Y").order_by('meeting_date')
    context = {
        'meetings': meetings,
    }
    return render(request, 'pica/list_finish_check.html', context)


def list_approve_meeting(request, id):
    meeting = Meeting.objects.get(id=id)
    approvals = Approval.objects.filter(approval2meeting=meeting).order_by('sequence_no')
    context = {
        'meeting': meeting,
        'approvals': approvals,
    }
    return render(request, 'pica/list_approve_meeting.html', context)


def finish_check(request, id, op):
    meeting = Meeting.objects.get(id=id)
    bod_present = User.objects.filter(user2meeting=meeting, user2profile__bod="Y")
    if bod_present.count() == 0:  ## Check whether Internal Participant for this meeting has been inputted or not
        messages.error(request,
                       "Internal Participant for this meeting is empty. Please register participant first!")
        return redirect('pica:list_meeting', op="O")
    meeting.cpmd_checked = "Y"
    meeting.save()
    forum = Forum.objects.get(forum2meeting=meeting)
    workflows = Workflow.objects.filter(workflow2forum=forum).order_by('sequence_no')
    first_approval = True
    for workflow in workflows:
        approval = Approval.objects.create(approval2meeting=meeting,
                                           bod_name=workflow.bod_name, sequence_no=workflow.sequence_no)
        bod = User.objects.filter(user2workflow=workflow)[
            0]  # kita gunakan filter maka akan dihasilkan list, sehingga kita gunakan [0]
        approval.approval2user.add(bod)
        approval.email = bod.email

        if bod in bod_present:
            approval.present = "P"
            # Create Token for every approval
            token = str(random.random()).split('.')[1]
            approval.token_code = token
            if first_approval:
                approval.editable = "Y"
                first_approval = False
        else:
            approval.present = "N"
        approval.save()
    # Send email approve to BOD
    # http://my-domain.com/verify/<token>/
    approval = Approval.objects.filter(approval2meeting=meeting, editable="Y").order_by('sequence_no')[0]
    domain_name = get_current_site(request).domain
    token = approval.token_code
    link = f'http://{domain_name}/verify/{token}'
    link_epica = 'https://epica.tta-apps.com'
    # Setup email for BOD
    topics = Topic.objects.filter(topic2meeting=meeting)
    first_attach = True
    bod = True
    pic_cpmd = User.objects.filter(user2forum=forum, user2profile__cpmd='Y')
    pic_secretary = User.objects.filter(user2forum=forum, user2profile__secretary='Y')
    context = {
        'meeting': meeting,
        'topics': topics,
        'link': link,
        'link_epica': link_epica,
        'bod': bod,
        'bod_name': approval.bod_name,
        'pic_cpmd': pic_cpmd,
        'pic_secretary': pic_secretary,
    }
    html_message = render_to_string('pica/email_notif_bod.html', context)
    send_email_approve.delay(meeting.id, html_message, bod, first_attach)
    bod = False
    # Send email for CPMD team and secretary (without button approval)
    bod = False
    context = {
        'meeting': meeting,
        'topics': topics,
        'link': link,
        'link_epica': link_epica,
        'bod': bod,
        'bod_name': approval.bod_name,
        'pic_cpmd': pic_cpmd,
        'pic_secretary': pic_secretary,
    }
    html_message = render_to_string('pica/email_notif_bod.html', context)
    send_email_approve.delay(meeting.id, html_message, bod, first_attach)
    messages.success(request, "Proses finish check has been completed.")
    return redirect('pica:list_meeting', op=op)


# Activity Zone
def list_activity(request):
    topics = Topic.objects.filter(topic2user=request.user, status__in=['O', 'H', 'P'])
    context = {
        'topics': topics,
    }
    return render(request, 'pica/list_activity.html', context)


def list_notes(request):
    topics = Topic.objects.filter(topic2user=request.user, category__in=['NT'])
    context = {
        'topics': topics,
    }
    return render(request, 'pica/list_notes.html', context)


def list_update_activity(request, id):
    topic = Topic.objects.get(id=id)
    activities = Activity.objects.filter(activity2topic=topic).order_by('activity_date')
    meeting = Meeting.objects.get(meeting2topic=topic)
    context = {
        'topic': topic,
        'activities': activities,
        'meeting': meeting,
    }
    return render(request, 'pica/list_update_activity.html', context)


class InputActivityView(View):
    def get(self, request, id):
        topic = Topic.objects.get(id=id)
        meeting = Meeting.objects.get(meeting2topic=topic)
        form = ActivityForm()
        context = {
            'form': form,
            'topic': topic,
            'meeting': meeting,
        }
        return render(request, 'pica/input_activity.html', context)

    def post(self, request, id):
        topic = Topic.objects.get(id=id)
        meeting = Meeting.objects.get(meeting2topic=topic)
        form = ActivityForm(request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data['activity_date'] < topic.topic2meeting.meeting_date:
                messages.error(request, "Activity date cannot lower than meeting date")
                form = ActivityForm()
                context = {
                    'form': form,
                    'topic': topic,
                    'meeting': meeting,
                }
                return render(request, 'pica/input_activity.html', context)
            new_activity = form.save(commit=False)
            new_activity.activity2topic = topic
            new_activity.activity2user = request.user
            new_activity.save()
            topic.status = "P"
            topic.save()
            messages.success(request, "Data Activity has been saved!")
            form = ActivityForm()
            context = {
                'form': form,
                'topic': topic,
            }
            return render(request, 'pica/input_activity.html', context)
        else:
            messages.success(request, "Invalid data, please try again!")
            form = ActivityForm()
            context = {
                'form': form,
                'topic': topic,
            }
            return render(request, 'pica/input_activity.html', context)


class UpdateActivityView(View):
    def get(self, request, id):
        activity = Activity.objects.get(id=id)
        topic = Topic.objects.get(topic2activity=activity)
        form = UpdateActivityForm(instance=activity)
        context = {
            'form': form,
            'activity': activity,
            'topic': topic,
        }
        return render(request, 'pica/update_activity.html', context)

    def post(self, request, id):
        activity = Activity.objects.get(id=id)
        topic = Topic.objects.get(topic2activity=activity)
        form = UpdateActivityForm(request.POST, request.FILES, instance=activity)
        if form.is_valid():
            form.save()
            messages.success(request, "Data Activity has been updated!")
            return redirect('pica:list_update_activity', topic.id)
        else:
            form = UpdateActivityForm(instance=activity)
            context = {
                'form': form,
                'activity': activity,
                'topic': topic,
            }
            return render(request, 'pica/update_outside.html', context)


class DeleteActivityView(View):
    def get(self, request, id):
        activity = Activity.objects.get(id=id)
        topic = Topic.objects.get(topic2activity=activity)
        context = {
            'activity': activity,
            'topic': topic,
        }
        return render(request, 'pica/delete_activity.html', context)

    def post(self, request, id):
        activity = Activity.objects.get(id=id)
        topic = Topic.objects.get(topic2activity=activity)
        activity.delete()
        messages.success(request, "Data Activity has been deleted.")
        return redirect('pica:list_update_activity', topic.id)


def close_pica(request, id):
    topic = Topic.objects.get(id=id)
    topic.status = "C"
    topic.save()
    meeting_id = topic.topic2meeting.id
    meeting = Meeting.objects.get(id=meeting_id)
    cpmds = meeting.meeting2forum.forum2user.all()
    closed_by = request.user.first_name + ' ' + request.user.last_name
    forum_name = meeting.meeting2forum.forum_name
    topic_name = topic.topic_name
    meeting_date = meeting.meeting_date
    problem = topic.problem_info
    action = topic.action
    pic_list = []
    pic = request.user
    for cpmd in cpmds:
        if cpmd.user2profile.cpmd == "Y":
            pic_list.append(cpmd.email)

    # Activity
    activities = Activity.objects.filter(activity2topic=topic, activity2user=pic)
    # Sending Email
    subject = f"Notifikasi Close PICA by {closed_by}"
    message = f"Dear Tim CPMD,\n\n" + f"{closed_by} menyatakan telah melakukan Closing PICA yang diassign kepadanya. \n" + \
              f"Forum : {forum_name} \n" + f'Date : {meeting_date} \n' + f"Problem : {problem} \n" + \
              f"Action : {action}"
    from_email = settings.EMAIL_HOST_USER
    recipient_list = pic_list
    fail_silently = True
    today = date.today()
    due_date = topic.due_date
    context = {
        'closed_by': closed_by,
        'forum_name': forum_name,
        'meeting_date': meeting_date,
        'problem': problem,
        'action': action,
        'due_date': due_date,
        'topic_name': topic_name,
        'today': today,
        'activities': activities,
        'pic': pic,
    }
    html_message = render_to_string('pica/close_pica.html', context)
    send_mail(subject=subject, message=message, from_email=from_email, recipient_list=recipient_list,
              fail_silently=fail_silently, html_message=html_message)
    messages.success(request, "Topic has been closed.")
    return redirect('pica:list_activity')


def status_activity(request, id, op):
    topic = Topic.objects.get(id=id)
    meeting = Meeting.objects.get(meeting2topic=topic)
    activities = Activity.objects.filter(activity2topic=topic)
    context = {
        'activities': activities,
        'op': op,
        'meeting': meeting,
    }
    return render(request, 'pica/status_activity.html', context)


# Outside Participants
def list_outside(request):
    outsides = Outside.objects.all()
    context = {
        'outsides': outsides,
    }
    return render(request, 'pica/list_outside.html', context)


class InputOutsideView(View):
    def get(self, request):
        form = OutsideForm()
        context = {
            'form': form,
        }
        return render(request, 'pica/input_outside.html', context)

    def post(self, request):
        form = OutsideForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Data Outside Participant has been saved!")
            form = OutsideForm()
            context = {
                'form': form,
            }
            return render(request, 'pica/input_outside.html', context)


class UpdateOutsideView(View):
    def get(self, request, id):
        outside = Outside.objects.get(id=id)
        form = OutsideForm(instance=outside)
        context = {
            'form': form,
            'outside': outside,
        }
        return render(request, 'pica/update_outside.html', context)

    def post(self, request, id):
        outside = Outside.objects.get(id=id)
        form = OutsideForm(request.POST, instance=outside)
        if form.is_valid():
            form.save()
            messages.success(request, "Data Outside Participant has been updated!")
            return redirect('pica:list_outside')
        else:
            form = CompanyForm(instance=outside)
            context = {
                'form': form,
                'outside': outside,
            }
            return render(request, 'pica/update_outside.html', context)


class DeleteOutsideView(View):
    def get(self, request, id):
        outside = Outside.objects.get(id=id)
        context = {
            'outside': outside,
        }
        return render(request, 'pica/delete_outside.html', context)

    def post(self, request, id):
        outside = Outside.objects.get(id=id)
        outside.delete()
        messages.success(request, "Data Outside Participant has been deleted.")
        return redirect('pica:list_outside')


def update_outside_participant(request, id, op):
    meeting = Meeting.objects.get(id=id)
    outsides_in_meeting = Outside.objects.filter(outside2meeting=meeting)
    outsides = Outside.objects.all()
    context = {
        'outsides': outsides,
        'outsides_in_meeting': outsides_in_meeting,
        'meeting': meeting,
        'op': op,
    }
    return render(request, 'pica/update_outside_participant.html', context)


def add_outside_to_meeting(request, meet, id, op):
    meeting = Meeting.objects.get(id=meet)
    new_outside = Outside.objects.get(id=id)
    meeting.meeting2outside.add(new_outside)
    meeting.save()
    return redirect('pica:update_outside_participant', id=meeting.id, op=op)


def delete_outside_from_meeting(request, meet, id, op):
    meeting = Meeting.objects.get(id=meet)
    current_outside = Outside.objects.get(id=id)
    meeting.meeting2outside.remove(current_outside)
    return redirect('pica:update_outside_participant', id=meeting.id, op=op)


## Topic Zone
def list_topic(request, id, op):
    meeting = Meeting.objects.get(id=id)
    topics = Topic.objects.filter(topic2meeting=meeting)
    # users = User.objects.all()
    context = {
        'topics': topics,
        'meeting': meeting,
        # 'users': users,
        'op': op,
    }
    return render(request, 'pica/list_topic.html', context)


class InputTopicView(View):
    def get(self, request, id, op):
        meeting = Meeting.objects.get(id=id)
        form = TopicForm()
        context = {
            'form': form,
            'meeting': meeting,
            'op': op,
        }
        return render(request, 'pica/input_topic.html', context)

    def post(self, request, id, op):
        meeting = Meeting.objects.get(id=id)
        form = TopicForm(request.POST, request.FILES)
        if form.is_valid():
            new_topic = form.save(commit=False)
            new_topic.topic2meeting = meeting
            new_topic.save()
            messages.success(request, "Data Topic has been saved successfully!")
            return redirect('pica:search_incharge', meeting.id, op, new_topic.id)
        else:
            messages.error(request, "Invalid data. Please try again!")
            form = TopicForm(request.POST, request.FILES)
            context = {
                'form': form,
                'meeting': meeting,
                'op': op,
            }
            return render(request, 'pica/input_topic.html', context)


class UpdateTopicView(View):
    def get(self, request, meet, id, op):
        meeting = Meeting.objects.get(id=meet)
        topic = Topic.objects.get(id=id)
        form = UpdateTopicForm(instance=topic)
        context = {
            'form': form,
            'meeting': meeting,
            'topic': topic,
            'op': op,
        }
        return render(request, 'pica/update_topic.html', context)

    def post(self, request, meet, id, op):
        meeting = Meeting.objects.get(id=meet)
        topic = Topic.objects.get(id=id)
        form = UpdateTopicForm(request.POST, request.FILES, instance=topic)
        if form.is_valid():
            cat = request.POST.get('category')
            sts = request.POST.get('status')
            if cat == "NT" and sts != "C":
                messages.error(request, "For Notes Category, status topic should Closed.")
                form = UpdateTopicForm(instance=topic)
                context = {
                    'form': form,
                    'meeting': meeting,
                    'topic': topic,
                    'op': op,
                }
                return render(request, 'pica/update_topic.html', context)
            if topic.topic2user is None:
                messages.error(request, "Please assign this PICA to somebody.")
                form = UpdateTopicForm(instance=topic)
                context = {
                    'form': form,
                    'meeting': meeting,
                    'topic': topic,
                    'op': op,
                }
                return render(request, 'pica/update_topic.html', context)
            form.save()
            messages.success(request, "Data Topic has been updated!")
            return redirect('pica:list_topic', id=meeting.id, op=op)
        else:
            messages.error(request, "Data Topic is invalid! Please try again.")
            form = UpdateTopicForm(instance=topic)
            context = {
                'form': form,
                'meeting': meeting,
                'topic': topic,
                'op': op,
            }
            return render(request, 'pica/update_topic.html', context)


def update_pic_topic(request, meet, id, op):
    meeting = Meeting.objects.get(id=meet)
    topic = Topic.objects.get(id=id)
    user_in_topic = User.objects.filter(user2topic=topic)
    all_users_non_bod = User.objects.filter(user2profile__bod="N")
    context = {
        'all_users_non_bod': all_users_non_bod,
        'user_in_topic': user_in_topic,
        'meeting': meeting,
        'topic': topic,
        'op': op,
    }
    return render(request, 'pica/update_pic_topic.html', context)


def add_pic_to_topic(request, tpk, id, op):
    topic = Topic.objects.get(id=tpk)
    meeting = Meeting.objects.get(meeting2topic=topic)
    new_pic = User.objects.get(id=id)
    topic.topic2user.add(new_pic)
    topic.save()
    return redirect('pica:update_pic_topic', meet=meeting.id, id=topic.id, op=op)


def delete_pic_from_topic(request, tpk, id, op):
    topic = Topic.objects.get(id=tpk)
    meeting = Meeting.objects.get(meeting2topic=topic)
    current_pic = User.objects.get(id=id)
    topic.topic2user.remove(current_pic)
    return redirect('pica:update_pic_topic', meet=meeting.id, id=topic.id, op=op)


def change_pica_status(request, id):
    topic = Topic.objects.get(id=id)
    topic.status = "P"
    topic.save()
    forum_name = topic.topic2meeting.meeting2forum.forum_name
    meeting_date = topic.topic2meeting.meeting_date
    problem = topic.problem_info
    action = topic.action
    pics = topic.topic2user
    pic_list = []
    pic_list.append(pics.email)

    # Sending Email
    subject = f"Notifikasi Re-Open PICA by tim CPMD"
    message = f"Dear All,\n\n" + f"Bersama ini Tim CPMD menyatakan telah melakukan Re-Open PICA dengan detail seperti dibawah ini: \n" + \
              f"Forum : {forum_name} \n" + f'Date : {meeting_date} \n' + f"Problem : {problem} \n" + \
              f"Action : {action}"
    from_email = settings.EMAIL_HOST_USER
    recipient_list = pic_list
    fail_silently = True
    today = date.today()
    due_date = topic.due_date
    topic_name = topic.topic_name
    context = {
        'forum_name': forum_name,
        'meeting_date': meeting_date,
        'problem': problem,
        'action': action,
        'due_date': due_date,
        'topic_name': topic_name,
        'today': today,
    }
    html_message = render_to_string('pica/change_status_pica.html', context)
    send_mail(subject=subject, message=message, from_email=from_email, recipient_list=recipient_list,
              fail_silently=fail_silently, html_message=html_message)
    messages.success(request, "Status Topic has been changed to Progress")
    return redirect('pica:search_all')


# Meeting Zone
def view_meeting_approved(request):
    context = {

    }
    return render(request, 'pica/view_meeting.html', context)


def search_participant(request, id, op):
    meeting = Meeting.objects.get(id=id)
    all_users = User.objects.filter(is_superuser=False)
    user_in_meeting = User.objects.filter(user2meeting=meeting)
    user_not_in_meeting = all_users.exclude(user2meeting=meeting)
    q_all = request.GET.get('q_all')
    available_user = user_not_in_meeting
    # Filter by Topic Name, Problem Info, Action
    if is_valid_queryparam(q_all):
        vector = SearchVector('first_name', 'last_name')
        query = SearchQuery(q_all)
        available_user = user_not_in_meeting.annotate(search=vector).filter(search=query)
    available_user = available_user.order_by('first_name')
    # paginator = Paginator(available_user, 10)
    # page_number = request.GET.get('page')
    # page = paginator.get_page(page_number)
    # page_range = page.paginator.page_range
    context = {
        'available_user': available_user,
        'user_in_meeting': user_in_meeting,
        # 'page_range': page_range,
        'meeting': meeting,
        'op': op,
    }

    return render(request, 'pica/search_participants.html', context)


class InputAttachmentView(View):
    def get(self, request, id, op):
        meeting = Meeting.objects.get(id=id)
        lampirans = Lampiran.objects.filter(lampiran2meeting=meeting)
        total_size = 0
        for lampir in lampirans:
            total_size += lampir.lampir.size
        total_size = total_size / (1024 * 1024)
        form = UploadFileForm()
        context = {
            'form': form,
            'meeting': meeting,
            'op': op,
            'lampirans': lampirans,
            'total_size': total_size,
        }
        return render(request, 'pica/input_attachments.html', context)

    def post(self, request, id, op):
        meeting = Meeting.objects.get(id=id)
        form = UploadFileForm(request.POST, request.FILES)
        lampirans = Lampiran.objects.filter(lampiran2meeting=meeting)
        if form.is_valid():
            form.clean_files()
            files = request.FILES.getlist('files')
            total_size = 0
            for file in files:
                Lampiran.objects.create(lampir=file, lampiran2meeting=meeting)
            lampirans = Lampiran.objects.filter(lampiran2meeting=meeting)
            for lampir in lampirans:
                total_size += lampir.lampir.size
                filename = lampir.lampir.name
                lampir.nama_file = filename.split('/')[-1]
                lampir.save()
            if total_size / (1024 * 1024) > 25:
                messages.error(request, "Total size exceeded 25 Mb")
                for lampir in lampirans:
                    lampir.delete()
                return redirect('pica:input_attachment', id=meeting.id, op=op)
            else:
                messages.success(request, "File attachments has been saved successfully!")
                return redirect('pica:list_meeting', op=op)
        else:
            messages.error(request, "Invalid data. Please try again!")
            form = UploadFileForm()
            context = {
                'form': form,
                'meeting': meeting,
                'op': op,
                'lampirans': lampirans,
            }
            return render(request, 'pica/input_attachments.html', context)


class InputActivityAttachmentView(View):
    def get(self, request, id, id2):
        meeting = Meeting.objects.get(id=id)
        activity = Activity.objects.get(id=id2)
        topic = Topic.objects.get(topic2activity=activity)
        doc_images = Docimg.objects.filter(docimg2activity=activity)
        doc_pdfs = Docpdf.objects.filter(docpdf2activity=activity)
        total_size = 0
        if doc_images:
            for img in doc_images:
                total_size += img.doc_image.size
        if doc_pdfs:
            for pdf in doc_pdfs:
                total_size += pdf.doc_pdf.size
        form = UploadAttachmentsForm()
        context = {
            'form': form,
            'meeting': meeting,
            'doc_images': doc_images,
            'doc_pdfs': doc_pdfs,
            'topic': topic,
            'total_size': total_size,
        }
        return render(request, 'pica/activity_attachments.html', context)

    def post(self, request, id, id2):
        meeting = Meeting.objects.get(id=id)
        activity = Activity.objects.get(id=id2)
        topic = Topic.objects.get(topic2activity=activity)
        form = UploadAttachmentsForm(request.POST, request.FILES)
        if form.is_valid():
            # form.clean_files()
            total_size = 0
            files1 = request.FILES.getlist('files1')
            files2 = request.FILES.getlist('files2')
            for f in files1:
                if f.content_type != "application/pdf":
                    messages.error(request, "Invalid file type! Please refer to file type allowed (pdf/image). ")
                    return redirect('pica:input_activity_attachment', id=meeting.id, id2=activity.id)
            for f in files2:
                if f.content_type not in ["image/jpeg", "image/jpg", "image/png"]:
                    messages.error(request, "Invalid file type! Please refer to file type allowed (pdf/image). ")
                    return redirect('pica:input_activity_attachment', id=meeting.id, id2=activity.id)
            for file in files1:
                Docpdf.objects.create(doc_pdf=file, docpdf2activity=activity)
            for file in files2:
                Docimg.objects.create(doc_image=file, docimg2activity=activity)
            lampir1 = Docpdf.objects.filter(docpdf2activity=activity)
            for lampir in lampir1:
                total_size += lampir.doc_pdf.size
                filename = lampir.doc_pdf.name
                lampir.nama_file = filename.split('/')[-1]
                lampir.save()
            lampir2 = Docimg.objects.filter(docimg2activity=activity)
            for lampir in lampir2:
                total_size += lampir.doc_image.size
                filename = lampir.doc_image.name
                lampir.nama_file = filename.split('/')[-1]
                lampir.save()
            if total_size / (1024 * 1024) > 25:
                messages.error(request, "Total size attachments exceeded 25 Mb. Please try again.")
                for lampir in lampir1:
                    lampir.delete()
                for lampir in lampir2:
                    lampir.delete()
                activity.having_attachments = "N"
                activity.save()
                return redirect('pica:input_activity_attachment', id=meeting.id, id2=activity.id)
            else:
                messages.success(request, "File attachments has been saved successfully!")
                activity.having_attachments = "Y"
                activity.save()
                return redirect('pica:list_update_activity', id=topic.id)
        else:
            messages.error(request, "Invalid data. Please try again!")
            doc_images = Docimg.objects.filter(docimg2activity=activity)
            doc_pdfs = Docpdf.objects.filter(docpdf2activity=activity)
            total_size = 0
            if doc_images:
                for img in doc_images:
                    total_size += img.doc_image.size
            if doc_pdfs:
                for pdf in doc_pdfs:
                    total_size += pdf.doc_pdf.size
            total_size_attachment = total_size
            form = UploadAttachmentsForm()
            context = {
                'form': form,
                'meeting': meeting,
                'doc_images': doc_images,
                'doc_pdfs': doc_pdfs,
                'topic': topic,
                'total_size': total_size,
            }
            return render(request, 'pica/activity_attachments.html', context)


def list_activity_attachment(request, id, meet_id):
    meeting = Meeting.objects.get(id=meet_id)
    activity = Activity.objects.get(id=id)
    doc_images = Docimg.objects.filter(docimg2activity=activity)
    doc_pdfs = Docpdf.objects.filter(docpdf2activity=activity)
    context = {
        'doc_images': doc_images,
        'doc_pdfs': doc_pdfs,
        'activity': activity,
        'meeting': meeting,
    }
    return render(request, 'pica/list_activity_attachment.html', context)


def delete_lampiran(request, id, op, id2):
    meeting = Meeting.objects.get(id=id)
    lampiran = Lampiran.objects.get(id=id2)
    lampiran.delete()
    messages.success(request, "File attachments has been deleted successfully!")
    return redirect('pica:input_attachment', id=meeting.id, op=op)


def delete_pdf(request, id, id2):
    meeting = Meeting.objects.get(id=id)
    doc_pdf = Docpdf.objects.get(id=id2)
    activity = Activity.objects.get(activity2docpdf=doc_pdf)
    doc_pdf.delete()
    messages.success(request, "File pdf attachment has been deleted successfully!")
    return redirect('pica:input_activity_attachment', id=meeting.id, id2=activity.id)


def delete_image(request, id, id2):
    meeting = Meeting.objects.get(id=id)
    doc_image = Docimg.objects.get(id=id2)
    activity = Activity.objects.get(activity2docimg=doc_image)
    doc_image.delete()
    messages.success(request, "File (jpeg/jpg/png) attachment has been deleted successfully!")
    return redirect('pica:input_activity_attachment', id=meeting.id, id2=activity.id)


def list_meeting(request, op):
    today = date.today()
    if request.user.user2profile.secretary == "Y":
        secretary = True
    else:
        secretary = False
    if op == "I":
        meetings = Meeting.objects.filter(meeting_date__gte=today, cpmd_checked="N").order_by('meeting_date')
    else:
        meetings = Meeting.objects.filter(meeting_date__lt=today, cpmd_checked="N").order_by('meeting_date')
    context = {
        'meetings': meetings,
        'op': op,
        'secretary': secretary,
    }
    return render(request, 'pica/list_meeting.html', context)


def list_complete_approve(request):
    meetings = Meeting.objects.filter(complete_approval="Y").order_by('meeting_date')
    bulan = request.GET.get('bulan')
    tahun = request.GET.get('tahun')
    forum_id = request.GET.get('forum_id')
    forums = Forum.objects.all()
    if is_valid_queryparam(forum_id) and forum_id != 'Choose...':
        obj_forum = Forum.objects.get(id=forum_id)
        meetings = meetings.filter(meeting2forum=obj_forum)
    if is_valid_queryparam(bulan) and bulan != 'Choose...':
        if is_valid_queryparam(tahun) and tahun != 'Choose...':
            meetings = meetings.filter(meeting_date__month=bulan)
            meetings = meetings.filter(meeting_date__year=tahun)
    context = {
        'meetings': meetings,
        'forums': forums,
    }
    return render(request, 'pica/list_complete_approve.html', context)


class InputMeetingView(View):
    def get(self, request, op):
        form = MeetingForm()
        context = {
            'form': form,
            'op': op,
        }
        return render(request, 'pica/input_meeting.html', context)

    def post(self, request, op):
        forum = request.POST.get('meeting2forum')
        meeting_date = request.POST.get('meeting_date')
        if Meeting.objects.filter(meeting2forum=forum, meeting_date=meeting_date).exists():
            messages.error(request, "Meeting already registered on the same date. Please try again.")
            form = MeetingForm(request.POST)
            context = {
                'form': form,
                'op': op,
            }
            return render(request, 'pica/input_meeting.html', context)
        form = MeetingForm(request.POST)
        if form.is_valid():
            data_cleaned = form.cleaned_data
            meeting_date = data_cleaned['meeting_date']
            meet = form.save(commit=False)
            year = meeting_date.year
            month = meeting_date.month
            day = meeting_date.day
            forum = Forum.objects.get(id=forum)
            refno = f"{year}.{month}.{day} - {forum.forum_name}"
            meet.ref_no = refno
            meet.save()
            messages.success(request, "Data meeting has been saved successfully!")
            return redirect("pica:list_meeting", op)
        else:
            messages.error(request, "Invalid input!")
            form = MeetingForm(request.POST)
            context = {
                'form': form,
                'op': op,
            }
            return render(request, 'pica/input_meeting.html', context)


class UpdateMeetingView(View):
    def get(self, request, id, op):
        meeting = Meeting.objects.get(id=id)
        refno = meeting.ref_no
        form = UpdateMeetingForm(instance=meeting)
        context = {
            'form': form,
            'meeting': meeting,
            'op': op,
            'refno': refno,
        }
        return render(request, 'pica/update_meeting.html', context)

    def post(self, request, id, op):
        meeting = Meeting.objects.get(id=id)
        form = UpdateMeetingForm(request.POST, instance=meeting)
        if form.is_valid():
            form.save()
            messages.success(request, "Data Meeting has been updated!")
            return redirect('pica:list_meeting', op)
        else:
            messages.error(request, "Data Meeting is invalid! Please try again.")
            form = UpdateForumForm(instance=meeting)
            context = {
                'form': form,
                'meeting': meeting,
                'op': op,
            }
            return render(request, 'pica/update_meeting.html', context)


def update_internal_participant(request, id, op):
    meeting = Meeting.objects.get(id=id)
    user_in_meeting = User.objects.filter(user2meeting=meeting)
    all_users = User.objects.all()
    context = {
        'all_users': all_users,
        'user_in_meeting': user_in_meeting,
        'meeting': meeting,
        'op': op,
    }
    return render(request, 'pica/update_internal_participant.html', context)


def add_participant_to_meeting(request, meet, id, op):
    meeting = Meeting.objects.get(id=meet)
    new_participant = User.objects.get(id=id)
    meeting.meeting2user.add(new_participant)
    meeting.save()
    return redirect('pica:search_participant', id=meeting.id, op=op)


def delete_participant_from_meeting(request, meet, id, op):
    meeting = Meeting.objects.get(id=meet)
    current_participant = User.objects.get(id=id)
    meeting.meeting2user.remove(current_participant)
    return redirect('pica:search_participant', id=meeting.id, op=op)


# List Secretary
def list_secretary(request, id):
    forum = Forum.objects.get(id=id)
    secretaries = User.objects.filter(user2profile__secretary="Y")
    secretaries_in_forum = User.objects.filter(user2forum=forum, user2profile__secretary="Y")
    context = {
        'secretaries': secretaries,
        'forum': forum,
        'secretaries_in_forum': secretaries_in_forum,
    }
    return render(request, 'pica/list_secretary.html', context)


def update_secretary(request, id):
    forum = Forum.objects.get(id=id)
    secretaries = User.objects.filter(user2profile__secretary="Y")
    secretaries_in_forum = User.objects.filter(user2forum=forum, user2profile__secretary="Y")
    context = {
        'secretaries': secretaries,
        'forum': forum,
        'secretaries_in_forum': secretaries_in_forum,
    }
    return render(request, 'pica/update_secretary.html', context)


def add_secretary_to_forum(request, id, forum):
    new_secretary = User.objects.get(id=id)
    current_forum = Forum.objects.get(id=forum)
    current_forum.forum2user.add(new_secretary)
    current_forum.save()
    return redirect('pica:update_secretary', forum)


def delete_secretary_from_forum(request, id, forum):
    current_secretary = User.objects.get(id=id)
    current_forum = Forum.objects.get(id=forum)
    current_forum.forum2user.remove(current_secretary)
    return redirect('pica:update_secretary', forum)


# List CPMD
def list_cpmd(request, id):
    forum = Forum.objects.get(id=id)
    cpmds = User.objects.filter(user2profile__cpmd="Y")
    cpmd_in_forum = User.objects.filter(user2forum=forum, user2profile__cpmd="Y")
    context = {
        'cpmds': cpmds,
        'forum': forum,
        'cpmd_in_forum': cpmd_in_forum,
    }
    return render(request, 'pica/list_cpmd.html', context)


def update_cpmd(request, id):
    forum = Forum.objects.get(id=id)
    cpmds = User.objects.filter(user2profile__cpmd="Y")
    cpmd_in_forum = User.objects.filter(user2forum=forum, user2profile__cpmd="Y")
    context = {
        'cpmds': cpmds,
        'forum': forum,
        'cpmd_in_forum': cpmd_in_forum,
    }
    return render(request, 'pica/update_cpmd.html', context)


def add_cpmd_to_forum(request, id, forum):
    new_cpmd = User.objects.get(id=id)
    current_forum = Forum.objects.get(id=forum)
    current_forum.forum2user.add(new_cpmd)
    current_forum.save()
    return redirect('pica:update_cpmd', forum)


def delete_cpmd_from_forum(request, id, forum):
    current_cpmd = User.objects.get(id=id)
    current_forum = Forum.objects.get(id=forum)
    current_forum.forum2user.remove(current_cpmd)
    return redirect('pica:update_cpmd', forum)


## Workflow Zone
def list_workflow(request, id):
    forum = Forum.objects.get(id=id)
    bod_in_workflow = User.objects.filter(user2workflow__workflow2forum=forum)
    current_workflow = Workflow.objects.filter(workflow2forum=forum).order_by('sequence_no')
    context = {
        'bod_in_workflow': bod_in_workflow,
        'forum': forum,
        'current_workflow': current_workflow,
    }
    return render(request, 'pica/list_workflow.html', context)


def update_workflow(request, id):
    forum = Forum.objects.get(id=id)
    bod_workflow = User.objects.filter(user2workflow__workflow2forum=forum)
    bod_user = User.objects.filter(user2profile__bod='Y')
    context = {
        'bod_user': bod_user,
        'bod_workflow': bod_workflow,
        'forum': forum,
    }
    return render(request, 'pica/update_workflow.html', context)


def add_bod_to_workflow(request, id, forum):
    new_bod = User.objects.get(id=id)
    current_forum = Forum.objects.get(id=forum)
    new_workflow = Workflow.objects.create(workflow2forum=current_forum)
    new_workflow.workflow2user.add(new_bod)
    new_workflow.bod_name = new_bod.first_name + ' ' + new_bod.last_name
    new_workflow.save()
    return redirect('pica:update_workflow', forum)


def delete_bod_from_workflow(request, id, forum):
    current_bod = User.objects.get(id=id)
    current_forum = Forum.objects.get(id=forum)
    bod = Workflow.objects.get(workflow2forum=current_forum, workflow2user=current_bod)
    bod.delete()
    return redirect('pica:update_workflow', forum)


class EditWorkflowView(View):
    def get(self, request, id, forum):
        current_workflow = Workflow.objects.get(id=id)
        current_forum = Forum.objects.get(id=forum)
        form = EditWorkflowForm(instance=current_workflow)
        context = {
            'form': form,
            'current_workflow': current_workflow,
            'current_forum': current_forum,
        }
        return render(request, 'pica/edit_workflow.html', context)

    def post(self, request, id, forum):
        current_workflow = Workflow.objects.get(id=id)
        current_forum = Forum.objects.get(id=forum)
        form = EditWorkflowForm(request.POST, instance=current_workflow)
        if form.is_valid():
            form.save()
            messages.success(request, "Position and Sequence has been updated!")
            return redirect('pica:list_workflow', current_forum.id)
        else:
            messages.error(request, "Invalid data, please try again.")
            return redirect('pica:edit_workflow', [current_workflow.id, current_forum.id])


## Forum Zone

def list_forum(request):
    forums = Forum.objects.all()
    context = {
        'forums': forums,
    }
    return render(request, 'pica/list_forum.html', context)


class InputForumView(View):
    def get(self, request):
        form = ForumForm()
        context = {
            'form': form,
        }
        return render(request, 'pica/input_forum.html', context)

    def post(self, request):
        form = ForumForm(request.POST)
        if form.is_valid():
            forum_name = request.POST.get('forum_name')
            forum_exist = Forum.objects.filter(forum_name=forum_name).exists()
            if forum_exist:
                messages.error(request, "Forum Name is already taken! Try another one.")
                context = {
                    'form': form,
                }
                return render(request, 'pica/input_forum.html', context)
            form.save()
            messages.success(request, "Data Forum has been saved!")
            form = ForumForm()
            context = {
                'form': form,
            }
            return render(request, 'pica/input_forum.html', context)
        else:
            messages.error(request, "Invalid data. Please try again!")
            form = ForumForm(request.POST)
            context = {
                'form': form,
            }
            return render(request, 'pica/input_forum.html', context)


class UpdateForumView(View):
    def get(self, request, id):
        forum = Forum.objects.get(id=id)
        form = UpdateForumForm(instance=forum)
        context = {
            'form': form,
            'forum': forum,
        }
        return render(request, 'pica/update_forum.html', context)

    def post(self, request, id):
        forum = Forum.objects.get(id=id)
        form = UpdateForumForm(request.POST, instance=forum)
        if form.is_valid():
            form.save()
            messages.success(request, "Data Forum has been updated!")
            return redirect('pica:list_forum')
        else:
            messages.error(request, "Data Forum is invalid! Please try again.")
            form = UpdateForumForm(instance=forum)
            context = {
                'form': form,
                'forum': forum,
            }
            return render(request, 'pica/update_forum.html', context)


class DeleteForumView(View):
    def get(self, request, id):
        forum = Forum.objects.get(id=id)
        context = {
            'forum': forum,
        }
        return render(request, 'pica/delete_forum.html', context)

    def post(self, request, id):
        forum = Forum.objects.get(id=id)
        forum.delete()
        messages.success(request, "Data Forum has been deleted.")
        return redirect('pica:list_forum')


## Company Zone
def list_company(request):
    companies = Company.objects.all().order_by('short_code')
    context = {
        'companies': companies,
    }
    return render(request, 'pica/list_company.html', context)


class InputCompanyView(View):
    def get(self, request):
        form = CompanyForm()
        context = {
            'form': form,
        }
        return render(request, 'pica/input_company.html', context)

    def post(self, request):
        form = CompanyForm(request.POST, request.FILES)
        if form.is_valid():
            short = request.POST.get('short_code')
            if Company.objects.filter(short_code=short).exists():
                messages.error(request, "Company Code is already taken! Try another one.")
                context = {
                    'form': form,
                }
                return render(request, 'pica/input_company.html', context)
            form.save()
            messages.success(request, "Data Company has been saved!")
            form = CompanyForm()
            context = {
                'form': form,
            }
            return render(request, 'pica/input_company.html', context)
        else:
            messages.error(request, "Data was invalid. Please try again!")
            context = {
                'form': form,
            }
            return render(request, 'pica/input_company.html', context)


class UpdateCompanyView(View):
    def get(self, request, id):
        company = Company.objects.get(id=id)
        form = UpdateCompanyForm(instance=company)
        context = {
            'form': form,
            'company': company,
        }
        return render(request, 'pica/update_company.html', context)

    def post(self, request, id):
        company = Company.objects.get(id=id)
        form = UpdateCompanyForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, "Data Company has been updated!")
            return redirect('pica:list_company')
        else:
            form = CompanyForm(instance=company)
            context = {
                'form': form,
                'company': company,
            }
            return render(request, 'pica/update_company.html', context)


class DeleteCompanyView(View):
    def get(self, request, id):
        company = Company.objects.get(id=id)
        context = {
            'company': company,
        }
        return render(request, 'pica/delete_company.html', context)

    def post(self, request, id):
        company = Company.objects.get(id=id)
        company.delete()
        messages.success(request, "Data Company has been deleted.")
        return redirect('pica:list_company')


# Outstanding PICA Zone
def overdue_all_pica(request):
    hari_ini = date.today()
    tta_topics = Topic.objects.filter(topic2meeting__meeting2forum__forum_name="BOD TTA")
    tta_topics = tta_topics.filter(due_date__lte=hari_ini, status__in=['O', 'P'])
    tta_count = tta_topics.count()
    abb_topics = Topic.objects.filter(topic2meeting__meeting2forum__forum_name="BOD ABB-ABJ")
    abb_topics = abb_topics.filter(due_date__lte=hari_ini, status__in=['O', 'P'])
    abb_count = abb_topics.count()
    smm_topics = Topic.objects.filter(topic2meeting__meeting2forum__forum_name="BOD SMM")
    smm_topics = smm_topics.filter(due_date__lte=hari_ini, status__in=['O', 'P'])
    smm_count = smm_topics.count()
    top_topics = Topic.objects.filter(topic2meeting__meeting2forum__forum_name="BOD TOP-ABP")
    top_topics = top_topics.filter(due_date__lte=hari_ini, status__in=['O', 'P'])
    top_count = top_topics.count()
    kcm_topics = Topic.objects.filter(topic2meeting__meeting2forum__forum_name="BOD KCM")
    kcm_topics = kcm_topics.filter(due_date__lte=hari_ini, status__in=['O', 'P'])
    kcm_count = kcm_topics.count()
    pmm_topics = Topic.objects.filter(topic2meeting__meeting2forum__forum_name="BOD PMM")
    pmm_topics = pmm_topics.filter(due_date__lte=hari_ini, status__in=['O', 'P'])
    pmm_count = pmm_topics.count()
    context = {
        'tta': tta_topics,
        'abb': abb_topics,
        'smm': smm_topics,
        'top': top_topics,
        'kcm': kcm_topics,
        'pmm': pmm_topics,
        'tta_count': tta_count,
        'abb_count': abb_count,
        'smm_count': smm_count,
        'top_count': top_count,
        'kcm_count': kcm_count,
        'pmm_count': pmm_count,
    }
    return render(request, 'pica/overdue_topic.html', context)


def ongoing_all_pica(request):
    hari_ini = date.today()
    tta_topics = Topic.objects.filter(topic2meeting__meeting2forum__forum_name="BOD TTA")
    tta_topics = tta_topics.filter(due_date__gte=hari_ini, status__in=['O', 'P'])
    tta_count = tta_topics.count()
    abb_topics = Topic.objects.filter(topic2meeting__meeting2forum__forum_name="BOD ABB-ABJ")
    abb_topics = abb_topics.filter(due_date__gte=hari_ini, status__in=['O', 'P'])
    abb_count = abb_topics.count()
    smm_topics = Topic.objects.filter(topic2meeting__meeting2forum__forum_name="BOD SMM")
    smm_topics = smm_topics.filter(due_date__gte=hari_ini, status__in=['O', 'P'])
    smm_count = smm_topics.count()
    top_topics = Topic.objects.filter(topic2meeting__meeting2forum__forum_name="BOD TOP-ABP")
    top_topics = top_topics.filter(due_date__gte=hari_ini, status__in=['O', 'P'])
    top_count = top_topics.count()
    kcm_topics = Topic.objects.filter(topic2meeting__meeting2forum__forum_name="BOD KCM")
    kcm_topics = kcm_topics.filter(due_date__gte=hari_ini, status__in=['O', 'P'])
    kcm_count = kcm_topics.count()
    pmm_topics = Topic.objects.filter(topic2meeting__meeting2forum__forum_name="BOD PMM")
    pmm_topics = pmm_topics.filter(due_date__gte=hari_ini, status__in=['O', 'P'])
    pmm_count = pmm_topics.count()
    context = {
        'tta': tta_topics,
        'abb': abb_topics,
        'smm': smm_topics,
        'top': top_topics,
        'kcm': kcm_topics,
        'pmm': pmm_topics,
        'tta_count': tta_count,
        'abb_count': abb_count,
        'smm_count': smm_count,
        'top_count': top_count,
        'kcm_count': kcm_count,
        'pmm_count': pmm_count,
    }
    return render(request, 'pica/ongoing_topic.html', context)


# Approval zone
def status_approval(request):
    hari_ini = date.today()
    if request.user.user2profile.cpmd == "Y":
        forum_list = Forum.objects.all()
    else:
        forum_list = Forum.objects.filter(forum2user=request.user)
    tta_meetings = Meeting.objects.filter(meeting2forum__forum_name="BOD TTA").filter(cpmd_checked="Y")
    tta_meetings = tta_meetings.filter(complete_approval="N")
    tta_count = tta_meetings.count()
    abb_meetings = Meeting.objects.filter(meeting2forum__forum_name="BOD ABB-ABJ").filter(cpmd_checked="Y")
    abb_meetings = abb_meetings.filter(complete_approval="N")
    abb_count = abb_meetings.count()
    smm_meetings = Meeting.objects.filter(meeting2forum__forum_name="BOD SMM").filter(cpmd_checked="Y")
    smm_meetings = smm_meetings.filter(complete_approval="N")
    smm_count = smm_meetings.count()
    top_meetings = Meeting.objects.filter(meeting2forum__forum_name="BOD TOP-ABP").filter(cpmd_checked="Y")
    top_meetings = top_meetings.filter(complete_approval="N")
    top_count = top_meetings.count()
    kcm_meetings = Meeting.objects.filter(meeting2forum__forum_name="BOD KCM").filter(cpmd_checked="Y")
    kcm_meetings = kcm_meetings.filter(complete_approval="N")
    kcm_count = kcm_meetings.count()
    pmm_meetings = Meeting.objects.filter(meeting2forum__forum_name="BOD PMM").filter(cpmd_checked="Y")
    pmm_meetings = pmm_meetings.filter(complete_approval="N")
    pmm_count = pmm_meetings.count()
    context = {
        'forum_list': forum_list,
        'tta_meetings': tta_meetings,
        'abb_meetings': abb_meetings,
        'smm_meetings': smm_meetings,
        'top_meetings': top_meetings,
        'kcm_meetings': kcm_meetings,
        'pmm_meetings': pmm_meetings,
        'tta_count': tta_count,
        'abb_count': abb_count,
        'smm_count': smm_count,
        'top_count': top_count,
        'kcm_count': kcm_count,
        'pmm_count': pmm_count,
    }
    return render(request, 'pica/status_approval.html', context)


def cek_status_approval(request, id):
    meeting = Meeting.objects.get(id=id)
    approvers = Approval.objects.filter(approval2meeting=meeting)
    context = {
        'meeting': meeting,
        'approvers': approvers,
    }
    return render(request, 'pica/cek_status_approval.html', context)


def verify(request, token):
    approval = Approval.objects.filter(token_code=token).first()
    if not approval:
        return Http404("Invalid data!")
    else:
        approval.approved = "Y"
        approval.editable = "N"
        approval.save()
        meeting = Meeting.objects.get(meeting2approval=approval)
        forum = Forum.objects.get(forum2meeting=meeting)
        # Send email approve
        # http://my-domain.com/verify/<token>/
        approvals = Approval.objects.filter(approval2meeting=meeting).order_by('sequence_no')
        for approval in approvals:
            if approval.present != "P":
                continue
            if approval.approved == "Y":
                continue
            approval.editable = "Y"
            approval.save()
            break
        approval = Approval.objects.filter(approval2meeting=meeting, editable="Y").order_by('sequence_no').first()
        domain_name = get_current_site(request).domain
        if approval:
            first_attach = False
            token = approval.token_code
            link = f'http://{domain_name}/verify/{token}'
            link_epica = f"http://epica.tta-apps.com"
            # Setup email for BOD
            topics = Topic.objects.filter(topic2meeting=meeting)
            bod = True
            pic_cpmd = User.objects.filter(user2forum=forum, user2profile__cpmd='Y')
            pic_secretary = User.objects.filter(user2forum=forum, user2profile__secretary='Y')
            context = {
                'meeting': meeting,
                'topics': topics,
                'link': link,
                'link_epica': link_epica,
                'bod': bod,
                'bod_name': approval.bod_name,
                'pic_cpmd': pic_cpmd,
                'pic_secretary': pic_secretary,
            }
            html_message = render_to_string('pica/email_notif_bod.html', context)
            send_email_approve.delay(meeting.id, html_message, bod, first_attach)
        else:
            # Check if this is last approval
            total_bod = approvals.count()
            bod_absent = approvals.filter(present="N").count()
            bod_approve = approvals.filter(approved="Y").count()
            if total_bod == bod_approve + bod_absent:  # this is the last approval
                meeting.complete_approval = "Y"
                meeting.save()
                link = f'http://{domain_name}/'
                send_email_notif.delay(meeting.id, link)  # Using Celery to send email notifications
        return HttpResponse("Data has been approved!")


def export_to_excel(request, id):
    meeting = Meeting.objects.get(id=id)
    topics = Topic.objects.filter(topic2meeting=meeting)
    response = HttpResponse(content_type='application/ms-excel')
    filename = f"{meeting.meeting2forum.forum_name}-{meeting.meeting_date.strftime('%Y-%m-%d')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename={filename}'
    title_name = f"{meeting.meeting2forum.forum_name}- ({meeting.meeting_date.strftime('%d-%m-%Y')})"
    meeting_date = meeting.meeting_date.strftime('%d-%m-%Y')
    wb = Workbook()
    ws = wb.active
    ws.title = "Meeting " + title_name
    title = ["Meeting " + title_name]
    a1 = ws['A1']
    a1.font = Font(size=16)
    ws.append(title)

    ws.insert_rows(1)

    # Add headers
    headers = ["Issue Date", "Div/Dept.", "Company", "Topic", "Problem Identification", "Corrective Action",
               "Due Date", "PIC"]
    ws.append(headers)

    # Add data from the model
    for topic in topics:
        topic_date = topic.due_date.strftime('%d-%m-%Y')
        pic_name = topic.topic2incharge.first_name + ' ' + topic.topic2incharge.last_name
        ws.append(
            [meeting_date, topic.topic2department.name, topic.topic2company.name, topic.topic_name, topic.problem_info,
             topic.action, topic_date, pic_name])

    # Save the workbook to the HttpResponse
    wb.save(response)
    return response


def view_mom_complete_approve(request, id):
    meeting = Meeting.objects.get(id=id)
    topics = Topic.objects.filter(topic2meeting=meeting)
    context = {
        'topics': topics,
    }
    return render(request, 'pica/view_mom_complete_approve.html', context)

# def send_activity_duedate_notifications(request):
#     topics = Topic.objects.filter(status__in=['O', 'P'])
#     hari_ini = dt.date.today()
#     h_plus_one = dt.timedelta(days=1)
#     h_plus_six = dt.timedelta(days=6)
#     notif_topics = []
#     notif_users = []
#     for topic in topics:
#         due = topic.due_date
#         if due == hari_ini + h_plus_one:
#             notif_topics.append(topic)
#             continue
#         if due + h_plus_six == hari_ini:
#             notif_topics.append(topic)
#             continue
#     for topic in notif_topics:
#         if topic.topic2user not in notif_users:
#             notif_users.append(topic.topic2user)
#     for notif_user in notif_users:
#         topics = []
#         for notif_topic in notif_topics:
#             if notif_topic.topic2user == notif_user:
#                 topics.append(notif_topic)
#                 continue
