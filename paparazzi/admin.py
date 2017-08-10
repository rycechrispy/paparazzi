# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from .models import Item, Stock, UserItemStock

admin.site.register(Item)
admin.site.register(Stock)
admin.site.register(UserItemStock)