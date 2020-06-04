# -*- coding: utf-8 -*-

"""Генератор тестовых данных. Пример запуска python test_data 10 users."""

import sys
import os
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(BASE_DIR)

from app.models import metadata, Session
from sqlalchemy.types import Integer, String, Date, DateTime
from faker import Faker

fake = Faker()


def create_data(num, model_name):
    """Создает num записей для model модели."""
    i = 0
    model = Session.query(metadata.tables[model_name])
    while i < num:
        object_data = {}
        for column in model.column_descriptions:
            if isinstance(column['type'], Integer) and column['name'] != 'id':
                if fk := column['expr'].foreign_keys:
                    t_model, t_pk = next(iter(fk)).target_fullname.split('.')
                    t_obj = Session.query(metadata.tables[t_model]).first()
                    object_data[column['name']] = getattr(t_obj, t_pk)
                else:
                    object_data[column['name']] = random.randint
            if isinstance(column['type'], String):
                if column['name'] == 'email':
                    object_data[column['name']] = fake.email()
                else:
                    object_data[column['name']] = fake.name()
            if isinstance(column['type'], Date):
                object_data[column['name']] = fake.date()
            if isinstance(column['type'], DateTime):
                object_data[column['name']] = fake.date_time()

        insert_query = metadata.tables[model_name].insert().values(**object_data)
        Session.execute(insert_query)
        Session.commit()
        i += 1


def clear_data(model_name):
    """Полная очистка БД."""
    insert_query = metadata.tables[model_name].delete()
    Session.execute(insert_query)
    Session.commit()


if __name__ == "__main__":
    if sys.argv[1] == '--clear':
        clear_data(sys.argv[2])
    else:
        create_data(int(sys.argv[1]), sys.argv[2])
