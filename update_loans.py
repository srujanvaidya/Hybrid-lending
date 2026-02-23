import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from api.models import LoanRequest

loans = LoanRequest.objects.filter(status='Pending')
count = loans.update(status='Approved')
print(f"Updated {count} loans to Approved.")
