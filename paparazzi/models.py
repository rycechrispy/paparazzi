# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.utils.encoding import python_2_unicode_compatible

class EnumField(models.Field):
    def __init__(self, *args, **kwargs):
        super(EnumField, self).__init__(*args, **kwargs)
        assert self.choices, "Need choices for enumeration"

    def db_type(self, connection):
        if not all(isinstance(col, basestring) for col, _ in self.choices):
            raise ValueError("MySQL ENUM values should be strings")
        return "ENUM({})".format(','.join("'{}'".format(col) 
                                          for col, _ in self.choices))

@python_2_unicode_compatible
class Item(models.Model):
    categories = (
        ("bracelet", "Bracelet"),
        ("earring", "Earring"),
        ("ring", "Ring"),
        ("necklace", "Necklace"), 
        ("hair-clip", "Hair-Clip"),
        ("headband", "Headband"),
    )

    title_original = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255, db_index=True)
    color = models.CharField(max_length=128, db_index=True, null=True)
    image_url = models.URLField(max_length=1536, null=True)
    url = models.URLField(max_length=1536, null=True)
    being_sold = models.BooleanField(default=False, db_index=True)
    category = EnumField(choices=categories, default=None, null=True)
    date_found_sold = models.DateField(default=None, db_index=True, null=True)
    date_created = models.DateField(db_index=True)
    last_modified = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        unique_together = ('title', 'color',)

    def __str__(self):
        return self.title_original

    @classmethod
    def create(cls, title_original, title, date_created, color=None, image_url=None, url=None, being_sold=False, date_found_sold=None):
        item = cls()
        item.title_original = title_original
        item.title = title
        item.color = color
        item.image_url = image_url
        item.url = url
        item.being_sold = being_sold
        item.date_found_sold = date_found_sold
        item.date_created = date_created
        return item

    def _hash_url(self):
        url_bytes = self.image_url.encode('utf-8')
        self.url_hash = sha.new(url_bytes).hexdigest()
        return self.url_hash

    def _update(self, obj, session=None):
        columns = obj.__dict__.keys()
        for col in columns:
            value = getattr(obj, col)
            if value == '':
                value = None
            setattr(self, col, value)
        obj.save()

    @classmethod
    def from_dict(cls, data, session=None):
        title_original = data.get('title_original')
        title = data.get('title')

        obj = cls.create(title_original, title)
        for name, value in data.iteritems():
            if value == '':
                value = None
            setattr(obj, name, value)
        return obj

@python_2_unicode_compatible
class Stock(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0, db_index=True)
    date_created = models.DateField(db_index=True)
    last_modified = models.DateTimeField(auto_now=True, db_index=True)

    def __str__(self):
        return '%s, %s' % (self.item, self.quantity)

    @classmethod
    def create(cls, item_id, quantity, date_created):
        item = cls()
        item.item_id = item_id
        item.quantity = quantity
        item.date_created = date_created
        return item

    @classmethod
    def from_dict(cls, data, session=None):
        item_id = data.get('item_id')
        quantity = data.get('quantity')
        obj = cls(item_id, quantity)
        return obj

@python_2_unicode_compatible
class UserItemStock(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity_reserved = models.IntegerField(default=0, db_index=True)
    date_created = models.DateField(db_index=True)
    last_modified = models.DateTimeField(auto_now=True, db_index=True)

    def __str__(self):
        return self.quantity_reserved