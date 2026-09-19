from backend import create_app

app = create_app()
client = app.test_client()

home = client.get('/')
print('HOME', home.status_code, 'ByteNest' in home.get_data(as_text=True))

signup = client.post('/api/signup', json={'username': 'tester', 'email': 'tester@example.com', 'password': 'pass123'})
print('SIGNUP', signup.status_code, signup.get_json())

login = client.post('/api/login', json={'username_or_email': 'tester', 'password': 'pass123'})
print('LOGIN', login.status_code, login.get_json())

create_file = client.post('/api/files', json={'title': 'Notes', 'content': 'hello'})
print('CREATE', create_file.status_code, create_file.get_json())

list_files = client.get('/api/files')
print('LIST', list_files.status_code, list_files.get_json()['files'][0]['title'])

logout = client.post('/api/logout')
print('LOGOUT', logout.status_code, logout.get_json())
