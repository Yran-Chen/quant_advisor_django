import psycopg2
from database.DB_Database import Database
import pandas as pd
import numpy as np
import time
import os
import datetime
import util.datetime_process as dtp

class FutUserDatabase(Database):
    def __init__(self, db_name, host_name, user_name, pwd, port):
        Database.__init__(self,db_name,host_name,user_name,pwd,port)
        self.connnect_db()

    def add_data(self, table_name, df, if_new_col = True,keys= None):
        cursor = self.db.cursor()
        columns = self.get_columns_name(table_name)
        columns_new = df.columns
        columns_diff = list(set(columns_new).difference(set(columns)))
        if not columns_diff:
            return self.insert_data(table_name,df,keys=keys)
        else:
            if if_new_col:
                for col in columns_diff:
                    self.add_columns(table_name,col,self.type_trans(col))
                return self.insert_data(table_name,df,keys=keys)
            else:
                raise ValueError('Columns {} are not in table {}.'.format(columns_diff,table_name))

    def add_columns(self,table_name,columns_name,datatype):
        columns = self.get_columns_name(table_name)
        # print(columns)
        cursor = self.db.cursor()
        if columns_name in columns:
            print('Columns {} already existed.'.format(columns_name))
            return
        sql = "alter table {} add column {} {}" .format(
                table_name,columns_name,datatype
            )
        print(sql)
        try:
            cursor.execute(sql)
            self.db.commit()
        except:
            self.db.commit()
            print(
                "Failed to add columns to table {}".format(table_name)
            )
        cursor.close()

    def insert_data(self,table_name,df,keys):
        print('inserting data...')
        def insert_sql(cursor,table_name,col_name,data):
            sql = "INSERT into {0}({1}) VALUES{2} RETURNING pid".format(
                table_name,
                col_name,
                tuple(data.values)
            ).replace('nan','null')
            print(sql)
            try:
                cursor.execute(sql)
                return cursor.fetchall()
            except:
                print(
                    "Inserting Error."
                )
        cursor = self.db.cursor()
        col_name = self.list_rename(df.columns.values)
        if keys is not None:
            keys_name = self.list_rename(keys)
        for i in range(0, len(df.index)):
                data = df.iloc[i]
                key_flag = 0
                if keys is not None:
                    key_flag = key_flag | self.search_keys(table_name,keys_name,data[keys])
                    # print(key_flag,data[keys])
                    if key_flag:
                        insert_sql(cursor,table_name,col_name,data)
                        self.db.commit()
                    else:
                        continue
                else:
                    insert_sql(cursor,table_name,col_name,data)
                    self.db.commit()
        cursor.close()
        return

    def search_keys(self,table_name,key_name,key_values):
        cursor = self.db.cursor()
        sql = "SELECT * FROM {0} where ({1}) = {2}".format(
            table_name,key_name,tuple(key_values.values))
        try:
            print(sql)
            cursor.execute(sql)
            results = cursor.fetchall()
        except:
            raise ValueError(
                "Searching Error."
            )
        cursor.close()
        if not results:
            return 1
        else:
            return 0

    def list_rename(self,list_name):
        return ",".join(list_name)

    def type_trans(self,name):
        if name.endswith('id'):
            return 'varchar'
        elif name.endswith('date'):
            return 'date'
        elif name == 'code' or name == 'instrument':
            return 'varchar'
        elif name.startswith('near') or name.startswith('main') or name.endswith ('method') or name.endswith('param') or name == 'freq_unit' or name.startswith('index'):
            return 'varchar'
        elif name == 'weighted' or name.startswith('is') or name.startswith('if'):
            return 'bool'
        elif name.startswith('fut'):
            return 'varchar'
        elif name.endswith('selected'):
            return 'varchar'
        else:
            return 'double precision'

    def add_user_db(self, df, table_name = 'fut_automation'):
        return self.add_data(table_name=table_name, df=df, if_new_col=False, keys=None)


    def get_user_df (self,uid,table_name = 'fut_automation'):
        sql = "select * from {} " \
              "where uid = '{}'".format(table_name,uid)
        cursor = self.db.cursor()

        try:
            cursor.execute(sql)
            result = cursor.fetchall()
            # print(result)
            columns = self.get_columns_name(table_name)
            df = pd.DataFrame(result, columns=columns)

            for col in ["date", "start_date", "end_date"]:
                if col not in df.keys():
                    continue
                df[col] = df[col].map(dtp.date2datetime)
            cursor.close()
            return df
        except:
            print(
                "Failed to get data from table {}".format(table_name)
            )
            cursor.close()

    def get_list(self, uid, table_name='fut_automation'):
        """查数据库列表"""

        sql = "select pid, name from {} where uid='{}'".format(table_name, uid)
        cursor = self.db.cursor()
        try:
            cursor.execute(sql)
            result = cursor.fetchall()
            self.db.commit()
            # print('1')
        except Exception as e:
            self.db.rollback()
            cursor.execute(sql)
            result = cursor.fetchall()
            self.db.commit()
            # print('2')
        cursor.close()

        # cursor.execute(sql)
        # result = cursor.fetchall()
        # self.db.commit()
        # cursor.close()
        return result



    def get_list_value(self,uid,name,table_name = 'fut_automation'):
        """查数据库进行展示"""

        sql = "select * from {} " \
              "where uid = '{}' and name='{}'".format(table_name,uid,name)
        cursor = self.db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        print(sql)
        try:
            cursor.execute(sql)
            result = cursor.fetchall()    # 返回的是value
            self.db.commit()

            result_dict = dict(result[0])
            cursor.close()
            return result_dict
        except:
            print(
                "Failed to get data from table {}".format(table_name)
            )
            cursor.close()

    def delete_list_value(self, pid, name, table_name='fut_automation'):
        """删除"""

        sql = "delete from {} where pid = {} and name = '{}'".format(table_name, pid, name)
        cursor = self.db.cursor()
        cursor.execute(sql)
        self.db.commit()
        cursor.close()

    def save_value(self, dict):
        """更新保存"""

        # self.delete_list_value(str(dict['pid']) ,dict['name'])
        print('保存数据。。。')
        end_date = dict['end_date']
        # print(type(end_date))
        name = dict['name']
        opt_method = dict['opt_method']
        pid = int(dict['pid'])
        selected = dict['selected']
        start_date = dict['start_date']
        uid = dict['uid']
        opt_param = dict['opt_param']

        sql = "update fut_automation set end_date='{}', name='{}', opt_method='{}', selected='{}', start_date='{}', uid='{}', opt_param='{}' where pid={}".format(end_date, name, opt_method, selected, start_date, uid, opt_param, pid)
        print(sql)
        cursor = self.db.cursor()
        try:
            cursor.execute(sql)
            self.db.commit()
            # print('1')
        except Exception as e:
            self.db.rollback()
            cursor.execute(sql)
            self.db.commit()
            # print('2')
        cursor.close()


    def get_pid_df (self,uid,name = None,table_name = 'fut_automation'):
        if name is not None:
            sql = "select pid,uid,name from {} " \
              "where uid = '{}' and name = '{}' ".format(table_name,uid,name)
        else:
            sql = "select pid,uid,name from {} " \
              "where uid = '{}' ".format(table_name,uid)
        cursor = self.db.cursor()
        try:
            # print(sql)
            cursor.execute(sql)
            result = cursor.fetchall()
            columns = self.get_columns_name(table_name)
            df = pd.DataFrame.from_dict(result)
            return df
        except:
            print(
                "Failed to get pid from table {}".format(table_name)
            )
            cursor.close()

    # def get_pid_value(self, uid, pid, name=None, table_name = 'fut_automation'):
    #     if name:
    #         sql = "select * from {} where uid = {} and name = {} and pid = {}".format(table_name, uid, name, pid)
    #
    #     cursor = self.db.cursor()
    #     try:
    #         # print(sql)
    #         cursor.execute(sql)
    #         result = cursor.fetchall()
    #         columns = self.get_columns_name(table_name)
    #         df = pd.DataFrame.from_dict(result)
    #         return df
    #     except:
    #         print(
    #             "Failed to get pid from table {}".format(table_name)
    #         )
    #         cursor.close()

if __name__ == "__main__":

    db_name = 'ultralpha_db'
    host_name = '129.211.81.69'
    user = 'cyr'
    password = 'ultralpha2020_frozenduck'
    port = '5432'
    fut_name = 'al'
    start_date = '2010-04-01'
    end_date = '2014-04-01'

    fb = FutUserDatabase(db_name = db_name,host_name = host_name, user_name = user, pwd = password,port = port )

    df_master = fb.get_user_df(uid='master')
    print(df_master)
    # for i in df_master.index:
    #     print(df_master.loc[i].to_dict())

    # df = pd.read_csv("D:\!Ultralpha\!MyQuant\save\\fut_user_test.csv")
    # print(df)
    # fb.add_data(table_name='fut_automation',df=df,if_new_col=False)
