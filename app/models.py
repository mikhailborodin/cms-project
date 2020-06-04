# -*- coding: utf-8 -*-

"""Модели данных."""

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from .settings import DATABASE

metadata = sa.MetaData()
some_engine = sa.create_engine(DATABASE)
Session = sessionmaker(bind=some_engine)
Session = Session()

Users = sa.Table(
    'users',
    metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('name', sa.String(255)),
    sa.Column('username', sa.String(255), nullable=False),
    sa.Column('email', sa.String(255), nullable=False),
    sa.Column('birthday', sa.Date),
)

Stores = sa.Table(
    'stores',
    metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('title', sa.String(255)),

)
Orders_goods = sa.Table(
    'orders_goods',
    metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('order_id', sa.Integer, sa.ForeignKey('orders.id')),
    sa.Column('good_id', sa.Integer, sa.ForeignKey('goods.id')),
    sa.Column('num', sa.Integer),

)
Goods = sa.Table(
    'goods',
    metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('title', sa.String(255)),
    sa.Column('store_id', sa.Integer, sa.ForeignKey('stores.id')),
)

Orders = sa.Table(
    'orders',
    metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE')),
    sa.Column('created_at', sa.DateTime),
)

