# -*- coding: utf-8 -*-
import time
from datetime import datetime,timedelta
import os
import re
import json
import hashlib
from decimal import Decimal
from django.http import HttpResponse
import urllib.request


'''
    --JSON编码额外识别--
    decimal和datetime类转化为json时会报错，此类用来识别decimal和datetime类
'''
class ExtendJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.strftime(DATETIME_FORMAT)
        return super(ExtendJSONEncoder, self).default(obj)

'''
    --获取客户端的ip--
'''
def get_client_ip(request):
    if ('HTTP_REFERER' in request.META) or ('REMOTE_ADDR' in request.META):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[-1].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    else:
        return ''

'''
    --接口装饰器--
    表单验证
    验证必要cookie
    数据预处理
    权限验证
    用户信息拉取
    数据组织
    缓存设置
'''
def check(formclass='', auth='none', admin_level=1, tracename='', cookies=[]):
    def out_wrapper(func):
        def wrapper(request):
            ''' 获取用户ip '''
            request.ip = get_client_ip(request)
            if 'HTTP_USER_AGENT' in request.META:
                request.agent = request.META['HTTP_USER_AGENT']
            else:
                request.agent = ''

            ''' 预处理请求参数 '''
            if request.method == 'POST':
                request.POST = request.POST.copy()
                req = request.POST
            else:
                request.GET = request.GET.copy()
                req = request.GET

            ''' 验证必要cookie '''
            if len(cookies)>0:
                for i in range(len(cookies)):
                    if (cookies[i] in request.COOKIES) == False:
                        return ReturnResponse(ReturnData(22))

            ''' 用户登录验证 '''
            '''
                none - 无需登录即可使用
                user - 需要以用户身份登录
                admin - 需要管理员身份登录
                either - 用户或管理员（等级>0）均可
            '''
            # usertoken = ''
            # request.users = {'userid':''}
            # request.admin = {'userid':''}
            # ''' 如果是测试服，则设置用户为ceshi '''
            # meta = request.META
            # if 'HTTP_REFERER' in meta:
            #     origin = request.META['HTTP_REFERER']
            # elif 'HTTP_ORIGIN' in meta:
            #     origin = request.META['HTTP_ORIGIN']
            # else:
            #     origin = ''
            # if origin=='' or re.match( r'^http://192.168|http://localhost',origin):
            #     request.users = {'userid':'ceshi'}
            #     request.admin = {'userid':'ceshi'}
            # # ''' 否则根据usertoken获取user或admin信息 '''
            # else:
            #     if ('usertoken' in request.COOKIES) == True:
            #         usertoken = request.COOKIES.get('usertoken')
            #         atime = int(time.time())
            #         qs = master.models.Token.objects.filter(user_token=usertoken).filter(expire_time__gt=atime)
            #         if qs.count()>0:
            #             request.users = list(qs.values())[0]
            #         qs = master.models.AdminToken.objects.filter(user_token=usertoken).filter(expire_time__gt=atime)
            #         if qs.count()>0:
            #             request.admin = list(qs.values())[0]
            #
            # if auth=="none":
            #     pass
            # elif auth=="user":
            #     if request.users['userid']=='':
            #         if usertoken=='':
            #             return ReturnResponse(ReturnData(11))
            #         else:
            #             return ReturnResponse(ReturnData(12))
            # elif auth=="admin":
            #     if request.admin['userid']=='':
            #         if usertoken=='':
            #             return ReturnResponse(ReturnData(11))
            #         else:
            #             return ReturnResponse(ReturnData(12))
            #     al = master.models.AdminAccount.objects.filter(userid=request.admin['userid'])[0].level
            #     if al<admin_level:
            #         return ReturnResponse(ReturnData(25))
            #     # 看是否需要trace管理员的操作
            #     if tracename!='':
            #         userid = request.admin['userid']
            #         do_function = func.__name__
            #         params = ['{}={}'.format(key, kwargs[key]) for key in req]  # and kwargs[key] != '']
            #         do_params = '&'.join(params)
            #         master.models.AdminTrace.objects.create(userid=userid,do_name=tracename,do_function=do_function,do_params=do_params,do_time=int(time.time()))
            # elif auth=="either":
            #     if request.users['userid']=='' and request.admin['userid']=='':
            #         if usertoken=='':
            #             return ReturnResponse(ReturnData(11))
            #         else:
            #             return ReturnResponse(ReturnData(12))


            ''' 表单验证及数据处理 '''
            if formclass!='':
                form = formclass(req)
                if form.is_valid() == False:
                    return ReturnResponse(ReturnData(21))
                else:
                    for key in form.cleaned_data:
                        req[key] = form.cleaned_data[key]

            ''' 异常处理 '''
            return ReturnResponse(func(request))
            # try:
            #     return ReturnResponse(func(request))
            # except Exception as e:
            #     return ReturnResponse(ReturnData(99))

        return wrapper
    return out_wrapper

'''
    -- 组织返回数据 --
'''
def ReturnData(code=0,message='',data=[],cookies=[]):
    MESSAGES={
        0:'success',
        11:'缺少token',
        12:'token不正确或已过期',
        21:'请求参数不正确',
        22:'缺少必要cookie',
        23:'验证码错误',
        24:'需要管理员权限',
        25:'权限不足',
        71:'请求过于频繁',
        72:'超过每小时限额',
        73:'超过每天限额',
        74:'不在允许时间范围内',
        81:'记录已存在',
        82:'记录不存在',
        83:'不能重复操作',
        84:'数据超出记录范围',
        85:'数据存在其他依赖',
        86:'数据已经生效，不能再修改',
        98:'第三方接口返回错误',
        99:'服务器异常'
    }
    if message=='':
        message = MESSAGES.get(code)
    ret = {'data':{'code':code,'message':message,'data':data},'cookies':cookies}
    return ret

'''
    -- 返回数据 --
    在返回数据之前还要处理一下cookie
'''
def ReturnResponse(returnData):
    re = HttpResponse(json.dumps(returnData['data'], cls=ExtendJSONEncoder))
    cookies = returnData['cookies']
    for i in range(len(cookies)):
        cookies[i]['domain'] = '.sigmoid.cc'
        cookies[i]['max_age'] = 60*60*24*30
        re.set_cookie(**cookies[i])
    return re


'''
    -- 表单数据处理包装 --
    clean_data的包装，可以将4行代码缩减为2行
    s-self
    n-name
    d-default
'''
def cleanData(s,n,d):
    v = s.cleaned_data[n]
    if v is None or v=='':
        v = d
    return v




'''
    -- 获取分页列表包装 --
    get_list类通用包装方法，自动生成返回值
    ws-查询集
    page_size-页容
    page_num-页码
'''
def createList(ws,page_size,page_num):
    ajson = {'total':0,'page_size':page_size,'page_num':0,'list':[]}
    wc = ws.count()
    if wc>0:
        ajson['total'] = wc
        if wc<page_size*page_num:
            page_num = int(wc/page_size)
        start = page_size*page_num
        end = min(wc,start+page_size)
        wl = list(ws[start:end].values())
        ajson['page_num'] = page_num
        ajson['page_size'] = page_size
        ajson['list'] = wl
    return ajson
