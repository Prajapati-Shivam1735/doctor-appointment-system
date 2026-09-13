from django.db import models

from django.contrib.auth.models import User

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile', null=True, blank=True)
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='doctors')
    specialization = models.CharField(max_length=150)
    phone = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)

    def __str__(self):
        # Agar name me pehle se 'Dr.' hai toh dubara na jode
        prefix = "" if self.name.strip().startswith("Dr.") else "Dr. "
        return f"{prefix}{self.name} ({self.department.name})"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    patient_name = models.CharField(max_length=100)
    patient_email = models.EmailField()
    patient_phone = models.CharField(max_length=15)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    symptoms = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient_name} - {self.doctor.name} ({self.appointment_date})"