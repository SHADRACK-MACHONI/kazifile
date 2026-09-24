from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('upload/', views.upload_view, name='upload'),
    path('delete/<int:doc_id>/', views.delete_document, name='delete_document'),
    path('share/<int:doc_id>/', views.create_share_link, name='create_share_link'),
    path('shared/<str:token>/', views.view_shared_document, name='view_shared_document'),
    path('logs/<int:doc_id>/', views.document_log_view, name='document_log'),
    path('verify/', views.verify_document_view, name='verify_document'),
]