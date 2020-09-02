from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, JsonResponse
from django.contrib import auth
from django.contrib.auth.models import User

import json


def register(request):
	"""注册"""

	username = request.POST.get('username')
	pwd = request.POST.get('password')
	email = request.POST.get('email')

	users = User.objects.filter(username=username)
	if users:
		return JsonResponse({'status':'1', 'message':'用户名已经存在'})
	users = User.objects.filter(email=email)
	if users:
		return JsonResponse({'status':'2', 'message':'邮箱已经被注册'})

	user = User.objects.create_user(username=username, password=pwd, email=email)
	user.save()
	if user:
		return JsonResponse({'status':'0','message':'注册成功'})


def login(request):
	"""登录"""

	username = request.POST.get('username')
	password = request.POST.get('password')
	# utype = request.POST.get('utype')

	print(request.COOKIES.get('session_id'))
	print(username)

	user = auth.authenticate(username=username, password=password)

	if user is not None and user.is_active:
		#设置session内部的字典内容
		auth.login(request, user)
		session_id = request.session.session_key
		print(session_id)
		request.session.set_expiry(0)
		response = JsonResponse({'status':'0', 'message':'success'})
		response["Access-Control-Allow-Credentials"] = "true"
		response.set_cookie("session_id", session_id, max_age=10000)
		response.set_cookie("username", username)
		# session_tmp = request.session
		request.session['is_login']='true'
		request.session['username']=username

		#print(request.session[session_id])
		return response
	else:
		return JsonResponse({'status':'1','message':'账号或者密码错误'})


def logout(request):
	"""退出登录"""
	# 删除所有当前请求相关的session

	auth.logout(request)
	ss_id = request.COOKIES.get('session_id')
	# all_ = request.COOKIES.get()
	print(ss_id)
	# print(all_)
	# request.COOKIES.clear()
	response = JsonResponse({'status':'0','message':'logout'})
	response.delete_cookie('username')
	response.delete_cookie('session_id')
	request.session.delete(ss_id)
	return response


def check(request):
	print(request.COOKIES.get('session_id'))
	session_id = request.session.session_key
	print(session_id)
	return JsonResponse({'status':'2','message':'注册失败'})
