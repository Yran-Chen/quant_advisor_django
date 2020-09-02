from django.http import HttpResponse, JsonResponse

sign_map = {"gt": ">",
            "ge": ">=",
            "lt": "<",
            "le": "<=",
            "eq": "=",
            "neq": "!="}


def url_strat_parse(request):
    """解析URL的策略"""

    indi_startd = request.GET.get('start_date')
    indi_endd = request.GET.get('end_date')
    indi_select = request.GET.get('selected')
    indi_opt_method = request.GET.get('opt_method')
    indi_opt_param = request.GET.get('opt_param')

    indi_name = request.GET.get('name')
    indi_uid = request.GET.get('uid')

    if indi_name is not None:
        content = {
        'name':indi_name,
        'uid':indi_uid,
        'start_date':indi_startd,
        'end_date':indi_endd,
        'opt_method':indi_opt_method,
        'opt_param':indi_opt_param,
        'selected':indi_select[0:-1],
        }
        # return {
        # 'name':indi_name,
        # 'uid':indi_uid,
        # 'start_date':indi_startd,
        # 'end_date':indi_endd,
        # 'opt_method':indi_opt_method,
        # 'opt_param':indi_opt_param,
        # 'selected':indi_select[0:-1],
        # }
        return content
    else:
        return None

def url_uid_parse(request):
    uid = request.GET.get('uid')
    if uid is not None:
        return uid
    else:
        return None

def url_user_session_parse(request):
    """解析URL，返回用户名"""

    # return request.COOKIES.get('username')
    print('解析URL，返回用户名')
    if request.method == 'GET':
        uid = request.GET.get('uid')

        # print(uid)
    if request.method == 'POST':
        uid = request.COOKIES.get('username')
    return uid
    # return request.COOKIES.get('username')

def url_selected_parse(request):

    indi_startd = request.GET.get('start_date')
    indi_endd = request.GET.get('end_date')
    indi_select = request.GET.get('selected')
    # print('0')
    # print(indi_select)
    # print('1')
    # print(indi_startd)
    # print(indi_select.split(',')[0:-1])
    if indi_select is not None:
        return indi_select.split(',')[0:-1],indi_startd,indi_endd
    else:
        return None,None,None

def url_condition_parse(request,indi):

    indi_1 = request.GET.get(indi+"1")
    indi_2 = request.GET.get(indi+"2")
    sign_1 = request.GET.get(indi+"_rule1")
    sign_2 = request.GET.get(indi+"_rule2")
    andor = request.GET.get(indi+"_andor", "and")

    # eq_1_flag: True -- 表达式完整， 否则反之
    eq_1_flag = ( indi_1 and indi_1.strip()) and ( sign_1 and sign_1.strip())
    eq_2_flag = ( indi_2 and indi_2.strip()) and ( sign_2 and sign_2.strip())
    # print("-" * 7)
    # print(indi_1, sign_1, eq_1_flag, indi_2, sign_2, eq_2_flag)
    # print('PARSING.')

    if (not eq_1_flag) and (not eq_2_flag):
        # print('fked up.')
        return None
    elif eq_1_flag and eq_2_flag:
        # print("double conditions", andor)
        # print(indi, sign_map[sign_1], indi_1)
        # print(indi, sign_map[sign_2], indi_2)
        condition =  indi + " " + sign_map[sign_1] + " " + indi_1 + " " \
                    +andor+ \
                    " " + indi + " " + sign_map[sign_2] + " " +  indi_2
        # print('1',condition)
    elif eq_1_flag:
        condition = indi + " " + sign_map[sign_1] + " " + indi_1
        # print('2',condition)
    elif eq_2_flag:
        condition =  indi + " " + sign_map[sign_2] + " " + indi_2
        # print('3',condition)
    return condition
