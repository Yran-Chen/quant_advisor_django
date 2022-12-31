# -*- coding: utf-8 -*-
"""
Created on Wed Dec  4 17:31:04 2019

@author: ultralpha
"""
# from Performance import Performance
import pandas as pd
import numpy as np
from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt import risk_models
from pypfopt import expected_returns
# from pypfopt import value_at_risk
# from pypfopt import hierarchical_risk_parity
import util.datetime_process as dtp
from dateutil.parser import parse


class Portfopt():
    def __init__(self,returns):
        flag = 0
        self.returns = returns
        self.begin_year = self.returns.index[0].strftime("%Y-%m-%d")[:4]
        self.end_year = self.returns.index[-1].strftime("%Y-%m-%d")[:4]

    def maximum_sharpe(self, freq="M"):
        s={}
        for i in range(int(self.begin_year),int(self.end_year)+1):
            ret = self.returns[str(i)].sum()
            cov = self.returns[str(i)].cov()
            ef = EfficientFrontier(ret, cov)
            raw_weights = ef.max_sharpe()
            cleaned_weights = ef.clean_weights()
            s[str(i)]= cleaned_weights
        return s

    def maxiumum_sharpe_monthly(self):
        flag = 0
        for i in range(1,len(self.returns)+1):
            s={}
            ret = self.returns.iloc[max(0,i-12):i,:]
            ret_s = ret.sum()
            cov = ret.cov()
            ef = EfficientFrontier(ret_s, cov)
            raw_weights = ef.max_sharpe()
            cleaned_weights = ef.clean_weights()
            s[self.returns.index[i-1]] = cleaned_weights
            df = pd.DataFrame(s)
            if flag==0:
                final_weights = df
                flag=1
            else:
                final_weights = final_weights.join(df)

        final_weights = final_weights.T
        return final_weights

    def minimize_cVaR(self):
        s={}
        for i in range(int(self.begin_year),int(self.end_year)+1):
            ret = self.returns[str(i)]
            ret = ret.dropna()
            x = value_at_risk.CVAROpt(ret)
            s[str(i)] = x.min_cvar()
        return s

    def hierarchical_risk_parity(self):
        s = {}
        for i in range(int(self.begin_year),int(self.end_year)+1):
            ret = self.returns[str(i)]
            ret = ret.dropna()
            x = hierarchical_risk_parity.HRPOpt(ret)
            s[str(i)] = x.hrp_portfolio()
        return s

if __name__ == "__main__":
    df = pd.read_csv("stock_price.csv",index_col="date")
    print(df)
    df.index = [parse(i) for i in df.index]
    df = df.dropna()
    df = df.diff(1) / df.shift(1)
    df = df.dropna()
    print(df)

    s = Portfopt(df)
    weight = s.maximum_sharpe()
    weight = pd.DataFrame(weight).T
    print(weight)
