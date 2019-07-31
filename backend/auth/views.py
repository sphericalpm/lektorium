import json
from time import time
from bson.objectid import ObjectId

from aiohttp import web
from aiohttp_security import remember, forget, authorized_userid


def redirect(request, router_name):
    url = request.app.router[router_name].url()
    raise web.HTTPFound(url)


async def get_user_by_name(conn, username):
    result = await conn.fetchrow(
        users
        .select()
        .where(users.c.username == username)
    )
    return result


async def validate_login_form(conn, form):

    username = form['username']
    password = form['password']

    if not username:
        return 'username is required'
    if not password:
        return 'password is required'

    user = await get_user_by_name(conn, username)

    if not user:
        return 'Invalid username'
    if not check_password_hash(password, user['password_hash']):
        return 'Invalid password'
    else:
        return None


class Login(web.View):
    async def login(request):
        username = await authorized_userid(request)
        if username:
            raise redirect(request.app.router, 'index')

        if request.method == 'POST':
            form = await request.post()

            async with request.app['db_pool'].acquire() as conn:
                error = await validate_login_form(conn, form)

                if error:
                    return {'error': error}
                else:
                    response = redirect(request.app.router, 'index')

                    user = await get_user_by_name(conn, form['username'])
                    await remember(request, response, user['username'])

                    raise response

        return {}


class Logout(web.View):
    async def logout(request):
        response = redirect(request.app.router, 'login')
        await forget(request, response)
        return response