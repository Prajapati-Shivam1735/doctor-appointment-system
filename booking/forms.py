from django import forms
from django.utils import timezone
from .models import Appointment

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = [
            'patient_name', 'patient_email', 'patient_phone', 
            'doctor', 'appointment_date', 'appointment_time', 
            'symptoms', 'payment_method'
        ]
        widgets = {
            'patient_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'patient_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'patient_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'doctor': forms.Select(attrs={'class': 'form-select'}),
            'appointment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'appointment_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'symptoms': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Describe symptoms...'}),
            'payment_method': forms.RadioSelect(attrs={'class': 'form-check-input'}),
        }

    def clean_appointment_date(self):
        appointment_date = self.cleaned_data.get('appointment_date')
        if appointment_date and appointment_date < timezone.localdate():
            raise forms.ValidationError("You cannot book an appointment for a past date.")
        return appointment_date

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        appointment_date = cleaned_data.get('appointment_date')
        appointment_time = cleaned_data.get('appointment_time')

        if doctor and appointment_date and appointment_time:
            conflict = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time
            ).exclude(status='CANCELLED')

            if self.instance and self.instance.pk:
                conflict = conflict.exclude(pk=self.instance.pk)

            if conflict.exists():
                raise forms.ValidationError(
                    f"Dr. {doctor.name} is already booked on {appointment_date} at {appointment_time}. Please select another time slot."
                )
        return cleaned_data