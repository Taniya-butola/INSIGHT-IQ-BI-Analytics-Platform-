import requests

s = requests.Session()
r = s.post('http://127.0.0.1:5000/api/auth/login', json={'email':'test2@example.com','password':'Test1234'})
print('login', r.status_code)
print(r.text)

token = r.json().get('access_token')
if token:
    r2 = s.post('http://127.0.0.1:5000/api/datasets/2/eda', headers={'Authorization': f'Bearer {token}'})
    print('eda', r2.status_code)
    print(r2.text)
