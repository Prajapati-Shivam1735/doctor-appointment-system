from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Doctor(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='doctors')
    name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=150)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=500.00)

    def __str__(self):
        prefix = "" if self.name.strip().startswith("Dr.") else "Dr. "
        return f"{prefix}{self.name} ({self.department.name})"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('AT_CLINIC', 'Pay at Hospital / Clinic'),
        ('ONLINE', 'Pay Online (UPI / Card)'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
    ]

    patient_name = models.CharField(max_length=100)
    patient_email = models.EmailField()
    patient_phone = models.CharField(max_length=15)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    symptoms = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Payment Fields
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='AT_CLINIC')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient_name} - {self.doctor.name} ({self.appointment_date})"