import requests

# Make sure to run the Django development server first: `python manage.py runserver`

BASE_URL = 'http://127.0.0.1:8000/api'
ESP32_LOAN_URL = f'{BASE_URL}/esp32/loan-request/'

def test_esp32_endpoint(amount, tenure):
    print(f"Testing disabled-auth ESP32 Loan Endpoint...")
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    loan_data = {
        'amount': amount,
        'tenure': tenure
    }
    
    print(f"Requesting loan of {amount} for {tenure} months via ESP32 endpoint...")
    loan_response = requests.post(ESP32_LOAN_URL, json=loan_data, headers=headers)
    
    print(f"Response Status: {loan_response.status_code}")
    print(f"Response Data: {loan_response.json()}")

if __name__ == '__main__':
    test_esp32_endpoint(amount=50.25, tenure=6)
