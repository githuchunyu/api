from django.shortcuts import render
from django import forms
from blog import models
from api.base import check,ReturnData,cleanData,createList
import os
import hashlib
import time
from django.db.models import F
# Create your views here.


''' 获取博客种类列表 '''
@check()
def list_kinds(request):
    kds = list(models.Kinds.objects.all().values())
    return ReturnData(data=kds)

''' 新增种类 '''
class KindSaveForm(forms.Form):
    id = forms.IntegerField()
    title = forms.CharField()

@check(formclass=KindSaveForm)
def save_kind(request):
    id = int(request.POST.get('id'))
    title = request.POST.get('title')
    if id==0:
        models.Kinds.objects.create(title=title)
    else:
        models.Kinds.objects.filter(id=id).update(title=title)
    return ReturnData()


''' 删除种类 '''
class KindDeleteForm(forms.Form):
    id = forms.IntegerField()

@check(formclass=KindDeleteForm)
def delete_kind(request):
    id = int(request.POST.get('id'))
    ats = models.List.objects.filter(kind=id)
    if ats.count()>0:
        return ReturnData(85)
    else:
        models.Kinds.filter(id=id).delete()
        return ReturnData()


''' 获取博客列表 '''
class ListForm(forms.Form):
    kind = forms.IntegerField(required=False)
    def clean_kind(self):
        return cleanData(self,'kind',0)
    page_size = forms.IntegerField(required=False)
    def clean_page_size(self):
        return cleanData(self,'page_size',12)
    page_num = forms.IntegerField(required=False)
    def clean_page_num(self):
        return cleanData(self,'page_num',0)
    state = forms.IntegerField(required=False)
    def clean_state(self):
        return cleanData(self,'state',100)

@check(formclass=ListForm)
def list_blogs(request):
    kind = int(request.GET.get('kind'))
    page_size = int(request.GET.get('page_size'))
    page_num = int(request.GET.get('page_num'))
    state = int(request.GET.get('state'))
    if kind==0:
        blogs = models.List.objects.all()
    else:
        blogs = models.List.objects.filter(kind=kind)
    if state!=100:
        blogs = blogs.filter(state=state)
    ajson = createList(ws=blogs,page_num=page_num,page_size=page_size)
    for i in range(len(ajson['list'])):
        ajson['list'][i]['kind_text'] = models.Kinds.objects.get(id=ajson['list'][i]['kind']).title
    return ReturnData(data=ajson)


''' 获取博客内容 '''
class DetailBlogForm(forms.Form):
    id = forms.IntegerField()

@check(formclass=DetailBlogForm)
def detail_blog(request):
    id = int(request.GET.get('id'))
    ajson = list(models.List.objects.filter(id=id).values())[0]
    ajson['kind_text'] = models.Kinds.objects.get(id=ajson['kind']).title
    return ReturnData(data=ajson)


''' 编辑博客内容 '''
class BlogSaveForm(forms.Form):
    id = forms.IntegerField()
    kind = forms.IntegerField()
    title = forms.CharField()
    intro = forms.CharField()
    cover_url = forms.CharField()
    content = forms.CharField()
    tags = forms.CharField(required=False)

@check(formclass=BlogSaveForm)
def save_blog(request):
    id = int(request.POST.get('id'))
    kind = int(request.POST.get('kind'))
    title = request.POST.get('title')
    intro =  request.POST.get('intro')
    cover_url = request.POST.get('cover_url')
    content = request.POST.get('content')
    tags = request.POST.get('tags')
    canshu = {'kind':kind,'title':title,'intro':intro,'cover_url':cover_url,'content':content,'tags':tags}
    if id==0:
        canshu['time_create'] = int(time.time())
        ws = models.List.objects.create(**canshu)
    else:
        models.List.objects.filter(id=id).update(**canshu)
    return ReturnData()

''' 修改博客状态 '''
class BlogStateForm(forms.Form):
    id = forms.IntegerField()
    state = forms.ChoiceField(choices=((-1,'已删除'),(0,'未上线'),(1,'已上线')))

@check(formclass=BlogStateForm)
def state_blog(request):
    id = int(request.POST.get('id'))
    state = int(request.POST.get('state'))
    if state==1:
        models.List.objects.filter(id=id).update(state=state,time_publish=int(time.time()))
    else:
        models.List.objects.filter(id=id).update(state=state)
    return ReturnData()

''' 修改分类 '''
class BlogKindForm(forms.Form):
    id = forms.IntegerField()
    kind = forms.IntegerField()

@check(formclass=BlogKindForm)
def kind_blog(request):
    id = int(request.POST.get('id'))
    kind = int(request.POST.get('kind'))
    models.List.objects.filter(id=id).update(kind=kind)
    return ReturnData()


''' 浏览博客 '''
class BlogViewForm(forms.Form):
    id = forms.IntegerField()

@check(formclass=BlogViewForm)
def view_blog(request):
    id = int(request.POST.get('id'))
    models.List.objects.filter(id=id).update(count_view=F('count_view')+1)
    return ReturnData()

''' 点赞博客 '''
class BlogZanForm(forms.Form):
    id = forms.IntegerField()

@check(formclass=BlogZanForm)
def zan_blog(request):
    id = int(request.POST.get('id'))
    models.List.objects.filter(id=id).update(count_zan=F('count_zan')+1)
    return ReturnData()


''' 上传封面图 '''
@check()
def upload_cover(request):
    img = request.FILES.get('file')
    ext = os.path.splitext(img.name)[1].replace(".","")
    newname = hashlib.md5((img.name+str(time.time())).encode('utf-8')).hexdigest()+'.'+ext
    path=os.path.join('/home/web/img/blog',newname)
    with open(path,'wb') as pic:
        for p in img.chunks():
            pic.write(p)
    return ReturnData(data="https://img.huchunyu.com/blog/"+newname)
