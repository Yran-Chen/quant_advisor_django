# -*- coding: utf-8 -*-
"""
Created on Fri Dec 13 16:37:47 2019

@author: ultralpha
"""
import sys

sys.path.append('../')

#from fatherdirname import xxx

import numpy as np
import pandas as pd
import util.datetime_process as dtp

class Performace_evaluator:
    def __init__(self,weights=[],ret=[],loss_weight = None):
        self.weights = weights
        self.raw_ret = ret
        self.loss_weight = loss_weight
        self.average_ret = ret.mean()
        self.ss  = self.raw_ret - self.average_ret

        self.strategy = self.raw_ret.columns
        self.strategy_num = len(ret)
        self.cov_matrix = self.raw_ret.cov().values
        self.ret = self.raw_ret.sum().values



    def run(self,target):
        if target == "Mean_variance":
            return self.Mean_Variance()
        if target == 'Mean_v':
            return self.Mean_v()

        elif target == "Semi_Variance":
            return self.Semi_Variance()

        elif target == "Mean_absolute_deviation":
            return self.Mean_absolute_deviation()

        elif target == "Mean_absolute_deviations":
            return self.Mean_absolute_deviation()

        elif target == "Maximize_calmar_ratio":
            return self.Maximize_calmar_ratio()

        elif target == 'Sharpe':
            return self.Sharpe()

        elif target == 'test_':


            return [self.Mean_Variance()[0] * self.loss_weight[0],
                    self.Maximize_calmar_ratio()[0] * self.loss_weight[1],
                    self.Sharpe()[0] * self.loss_weight[2]
                    ],\
                   self.weights, \
                   self.strategy



    def softmax(self,df):
        def softmax(x):
            return np.exp(x) / np.sum(np.exp(x), axis=0)
        return softmax(df)

    def Sharpe(self):
        IR = self.IR()
        return (-1.0 * IR) * np.sqrt(252), self.weights, self.strategy

    def IR(self):
        daily_pnl = self.raw_ret.apply(lambda x:np.average(x,weights=self.weights),1)
        if (np.array(daily_pnl)==0.0).all() or len(daily_pnl) == 1:
            return 0.0
        else:
            return daily_pnl.mean()/ daily_pnl.std()
        # return daily_pnl.groupby(daily_pnl.index.year).mean() / daily_pnl.groupby(daily_pnl.index.year).std()

    def Mean_Variance(self,lamda=0.1):
#        print(self.cov_matrix.shape)
#        print(self.ret.shape)
#        print(self.weights.shape)

        ret = self.weights @  self.ret
        cov = self.weights.T @ self.cov_matrix @ self.weights
        utility = lamda * cov - (1-lamda) * ret
        print(ret,cov)
        return  utility, self.weights, self.strategy

    def Mean_v(self,lamda = 0.1):
        ret = self.average_ret
        cov = [1] @ self.cov_matrix @ [1]
        utility = lamda * cov - (1-lamda) * ret
        # print(self.raw_ret)
        # print(ret,cov)
        return -utility[0], self.weights, self.strategy

    def Semi_Variance():
        pass

    def Mean_absolute_deviation(self, lamda=0.1):
        self.ss = self.ss.apply(np.abs)
        x = self.ss.sum()
        x = (x.values @ self.weights) / len(x)
        r_average = self.weights @ self.average_ret.values
        utility = lamda * x - r_average * (1-lamda)
        return utility, self.weights, self.strategy

    def Variace_with_skewness(self):
        pass

    def Maximize_calmar_ratio(self):
        def max_draw_down(data):
            date = data.index
            ret = data.values
            high = ret[0]
            try:
                max_down = (ret[0]-ret[1])/ret[0]
            except:
                max_down=[0]
            start_date = date[0]
            end_date = date[0]
            for i in range(len(date)):
                if ret[i]>=high:
                    high = ret[i]
                    x_date = date[i]
                if (high-ret[i])/high > max_down:
                    max_down = (high-ret[i])/high
                    start_date = x_date
                    end_date = date[i]
            return max_down[0]
        if (np.array(self.raw_ret)==0.0).all() or len(self.raw_ret) == 1:
            return 0, self.weights, self.strategy
        else:
            s = self.raw_ret.apply(lambda x:np.average(x,weights=self.weights),1)
            ret = s.sum()
            ss = [100,]
            for i in range(len(s)):
                ss.append(ss[-1]*(1+s.values[i]))
            s = pd.DataFrame(ss[1:],index = s.index)
            max_down = max_draw_down(s)
            if max_down != 0:
                calmar_ratio = ret / max_down
            else:
                calmar_ratio = 0.0
            return -calmar_ratio, self.weights, self.strategy

if __name__ == "__main__":
    df = pd.read_csv("stock_price.csv",index_col="date")

    df = df.dropna()
    df = df.diff(1) / df.shift(1)
    df = df.dropna()
    df.index = [dtp.str2date(i) for i in df.index]
    weights = np.random.random(len(df.columns))
    weights = weights / weights.sum()
#    print(weights)
    x = Performace_evaluator(weights,df)
    print(x.run("test_"))
