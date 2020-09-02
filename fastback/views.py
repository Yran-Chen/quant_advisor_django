from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import json
import os
import numpy as np
import time
import pandas as pd
# from fastback.preprocess import
# from database.DB_Factors import data_proxy

import util.Parser_dataview as Parser_dataview
from util.dataview import DataView
from cache.cache_pool import CachePool
import util.Url_parse as upar
import util.datetime_process as dtp
from cache.cache_pool import CachePool
from cache.cache_pool import FutStrategyPool,FutStrategy
from portfo_optimize.portfo_optimization import portfo_optimize
from datetime import datetime


# UserSPool = FutStrategyPool('master')

def run_return_user_portfolio(request, cachepool_ = None, user_proxy = None):
    """返回用户策略"""

    print('返回用户策略。。。')
    # uid = request.get('uid')
    uid = upar.url_user_session_parse(request)
    # uid = 'wangdi'
    print('33')
    cachepool_.load_strategy_for_user(uid,user_proxy)

    result = cachepool_.get_pid_for_user(uid = uid,user_proxy = user_proxy)
    print('22')
    print(result)


    return cachepool_.get_pid_for_user(uid = uid,user_proxy = user_proxy)

def run_copy_strat(request,cachepool_ = None, user_proxy = None):

    stra_dic = upar.url_strat_parse(request)
    print(stra_dic)
    # uid = upar.url_user_session_parse(request)

    uid = 'wangdi'
    stra_dic['uid'] = uid
    print(stra_dic)

    if cachepool_ is not None:

        strat_temp = FutStrategy()
        strat_temp.strat_load_from_dic(stra_dic)

        cachepool_.load_strategy_for_user(uid = strat_temp.uid, user_proxy= user_proxy)
        cachepool_.save_strategy_for_user(strat =strat_temp ,uid = strat_temp.uid, user_proxy=user_proxy)
        # cachepool_.load_strategy_for_user(uid = strat_temp.uid, user_proxy= user_proxy)

        return stra_dic

    else:
        print('\nDO NOT LET IT HAPPEN.\n')

def return_condition(request):
    condition = None
    for indi in ["returns", "sharpe", "max_drawdown", "std", "ir"]:
        condition_i = upar.url_condition_parse(request,indi)
        if condition_i is not None:
            print ("Filter:",condition)
            if condition is None:
                condition = condition_i
            else:
                condition = '({})&({})'.format(condition_i, condition)
    return condition

def run_condition_filter(request,dataview_ = None,cachepool_ = None):
    condition =  return_condition(request)
    filtered_perf_df = dataview_.run_filter_performance(condition)
    # print(filtered_perf_df)
    keys = filtered_perf_df[['alpha_id','op_id']]
    keys_new = keys
    if CACHE_:
        keys_new = cachepool_.find_filter_key(keys.copy())
        # print('New key:\n',keys_new)
        # print("Existed key:\n",keys)
    return keys_new,keys,filtered_perf_df

def run_portfolio_opt(request,ret_p,method = "Sharpe",freq = 'M'):
    selected,start_date,end_date = upar.url_selected_parse(request)
    # print(selected)
    if selected is None:
        return ret_p
    else:
        portopt = portfo_optimize(ret_p[selected])
        portopt.optimize(target=method, GA=0, freq=freq)
        ret_opt = portopt.strategy_combine()
        ret_p = ret_p[selected]
        ret_p.insert(0,"{}_opt".format(method),ret_opt)
        return ret_p

def portfolio_list_trans_format(port_df):
    """策略列表转换"""

    print('策略列表开始转换')
    print(port_df)
    port_dic = {'status':0,
    'message':"success",
    'defaultValue':"1",}
    content_dic = {}
    for i in port_df.index:
        pid = str(port_df.loc[i][0])
        name =port_df.loc[i][2]

        content_dic[pid] = {
            "label": name,
            "pid": pid,
            "account":"",
            "passwd":"",
            "api":"",
            "amount":""
        }
    port_dic['content']   = content_dic

    return port_dic

def ret_trans_format(ret_df):
    ret_dic = {}
    series = []
    xdata = list([dtp.date2str(di) for di in ret_df.index])
    label = list(ret_df.columns)
    for i in label:
        series.append(
            {"name":i,"type":"line","data":list(ret_df[i]),}
        )
    ret_dic['xdata'] = xdata
    ret_dic['label'] = label
    ret_dic['series'] = series
    return ret_dic

