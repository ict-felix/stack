from django.conf.urls.defaults import *
from egeni.clearinghouse.models import AggregateManager

urlpatterns = patterns('egeni.clearinghouse.views',
    url(r'^$', 'home', name='home'),
    url(r'^(?P<slice_id>\w+)/slice_detail/$', 'slice_detail', name='slice_detail'),
    url(r'^(?P<slice_id>\w+)/slice_flash_detail/$', 'slice_flash_detail', name='slice_flash_detail'),
    url(r'^(?P<slice_id>\w+)/slice_flash_detail/topo/$', 'slice_get_topo', name='slice_get_topo'),
    url(r'^(?P<slice_id>\w+)/slice_flash_detail/img/(?P<img_name>[\w.]+)$', 'slice_get_img', name='slice_get_img'),
    url(r'^(?P<slice_id>\w+)/slice_flash_detail/plugin.jar$', 'slice_get_plugin', name='slice_get_plugin'),
    url(r'^(?P<slice_id>\w+)/slice_flash_detail/plugin.xsd$', 'slice_get_xsd', name='slice_get_xsd'),
#    url(r'^(?P<slice_id>\w+)/(?P<am_id>\d+)/selectnodes/$', 'resv_sel_nodes', name='sel_nodes'),
#    url(r'^aggmgr-(?P<am_id>\d+)/detail/$', 'aggmgr_detail', name='am_detail'),
#    (r'^create/$', 'create'),
#    (r'^(?P<object_id>\d+)/delete/$', 'delete'),
#    (r'^(?P<aggMgr_id>\d+)/node/(?P<node_id>\w+)/reserve/$', 'node_reserve'),
)

