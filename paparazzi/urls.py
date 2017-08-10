from django.conf.urls import url

import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(?P<page>[0-9]+)/$', views.index, name='index'),
    url(r'^admin$', views.admin, name='admin'),
    url(r'^get_admin_items$', views.get_admin_items, name='get_admin_items'),
    url(r'^get_stock_items$', views.get_stock_items, name='get_stock_items'),
    url(r'^sell_item$', views.sell_item, name='sell_item'),
    url(r'^delete_item$', views.delete_item, name='delete_item'),
]