import sqlite3
from enum import Enum
from sqlalchemy import create_engine
import pandas as pd

class Tables(Enum):
    champions_data = 'champions_data'

class SQLite:
    def __init__(self,name):
        self.db = create_engine(f'sqlite://{name}', echo=False)

    def drop(self,table):
        with sqlite3.connect(self.base) as connect:
            cursor = connect.cursor()
            cursor.execute(f'DROP TABLE {table}')
        return f'Удалена таблица ({table})'

    def from_df(self,df,name):
        df.to_sql(name, con=self.db)

    def from_column(self, df, col_name):
        df = pd.DataFrame.from_dict(df[col_name].to_dict(),orient='index')
        self.from_df(df,col_name)
