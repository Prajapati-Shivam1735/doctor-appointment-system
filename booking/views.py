from django.db import models
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Doctor, Department, Appointment
from .forms import AppointmentForm

def home(request):
    dept_id = request.GET.get('dept')
    departments = Department.objects.all()
    
    if dept_id:
        doctors = Doctor.objects.filter(department_id=dept_id).select_related('department')
    else:
        doctors = Doctor.objects.select_related('department').all()
        
    return render(request, 'booking/home.html', {
        'doctors': doctors, 
        'departments': departments,
        'selected_dept': dept_id
    })

def book_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save()
            return render(request, 'booking/success.html', {'appointment': appointment})
    else:
        doctor_id = request.GET.get('doctor_id')
        initial_data = {}
        if doctor_id:
            initial_data['doctor'] = doctor_id
        form = AppointmentForm(initial=initial_data)
        
    return render(request, 'booking/book.html', {'form': form})


def my_appointments(request):
    query = request.GET.get('q', '').strip()
    appointments = []
    searched = False
    
    if query:
        searched = True
        # Email ya Phone number dono se search kar sakega
        appointments = Appointment.objects.filter(
            models.Q(patient_email__iexact=query) | models.Q(patient_phone__icontains=query)
        ).select_related('doctor', 'doctor__department').order_by('-created_at')

    return render(request, 'booking/my_appointments.html', {
        'appointments': appointments,
        'query': query,
        'searched': searched
    })

from django.contrib.auth.decorators import login_required

@login_required
def staff_dashboard(request):
    status_filter = request.GET.get('status', '')
    appointments = Appointment.objects.select_related('doctor', 'doctor__department').order_by('-appointment_date', '-appointment_time')
    
    if status_filter:
        appointments = appointments.filter(status=status_filter)
        
    return render(request, 'booking/staff_dashboard.html', {
        'appointments': appointments,
        'status_filter': status_filter
    })

@login_required
def update_appointment_status(request, app_id, new_status):
    if request.method == 'POST':
        try:
            appointment = Appointment.objects.get(id=app_id)
            if new_status in ['PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED']:
                appointment.status = new_status
                appointment.save()
        except Appointment.DoesNotExist:
            pass
    return redirect(request.META.get('HTTP_REFERER', 'staff_dashboard'))