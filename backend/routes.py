from auth.views import Login, Logout, test1

routes = [
    ('*', '/api/login', Login, 'login'),
    ('*', '/api/logout', Logout, 'logout'),
    ('*', '/api/test1', test1, 'test1'),
]