def performance_trans_format(perf_df):
    def ids_to_name(df):
        df['name'] = df.apply(lambda row: '{}${}'.format(row['alpha_id'],row['op_id']),axis=1)
        df.drop(["alpha_id",'op_id'], axis=1, inplace=True)
        for col in ["date", "start_date", "end_date"]:
            if col not in df.keys():
                continue
            df[col] = df[col].map(dtp.date2str)
        return pd.DataFrame(df)
    perf_df = ids_to_name(perf_df)
    configHeader = []
    tableData = []
    name_label = None
    perf_dic = {}
    conf_ = list(perf_df.columns)

    for conf_i in conf_:
        if conf_i == 'name':
            configHeader.insert(0,{
                "prop":  conf_i,
                "fixed" : True,
                "label": conf_i,
                "sortable":True
            })
        elif conf_i.endswith('date') is False:
            configHeader.append({
                "prop":  conf_i,
                "fixed" : False,
                "label": conf_i,
                "sortable":True
            })
    for i in perf_df.index:
        dx = perf_df.loc[i].to_dict()
        tableData.append(dx)
    name_label = list(perf_df['name'])
    perf_dic['configHeader'] = configHeader
    perf_dic['tableData'] = tableData
    perf_dic['label'] = name_label
    return perf_dic

def parser_eval(expression,factor_dict):
    parser = Parser_dataview.Parser( )
    expr = parser.parse(expression)
    expr_parsed = expr.evaluate(factor_dict)
    return expr_parsed

def dataframe_2dict(df):
    dict = {}
    for key in df.columns:
        dict[key] = df[key]
    return dict

def load_all_strategy_cache(load_dir = 'all_strategy.csv'):
    df = pd.read_csv(load_dir)

    for col in ["date", "start_date", "end_date"]:
        if col not in df.keys():
            continue
        df[col] = df[col].map(dtp.date2datetime)
    df = df.set_index(['date']).iloc[:,:].diff(1)
    return df

# Create your views here.

#debug_ choice
DEBUG_ = True
CACHE_ = True
from database.db_init import data_proxy,future_proxy,user_proxy

dataViewDefault = DataView(data_proxy=data_proxy, future_proxy = future_proxy)
cachePoolDefault = CachePool()

if DEBUG_:
    ret_p = load_all_strategy_cache()
    cachePoolDefault.save_all_strategy_from_cache(ret_p)

def index(request):
    """对请求指标和指标参数进行提交，并填充回测界面"""

    upar.url_user_session_parse(request)
    keys_new,keys,filtered_perf_df = run_condition_filter(request,dataViewDefault,cachePoolDefault)   # keys 是alpha_id和op_id的二维数组，filtered_perf_df返回的是策略的二维数组
    perf_dict = performance_trans_format(filtered_perf_df)
    # time.sleep(5)
    ret_p = dataViewDefault.get_match_stras_withindex(keys_new)
    # ret_p.to_csv('aaa.csv')    # 先存数据，用来测试

    if CACHE_:
            cachePoolDefault.save_key_values(ret_p)
            ret_p = cachePoolDefault.load_key_values(keys)

    ret_dic = ret_trans_format(ret_p.cumsum())
    # print(perf_dict)
    print('parse end.')
    # print(perf_dict)
    callback = "success_jsonp"
    load_dic = callback + "(" + json.dumps(perf_dict) + ")"
    print(load_dic)
    return HttpResponse(load_dic)

def portfo_opt(request):
    """回测计算和展示"""

    keys_new,keys,filtered_perf_df = run_condition_filter(request,dataViewDefault,cachePoolDefault)        # 运行条件过滤
    ret_p = dataViewDefault.get_match_stras_withindex(keys_new)

    if CACHE_:
            cachePoolDefault.save_key_values(ret_p)
            ret_p = cachePoolDefault.load_key_values(keys)
    ret_p = run_portfolio_opt(request,ret_p)

    uid = request.session.get('username')
    # uid = 'wangdi'
    user = User.objects.filter(username=uid, is_staff=False)
    if user:
        ret_p = ret_p['20100105': '20171229']

    ret_dic = ret_trans_format(ret_p.cumsum())
    # print('optimization end.')

    callback = "success_jsonp"
    load_dic = callback + "(" + json.dumps(ret_dic) + ")"

    return HttpResponse(load_dic)

# def user_portfolio(request):
#     """请求组合列表"""
#
#     print('请求组合列表。。。。')
#     ret_portfo_list_dic =  portfolio_list_trans_format( run_return_user_portfolio(request, cachePoolDefault, user_proxy) )
#
#     # ret_portfo_list_dic =  portfolio_list_trans_format( run_return_user_portfolio(request,cachePoolDefault, user_proxy) )
#     print(ret_portfo_list_dic)
#     response = JsonResponse(ret_portfo_list_dic)
#
#     # response["Access-Control-Allow-Credentials"] = "true"
#     return response

def copy_strat(request):
    """创建策略组合"""

    dict = run_copy_strat(request, cachePoolDefault, user_proxy)
    # print('44')
    # print(dict)

    pid = user_proxy.get_list_value(dict['uid'],dict['name'])['pid']
    # print(pid)
    callback = "success_jsonp"
    load_dic = callback + "(" + json.dumps(pid) + ")"
    # print(load_dic)
    # pid = json.dumps(pid)
    # print(pid)
    return HttpResponse(load_dic)
    # return JsonResponse(pid, safe=False)

