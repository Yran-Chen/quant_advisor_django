from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import json
import os
import numpy as np


def test():
    path = "../example.json"
    # path.replace("\\", os.sep)
    with open(path, "r") as load_f:
        load_dic = json.load(load_f)

    print (load_dic.keys())
    # print (load_dic['xdata'])
    print (load_dic['xdata'])
    # print (load_dic['label'].head(5))


if __name__ == '__main__':
    # test()
