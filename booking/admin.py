from django.contrib import admin
from .models import Department, Doctor, Appointment

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'specialization', 'phone', 'consultation_fee')
    list_filter = ('department',)
    search_fields = ('name', 'specialization', 'email')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'doctor', 'appointment_date', 'appointment_time', 'patient_phone', 'status')
    list_filter = ('status', 'appointment_date', 'doctor')
    search_fields = ('patient_name', 'patient_phone', 'patient_email')
    list_editable = ('status',)
    date_hierarchy = 'appointment_date'