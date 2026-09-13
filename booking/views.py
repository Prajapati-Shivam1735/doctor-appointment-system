from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from .models import Doctor, Department, Appointment
from .forms import AppointmentForm

def send_booking_email(appointment, subject, message_body):
    """Helper function to send simulated email notifications"""
    try:
        send_mail(
            subject=subject,
            message=message_body,
            from_email=None,
            recipient_list=[appointment.patient_email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Email sending error: {e}")

def home(request):
    dept_id = request.GET.get('dept')
    search_query = request.GET.get('q', '').strip()
    departments = Department.objects.all()
    doctors = Doctor.objects.select_related('department').all()

    if dept_id:
        doctors = doctors.filter(department_id=dept_id)

    if search_query:
        doctors = doctors.filter(
            models.Q(name__icontains=search_query) |
            models.Q(specialization__icontains=search_query) |
            models.Q(department__name__icontains=search_query) |
            models.Q(department__description__icontains=search_query)
        ).distinct()

    return render(request, 'booking/home.html', {
        'doctors': doctors, 
        'departments': departments,
        'selected_dept': dept_id,
        'search_query': search_query
    })

def book_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save()
            # Send booking confirmation email
            email_msg = (
                f"Hello {appointment.patient_name},\n\n"
                f"Your appointment with Dr. {appointment.doctor.name} has been received.\n"
                f"Date: {appointment.appointment_date}\n"
                f"Time: {appointment.appointment_time}\n"
                f"Current Status: {appointment.get_status_display()}\n\n"
                f"Thank you for choosing DocPulse!"
            )
            send_booking_email(appointment, "Appointment Reserved - DocPulse", email_msg)
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
        appointments = Appointment.objects.filter(
            models.Q(patient_email__iexact=query) | models.Q(patient_phone__icontains=query)
        ).select_related('doctor', 'doctor__department').order_by('-created_at')

    return render(request, 'booking/my_appointments.html', {
        'appointments': appointments,
        'query': query,
        'searched': searched
    })

def cancel_appointment_by_patient(request, app_id):
    if request.method == 'POST':
        appointment = get_object_or_404(Appointment, id=app_id)
        if appointment.status != 'COMPLETED':
            appointment.status = 'CANCELLED'
            appointment.save()
            # Cancellation email
            email_msg = f"Hello {appointment.patient_name},\n\nYour appointment with Dr. {appointment.doctor.name} on {appointment.appointment_date} has been CANCELLED."
            send_booking_email(appointment, "Appointment Cancelled - DocPulse", email_msg)
    return redirect(request.META.get('HTTP_REFERER', 'my_appointments'))

def reschedule_appointment(request, app_id):
    appointment = get_object_or_404(Appointment, id=app_id)
    if request.method == 'POST':
        new_date = request.POST.get('appointment_date')
        new_time = request.POST.get('appointment_time')

        if new_date and new_time:
            # Conflict check
            conflict = Appointment.objects.filter(
                doctor=appointment.doctor,
                appointment_date=new_date,
                appointment_time=new_time
            ).exclude(status='CANCELLED').exclude(id=appointment.id)

            if conflict.exists():
                messages.error(request, f"Dr. {appointment.doctor.name} is already booked at that slot.")
            else:
                appointment.appointment_date = new_date
                appointment.appointment_time = new_time
                appointment.status = 'PENDING'
                appointment.save()
                email_msg = f"Hello {appointment.patient_name},\n\nYour appointment with Dr. {appointment.doctor.name} has been rescheduled to {new_date} at {new_time}."
                send_booking_email(appointment, "Appointment Rescheduled - DocPulse", email_msg)
                messages.success(request, "Appointment successfully rescheduled!")
                return redirect(f"/track/?q={appointment.patient_phone}")

    return render(request, 'booking/reschedule.html', {'appointment': appointment})

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
        appointment = get_object_or_404(Appointment, id=app_id)
        if new_status in ['PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED']:
            appointment.status = new_status
            appointment.save()
            # Send status update email to patient
            email_msg = (
                f"Hello {appointment.patient_name},\n\n"
                f"The status of your appointment with Dr. {appointment.doctor.name} has been updated to: {appointment.get_status_display()}.\n"
                f"Date: {appointment.appointment_date} at {appointment.appointment_time}."
            )
            send_booking_email(appointment, f"Appointment Status: {appointment.get_status_display()}", email_msg)
    return redirect(request.META.get('HTTP_REFERER', 'staff_dashboard'))