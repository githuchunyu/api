from django.db import models

# Create your models here.
''' 文章分类 '''
class Kinds(models.Model):
    title = models.CharField(max_length=32)

''' 文章列表 '''
class List(models.Model):
    title = models.CharField(max_length=256)
    kind = models.IntegerField()
    time_create = models.IntegerField(default=0)
    time_publish = models.IntegerField(default=0)
    state = models.IntegerField(default=0)
    count_view = models.IntegerField(default=0)
    count_zan = models.IntegerField(default=0)
    cover_url = models.CharField(max_length=128)
    content = models.TextField()
    intro = models.TextField(default='')
    tags = models.CharField(max_length=256,default='')
