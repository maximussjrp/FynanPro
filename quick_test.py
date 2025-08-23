import requests

s = requests.Session()
r = s.post('http://127.0.0.1:5000/login', data={'email':'admin@fynanpro.com','password':'admin123'})
print(f"Login: {r.status_code} Cookies: {dict(s.cookies)}")

d = s.get('http://127.0.0.1:5000/dashboard') 
print(f"Dashboard: {d.status_code} URL: {d.url}")

if d.status_code == 200 and 'login' not in d.url:
    print("✅ LOGIN FUNCIONOU!")
else:
    print("❌ Login ainda não funcionou")
