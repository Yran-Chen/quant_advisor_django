import numpy as np
import time
import pandas as pd


class CachePool():

    def __init__(self):
        # self.keys = []
        self.save_pool = {}
        self.user_pool = {}
        self.run_kernel = {}

    def save_strategy_for_user(self,strat,uid=None,user_proxy = None):
        """用户保存策略"""

        # if uid not in self.user_pool.keys():
        if uid not in self.user_pool.keys():
            print ('User not init.')
        else:
            stra_dict = strat.to_dict()
            df = pd.DataFrame.from_dict(stra_dict,orient='index').T
            pid = user_proxy.add_user_db(df)
            print('1')
            print(pid)
            # self.user_pool['uid'][''] =
        # self.user_pool[strat['uid']].add2stra_pool(strat)

    def load_strategy_for_user(self,uid,user_proxy = None):
        """用户加载策略"""

        if uid in self.user_pool.keys():
            # print('1')
            return self.user_pool[uid]
        else:
            # print('2')
            futStratPoolTmp = FutStrategyPool(uid)
            user_df = user_proxy.get_user_df(uid=uid)
            # print('3')
            # print(user_df)
            futStratPoolTmp.load_from_df(user_df)
            self.user_pool[uid] = futStratPoolTmp
            # print(self.user_pool[uid])

            return self.user_pool[uid]

    def get_pid_for_user(self, uid, name=None, user_proxy=None):

        return user_proxy.get_pid_df(uid=uid,name=name)

    def run_forward(self,dataview):
        return 0

    def save_key_values(self, stras_df):
        for key in stras_df.columns:
            if self.save_pool[key] is not None:
                self.save_pool[key] = stras_df[key]
        return 0

    def load_key_values(self, key_df):
        keys = self.df2keys(key_df)
        stras_df_ = pd.DataFrame()
        for key in keys:
            stras_df_.insert(0, key, self.save_pool[key])
        return stras_df_

    def find_filter_key(self, key_df):
        keyset = self.df2keys(key_df)
        already_saved_key = []
        for key in keyset:
            if key in self.save_pool.keys():
                already_saved_key.append(key)
            else:
                self.save_pool[key] = None
        # print(keyset)
        # print(already_saved_key)
        # print(self.save_pool.keys())
        if already_saved_key is not None:
            # print('ASK :',already_saved_key)
            for ki in already_saved_key:
                alpha_id, op_id = ki.split('$')
                index_ = key_df.loc[key_df['alpha_id'] == alpha_id].index
                index_ = key_df.loc[index_].loc[key_df['op_id'] == op_id].index
                # print(index_)
                key_df.drop(index=index_, axis=0, inplace=True)
        # print(key_df)
        return key_df

    def save_all_strategy_from_cache(self, stras_df):
        for key in stras_df.columns:
                    self.save_pool[key] = stras_df[key]

    def save_filter_key(self, key_df):
        keyset = self.df2keys(key_df)
        already_saved_key = []
        for key in keyset:
            if key in self.save_pool.keys():
                already_saved_key.append(key)
            else:
                self.save_pool[key] = None
            # self.save_pool[key] = stras_df[key]
        return already_saved_key

    @staticmethod
    def keys2df(keys):
        df = pd.DataFrame(columns=['alpha_id', 'op_id'])
        for key in keys:
            alpha_id, op_id = key.split('$')
            df.insert(value=[alpha_id, op_id])
        print(df)
        return df

    @staticmethod
    def df2keys(df):
        keyset = []
        # print(df)
        for i in df.index:
            # print(i)alpha_id=alpha_id.replace('-','_'), op_id=op_id.replace('-','_')
            keyset.append('{0}${1}'.format(df.loc[i]['alpha_id'], df.loc[i]['op_id']))
        return keyset

class FutStrategyPool():
    """策略缓存池"""

    def __init__(self,uid):
        self.uid = uid
        self.stra_pool = {}

    def add2stra_pool(self,strat):
        if strat.uid == self.uid:
            self.stra_pool[strat.name] = strat
        else:
            print('Wrong User. Cant Copy.')

    def get_strat_name(self):
        return self.stra_pool.keys()

    def load_from_df(self,df):
            for i in df.index:
                strat_tmp = FutStrategy()
                strat_tmp.strat_load_from_dic(  df.loc[i].to_dict()  )
                self.stra_pool[strat_tmp.name] = strat_tmp

class FutStrategy():
    def __init__(self):
        self.uid = None
        self.name = None
        self.start_date = None
        self.end_date = None
        self.selected = None
        self.opt_method = None
        self.opt_param = None
        self.pid = None

    def strat_load_from_dic(self,strat_dic):

        for key, value in strat_dic.items():
            if value is None or len(str(value))==0:
                strat_dic[key] = np.nan

        self.uid = strat_dic['uid']
        self.name = strat_dic['name']
        self.start_date = strat_dic['start_date']
        self.end_date = strat_dic['end_date']
        self.selected = strat_dic['selected']
        self.opt_method = strat_dic['opt_method']
        self.opt_param = strat_dic['opt_param']

    def to_dict(self):
        strat_dic = {}
        strat_dic['uid'] = self.uid
        strat_dic['name'] = self.name
        strat_dic['start_date'] = self.start_date
        strat_dic['end_date'] = self.end_date
        strat_dic['selected'] = self.selected
        strat_dic['opt_method'] = self.opt_method
        strat_dic['opt_param'] = self.opt_param

        return strat_dic

# cachePoolDefault = CachePool()
