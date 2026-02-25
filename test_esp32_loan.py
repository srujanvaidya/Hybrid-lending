import requests

# Make sure to run the Django development server first: `python manage.py runserver`

BASE_URL = 'http://127.0.0.1:8000/api'
LOGIN_URL = f'{BASE_URL}/login/'
ESP32_LOAN_URL = f'{BASE_URL}/esp32/loan-request/'

def test_esp32_endpoint(email, password, amount, tenure):
    print(f"Logging in as {email}...")
    # 1. Login to get the token
    login_data = {
        'email': email,
        'password': password
    }
    
    response = requests.post(LOGIN_URL, json=login_data)
    
    if response.status_code != 200:
        print(f"Login failed: {response.status_code} - {response.text}")
        return
        
    token = response.json().get('token')
    print(f"Login successful. Token: {token}")
    
    # 2. Call the ESP32 endpoint with the token
    headers = {
        'Authorization': f'Token {token}',
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
    # Replace with a valid borrower email and password from your DB
    test_email = "borrower@example.com" 
    test_password = "password123"
    
    test_esp32_endpoint(test_email, test_password, amount=100.50, tenure=12)
