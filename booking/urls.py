from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('book/', views.book_appointment, name='book_appointment'),
    path('track/', views.my_appointments, name='my_appointments'),
    path('appointment/<int:app_id>/cancel/', views.cancel_appointment_by_patient, name='patient_cancel'),
    path('appointment/<int:app_id>/reschedule/', views.reschedule_appointment, name='reschedule_appointment'),
    path('dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('appointment/<int:app_id>/status/<str:new_status>/', views.update_appointment_status, name='update_status'),
]