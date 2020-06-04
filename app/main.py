# -*- coding: utf-8 -*-

"""Модели данных."""

import asyncio
import json
from datetime import datetime
from http import HTTPStatus

import aioredis

from aiohttp import web
from aiohttp_session import STORAGE_KEY, get_session, new_session, setup
from aiohttp_session.redis_storage import RedisStorage
from app.models import Session, metadata
from app.serializers import get_serializer
from app.settings import REDIS


async def make_redis_pool():
    redis_address = REDIS
    return await aioredis.create_redis_pool(redis_address, timeout=1)


def login_required(fn):
    """Декоратор для проверки авторизации."""
    async def wrapped(request, *args, **kwargs):
        app = request.app
        router = app.router
        session = await get_session(request)
        if 'user_id' not in session:
            return web.HTTPFound(router['login'].url_for())
        user_id = session['user_id']
        user = Session.query(metadata.tables['users']).filter_by(id=user_id)
        app['user'] = user[0]
        return await fn(request, *args, **kwargs)
    return wrapped


@login_required
async def handler(request):
    """Метод возрващает информмацию о пользователе и историю его заказов."""
    user = request.app['user']
    user_info = get_serializer('users')(user).to_json()
    orders_qs = Session.query(metadata.tables['orders']).filter_by(user_id=user.id).all()
    user_info['orders'] = get_serializer('orders')(orders_qs).to_json()
    return web.Response(body=json.dumps(user_info), content_type='application/json')


async def public_detail(request):
    """Публичный метод просмотра детальной информации объекта модели."""
    model = request.match_info['model']
    object_id = request.match_info['id']
    qs = Session.query(metadata.tables[model]).filter_by(id=object_id).first()
    json_object = get_serializer(model)(qs, id=object_id).to_json()
    return web.Response(body=json.dumps(json_object), content_type='application/json')


async def public_list(request):
    """Публичный метод просмотра детальной информации списка обёектов модели."""
    model = request.match_info['model']
    qs = Session.query(metadata.tables[model]).all()
    json_list = get_serializer(model)(qs).to_json()  # [to_json(obj._asdict()) for obj in qs]
    return web.Response(body=json.dumps(json_list), content_type='application/json')


async def login(request):
    """Метод авторизации пользователя."""
    router = request.app.router
    form = await request.json()
    try:
        user = Session.query(metadata.tables['users']).filter_by(**form)
        session = await new_session(request)
        session['user_id'] = user[0].id
        return web.HTTPFound(router['restricted'].url_for())
    except ValueError or KeyError:
        return web.Response(text='No such user', status=HTTPStatus.FORBIDDEN)


async def logout(request):
    """Метод деавторизации пользователя."""
    storage = request.get(STORAGE_KEY)
    with await storage._redis as conn:
        cookie = storage.load_cookie(request)
        key = 'AIOHTTP_SESSION_' + cookie
        data = await conn.get(key)
        if data is not None:
            conn.delete(key)
    return web.Response(status=HTTPStatus.OK)


@login_required
async def add_order(request):
    """Метод добавления заказа пользователем."""
    user = request.app['user']
    request_body = await request.json()
    order_data = {
        'user_id': user.id,
        'created_at': datetime.now().isoformat()
    }
    insert_query = metadata.tables['orders'].insert().values(**order_data)
    result = Session.execute(insert_query)
    Session.commit()
    [item.update({'order_id': result.inserted_primary_key[0]}) for item in request_body]
    Session.execute(metadata.tables['orders_goods'].insert(), request_body)
    Session.commit()
    return web.Response(status=HTTPStatus.CREATED)


def make_app():
    loop = asyncio.get_event_loop()
    redis_pool = loop.run_until_complete(make_redis_pool())
    storage = RedisStorage(redis_pool)

    async def dispose_redis_pool(app):
        redis_pool.close()
        await redis_pool.wait_closed()

    app = web.Application()
    setup(app, storage)
    app.on_cleanup.append(dispose_redis_pool)
    app.router.add_get(r'/', handler, name='restricted')
    app.router.add_post(r'/login', login, name='login')
    app.router.add_post(r'/logout', logout, name='logout')
    app.router.add_post(r'/order', add_order, name='add_order')
    app.router.add_get(r'/{model:\s+}', public_list, name='list')
    app.router.add_get(r'/{model:\s+}/{id:\d+}', public_detail, name='detail')
    return app


web.run_app(make_app())
