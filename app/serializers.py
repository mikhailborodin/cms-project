# -*- coding: utf-8 -*-

"""Сериалайзеры моделей данных."""


from datetime import date

from app.models import Session, metadata


class BaseSerializer(object):
    qs = {}

    @staticmethod
    def _from_obj_to_dict(obj):
        res = {}
        as_dict = obj._asdict()
        for attr, val in as_dict.items():
            if isinstance(val, date):
                res[attr] = val.isoformat()
            else:
                res[attr] = val
        return res

    def to_json(self):
        """
        метод генерации json из объекта sqlalchemy
        :param obj: object
        :return: json
        """
        if isinstance(self.qs, list):
            return [self._from_obj_to_dict(item) for item in self.qs]
        else:
            return self._from_obj_to_dict(self.qs)


class GoodsSerializer(BaseSerializer):
    def __init__(self, qs):
        self.qs = qs


class StoresSerializer(BaseSerializer):
    def __init__(self, qs, id=None):
        self.qs = qs
        self.id = id

    def to_json(self):
        json = super().to_json()
        if not isinstance(self.qs, list):
            qoods_qs = Session.query(metadata.tables['goods']).filter_by(store_id=self.id).all()
            json['goods'] = GoodsSerializer(qoods_qs).to_json()
        return json


class UsersSerializer(BaseSerializer):
    def __init__(self, qs):
        self.qs = qs


class OrdersSerializer(BaseSerializer):
    def __init__(self, qs):
        self.qs = qs


def get_serializer(model_name):
    serializers = {
        'stores': StoresSerializer,
        'users': UsersSerializer,
        'orders': OrdersSerializer,
    }
    return serializers[model_name]
