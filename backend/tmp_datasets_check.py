import requests

s = requests.Session()
r = s.post('http://127.0.0.1:5000/api/auth/login', json={'email':'taniyabutola16@gmail.com','password':'Test1234'})
print('login', r.status_code)
print(r.text)

token = r.json().get('access_token')
if token:
    r2 = s.get('http://127.0.0.1:5000/api/datasets', headers={'Authorization': f'Bearer {token}'})
    print('datasets', r2.status_code)
    print(r2.text)
