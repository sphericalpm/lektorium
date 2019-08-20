from time import time
from typing import Dict
from aiohttp import web
from aiohttp_session import get_session
from aiohttp_security import remember, forget, authorized_userid


def redirect(request, router_name: str):
    url = request.app.router[router_name].url()
    raise web.HTTPFound(url)


def set_session(session, username: str, request):
    session['user'] = username
    session['last_visit'] = time()
    redirect(request, 'main')


async def validate_login_form(data: Dict[str, str]):
    username = data['username']
    if not username:
        return 'username is required'
    return None


class Login(web.View):
    async def get(self):
        session = await get_session(self.request)
        if session.get('user'):
            redirect(self.request, 'main')
        return {'content': 'Please enter login or email'}

    async def post(self):
        data = await self.request.post()
        error = await validate_login_form(data)
        if error:
            return {'error': error}

        session = await get_session(self.request)
        set_session(session, data['username'], self.request)


class Logout(web.View):
    async def logout(request):
        response = redirect(request.app.router, 'login')
        await forget(request, response)
        return response
