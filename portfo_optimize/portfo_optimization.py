import pandas as pd
import numpy as np
import datetime
from dateutil.parser import parse
from portfo_optimize.portfopt import Portfopt
import matplotlib.pyplot as plt

class portfo_optimize():

    def __init__(self,ret):
        """
        :param ret: the ret is dataframe, the index is the date and the columns are the strategy name, the value is daily pnl
        """
        if isinstance(ret,pd.DataFrame):
            self.ret = ret

    def _resample_date(self, freq):
        if isinstance(self.ret.index[0], datetime.datetime) and freq in ["M","3M","6M","Y"]:
            return self.ret.resample(freq).sum()

    def optimize(self, target="Sharpe", GA=0, freq="M"):
        ret = self._resample_date(freq)

        if GA == False:
            if target == "Sharpe":
                s = Portfopt(self.ret)
                weight = s.maximum_sharpe()
                weight = pd.DataFrame(weight).T
                self.freq = freq
                self.weight = weight
                return weight
        else:
            pass

    def strategy_combine(self):

        ret = self.ret.resample("Y").sum()
        columns = self.ret.columns


        s = [1/len(columns)]*len(columns)
        weight = pd.DataFrame(s).T
        weight.columns = columns
        x = self.weight.index[0]
        weight.index = [x]

        weight = pd.concat([weight,self.weight.iloc[:-1,]])
        weight.index = self.weight.index

        total_ret = []
        for i in range(len(self.ret)):
            year = self.ret.index[i].strftime("%Y-%m-%d")[:4]
            total_ret.append(self.ret.iloc[i,:].values @ weight.loc[year,:].values)

        total_ret = pd.DataFrame(total_ret,columns=["combined_ret"],index=self.ret.index)
        return total_ret

if __name__ == "__main__":
    df = pd.read_csv("stock_price.csv",index_col="date")
    df.index = [parse(i) for i in df.index]
    # print(ret)
    df = df.dropna()
    df = df.diff(1) / df.shift(1)
    df = df.dropna()

    s = portfo_optimize(df)
    weight = s.optimize(target="Sharpe", GA=0, freq="M")

    total = s.strategy_combine()
    print(total)
