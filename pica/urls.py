from django.urls import path
from . import views

app_name = 'pica'

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    # InCharge
    path('search_incharge/<uuid:id>/<str:op>/<uuid:tpk>/', views.search_incharge,
         name="search_incharge"),
    path('add_inputter_to_topic/<uuid:id>/<str:op>/<uuid:tpk>/<int:usr>/<str:st>/', views.add_inputter_to_topic,
         name="add_inputter_to_topic"),
    path('add_incharge_to_topic/<uuid:id>/<str:op>/<uuid:tpk>/<int:usr>/', views.add_incharge_to_topic,
         name="add_incharge_to_topic"),
    path('delete_inputter_from_topic/<uuid:id>/<str:op>/<uuid:tpk>/<int:usr>/', views.delete_inputter_from_topic,
         name="delete_inputter_from_topic"),
    path('delete_incharge_from_topic/<uuid:id>/<str:op>/<uuid:tpk>/<int:usr>/', views.delete_incharge_from_topic,
         name="delete_incharge_from_topic"),

    # Company
    path('list_company/', views.list_company, name="list_company"),
    path('input_company/', views.InputCompanyView.as_view(), name="input_company"),
    path('update_company/<uuid:id>/', views.UpdateCompanyView.as_view(), name="update_company"),
    path('delete_company/<uuid:id>/', views.DeleteCompanyView.as_view(), name="delete_company"),

    # Forum
    path('list_forum/', views.list_forum, name="list_forum"),
    path('input_forum/', views.InputForumView.as_view(), name="input_forum"),
    path('update_forum/<uuid:id>/', views.UpdateForumView.as_view(), name="update_forum"),
    path('delete_forum/<uuid:id>/', views.DeleteForumView.as_view(), name="delete_forum"),

    # Meeting
    path('list_meeting/<str:op>/', views.list_meeting, name="list_meeting"),
    path('list_complete_approve/', views.list_complete_approve, name="list_complete_approve"),
    path('input_attachment/<uuid:id>/<str:op>/', views.InputAttachmentView.as_view(), name="input_attachment"),
    path('input_activity_attachment/<uuid:id>/<uuid:id2>/', views.InputActivityAttachmentView.as_view(),
         name="input_activity_attachment"),
    path('delete_lampiran/<uuid:id>/<str:op>/<uuid:id2>/', views.delete_lampiran, name="delete_lampiran"),
    path('delete_pdf/<uuid:id>/<uuid:id2>/', views.delete_pdf, name="delete_pdf"),
    path('delete_image/<uuid:id>/<uuid:id2>/', views.delete_image, name="delete_image"),
    path('input_meeting/<str:op>/', views.InputMeetingView.as_view(), name="input_meeting"),
    path('update_meeting/<uuid:id>/<str:op>/', views.UpdateMeetingView.as_view(), name="update_meeting"),

    # Meeting Approved
    path('list_meeting_pending/', views.list_meeting_pending, name="list_meeting_pending"),
    path('list_topic_review/<uuid:id>/', views.list_topic_review, name="list_topic_review"),
    path('review_topic/<uuid:tpk>/<uuid:apr>/', views.ReviewTopicView.as_view(), name="review_topic"),
    path('approve_meeting/<uuid:id>/', views.ApproveMeetingView.as_view(), name="approve_meeting"),

    # Outside Participant
    path('list_outside/', views.list_outside, name="list_outside"),
    path('input_outside/', views.InputOutsideView.as_view(), name="input_outside"),
    path('update_outside/<uuid:id>/', views.UpdateOutsideView.as_view(), name="update_outside"),
    path('update_outside_participant/<uuid:id>/<str:op>/', views.update_outside_participant,
         name="update_outside_participant"),
    path('add_outside_to_meeting/<uuid:meet>/<uuid:id>/<str:op>/', views.add_outside_to_meeting,
         name="add_outside_to_meeting"),
    path('delete_outside_from_meeting/<uuid:meet>/<uuid:id>/<str:op>/', views.delete_outside_from_meeting,
         name="delete_outside_from_meeting"),
    path('delete_outside/<uuid:id>/', views.DeleteOutsideView.as_view(), name="delete_outside"),

    # Topic
    path('input_topic/<uuid:id>/<str:op>/', views.InputTopicView.as_view(), name="input_topic"),
    path('update_pic_topic/<uuid:meet>/<uuid:id>/<str:op>/', views.update_pic_topic, name="update_pic_topic"),
    path('update_topic/<uuid:meet>/<uuid:id>/<str:op>/', views.UpdateTopicView.as_view(), name="update_topic"),
    path('add_pic_to_topic/<uuid:tpk>/<int:id>/<str:op>/', views.add_pic_to_topic,
         name="add_pic_to_topic"),
    path('delete_pic_from_topic/<uuid:tpk>/<int:id>/<str:op>/', views.delete_pic_from_topic,
         name="delete_pic_from_topic"),
    path('list_topic/<uuid:id>/<str:op>/', views.list_topic, name="list_topic"),
    path('overdue_all_pica/', views.overdue_all_pica, name='overdue_all_pica'),
    path('ongoing_all_pica/', views.ongoing_all_pica, name='ongoing_all_pica'),
    path('close_pica/<uuid:id>/', views.close_pica, name='close_pica'),
    path('change_pica_status/<uuid:id>/', views.change_pica_status, name='change_pica_status'),

    # Workflow
    path('update_workflow/<uuid:id>/', views.update_workflow, name="update_workflow"),
    path('update_cpmd/<uuid:id>/', views.update_cpmd, name="update_cpmd"),
    path('update_secretary/<uuid:id>/', views.update_secretary, name="update_secretary"),
    path('edit_workflow/<uuid:id>/<uuid:forum>/', views.EditWorkflowView.as_view(), name="edit_workflow"),
    path('add_bod_to_workflow/<int:id>/<uuid:forum>/', views.add_bod_to_workflow, name="add_bod_to_workflow"),
    path('add_cpmd_to_forum/<int:id>/<uuid:forum>/', views.add_cpmd_to_forum, name="add_cpmd_to_forum"),
    path('add_secretary_to_forum/<int:id>/<uuid:forum>/', views.add_secretary_to_forum, name="add_secretary_to_forum"),
    path('delete_bod_from_workflow/<int:id>/<uuid:forum>/', views.delete_bod_from_workflow,
         name="delete_bod_from_workflow"),
    path('delete_cpmd_from_forum/<int:id>/<uuid:forum>/', views.delete_cpmd_from_forum,
         name="delete_cpmd_from_forum"),
    path('delete_secretary_from_forum/<int:id>/<uuid:forum>/', views.delete_secretary_from_forum,
         name="delete_secretary_from_forum"),
    path('list_workflow/<uuid:id>/', views.list_workflow, name="list_workflow"),
    path('list_cpmd/<uuid:id>/', views.list_cpmd, name="list_cpmd"),
    path('list_secretary/<uuid:id>/', views.list_secretary, name="list_secretary"),

    # Internal Participant
    path('update_internal/<uuid:id>/<str:op>/', views.UpdateMeetingView.as_view(), name="update_internal"),
    # path('update_internal_participant/<uuid:id>/<str:op>/', views.update_internal_participant,
    #      name="update_internal_participant"),
    path('search_participant/<uuid:id>/<str:op>/', views.search_participant,
         name="search_participant"),
    path('add_participant_to_meeting/<uuid:meet>/<int:id>/<str:op>/', views.add_participant_to_meeting,
         name="add_participant_to_meeting"),
    path('delete_participant_from_meeting/<uuid:meet>/<int:id>/<str:op>/', views.delete_participant_from_meeting,
         name="delete_participant_from_meeting"),

    # Activity
    path('list_activity/', views.list_activity, name="list_activity"),
    path('list_notes/', views.list_notes, name="list_notes"),
    path('list_update_activity/<uuid:id>/', views.list_update_activity, name="list_update_activity"),
    path('input_activity/<uuid:id>/', views.InputActivityView.as_view(), name="input_activity"),
    path('update_activity/<uuid:id>/', views.UpdateActivityView.as_view(), name="update_activity"),
    path('delete_activity/<uuid:id>/', views.DeleteActivityView.as_view(), name="delete_activity"),
    path('status_activity/<uuid:id>/<int:op>/', views.status_activity, name="status_activity"),
    path('list_activity_attachment/<uuid:id>/<uuid:meet_id>/', views.list_activity_attachment,
         name="list_activity_attachment"),

    # Finish Check
    path('finish_check/<uuid:id>/<str:op>/', views.finish_check, name="finish_check"),
    path('list_finish_check/', views.list_finish_check, name='list_finish_check'),
    path('list_approve_meeting/<uuid:id>/', views.list_approve_meeting, name='list_approve_meeting'),

    # Search
    path('search_all/', views.search_all, name="search_all"),

    # PDF
    path('create_pdf/<uuid:id>/', views.create_pdf, name='create_pdf'),

    # Status Approval
    path('status_approval/', views.status_approval, name='status_approval'),
    path('cek_status_approval/<uuid:id>/', views.cek_status_approval, name='cek_status_approval'),
    path('verify/<str:token>/', views.verify, name='verify'),

    # Complete Approve
    path('export_to_excel/<uuid:id>/', views.export_to_excel, name='export_to_excel'),
    path('view_mom_complete_approve/<uuid:id>/', views.view_mom_complete_approve, name='view_mom_complete_approve'),

    # Reminder Notifications
    # path('reminder/', views.send_activity_duedate_notifications, name='send_activity_duedate_notifications'),
]
