import traceback
from app import create_app

app = create_app()
client = app.test_client()
r = client.post('/api/auth/login', json={'email':'taniyabutola16@gmail.com','password':'Test1234'})
print('login', r.status_code)
print(r.get_json())
token = r.get_json()['access_token']
try:
    resp = client.post('/api/datasets/2/eda', headers={'Authorization': f'Bearer {token}'})
    print('status', resp.status_code)
    print(resp.get_data(as_text=True)[:3000])
except Exception:
    traceback.print_exc()