def user_portfolio_list(request):
    """请求用户策略组合列表"""

    # uid = request.GET.get('uid')
    uid = 'wangdi'
    list = user_proxy.get_list(uid)
    index = []
    value = []
    for i in list:
        index.append(i[0])
        value.append(i[1])
    # print(index, value)
    dict1 = dict(zip(index, value))
    print(dict1)
    response = {
        "content": dict1
    }
    result = json.dumps(response)

    return HttpResponse(result)


def portfo_index(request):
    """请求组合列表中每个组合的内容"""

    print('请求组合列表内容。。。')
    json_dict = json.loads(request.body)
    uid = json_dict.get('uid')

    # uid = request.POST.get('uid')
    index = json_dict.get('index')
    label = json_dict.get('label')
    # print(uid, index)


    result_dict = user_proxy.get_list_value(uid, label)
    # print('1')
    # print(result_dict)

    # start_date = result_dict['start_date'].strftime("%Y-%m-%d %H:%M:%S")
    # end_date = result_dict['end_date'].strftime("%Y-%m-%d %H:%M:%S")
    if not result_dict['start_date']:
        # print('2')
        start_date = 'null'
        # print(start_date)
    else:
        start_date = result_dict['start_date'].strftime("%Y-%m-%d")
        # print(start_date)

    if not result_dict['end_date']:
        end_date = 'null'
    else:
        end_date = result_dict['end_date'].strftime("%Y-%m-%d")

    context = {
        "index": index,
        "label": label,
        "content":{
            "paras":{
                "start_date": start_date,
                "end_date": end_date,
                "fee":"",
                "opt_method": result_dict['opt_method'],
                "rebalance_strategy": "",
                "rebalance_threshold": "",
                "rebalance_number": "",
                "rebalance_unit": "",
                "stoploss_threshold": "",
                "stoploss_number": "",
                "stoploss_unit": "",
                },
            "allocationTable": [
                {
                    "name": "str1",
                    "allocation": 20,
                },
                {
                    "name": "str2",
                    "allocation": 80,
                }
            ]

            }
        }


    return JsonResponse(context, safe=False)
def portfo_delete(request):
    """删除组合内容"""

    print('删除组合列表')

    json_data = json.loads(request.body)
    # uid = json_data.get('uid')
    uid = 'wangdi'
    index = json_data.get('index')
    label = json_data.get('label')

    user_proxy.delete_list_value(index, label)
    result = user_proxy.get_list_value(uid, label)
    if not result:
        return JsonResponse({"index": index, "label": label, "status": "success", "reason": "删除地址成功"})
    else:
        return JsonResponse({"index": index, "label": label, "status": "failed", "reason": "删除地址失败"})

def portfo_save(request):
    """保存组合"""

    json_str = request.body.decode()
    json_dict = json.loads(json_str)
    json_paras = json_dict.get('data').get('paras')
    print(json_paras)
    json_allocation = json_dict.get('data').get('allocationTable')
    print(json_allocation)
    # print(json_dict)

    name = json_dict.get('label')
    # uid = request.COOKIES.get('username')
    uid = json_dict.get('uid')
    # uid = 'wangdi'
    end_date = json_paras.get('end_date')
    # print(end_date)
    opt_method = json_paras.get('opt_method')
    pid = json_dict.get('index')
    selected = json_paras.get('selected')
    start_date = json_paras.get('start_date')
    opt_param = json_paras.get('opt_param')

    dict = {
        "end_date": end_date,
        "name": name,
        "opt_method": opt_method,
        "pid": pid,
        "selected": selected,
        "start_date": start_date,
        "uid": uid,
        "opt_param": opt_param
        }

    # print(dict)

    try:
        user_proxy.save_value(dict)
        print('1')
    except:
        return JsonResponse({'status': 1, 'message': 'error'})   # 1:代表失败

    return JsonResponse({'status': 0, 'message': 'success'})   # 0: 代表成功

from django.contrib.auth.models import User
# from account.models import User
def pay_money(request):
    """付费功能（测试专用，测试成功）"""

    money = request.POST.get('money')
    uid = request.session.get('username')
    # uid = 'wangdi'

    if money:
        User.objects.filter(username=uid).update(is_staff=True)   # is_staff用来判断是否是vip用户
        # User.objects.filter(username=uid).update(email='123')

    return JsonResponse({'status': 0, 'message': 'success'})

def update_factors():
    """更新因子"""
    # 关键是：先获取到因子，有可能需要组合新的因子，然后保存更新因子

    pass

def get_factors():
    """获取因子"""


    pass

def timed_task():
    """处理定时任务"""

    pass
