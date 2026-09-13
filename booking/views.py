from django.db import models
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Doctor, Department, Appointment
from .forms import AppointmentForm

def home(request):
    doctors = Doctor.objects.select_related('department').all()
    departments = Department.objects.all()
    return render(request, 'booking/home.html', {'doctors': doctors, 'departments': departments})

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