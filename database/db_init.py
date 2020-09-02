from database.DB_Factors import FactorDatabase
from database.DB_Future import FutureDatabase
from database.DB_Fut_User import FutUserDatabase
from fastback.views import DEBUG_

db_name = 'ultralpha_db'
host_name = '129.211.81.69'
user = 'cyr'
password = 'ultralpha2020_frozenduck'
port = '5432'


data_proxy = FactorDatabase(db_name=db_name, host_name=host_name, user_name=user, pwd=password,port=port)
user_proxy = FutUserDatabase(db_name=db_name, host_name=host_name, user_name=user, pwd=password,port=port)
if not DEBUG_:
    future_proxy = FutureDatabase(db_name = db_name,host_name = host_name, user_name = user, pwd = password,port = port)

else:
    future_proxy = None
