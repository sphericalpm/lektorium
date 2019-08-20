from auth.views import Login, Logout

routes = [
    ('*', '/login', Login, 'login'),
    ('*', '/logout', Logout, 'logout'),
]
