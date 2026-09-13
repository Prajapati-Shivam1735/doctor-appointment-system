# Create your views here.


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
        form = AppointmentForm()
    return render(request, 'booking/book.html', {'form': form})