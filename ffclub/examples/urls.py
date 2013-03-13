from django.conf.urls.defaults import *

from . import views


urlpatterns = patterns('',
    url(r'^examples/$', views.home, name='examples.home'),
    url(r'^browserid/', include('django_browserid.urls')),
    url(r'^logout/?$', 'django.contrib.auth.views.logout', {'next_page': '/'},
        name='examples.logout'),
    url(r'^examples/bleach/?$', views.bleach_test, name='examples.bleach'),
)
