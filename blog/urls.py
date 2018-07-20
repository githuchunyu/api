from django.urls import path
from blog import views

urlpatterns = [
    path('kinds', views.list_kinds),
    path('kind/save', views.save_kind),
    path('kind/delete', views.delete_kind),
    path('list', views.list_blogs),
    path('detail', views.detail_blog),
    path('save', views.save_blog),
    path('state', views.state_blog),
    path('kind', views.kind_blog),
    path('view', views.view_blog),
    path('zan', views.zan_blog),
    path('cover', views.upload_cover),
]
