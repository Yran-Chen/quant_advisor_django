import pandas as pd
import datetime
# from backtest_params_pool import *
# from database.DB_Factors import  FactorDatabase
# from database.DB_Future import FutureDatabase
import util.Parser_dataview as Parser_dataview
import numpy as np
import math
import time
pd.set_option('display.max_columns', 20)
pd.set_option('display.max_rows', None)

condition_test= ['sharpe>0.3','max_drawdown<0.2']
condition_test= ['sharpe>0.3','max_drawdown<0.2']

class DataView():
    def __init__(self, data_proxy, future_proxy):
        self.strategy_key = None
        self.proxy =  data_proxy
        self.future_proxy = future_proxy
        self.parser = None
        self.condition = condition_test
        self.filtered_performance = None

    def param_generator(self,df=None):
        print(df[df["op_id"] == 3])
        param_pool = []
        # op_param_df = self.proxy.return_op_params()
        op_param_dict = self.dataframe_2dict(df.T)
        for _,op_param_i in op_param_dict.items():
            param_pool.append(self.dataframe_2dict(pd.DataFrame(op_param_i).T))
        return param_pool
        # pass

    def add(self):
        pass

    # todo: place this function
    # 从期货合约中解析出期货商品
    def extract_instrument_from_code(self, code):
        if isinstance(code, float):
            print(code)

        if code[1].isalpha():
            return code[:2]
        else:
            return code[:1]

    def get_match_stras(self):
        # get the matching strategy, alpha_id, op_id
        ids = self.filter()
        t0 = time.time()

        for i in ids.index:
            item = ids.iloc[i]
            alpha_id, op_id = ids.loc[i, "alpha_id"], ids.loc[i, "op_id"]
            print(alpha_id,op_id)
            trade_df = self.get_trade_df(alpha_id=alpha_id.replace('-','_'), op_id=op_id.replace('-','_'))
            trade_df = trade_df.sort_values(by = ["date"])
            daily_pnl = self.cal_daily_pnl(trade_df=trade_df)

        print("Total time usage ", time.time() - t0)

    def get_match_stras_withindex(self,ids):
        # get the matching strategy, alpha_id, op_id
        stras_df = pd.DataFrame()
        t0 = time.time()
        total_len = len(ids.index)
        _len = 0
        print('Start calculating... ')
        for i in ids.index:
            item = ids.loc[i]
            alpha_id, op_id = ids.loc[i, "alpha_id"], ids.loc[i, "op_id"]
            # print(alpha_id,op_id)
            trade_df = self.get_trade_df(alpha_id=alpha_id.replace('-','_'), op_id=op_id.replace('-','_'))
            trade_df = trade_df.sort_values(by = ["date"])
            daily_pnl = self.cal_daily_pnl(trade_df=trade_df)
            # print(daily_pnl.head(5))
            stras_df.insert(0,"{0}${1}".format(alpha_id,op_id),daily_pnl['pnl'])
            # print(stras_df.head(5))
            # stras_dic.update({"{0}&{1}".format(alpha_id,op_id):daily_pnl})
            _len = _len + 1
            print(' {}/{} Finished. Time usage: {:.2f} '.format(_len,total_len,(time.time() - t0)))
        print("Total time usage ", time.time() - t0)
        print(stras_df.head(5))
        return stras_df.fillna(0)


    def get_trade_df(self,alpha_id, op_id):

        op_cond = self.proxy.get_op_param_df(op_id).iloc[0]
        # print(op_cond)

        op_code_df = self.get_op_code_df(op_cond = op_cond)
        alpha_df = self.proxy.get_alpha_df(alpha_id=alpha_id,if_includes_date=False)
        alpha_df = alpha_df.set_index(['date','instrument'])[alpha_id]
        # print(alpha_df.head(5))
        # alpha_df = alpha_df.dropna(how = "any", axis= 0)
        alpha_df = alpha_df.dropna(how = "any", axis= 0).to_frame()
        alpha_df.columns = ["indicator"]
        # print(alpha_df.head())
        alpha_df = alpha_df.reset_index()
        op_code_df = op_code_df.reset_index()

        # print(op_code_df.head(5),alpha_df.head(5))
        # print(op_code_df.sort_values( by = ["date"])[:300])
        trade_df = pd.merge(op_code_df, alpha_df, on = ["date", "instrument"], how = "inner")
        trade_df = trade_df.dropna(how = "any", axis = 0)
        trade_df = trade_df.sort_values(by = ["date"])

        top = op_cond["top"]
        bottom = op_cond["bottom"]
        weighted = op_cond["weighted"]

        # todo: top, bottom default, value
        # top, bottom, nan -- > default value 0.25
        top = 0.25 if top != top else top
        bottom  = 0.25 if bottom != bottom else bottom
        # weighted , nan -- > default value false
        weighted = False if weighted != weighted else weighted

        trade_df = self.cal_hold(df = trade_df,top=top, bottom=bottom, weighted=weighted)
        # print(trade_df)

        return trade_df


    # 输入：ascending：False/True, False: 指标高者买入，指标低者卖出
    #       top：买入期货占总期货数比例
    #       bottom： 卖出期货数占总期货数比例
    #       weighted：False/True, False：等权交易，True：加权交易
    def cal_hold(self, df, ascending=False, top=0.25, bottom=0.25, weighted=False):
        def cal_holding(sub_df):
            # 等权交易
            if not weighted:
                tmp_df = sub_df.sort_values(by=['indicator'], ascending=ascending)
                num_futures = sub_df.shape[0]
                n0, n1 = math.ceil(num_futures * top), math.ceil(num_futures * bottom)
                if n0 + n1 > num_futures:
                    i_range = n0 + n1 - num_futures
                    n0, n1 = math.floor(num_futures * top), math.floor(num_futures * bottom)
                    for i in range(i_range):
                        if sub_df.iloc[n0 + i]["indicator"] > 0 and (not ascending):
                            n0 += 1
                        else:
                            n1 += 1
                weight_list_0 = [1 for _ in range(n0)]
                weight_list_1 = [-1 for _ in range(n1)]
                if len(weight_list_0) > 1:
                    weight_list_0[-1] = num_futures * top - math.floor(num_futures * top) \
                        if n0 != math.floor(num_futures * top) else 1
                if len(weight_list_1) > 1:
                    weight_list_1[0] = math.floor(num_futures * bottom) - num_futures * bottom \
                        if n1 != math.floor(num_futures * bottom) else -1
                num_mid = num_futures - len(weight_list_0) - len(weight_list_1)
                weight_mid = []
                if num_mid > 0:
                    weight_mid = [0 for _ in range(num_mid)]
                weight_list = weight_list_0 + weight_mid + weight_list_1
                abs_sum = sum([abs(ele) for ele in weight_list])
                weight_list = [ele / abs_sum for ele in weight_list]
                tmp_df["holding"] = weight_list
                return tmp_df
            # 加权交易
            else:
                # print("加权交易")
                sub_df = sub_df.sort_values('indicator', ascending=not ascending)
                sub_df["holding"] = np.arange(sub_df.shape[0]) + 1
                if sub_df.shape[0] > 1:
                    rank_mean = sub_df["holding"].mean()
                    sub_df["holding"] = sub_df["holding"].map(lambda x: x - rank_mean)
                    rank_sum = sum([abs(i) for i in list(sub_df["holding"])])
                    sub_df["holding"] = sub_df["holding"].map(lambda x: x / rank_sum)
                return sub_df

        df = df.groupby(["date"], as_index=False).apply(cal_holding)
        return df

    def cal_daily_pnl(self, trade_df):
        t0 = time.time()
        trade_df = trade_df.reset_index()
        date_df = pd.DataFrame()
        date_df["date"] = trade_df["date"].drop_duplicates().sort_values(ascending=True).reset_index(drop=True)
        date_df["next_date"] = date_df["date"].shift(-1)
        date_df = date_df.dropna(axis=0, how="any")
        # right： 换仓时间为当天交易日接近结束时，先平仓
        date_df["date_range"] = date_df.apply(
            lambda r: pd.date_range(start=r["date"], end=r["next_date"], closed="right"), axis=1)
        date_index_df = pd.DataFrame({"date": date_df.date.repeat(date_df.date_range.str.len()),
                                      "date_val": np.concatenate(date_df.date_range.values)})
        # print(date_index_df)
        trade_record = pd.merge(trade_df, date_index_df, on=["date"])
        t1 = time.time()

        # print("time duration 0 ", t1 - t0)

        date_index_df.rename(columns = {"date": "op_date", "date_val": "date"},  inplace = True)
        trade_record.rename(columns = {"date_val": "date", "date": "op_date"}, inplace = True)

        # 计算 daily value change
        df = self.future_proxy.get_daily_df(col_list=["code", "close"])
        df["date"] = df.index
        df = df.reset_index(drop=True)
        def cal_ratio(sub_df):
            sub_df = sub_df.sort_values(by = ["date"], ascending = True)
            sub_df["close_ratio"] = sub_df["close"].pct_change(periods=1)
            # print(sub_df)
            # sub_df["close_pre"] = sub_df["close"].shift(1)
            # sub_df["close_ratio"] = sub_df.apply(lambda r: r["close"]/r["close_pre"] - 1, axis =1)
            # # print(sub_df[-5:])
            return sub_df
        df = df.groupby(["code"], as_index = False).apply(cal_ratio)
        df = df.reset_index(drop  = True)

        t2 = time.time()
        # print("duration 1 ", t2 - t1)
        # print("-" * 77)
        # print(df[:100])

        trade_record = pd.merge(trade_record, df, on=["date", "code"], how="inner")
        # trade_record["return"] = trade_record.apply(lambda r: (r["close"] - r["open"]) / r["open"], axis=1)
        # print(trade_record[:100])
        # print("-" * 7)
        trade_record["close_ratio"] = trade_record.apply(lambda r: r["close_ratio"] * r["holding"], axis=1)

        # del df, date_df, date_index_df
        daily_pnl = trade_record[[ "date", "close_ratio"]].groupby(["date"], as_index=False).sum()
        daily_pnl.rename(columns = {"close_ratio": "daily_v_change"}, inplace = True)
        daily_pnl = pd.merge(daily_pnl, date_index_df, on = ["date"])

        # print("-" *7)
        # print(daily_pnl[:100])
        daily_pnl["daily_v_ratio"] = daily_pnl["daily_v_change"] + 1

        def cal_pnl(sub_df):
            sub_df = sub_df.sort_values(by=["date"], ascending = True)
            sub_df["cum_v"] = sub_df["daily_v_ratio"].cumprod()
            sub_df["cum_v_prev"] = sub_df["cum_v"].shift(1)
            sub_df = sub_df.fillna(1)
            sub_df["pnl"] = sub_df.apply(lambda r: r["cum_v"] - r["cum_v_prev"] , axis = 1)
            # print(sub_df)
            return  sub_df

        daily_pnl = daily_pnl.groupby(["op_date"]).apply(cal_pnl)
        # print("duration 2", time.time() - t2)
        # print(daily_pnl)
        # breakpoint()
        daily_pnl = daily_pnl[["date", "daily_v_change", "pnl"]]
        daily_pnl = daily_pnl.reset_index(drop = True)

        # print(daily_pnl)
        daily_pnl = daily_pnl.set_index(["date"])
        # print("Time usage ", time.time() - t0)
        # print(daily_pnl[:300])
        # print("-" * 3)
        return daily_pnl


    def get_op_code_df(self, op_cond):
        # todo get the column from DB factors
        code_df = self.proxy.get_op_code_df()
        # code_df = code_df.set_index(["date"])

        # get main code or nearest 1, 2, 3, 4 code
        # todo: add  code df check volume function
        if op_cond["is_main_contract_op"] == True:
            op_col = "main"
        else:
            op_col = "nearest_" + str(int(op_cond["n_nearest_index_op"]))

        op_code_df = code_df[[op_col]]
        op_code_df = op_code_df.rename(columns = {op_col: "code"})
        op_code_df = op_code_df.dropna(how = "any", axis = 0)

        # get matching future pool
        future_pool =  op_cond["fut_pool"]
        op_code_df["instrument"] = op_code_df["code"].map(self.extract_instrument_from_code)

        if isinstance(future_pool, str):
            future_pool = future_pool.split(",")
            op_code_df = op_code_df[op_code_df["instrument"].isin(future_pool)]

        op_code_df = op_code_df.reset_index()
        op_code_df = op_code_df.set_index(["date", "instrument"])

        # todo: check if static future pool, what if dynamic future pool

        return op_code_df


    def filter(self):
        df = self.proxy.get_performance_df()
        filter_result = np.ones(len(df))
        performance_dict = self.dataframe_2dict(df)
        for condition_i in self.condition:
                filter_result_i = self.parser_eval(condition_i, performance_dict)
                filter_result = np.logical_and(filter_result,filter_result_i)
        return df.loc[filter_result][['alpha_id','op_id']].reset_index(drop  = True)

    def filter_by_condition(self,condition_):
        df = self.proxy.get_performance_df()
        performance_dict = self.dataframe_2dict(df)
        filter_result = self.parser_eval(condition_, performance_dict)
        # print(filter_result)
        return df.loc[filter_result][['alpha_id','op_id']].reset_index(drop  = True)

    def run_filter_performance(self,condition_):
        df = self.proxy.get_performance_df()
        performance_dict = self.dataframe_2dict(df)
        filter_result = self.parser_eval(condition_, performance_dict)
        return df.loc[filter_result].reset_index(drop = True)

    def parser_eval(self, expression,factor_dict):
        if self.parser == None:
            print('Parser init...')
            self.parser = Parser_dataview.Parser()
        expr = self.parser.parse(expression)
        expr_parsed = expr.evaluate(factor_dict)
        return expr_parsed

    @staticmethod
    def dataframe_2dict(df):
        dict = {}
        for key in df.columns:
            dict[key] = df[key]
        return dict



# if __name__ == "__main__":
#     db_name = 'ultralpha_db'
#     host_name = '40.73.102.25'
#     user = 'cyr'
#     password = 'cyr'
#     port = '5432'
#     fut_name = 'al'
#     start_date = '2010-04-01'
#     end_date = '2014-04-01'
#     print ('YOUVEFKED UP.')
#
#     data_proxy = FactorDatabase(db_name=db_name, host_name=host_name, user_name=user, pwd=password,
#                                 port=port)
#     future_proxy = FutureDatabase(db_name = db_name,host_name = host_name, user_name = user, pwd = password,
#                               port = port )
#
#     dv = DataView(data_proxy=data_proxy, future_proxy = future_proxy)
#
#     keys = dv.filter()
#     dv.get_match_stras()

    # op_df = pd.read_csv('alpha_data\\op_param_df.csv')
    # print(op_df[:10])
    # param_pool = dv.param_generator(op_df)
    # print(param_pool)
