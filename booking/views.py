import io
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from .models import Doctor, Department, Appointment
from .forms import AppointmentForm
# from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
# from django.contrib.auth.decorators import login_required

# --- Patient Register ---
def patient_register(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        full_name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        # Check agar username (phone) pehle se exist karta hai
        if User.objects.filter(username=phone).exists():
            messages.error(request, "Yeh phone number pehle se registered hai!")
            return redirect('patient_register')

        # Naya user create karein
        user = User.objects.create_user(
            username=phone,
            email=email,
            password=password,
            first_name=full_name
        )
        login(request, user)
        messages.success(request, f"Welcome to DocPulse, {full_name}!")
        return redirect('book')

    return render(request, 'booking/patient_register.html')


# --- Patient Login ---
def patient_login(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        user = authenticate(request, username=phone, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect('book')
        else:
            messages.error(request, "Galat phone number ya password!")

    return render(request, 'booking/patient_login.html')

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
            appointment = form.save(commit=False)
            
            # Direct Pay at Clinic Setup
            appointment.payment_method = 'AT_CLINIC'
            appointment.payment_status = 'PENDING'
            appointment.status = 'CONFIRMED'
            appointment.save()

            # Confirmation Email
            try:
                email_msg = (
                    f"Hello {appointment.patient_name},\n\n"
                    f"Your appointment with Dr. {appointment.doctor.name} is confirmed for "
                    f"{appointment.appointment_date} at {appointment.appointment_time}.\n"
                    f"Appointment ID: #{appointment.id}\n"
                    f"Payment Option: Pay at Hospital (₹{appointment.doctor.consultation_fee}).\n\n"
                    f"Thank you for choosing DocPulse!"
                )
                send_booking_email(appointment, "Appointment Confirmed (Pay at Clinic) - DocPulse", email_msg)
            except Exception as e:
                print("Email sending error:", e)

            # Direct Success Page Render
            return render(request, 'booking/success.html', {'appointment': appointment})
    else:
        doctor_id = request.GET.get('doctor_id')
        form = AppointmentForm(initial={'doctor': doctor_id} if doctor_id else None)
        
    return render(request, 'booking/book.html', {'form': form})

@csrf_exempt
def payment_callback(request, app_id):
    appointment = get_object_or_404(Appointment, id=app_id)
    
    if request.method == 'POST':
        payment_id = request.POST.get('razorpay_payment_id', 'pay_test_default')
        
        # Update booking records
        appointment.razorpay_payment_id = payment_id
        appointment.payment_status = 'PAID'
        appointment.status = 'CONFIRMED'
        appointment.save()

        # Send confirmation email safely
        try:
            email_msg = (
                f"Dear {appointment.patient_name},\n\n"
                f"Your payment has been received successfully!\n"
                f"Appointment ID: #{appointment.id}\n"
                f"Doctor: Dr. {appointment.doctor.name}\n"
                f"Slot: {appointment.appointment_date} at {appointment.appointment_time}\n"
                f"Status: Confirmed\n\n"
                f"Thank you for choosing DocPulse!"
            )
            send_booking_email(appointment, "Appointment & Payment Confirmed - DocPulse", email_msg)
        except Exception as e:
            print("Email failed, but continuing:", e)

        return render(request, 'booking/success.html', {'appointment': appointment})

    return redirect('track_appointment')

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

@login_required(login_url='/admin/login/')
def staff_dashboard(request):
    status_filter = request.GET.get('status', '')
    all_appointments = Appointment.objects.select_related('doctor', 'doctor__department')
    
    # --- Analytics Calculations ---
    total_count = all_appointments.count()
    pending_count = all_appointments.filter(status='PENDING').count()
    confirmed_count = all_appointments.filter(status='CONFIRMED').count()
    completed_count = all_appointments.filter(status='COMPLETED').count()
    cancelled_count = all_appointments.filter(status='CANCELLED').count()

    # Total Revenue from Completed appointments
    total_revenue = all_appointments.filter(status='COMPLETED').aggregate(
        total=models.Sum('doctor__consultation_fee')
    )['total'] or 0

    appointments = all_appointments.order_by('-appointment_date', '-appointment_time')
    if status_filter:
        appointments = appointments.filter(status=status_filter)
        
    return render(request, 'booking/staff_dashboard.html', {
        'appointments': appointments,
        'status_filter': status_filter,
        'stats': {
            'total': total_count,
            'pending': pending_count,
            'confirmed': confirmed_count,
            'completed': completed_count,
            'cancelled': cancelled_count,
            'revenue': total_revenue,
        }
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

def download_appointment_pdf(request, app_id):
    appointment = get_object_or_404(Appointment, id=app_id)

    # In-memory buffer create karein
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # --- PDF Styling ---
    # Header Background Banner
    p.setFillColor(colors.HexColor("#0284c7"))
    p.rect(0, height - 100, width, 100, stroke=0, fill=1)

    # Header Brand Text
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 24)
    p.drawString(50, height - 55, "DocPulse Healthcare")
    p.setFont("Helvetica", 11)
    p.drawString(50, height - 75, "Official Appointment Confirmation Receipt")

    # Content Box Border
    p.setStrokeColor(colors.HexColor("#cbd5e1"))
    p.setLineWidth(1)
    p.roundRect(50, height - 420, width - 100, 300, 10, stroke=1, fill=0)

    # Details Title
    p.setFillColor(colors.HexColor("#0f172a"))
    p.setFont("Helvetica-Bold", 14)
    p.drawString(70, height - 140, f"Appointment Slip - Ref #{appointment.id:05d}")

    # Key-Value Details
    y = height - 175
    line_gap = 25
    details = [
        ("Patient Name:", appointment.patient_name),
        ("Contact Phone:", appointment.patient_phone),
        ("Email Address:", appointment.patient_email),
        ("Doctor Name:", appointment.doctor.name if appointment.doctor.name.startswith("Dr.") else f"Dr. {appointment.doctor.name}"),
        ("Department:", appointment.doctor.department.name),
        ("Specialization:", appointment.doctor.specialization),
        ("Scheduled Date:", str(appointment.appointment_date)),
        ("Scheduled Time:", str(appointment.appointment_time)),
        ("Status:", appointment.get_status_display()),
        ("Consultation Fee:", f"INR {appointment.doctor.consultation_fee}"),
    ]

    for label, val in details:
        p.setFont("Helvetica-Bold", 10)
        p.setFillColor(colors.HexColor("#475569"))
        p.drawString(70, y, label)

        p.setFont("Helvetica", 10)
        p.setFillColor(colors.HexColor("#0f172a"))
        p.drawString(200, y, str(val))
        y -= line_gap

    # Footer note
    p.setFont("Helvetica-Oblique", 9)
    p.setFillColor(colors.HexColor("#64748b"))
    p.drawString(50, height - 450, "Please present this digital receipt or printout at the reception 15 minutes before your time.")
    p.drawString(50, height - 465, "Generated automatically by DocPulse Healthcare Portal.")

    p.showPage()
    p.save()
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Appointment_{appointment.id}_{appointment.patient_name}.pdf"'
    return response

def user_logout(request):
    logout(request)
    return redirect('home')