import bs4
import re
import sqlite3
import random
import time
import sqlalchemy
from enum import Enum
import sql_helper
import pandas as pd
from sqlalchemy import create_engine

DATABASE = create_engine('sqlite:///Statistics_Analyzer.sqlite', echo=False)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey

Base = declarative_base()

def try_repeat(func):
    def wrapper(*args, **kwargs):
        for i in range(0, 100):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print('\nError:', e)
                time_sleep = random.randint(11, 21) / 10
                print(f'Ждем после ошибки {time_sleep} секунд.')
                time.sleep(time_sleep)

    return wrapper


from typing import Union, Optional, Tuple
from typing import Optional
from typing import Tuple


class ChampionData:
    class DataTypes(Enum):
        stats = 'Stats'
        image = 'Image'
        info = 'Info'
        general = ''

    def __init__(self, current_patch: str, data_type: Optional[Union[str, DataTypes]] = DataTypes.general):
        self.current_patch = current_patch
        if isinstance(data_type, self.DataTypes):
            self.data_type = data_type.value
        else:
            self.data_type = data_type
        self.data = self.__load_data()
        pass

    @property
    def __path_to_raw_data(self) -> str:
        return f'https://ddragon.leagueoflegends.com/cdn/{self.current_patch}.1/data/en_US/champion.json'

    @property
    def __database(self) -> sqlalchemy.engine.Engine:
        return DATABASE

    @property
    def __table_name(self) -> str:
        return f'{type(self).__name__}{self.data_type}'

    def __load_data(self, force: Optional[bool] = False) -> pd.DataFrame:
        if not self.__database.dialect.has_table(self.__database, self.__table_name) or force:
            self.__get_data()
        return pd.read_sql(self.__table_name, con=self.__database, index_col='index')

    def update_data(self) -> pd.DataFrame:
        self.__drop_table()
        return self.__load_data(force = True)


    def change_data_type(self,data_type: Optional[Union[str, DataTypes]] = DataTypes.general) -> pd.DataFrame:
        if isinstance(data_type, self.DataTypes):
            self.data_type = data_type.value
        else:
            self.data_type = data_type
        self.data = self.__load_data()
        return self.data

    def __get_data(self) -> None:
        champions_json = requests.get(self.__path_to_raw_data).json()['data']
        champions_data = pd.DataFrame.from_dict(champions_json, orient='index')
        if self.data_type == '':
            self.__rm__cols_from_df_by_types(champions_data, (dict,list))
        else:
            champions_data = pd.DataFrame.from_dict(champions_data[self.data_type.lower()].to_dict(), orient='index')
        champions_data.to_sql(self.__table_name, con=DATABASE)

    def __rm__cols_from_df_by_types(self, df: pd.DataFrame, var_types: Tuple[type,...]) -> None:
        for var_type in var_types:
            for column in df:
                if df[column].apply(isinstance, args=(var_type,)).all():
                    df.drop(column, axis=1, inplace=True)
    def __drop_table(self):
        table = sqlalchemy.MetaData(self.__database,reflect=True).tables.get(self.__table_name)
        table.drop(self.__database)





class GolGG:
    url = 'https://gol.gg/esports/home/'
    sql = sql_helper.SQLite('/Statistics_Analyzer.sqlite')

    @try_repeat
    def html_code(self):
        return requests.get(self.url, headers={'User-Agent': 'Mozilla/5.0'}).text

    def champion_data(self, current_patch):
        champions_json = \
        requests.get(f'https://ddragon.leagueoflegends.com/cdn/{current_patch}.1/data/en_US/champion.json').json()[
            'data']
        a = pd.DataFrame.from_dict(champions_json, orient='index')
        stats = pd.DataFrame.from_dict(a['stats'].to_dict(), orient='index')
        image = pd.DataFrame.from_dict(a['image'].to_dict(), orient='index')
        info = pd.DataFrame.from_dict(a['info'].to_dict(), orient='index')
        info.to_sql('ch_info', con=DATABASE)
        print(a)
        columns = champions_json.keys()
        try:
            self.sql.drop('Statistics_Analyzer', 'champions_info')
        except sqlite3.OperationalError:
            pass
        self.sql.create('Statistics_Analyzer', 'champions_info', get_column_names_from_json_list(champions_json))
        for key, value in champions_json.items():
            sqlite_insert_in_table('Statistics_Analyzer', 'champions_info', convert_dict_data_to_tuple(value))


def get_js_html(url):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    browser = webdriver.Chrome(chrome_options=options)
    browser.get(url)
    browser.add_cookie(
        {'domain': 'www.oddsportal.com', 'expiry': 1592838307.116539, 'httpOnly': False, 'name': 'op_user_cookie',
         'path': '/', 'secure': False, 'value': '1951440212'})
    browser.add_cookie(
        {'domain': 'www.oddsportal.com', 'expiry': 1592838307.116539, 'httpOnly': False, 'name': 'op_user_hash',
         'path': '/', 'secure': False, 'value': 'db965e5cd8a31d51a2966389b455176b'})
    browser.get(url)
    html = browser.page_source
    browser.quit()
    return html




@try_repeat
def get_html_code(url):
    return requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).text


def convert_dict_keys_to_tuple(dictionary):
    keys = list()
    for key, value in dictionary.items():
        [keys.append(f'{key}__{elem}') for elem in convert_dict_keys_to_tuple(value)] if type(
            value) == dict else keys.append(key)
    return keys


def get_column_names_from_json_list(json_list):
    return convert_dict_keys_to_tuple(next(iter(json_list.values())))


def sqlite_format_name_columns(name_columns, create_new_table_format=False):
    return fn.reduce(lambda a, x: a + x + (' LONGTEXT' if create_new_table_format is True else '') + ', ', name_columns,
                     '')[:-2]


def convert_dict_data_to_tuple(dictionary):
    values = list()
    for key, value in dictionary.items():
        [values.append(elem) for elem in convert_dict_data_to_tuple(value)] if type(value) == dict else values.append(
            str(value))
    return tuple(values)


def sqlite_create_table(base_name, table_name, name_columns):
    with sqlite3.connect(f'{base_name}.sqlite') as connect:
        cursor = connect.cursor()
        cursor.execute(f'CREATE TABLE {table_name} (champions {name_columns})')
        connect.commit()
    print(f'Создана таблица ({table_name})')


def sqlite_drop_table(base_name, table_name):
    with sqlite3.connect(f'{base_name}.sqlite') as connect:
        cursor = connect.cursor()
        cursor.execute(f'DROP TABLE {table_name}')
    print(f'Удалена таблица ({table_name})')


def sqlite_insert_in_table(base_name, table_name, keys):
    with sqlite3.connect(f'{base_name}.sqlite') as connect:
        cursor = connect.cursor()
        cursor.execute(f'PRAGMA table_info({table_name})')
        num_of_columns = cursor.fetchall()[-1][0]
        query = f'insert into {table_name} values (?{",?" * num_of_columns})'
        cursor.execute(query, keys)
        connect.commit()


@try_repeat
def get_champions_info(current_patch):
    champions_json = \
    requests.get(f'https://ddragon.leagueoflegends.com/cdn/{current_patch}.1/data/en_US/champion.json').json()['data']
    columns = sqlite_format_name_columns(get_column_names_from_json_list(champions_json), True)
    try:
        sqlite_drop_table('Statistics_Analyzer', 'champions_info')
    except sqlite3.OperationalError:
        pass
    sqlite_create_table('Statistics_Analyzer', 'champions_info', columns)
    for key, value in champions_json.items():
        sqlite_insert_in_table('Statistics_Analyzer', 'champions_info', convert_dict_data_to_tuple(value))


# @try_repeat
def get_number_of_matches(url='https://gol.gg/esports/home/'):
    html = get_html_code(str(re.findall('(.*?\/\/.*?)\/', url)[0]) +
                         str(bs4.BeautifulSoup(get_html_code(url), 'html.parser').find_all('table',
                                                                                           class_='table_list')[
                                 0].find_all('a')[1].get('href'))[2:])
    # return int(sorted(set(re.findall('\/game\/gameshow\.php\?id=([0-9]{1,})',html)))[-1])
    print(int(sorted(set(re.findall('\/game\/stats\\/([0-9]{1,})', html)))[-1]))
    return int(sorted(set(re.findall('\/game\/stats\\/([0-9]{1,})', html)))[-1])


@try_repeat
def get_matches_info_html(url, number_of_matches):
    with sqlite3.connect('Statistics_Analyzer.sqlite') as connect:
        cursor = connect.cursor()
        try:
            cursor.execute("CREATE TABLE matches_info_html (site_id INT, match_info_html LONGTEXT)")
            connect.commit()
            try:
                cursor.execute("SELECT  MAX(site_id) FROM matches_info_parsed")
                start_id = cursor.fetchall()[0][0] + 1
            except:
                start_id = 1
            print('Создание таблицы (matches_info_html)')

        except sqlite3.OperationalError:
            try:
                cursor.execute("SELECT  MAX(site_id) FROM matches_info_parsed")
                start_id_parsed = cursor.fetchall()[0][0] + 1
                cursor.execute("SELECT  MAX(site_id) FROM matches_info_html")
                start_id_html = cursor.fetchall()[0][0] + 1
                start_id = start_id_html if start_id_html > start_id_parsed else start_id_parsed
            except:
                try:
                    cursor.execute("SELECT  MAX(site_id) FROM matches_info_html")
                    start_id = cursor.fetchall()[0][0] + 1
                except:
                    start_id = 1
            print('Таблица существует (matches_info_html)')
        for i in range(start_id, number_of_matches + 1):
            cursor.execute("INSERT INTO matches_info_html (site_id,match_info_html) VALUES (?,?)",
                           (i, get_html_code(url + str(i))))
            connect.commit()
            print('\r%3.6s%% (%s/%s)' % (i * 100 / (number_of_matches), str(i), str(number_of_matches)), end='')


@try_repeat
def get_matches_info_json(number_of_matches):
    with sqlite3.connect('Statistics_Analyzer.sqlite') as connect:
        cursor = connect.cursor()
        try:
            cursor.execute(
                "CREATE TABLE matches_info_json (site_id INT, match_history LONGTEXT, match_timeline LONGTEXT)")
            connect.commit()
            try:
                cursor.execute("SELECT  MAX(site_id) FROM matches_info_parsed")
                start_id = cursor.fetchall()[0][0] + 1
            except TypeError:
                start_id = 1
            print('\nСоздание таблицы (matches_info_json)')
        except sqlite3.OperationalError:
            try:
                cursor.execute("SELECT  MAX(site_id) FROM matches_info_json")
                start_id = cursor.fetchall()[0][0] + 1
            except:
                start_id = 1
            print('\nТаблица существует (matches_info_json)')
        for i in range(start_id, number_of_matches + 1):
            cursor.execute("SELECT match_info_html FROM matches_info_html WHERE site_id=?", (i,))
            match_info_soup = bs4.BeautifulSoup(cursor.fetchall()[0][0], 'html.parser')
            # print(i)
            # print(match_info_soup.find_all('div', class_='col-xs-7')[0].text.split()[-1][1:-1])
            if match_info_soup.find_all('div', class_='col-xs-7')[0].text.split()[-1][1:-1] != 'CN' and \
                    match_info_soup.find_all('div', class_='col-xs-7')[0].text.split()[-1][1:-1] != 'WR' and len(
                match_info_soup.find_all('table')) > 6 and \
                    match_info_soup.find_all('div', class_='col-xs-7')[0].text.split()[-1][1:-1] != 'TR':

                # match_info_soup.find_all('table')[1].find('tr').find_all('td')[1].find('span').text != '0:00' and str(type(match_info_soup.find('a', text='Match history')))!="<class 'NoneType'>":
                # and datetime.datetime.strptime(match_info_soup.find_all('div', class_='col-sm-4')[2].text.split()[0],"%Y-%m-%d") >= datetime.datetime.strptime("2016-12-14", "%Y-%m-%d"):
                # print(match_info_soup.find('a', text='Match history').get('href'))
                url_match_history = str('https://acs.leagueoflegends.com/v1/stats/game/' + re.findall('details\/(.*)',
                                                                                                      match_info_soup.find(
                                                                                                          'a',
                                                                                                          text='Match history').get(
                                                                                                          'href'))[
                    0]).strip()
                url_check = len(re.findall('\?gameHash', url_match_history))
                if (url_check == 1):
                    url_match_timeline = str(re.sub('\?gameHash', '/timeline?gameHash', url_match_history))
                elif url_check == 0:
                    url_match_timeline = url_match_history + '/timeline'
                match_history = requests.get(url_match_history).json()

                match_timeline = requests.get(url_match_timeline).json()

                if str(match_history) == "{'httpStatus': 429, 'errorCode': 'CLIENT_RATE_LIMITED'}" or str(
                        match_timeline) == "{'httpStatus': 429, 'errorCode': 'CLIENT_RATE_LIMITED'}":
                    raise Exception('Ошибка CLIENT_RATE_LIMITED')
                cursor.execute("INSERT INTO matches_info_json (site_id,match_history,match_timeline) VALUES (?,?,?)",
                               (i, pickle.dumps(match_history), pickle.dumps(match_timeline)))
                connect.commit()
                # time.sleep(random.randint(8, 15) / 10)
            print('\r%3.6s%% (%s/%s)' % (i * 100 / (number_of_matches), str(i), str(number_of_matches)), end='')

        cursor.close()


def get_matches_info_parsed(number_of_matches):
    with sqlite3.connect('Statistics_Analyzer.sqlite') as connect:
        cursor = connect.cursor()
        try:
            cursor.execute("""CREATE TABLE matches_info_parsed (                    
                        site_id INTEGER,
                        championship INTEGER, 
                        server VARCHAR, 
                        match_date timestring, 
                        game_patch VARCHAR, 
                        match_time timestring, 
                        team VARCHAR, 
                        is_winner VARCHAR, 
                        side VARCHAR, 
                        enemy_team VARCHAR, 
                        first_blood VARCHAR,
                        first_tower VARCHAR,
                        bans VARCHAR,
                        top_nick VARCHAR, 
                        jungle_nick VARCHAR, 
                        mid_nick VARCHAR,
                        adc_nick VARCHAR,
                        sup_nick VARCHAR,
                        top_pick VARCHAR, 
                        jungle_pick VARCHAR, 
                        mid_pick VARCHAR, 
                        adc_pick VARCHAR, 
                        sup_pick VARCHAR,
                        top_cs VARCHAR, 
                        mid_cs VARCHAR, 
                        jungle_cs VARCHAR,  
                        bot_cs VARCHAR,  
                        sup_cs VARCHAR, 
                        enemy_top_cs VARCHAR, 
                        enemy_mid_cs VARCHAR, 
                        enemy_jungle_cs VARCHAR, 
                        enemy_bot_cs VARCHAR,  
                        enemy_sup_cs VARCHAR,
                        top_cs_jungle VARCHAR, 
                        mid_cs_jungle VARCHAR,
                        jungle_cs_jungle VARCHAR,
                        bot_cs_jungle VARCHAR,
                        sup_cs_jungle VARCHAR,
                        enemy_top_cs_jungle VARCHAR,
                        enemy_mid_cs_jungle VARCHAR, 
                        enemy_jungle_cs_jungle VARCHAR, 
                        enemy_bot_cs_jungle VARCHAR,  
                        enemy_sup_cs_jungle VARCHAR,
                        top_gold VARCHAR, 
                        mid_gold VARCHAR, 
                        jungle_gold VARCHAR,  
                        bot_gold VARCHAR,  
                        sup_gold VARCHAR, 
                        enemy_top_gold VARCHAR, 
                        enemy_mid_gold VARCHAR, 
                        enemy_jungle_gold VARCHAR, 
                        enemy_bot_gold VARCHAR, 
                        enemy_sup_gold VARCHAR,
                        top_xp VARCHAR, 
                        mid_xp VARCHAR, 
                        jungle_xp VARCHAR, 
                        bot_xp VARCHAR,  
                        sup_xp VARCHAR, 
                        enemy_top_xp VARCHAR, 
                        enemy_mid_xp VARCHAR, 
                        enemy_jungle_xp VARCHAR,
                        enemy_bot_xp VARCHAR,  
                        enemy_sup_xp VARCHAR,
                        top_lvl VARCHAR, 
                        mid_lvl VARCHAR, 
                        jungle_lvl VARCHAR,  
                        bot_lvl VARCHAR,  
                        sup_lvl VARCHAR, 
                        enemy_top_lvl VARCHAR, 
                        enemy_mid_lvl VARCHAR, 
                        enemy_jungle_lvl VARCHAR, 
                        enemy_bot_lvl VARCHAR,  
                        enemy_sup_lvl VARCHAR,
                        top_tower_get VARCHAR,
                        mid_tower_get VARCHAR,
                        bot_tower_get VARCHAR,
                        nexus_tower_get VARCHAR,
                        top_tower_lost VARCHAR,
                        mid_tower_lost VARCHAR,
                        bot_tower_lost VARCHAR,
                        nexus_tower_lost VARCHAR,
                        top_ingib_get VARCHAR,
                        mid_ingib_get VARCHAR,
                        bot_ingib_get VARCHAR,
                        top_ingib_lost VARCHAR,
                        mid_ingib_lost VARCHAR,
                        bot_ingib_lost VARCHAR,
                        dragon_get VARCHAR,
                        dragon_lost VARCHAR,
                        baron_get VARCHAR,
                        baron_lost VARCHAR,
                        herold_get VARCHAR,
                        herold_lost VARCHAR,
                        kill_top_ally VARCHAR,
                        death_top_ally VARCHAR,
                        assists_top_ally VARCHAR,
                        kill_jng_ally VARCHAR,
                        death_jng_ally VARCHAR,
                        assists_jng_ally VARCHAR,
                        kill_mid_ally VARCHAR,
                        death_mid_ally VARCHAR,
                        assists_mid_ally VARCHAR,
                        kill_adc_ally VARCHAR,
                        death_adc_ally VARCHAR,
                        assists_adc_ally VARCHAR,
                        kill_sup_ally VARCHAR,
                        death_sup_ally VARCHAR,
                        assists_sup_ally VARCHAR,
                        kill_top_enemy VARCHAR,
                        death_top_enemy VARCHAR,
                        assists_top_enemy VARCHAR,
                        kill_jng_enemy VARCHAR,
                        death_jng_enemy VARCHAR,
                        assists_jng_enemy VARCHAR,
                        kill_mid_enemy VARCHAR,
                        death_mid_enemy VARCHAR,
                        assists_mid_enemy VARCHAR,
                        kill_adc_enemy VARCHAR,
                        death_adc_enemy VARCHAR,
                        assists_adc_enemy VARCHAR,
                        kill_sup_enemy VARCHAR,
                        death_sup_enemy VARCHAR,
                        assists_sup_enemy VARCHAR,
                        simple_wards_ally VARCHAR, 
                        vision_wards_ally VARCHAR,
                        simple_wards_enemy VARCHAR, 
                        vision_wards_enemy VARCHAR,
                        kill_simple_wards_ally VARCHAR, 
                        kill_vision_wards_ally VARCHAR,
                        kill_simple_wards_enemy VARCHAR, 
                        kill_vision_wards_enemy VARCHAR,
                        ally_top_longestTimeSpentLiving VARCHAR,
                        ally_top_totalDamageDealt VARCHAR,
                        ally_top_magicDamageDealt VARCHAR,
                        ally_top_physicalDamageDealt VARCHAR,
                        ally_top_trueDamageDealt VARCHAR,
                        ally_top_totalDamageDealtToChampions VARCHAR,
                        ally_top_magicDamageDealtToChampions VARCHAR,
                        ally_top_physicalDamageDealtToChampions VARCHAR,
                        ally_top_trueDamageDealtToChampions VARCHAR,
                        ally_top_totalHeal VARCHAR,
                        ally_top_totalDamageTaken VARCHAR,
                        ally_top_magicalDamageTaken VARCHAR,
                        ally_top_physicalDamageTaken VARCHAR,
                        ally_top_trueDamageTaken VARCHAR,
                        ally_top_goldEarned VARCHAR,
                        ally_top_totalMinionsKilled VARCHAR,
                        ally_top_neutralMinionsKilled VARCHAR,
                        ally_top_neutralMinionsKilledTeamJungle VARCHAR,
                        ally_top_neutralMinionsKilledEnemyJungle VARCHAR,
                        ally_top_totalTimeCrowdControlDealt VARCHAR,
                        ally_top_wardsPlaced VARCHAR,
                        ally_top_wardsKilled VARCHAR,
                    ally_top_creepsPerMinDeltas0_10 VARCHAR,
                    ally_top_creepsPerMinDeltas10_20 VARCHAR,
                    ally_top_creepsPerMinDeltas20_30 VARCHAR,
                    ally_top_creepsPerMinDeltas30_end VARCHAR,
                    ally_top_xpPerMinDeltas0_10 VARCHAR,
                    ally_top_xpPerMinDeltas10_20 VARCHAR,
                    ally_top_xpPerMinDeltas20_30 VARCHAR,
                    ally_top_xpPerMinDeltas30_end VARCHAR,
                    ally_top_goldPerMinDeltas0_10 VARCHAR,
                    ally_top_goldPerMinDeltas10_20 VARCHAR,
                    ally_top_goldPerMinDeltas20_30 VARCHAR,
                    ally_top_goldPerMinDeltas30_end VARCHAR,
                    ally_top_csDiffPerMinDeltas0_10 VARCHAR,
                    ally_top_csDiffPerMinDeltas10_20 VARCHAR,
                    ally_top_csDiffPerMinDeltas20_30 VARCHAR,
                    ally_top_csDiffPerMinDeltas30_end VARCHAR,
                    ally_top_xpDiffPerMinDeltas0_10 VARCHAR,
                    ally_top_xpDiffPerMinDeltas10_20 VARCHAR,
                    ally_top_xpDiffPerMinDeltas20_30 VARCHAR,
                    ally_top_xpDiffPerMinDeltas30_end VARCHAR,
                    ally_top_damageTakenPerMinDeltas0_10 VARCHAR,
                    ally_top_damageTakenPerMinDeltas10_20 VARCHAR,
                    ally_top_damageTakenPerMinDeltas20_30 VARCHAR,
                    ally_top_damageTakenPerMinDeltas30_end VARCHAR,
                    ally_top_damageTakenDiffPerMinDeltas0_10 VARCHAR,
                    ally_top_damageTakenDiffPerMinDeltas10_20 VARCHAR,
                    ally_top_damageTakenDiffPerMinDeltas20_30 VARCHAR,
                    ally_top_damageTakenDiffPerMinDeltas30_end VARCHAR,
                        ally_jng_longestTimeSpentLiving VARCHAR,
                        ally_jng_totalDamageDealt VARCHAR,
                        ally_jng_magicDamageDealt VARCHAR,
                        ally_jng_physicalDamageDealt VARCHAR,
                        ally_jng_trueDamageDealt VARCHAR,
                        ally_jng_totalDamageDealtToChampions VARCHAR,
                        ally_jng_magicDamageDealtToChampions VARCHAR,
                        ally_jng_physicalDamageDealtToChampions VARCHAR,
                        ally_jng_trueDamageDealtToChampions VARCHAR,
                        ally_jng_totalHeal VARCHAR,
                        ally_jng_totalDamageTaken VARCHAR,
                        ally_jng_magicalDamageTaken VARCHAR,
                        ally_jng_physicalDamageTaken VARCHAR,
                        ally_jng_trueDamageTaken VARCHAR,
                        ally_jng_goldEarned VARCHAR,
                        ally_jng_totalMinionsKilled VARCHAR,
                        ally_jng_neutralMinionsKilled VARCHAR,
                        ally_jng_neutralMinionsKilledTeamJungle VARCHAR,
                        ally_jng_neutralMinionsKilledEnemyJungle VARCHAR,
                        ally_jng_totalTimeCrowdControlDealt VARCHAR,
                        ally_jng_wardsPlaced VARCHAR,
                        ally_jng_wardsKilled VARCHAR,
                    ally_jng_creepsPerMinDeltas0_10 VARCHAR,
                    ally_jng_creepsPerMinDeltas10_20 VARCHAR,
                    ally_jng_creepsPerMinDeltas20_30 VARCHAR,
                    ally_jng_creepsPerMinDeltas30_end VARCHAR,
                    ally_jng_xpPerMinDeltas0_10 VARCHAR,
                    ally_jng_xpPerMinDeltas10_20 VARCHAR,
                    ally_jng_xpPerMinDeltas20_30 VARCHAR,
                    ally_jng_xpPerMinDeltas30_end VARCHAR,
                    ally_jng_goldPerMinDeltas0_10 VARCHAR,
                    ally_jng_goldPerMinDeltas10_20 VARCHAR,
                    ally_jng_goldPerMinDeltas20_30 VARCHAR,
                    ally_jng_goldPerMinDeltas30_end VARCHAR,
                    ally_jng_csDiffPerMinDeltas0_10 VARCHAR,
                    ally_jng_csDiffPerMinDeltas10_20 VARCHAR,
                    ally_jng_csDiffPerMinDeltas20_30 VARCHAR,
                    ally_jng_csDiffPerMinDeltas30_end VARCHAR,
                    ally_jng_xpDiffPerMinDeltas0_10 VARCHAR,
                    ally_jng_xpDiffPerMinDeltas10_20 VARCHAR,
                    ally_jng_xpDiffPerMinDeltas20_30 VARCHAR,
                    ally_jng_xpDiffPerMinDeltas30_end VARCHAR,
                    ally_jng_damageTakenPerMinDeltas0_10 VARCHAR,
                    ally_jng_damageTakenPerMinDeltas10_20 VARCHAR,
                    ally_jng_damageTakenPerMinDeltas20_30 VARCHAR,
                    ally_jng_damageTakenPerMinDeltas30_end VARCHAR,
                    ally_jng_damageTakenDiffPerMinDeltas0_10 VARCHAR,
                    ally_jng_damageTakenDiffPerMinDeltas10_20 VARCHAR,
                    ally_jng_damageTakenDiffPerMinDeltas20_30 VARCHAR,
                    ally_jng_damageTakenDiffPerMinDeltas30_end VARCHAR,                 
                        ally_mid_longestTimeSpentLiving VARCHAR,
                        ally_mid_totalDamageDealt VARCHAR,
                        ally_mid_magicDamageDealt VARCHAR,
                        ally_mid_physicalDamageDealt VARCHAR,
                        ally_mid_trueDamageDealt VARCHAR,
                        ally_mid_totalDamageDealtToChampions VARCHAR,
                        ally_mid_magicDamageDealtToChampions VARCHAR,
                        ally_mid_physicalDamageDealtToChampions VARCHAR,
                        ally_mid_trueDamageDealtToChampions VARCHAR,
                        ally_mid_totalHeal VARCHAR,
                        ally_mid_totalDamageTaken VARCHAR,
                        ally_mid_magicalDamageTaken VARCHAR,
                        ally_mid_physicalDamageTaken VARCHAR,
                        ally_mid_trueDamageTaken VARCHAR,
                        ally_mid_goldEarned VARCHAR,
                        ally_mid_totalMinionsKilled VARCHAR,
                        ally_mid_neutralMinionsKilled VARCHAR,
                        ally_mid_neutralMinionsKilledTeamJungle VARCHAR,
                        ally_mid_neutralMinionsKilledEnemyJungle VARCHAR,
                        ally_mid_totalTimeCrowdControlDealt VARCHAR,
                        ally_mid_wardsPlaced VARCHAR,
                        ally_mid_wardsKilled VARCHAR,
                    ally_mid_creepsPerMinDeltas0_10 VARCHAR,
                    ally_mid_creepsPerMinDeltas10_20 VARCHAR,
                    ally_mid_creepsPerMinDeltas20_30 VARCHAR,
                    ally_mid_creepsPerMinDeltas30_end VARCHAR,
                    ally_mid_xpPerMinDeltas0_10 VARCHAR,
                    ally_mid_xpPerMinDeltas10_20 VARCHAR,
                    ally_mid_xpPerMinDeltas20_30 VARCHAR,
                    ally_mid_xpPerMinDeltas30_end VARCHAR,
                    ally_mid_goldPerMinDeltas0_10 VARCHAR,
                    ally_mid_goldPerMinDeltas10_20 VARCHAR,
                    ally_mid_goldPerMinDeltas20_30 VARCHAR,
                    ally_mid_goldPerMinDeltas30_end VARCHAR,
                    ally_mid_csDiffPerMinDeltas0_10 VARCHAR,
                    ally_mid_csDiffPerMinDeltas10_20 VARCHAR,
                    ally_mid_csDiffPerMinDeltas20_30 VARCHAR,
                    ally_mid_csDiffPerMinDeltas30_end VARCHAR,
                    ally_mid_xpDiffPerMinDeltas0_10 VARCHAR,
                    ally_mid_xpDiffPerMinDeltas10_20 VARCHAR,
                    ally_mid_xpDiffPerMinDeltas20_30 VARCHAR,
                    ally_mid_xpDiffPerMinDeltas30_end VARCHAR,
                    ally_mid_damageTakenPerMinDeltas0_10 VARCHAR,
                    ally_mid_damageTakenPerMinDeltas10_20 VARCHAR,
                    ally_mid_damageTakenPerMinDeltas20_30 VARCHAR,
                    ally_mid_damageTakenPerMinDeltas30_end VARCHAR,
                    ally_mid_damageTakenDiffPerMinDeltas0_10 VARCHAR,
                    ally_mid_damageTakenDiffPerMinDeltas10_20 VARCHAR,
                    ally_mid_damageTakenDiffPerMinDeltas20_30 VARCHAR,
                    ally_mid_damageTakenDiffPerMinDeltas30_end VARCHAR,
                        ally_adc_longestTimeSpentLiving VARCHAR,
                        ally_adc_totalDamageDealt VARCHAR,
                        ally_adc_magicDamageDealt VARCHAR,
                        ally_adc_physicalDamageDealt VARCHAR,
                        ally_adc_trueDamageDealt VARCHAR,
                        ally_adc_totalDamageDealtToChampions VARCHAR,
                        ally_adc_magicDamageDealtToChampions VARCHAR,
                        ally_adc_physicalDamageDealtToChampions VARCHAR,
                        ally_adc_trueDamageDealtToChampions VARCHAR,
                        ally_adc_totalHeal VARCHAR,
                        ally_adc_totalDamageTaken VARCHAR,
                        ally_adc_magicalDamageTaken VARCHAR,
                        ally_adc_physicalDamageTaken VARCHAR,
                        ally_adc_trueDamageTaken VARCHAR,
                        ally_adc_goldEarned VARCHAR,
                        ally_adc_totalMinionsKilled VARCHAR,
                        ally_adc_neutralMinionsKilled VARCHAR,
                        ally_adc_neutralMinionsKilledTeamJungle VARCHAR,
                        ally_adc_neutralMinionsKilledEnemyJungle VARCHAR,
                        ally_adc_totalTimeCrowdControlDealt VARCHAR,
                        ally_adc_wardsPlaced VARCHAR,
                        ally_adc_wardsKilled VARCHAR,
                    ally_adc_creepsPerMinDeltas0_10 VARCHAR,
                    ally_adc_creepsPerMinDeltas10_20 VARCHAR,
                    ally_adc_creepsPerMinDeltas20_30 VARCHAR,
                    ally_adc_creepsPerMinDeltas30_end VARCHAR,
                    ally_adc_xpPerMinDeltas0_10 VARCHAR,
                    ally_adc_xpPerMinDeltas10_20 VARCHAR,
                    ally_adc_xpPerMinDeltas20_30 VARCHAR,
                    ally_adc_xpPerMinDeltas30_end VARCHAR,
                    ally_adc_goldPerMinDeltas0_10 VARCHAR,
                    ally_adc_goldPerMinDeltas10_20 VARCHAR,
                    ally_adc_goldPerMinDeltas20_30 VARCHAR,
                    ally_adc_goldPerMinDeltas30_end VARCHAR,
                    ally_adc_csDiffPerMinDeltas0_10 VARCHAR,
                    ally_adc_csDiffPerMinDeltas10_20 VARCHAR,
                    ally_adc_csDiffPerMinDeltas20_30 VARCHAR,
                    ally_adc_csDiffPerMinDeltas30_end VARCHAR,
                    ally_adc_xpDiffPerMinDeltas0_10 VARCHAR,
                    ally_adc_xpDiffPerMinDeltas10_20 VARCHAR,
                    ally_adc_xpDiffPerMinDeltas20_30 VARCHAR,
                    ally_adc_xpDiffPerMinDeltas30_end VARCHAR,
                    ally_adc_damageTakenPerMinDeltas0_10 VARCHAR,
                    ally_adc_damageTakenPerMinDeltas10_20 VARCHAR,
                    ally_adc_damageTakenPerMinDeltas20_30 VARCHAR,
                    ally_adc_damageTakenPerMinDeltas30_end VARCHAR,
                    ally_adc_damageTakenDiffPerMinDeltas0_10 VARCHAR,
                    ally_adc_damageTakenDiffPerMinDeltas10_20 VARCHAR,
                    ally_adc_damageTakenDiffPerMinDeltas20_30 VARCHAR,
                    ally_adc_damageTakenDiffPerMinDeltas30_end VARCHAR,
                        ally_sup_longestTimeSpentLiving VARCHAR,
                        ally_sup_totalDamageDealt VARCHAR,
                        ally_sup_magicDamageDealt VARCHAR,
                        ally_sup_physicalDamageDealt VARCHAR,
                        ally_sup_trueDamageDealt VARCHAR,
                        ally_sup_totalDamageDealtToChampions VARCHAR,
                        ally_sup_magicDamageDealtToChampions VARCHAR,
                        ally_sup_physicalDamageDealtToChampions VARCHAR,
                        ally_sup_trueDamageDealtToChampions VARCHAR,
                        ally_sup_totalHeal VARCHAR,
                        ally_sup_totalDamageTaken VARCHAR,
                        ally_sup_magicalDamageTaken VARCHAR,
                        ally_sup_physicalDamageTaken VARCHAR,
                        ally_sup_trueDamageTaken VARCHAR,
                        ally_sup_goldEarned VARCHAR,
                        ally_sup_totalMinionsKilled VARCHAR,
                        ally_sup_neutralMinionsKilled VARCHAR,
                        ally_sup_neutralMinionsKilledTeamJungle VARCHAR,
                        ally_sup_neutralMinionsKilledEnemyJungle VARCHAR,
                        ally_sup_totalTimeCrowdControlDealt VARCHAR,
                        ally_sup_wardsPlaced VARCHAR,
                        ally_sup_wardsKilled VARCHAR,
                    ally_sup_creepsPerMinDeltas0_10 VARCHAR,
                    ally_sup_creepsPerMinDeltas10_20 VARCHAR,
                    ally_sup_creepsPerMinDeltas20_30 VARCHAR,
                    ally_sup_creepsPerMinDeltas30_end VARCHAR,
                    ally_sup_xpPerMinDeltas0_10 VARCHAR,
                    ally_sup_xpPerMinDeltas10_20 VARCHAR,
                    ally_sup_xpPerMinDeltas20_30 VARCHAR,
                    ally_sup_xpPerMinDeltas30_end VARCHAR,
                    ally_sup_goldPerMinDeltas0_10 VARCHAR,
                    ally_sup_goldPerMinDeltas10_20 VARCHAR,
                    ally_sup_goldPerMinDeltas20_30 VARCHAR,
                    ally_sup_goldPerMinDeltas30_end VARCHAR,
                    ally_sup_csDiffPerMinDeltas0_10 VARCHAR,
                    ally_sup_csDiffPerMinDeltas10_20 VARCHAR,
                    ally_sup_csDiffPerMinDeltas20_30 VARCHAR,
                    ally_sup_csDiffPerMinDeltas30_end VARCHAR,
                    ally_sup_xpDiffPerMinDeltas0_10 VARCHAR,
                    ally_sup_xpDiffPerMinDeltas10_20 VARCHAR,
                    ally_sup_xpDiffPerMinDeltas20_30 VARCHAR,
                    ally_sup_xpDiffPerMinDeltas30_end VARCHAR,
                    ally_sup_damageTakenPerMinDeltas0_10 VARCHAR,
                    ally_sup_damageTakenPerMinDeltas10_20 VARCHAR,
                    ally_sup_damageTakenPerMinDeltas20_30 VARCHAR,
                    ally_sup_damageTakenPerMinDeltas30_end VARCHAR,
                    ally_sup_damageTakenDiffPerMinDeltas0_10 VARCHAR,
                    ally_sup_damageTakenDiffPerMinDeltas10_20 VARCHAR,
                    ally_sup_damageTakenDiffPerMinDeltas20_30 VARCHAR,
                    ally_sup_damageTakenDiffPerMinDeltas30_end VARCHAR,
                        enemy_top_longestTimeSpentLiving VARCHAR,
                        enemy_top_totalDamageDealt VARCHAR,
                        enemy_top_magicDamageDealt VARCHAR,
                        enemy_top_physicalDamageDealt VARCHAR,
                        enemy_top_trueDamageDealt VARCHAR,
                        enemy_top_totalDamageDealtToChampions VARCHAR,
                        enemy_top_magicDamageDealtToChampions VARCHAR,
                        enemy_top_physicalDamageDealtToChampions VARCHAR,
                        enemy_top_trueDamageDealtToChampions VARCHAR,
                        enemy_top_totalHeal VARCHAR,
                        enemy_top_totalDamageTaken VARCHAR,
                        enemy_top_magicalDamageTaken VARCHAR,
                        enemy_top_physicalDamageTaken VARCHAR,
                        enemy_top_trueDamageTaken VARCHAR,
                        enemy_top_goldEarned VARCHAR,
                        enemy_top_totalMinionsKilled VARCHAR,
                        enemy_top_neutralMinionsKilled VARCHAR,
                        enemy_top_neutralMinionsKilledTeamJungle VARCHAR,
                        enemy_top_neutralMinionsKilledEnemyJungle VARCHAR,
                        enemy_top_totalTimeCrowdControlDealt VARCHAR,
                        enemy_top_wardsPlaced VARCHAR,
                        enemy_top_wardsKilled VARCHAR,
                    enemy_top_creepsPerMinDeltas0_10 VARCHAR,
                    enemy_top_creepsPerMinDeltas10_20 VARCHAR,
                    enemy_top_creepsPerMinDeltas20_30 VARCHAR,
                    enemy_top_creepsPerMinDeltas30_end VARCHAR,
                    enemy_top_xpPerMinDeltas0_10 VARCHAR,
                    enemy_top_xpPerMinDeltas10_20 VARCHAR,
                    enemy_top_xpPerMinDeltas20_30 VARCHAR,
                    enemy_top_xpPerMinDeltas30_end VARCHAR,
                    enemy_top_goldPerMinDeltas0_10 VARCHAR,
                    enemy_top_goldPerMinDeltas10_20 VARCHAR,
                    enemy_top_goldPerMinDeltas20_30 VARCHAR,
                    enemy_top_goldPerMinDeltas30_end VARCHAR,
                    enemy_top_csDiffPerMinDeltas0_10 VARCHAR,
                    enemy_top_csDiffPerMinDeltas10_20 VARCHAR,
                    enemy_top_csDiffPerMinDeltas20_30 VARCHAR,
                    enemy_top_csDiffPerMinDeltas30_end VARCHAR,
                    enemy_top_xpDiffPerMinDeltas0_10 VARCHAR,
                    enemy_top_xpDiffPerMinDeltas10_20 VARCHAR,
                    enemy_top_xpDiffPerMinDeltas20_30 VARCHAR,
                    enemy_top_xpDiffPerMinDeltas30_end VARCHAR,
                    enemy_top_damageTakenPerMinDeltas0_10 VARCHAR,
                    enemy_top_damageTakenPerMinDeltas10_20 VARCHAR,
                    enemy_top_damageTakenPerMinDeltas20_30 VARCHAR,
                    enemy_top_damageTakenPerMinDeltas30_end VARCHAR,
                    enemy_top_damageTakenDiffPerMinDeltas0_10 VARCHAR,
                    enemy_top_damageTakenDiffPerMinDeltas10_20 VARCHAR,
                    enemy_top_damageTakenDiffPerMinDeltas20_30 VARCHAR,
                    enemy_top_damageTakenDiffPerMinDeltas30_end VARCHAR,
                        enemy_jng_longestTimeSpentLiving VARCHAR,
                        enemy_jng_totalDamageDealt VARCHAR,
                        enemy_jng_magicDamageDealt VARCHAR,
                        enemy_jng_physicalDamageDealt VARCHAR,
                        enemy_jng_trueDamageDealt VARCHAR,
                        enemy_jng_totalDamageDealtToChampions VARCHAR,
                        enemy_jng_magicDamageDealtToChampions VARCHAR,
                        enemy_jng_physicalDamageDealtToChampions VARCHAR,
                        enemy_jng_trueDamageDealtToChampions VARCHAR,
                        enemy_jng_totalHeal VARCHAR,
                        enemy_jng_totalDamageTaken VARCHAR,
                        enemy_jng_magicalDamageTaken VARCHAR,
                        enemy_jng_physicalDamageTaken VARCHAR,
                        enemy_jng_trueDamageTaken VARCHAR,
                        enemy_jng_goldEarned VARCHAR,
                        enemy_jng_totalMinionsKilled VARCHAR,
                        enemy_jng_neutralMinionsKilled VARCHAR,
                        enemy_jng_neutralMinionsKilledTeamJungle VARCHAR,
                        enemy_jng_neutralMinionsKilledEnemyJungle VARCHAR,
                        enemy_jng_totalTimeCrowdControlDealt VARCHAR,
                        enemy_jng_wardsPlaced VARCHAR,
                        enemy_jng_wardsKilled VARCHAR,
                    enemy_jng_creepsPerMinDeltas0_10 VARCHAR,
                    enemy_jng_creepsPerMinDeltas10_20 VARCHAR,
                    enemy_jng_creepsPerMinDeltas20_30 VARCHAR,
                    enemy_jng_creepsPerMinDeltas30_end VARCHAR,
                    enemy_jng_xpPerMinDeltas0_10 VARCHAR,
                    enemy_jng_xpPerMinDeltas10_20 VARCHAR,
                    enemy_jng_xpPerMinDeltas20_30 VARCHAR,
                    enemy_jng_xpPerMinDeltas30_end VARCHAR,
                    enemy_jng_goldPerMinDeltas0_10 VARCHAR,
                    enemy_jng_goldPerMinDeltas10_20 VARCHAR,
                    enemy_jng_goldPerMinDeltas20_30 VARCHAR,
                    enemy_jng_goldPerMinDeltas30_end VARCHAR,
                    enemy_jng_csDiffPerMinDeltas0_10 VARCHAR,
                    enemy_jng_csDiffPerMinDeltas10_20 VARCHAR,
                    enemy_jng_csDiffPerMinDeltas20_30 VARCHAR,
                    enemy_jng_csDiffPerMinDeltas30_end VARCHAR,
                    enemy_jng_xpDiffPerMinDeltas0_10 VARCHAR,
                    enemy_jng_xpDiffPerMinDeltas10_20 VARCHAR,
                    enemy_jng_xpDiffPerMinDeltas20_30 VARCHAR,
                    enemy_jng_xpDiffPerMinDeltas30_end VARCHAR,
                    enemy_jng_damageTakenPerMinDeltas0_10 VARCHAR,
                    enemy_jng_damageTakenPerMinDeltas10_20 VARCHAR,
                    enemy_jng_damageTakenPerMinDeltas20_30 VARCHAR,
                    enemy_jng_damageTakenPerMinDeltas30_end VARCHAR,
                    enemy_jng_damageTakenDiffPerMinDeltas0_10 VARCHAR,
                    enemy_jng_damageTakenDiffPerMinDeltas10_20 VARCHAR,
                    enemy_jng_damageTakenDiffPerMinDeltas20_30 VARCHAR,
                    enemy_jng_damageTakenDiffPerMinDeltas30_end VARCHAR,
                        enemy_mid_longestTimeSpentLiving VARCHAR,
                        enemy_mid_totalDamageDealt VARCHAR,
                        enemy_mid_magicDamageDealt VARCHAR,
                        enemy_mid_physicalDamageDealt VARCHAR,
                        enemy_mid_trueDamageDealt VARCHAR,
                        enemy_mid_totalDamageDealtToChampions VARCHAR,
                        enemy_mid_magicDamageDealtToChampions VARCHAR,
                        enemy_mid_physicalDamageDealtToChampions VARCHAR,
                        enemy_mid_trueDamageDealtToChampions VARCHAR,
                        enemy_mid_totalHeal VARCHAR,
                        enemy_mid_totalDamageTaken VARCHAR,
                        enemy_mid_magicalDamageTaken VARCHAR,
                        enemy_mid_physicalDamageTaken VARCHAR,
                        enemy_mid_trueDamageTaken VARCHAR,
                        enemy_mid_goldEarned VARCHAR,
                        enemy_mid_totalMinionsKilled VARCHAR,
                        enemy_mid_neutralMinionsKilled VARCHAR,
                        enemy_mid_neutralMinionsKilledTeamJungle VARCHAR,
                        enemy_mid_neutralMinionsKilledEnemyJungle VARCHAR,
                        enemy_mid_totalTimeCrowdControlDealt VARCHAR,
                        enemy_mid_wardsPlaced VARCHAR,
                        enemy_mid_wardsKilled VARCHAR,
                    enemy_mid_creepsPerMinDeltas0_10 VARCHAR,
                    enemy_mid_creepsPerMinDeltas10_20 VARCHAR,
                    enemy_mid_creepsPerMinDeltas20_30 VARCHAR,
                    enemy_mid_creepsPerMinDeltas30_end VARCHAR,
                    enemy_mid_xpPerMinDeltas0_10 VARCHAR,
                    enemy_mid_xpPerMinDeltas10_20 VARCHAR,
                    enemy_mid_xpPerMinDeltas20_30 VARCHAR,
                    enemy_mid_xpPerMinDeltas30_end VARCHAR,
                    enemy_mid_goldPerMinDeltas0_10 VARCHAR,
                    enemy_mid_goldPerMinDeltas10_20 VARCHAR,
                    enemy_mid_goldPerMinDeltas20_30 VARCHAR,
                    enemy_mid_goldPerMinDeltas30_end VARCHAR,
                    enemy_mid_csDiffPerMinDeltas0_10 VARCHAR,
                    enemy_mid_csDiffPerMinDeltas10_20 VARCHAR,
                    enemy_mid_csDiffPerMinDeltas20_30 VARCHAR,
                    enemy_mid_csDiffPerMinDeltas30_end VARCHAR,
                    enemy_mid_xpDiffPerMinDeltas0_10 VARCHAR,
                    enemy_mid_xpDiffPerMinDeltas10_20 VARCHAR,
                    enemy_mid_xpDiffPerMinDeltas20_30 VARCHAR,
                    enemy_mid_xpDiffPerMinDeltas30_end VARCHAR,
                    enemy_mid_damageTakenPerMinDeltas0_10 VARCHAR,
                    enemy_mid_damageTakenPerMinDeltas10_20 VARCHAR,
                    enemy_mid_damageTakenPerMinDeltas20_30 VARCHAR,
                    enemy_mid_damageTakenPerMinDeltas30_end VARCHAR,
                    enemy_mid_damageTakenDiffPerMinDeltas0_10 VARCHAR,
                    enemy_mid_damageTakenDiffPerMinDeltas10_20 VARCHAR,
                    enemy_mid_damageTakenDiffPerMinDeltas20_30 VARCHAR,
                    enemy_mid_damageTakenDiffPerMinDeltas30_end VARCHAR,
                        enemy_adc_longestTimeSpentLiving VARCHAR,
                        enemy_adc_totalDamageDealt VARCHAR,
                        enemy_adc_magicDamageDealt VARCHAR,
                        enemy_adc_physicalDamageDealt VARCHAR,
                        enemy_adc_trueDamageDealt VARCHAR,
                        enemy_adc_totalDamageDealtToChampions VARCHAR,
                        enemy_adc_magicDamageDealtToChampions VARCHAR,
                        enemy_adc_physicalDamageDealtToChampions VARCHAR,
                        enemy_adc_trueDamageDealtToChampions VARCHAR,
                        enemy_adc_totalHeal VARCHAR,
                        enemy_adc_totalDamageTaken VARCHAR,
                        enemy_adc_magicalDamageTaken VARCHAR,
                        enemy_adc_physicalDamageTaken VARCHAR,
                        enemy_adc_trueDamageTaken VARCHAR,
                        enemy_adc_goldEarned VARCHAR,
                        enemy_adc_totalMinionsKilled VARCHAR,
                        enemy_adc_neutralMinionsKilled VARCHAR,
                        enemy_adc_neutralMinionsKilledTeamJungle VARCHAR,
                        enemy_adc_neutralMinionsKilledEnemyJungle VARCHAR,
                        enemy_adc_totalTimeCrowdControlDealt VARCHAR,
                        enemy_adc_wardsPlaced VARCHAR,
                        enemy_adc_wardsKilled VARCHAR,
                    enemy_adc_creepsPerMinDeltas0_10 VARCHAR,
                    enemy_adc_creepsPerMinDeltas10_20 VARCHAR,
                    enemy_adc_creepsPerMinDeltas20_30 VARCHAR,
                    enemy_adc_creepsPerMinDeltas30_end VARCHAR,
                    enemy_adc_xpPerMinDeltas0_10 VARCHAR,
                    enemy_adc_xpPerMinDeltas10_20 VARCHAR,
                    enemy_adc_xpPerMinDeltas20_30 VARCHAR,
                    enemy_adc_xpPerMinDeltas30_end VARCHAR,
                    enemy_adc_goldPerMinDeltas0_10 VARCHAR,
                    enemy_adc_goldPerMinDeltas10_20 VARCHAR,
                    enemy_adc_goldPerMinDeltas20_30 VARCHAR,
                    enemy_adc_goldPerMinDeltas30_end VARCHAR,
                    enemy_adc_csDiffPerMinDeltas0_10 VARCHAR,
                    enemy_adc_csDiffPerMinDeltas10_20 VARCHAR,
                    enemy_adc_csDiffPerMinDeltas20_30 VARCHAR,
                    enemy_adc_csDiffPerMinDeltas30_end VARCHAR,
                    enemy_adc_xpDiffPerMinDeltas0_10 VARCHAR,
                    enemy_adc_xpDiffPerMinDeltas10_20 VARCHAR,
                    enemy_adc_xpDiffPerMinDeltas20_30 VARCHAR,
                    enemy_adc_xpDiffPerMinDeltas30_end VARCHAR,
                    enemy_adc_damageTakenPerMinDeltas0_10 VARCHAR,
                    enemy_adc_damageTakenPerMinDeltas10_20 VARCHAR,
                    enemy_adc_damageTakenPerMinDeltas20_30 VARCHAR,
                    enemy_adc_damageTakenPerMinDeltas30_end VARCHAR,
                    enemy_adc_damageTakenDiffPerMinDeltas0_10 VARCHAR,
                    enemy_adc_damageTakenDiffPerMinDeltas10_20 VARCHAR,
                    enemy_adc_damageTakenDiffPerMinDeltas20_30 VARCHAR,
                    enemy_adc_damageTakenDiffPerMinDeltas30_end VARCHAR,
                        enemy_sup_longestTimeSpentLiving VARCHAR,
                        enemy_sup_totalDamageDealt VARCHAR,
                        enemy_sup_magicDamageDealt VARCHAR,
                        enemy_sup_physicalDamageDealt VARCHAR,
                        enemy_sup_trueDamageDealt VARCHAR,
                        enemy_sup_totalDamageDealtToChampions VARCHAR,
                        enemy_sup_magicDamageDealtToChampions VARCHAR,
                        enemy_sup_physicalDamageDealtToChampions VARCHAR,
                        enemy_sup_trueDamageDealtToChampions VARCHAR,
                        enemy_sup_totalHeal VARCHAR,
                        enemy_sup_totalDamageTaken VARCHAR,
                        enemy_sup_magicalDamageTaken VARCHAR,
                        enemy_sup_physicalDamageTaken VARCHAR,
                        enemy_sup_trueDamageTaken VARCHAR,
                        enemy_sup_goldEarned VARCHAR,
                        enemy_sup_totalMinionsKilled VARCHAR,
                        enemy_sup_neutralMinionsKilled VARCHAR,
                        enemy_sup_neutralMinionsKilledTeamJungle VARCHAR,
                        enemy_sup_neutralMinionsKilledEnemyJungle VARCHAR,
                        enemy_sup_totalTimeCrowdControlDealt VARCHAR,
                        enemy_sup_wardsPlaced VARCHAR,
                        enemy_sup_wardsKilled VARCHAR,
                    enemy_sup_creepsPerMinDeltas0_10 VARCHAR,
                    enemy_sup_creepsPerMinDeltas10_20 VARCHAR,
                    enemy_sup_creepsPerMinDeltas20_30 VARCHAR,
                    enemy_sup_creepsPerMinDeltas30_end VARCHAR,
                    enemy_sup_xpPerMinDeltas0_10 VARCHAR,
                    enemy_sup_xpPerMinDeltas10_20 VARCHAR,
                    enemy_sup_xpPerMinDeltas20_30 VARCHAR,
                    enemy_sup_xpPerMinDeltas30_end VARCHAR,
                    enemy_sup_goldPerMinDeltas0_10 VARCHAR,
                    enemy_sup_goldPerMinDeltas10_20 VARCHAR,
                    enemy_sup_goldPerMinDeltas20_30 VARCHAR,
                    enemy_sup_goldPerMinDeltas30_end VARCHAR,
                    enemy_sup_csDiffPerMinDeltas0_10 VARCHAR,
                    enemy_sup_csDiffPerMinDeltas10_20 VARCHAR,
                    enemy_sup_csDiffPerMinDeltas20_30 VARCHAR,
                    enemy_sup_csDiffPerMinDeltas30_end VARCHAR,
                    enemy_sup_xpDiffPerMinDeltas0_10 VARCHAR,
                    enemy_sup_xpDiffPerMinDeltas10_20 VARCHAR,
                    enemy_sup_xpDiffPerMinDeltas20_30 VARCHAR,
                    enemy_sup_xpDiffPerMinDeltas30_end VARCHAR,
                    enemy_sup_damageTakenPerMinDeltas0_10 VARCHAR,
                    enemy_sup_damageTakenPerMinDeltas10_20 VARCHAR,
                    enemy_sup_damageTakenPerMinDeltas20_30 VARCHAR,
                    enemy_sup_damageTakenPerMinDeltas30_end VARCHAR,
                    enemy_sup_damageTakenDiffPerMinDeltas0_10 VARCHAR,
                    enemy_sup_damageTakenDiffPerMinDeltas10_20 VARCHAR,
                    enemy_sup_damageTakenDiffPerMinDeltas20_30 VARCHAR,
                    enemy_sup_damageTakenDiffPerMinDeltas30_end VARCHAR)""")
            connect.commit()
            print('\nСоздание таблицы (matches_info_parsed)')
            cursor.execute('SELECT  (site_id) FROM matches_info_json')
            ids = ([int(str(elem).replace(",", "").replace(")", "").replace("(", "")) for elem in cursor.fetchall()])
        except sqlite3.OperationalError:
            print('\nТаблица существует (matches_info_parsed)')
            cursor.execute('SELECT  (site_id) FROM matches_info_json')
            ids = ([int(str(elem).replace(",", "").replace(")", "").replace("(", "")) for elem in cursor.fetchall()])
            cursor.execute('SELECT  MAX(site_id) FROM matches_info_parsed')
            old_ids = range(1, cursor.fetchall()[0][0] + 1)
            for old_id in old_ids:
                try:
                    ids.remove(old_id)
                except ValueError:
                    list()
        for k in ids:
            both_teams = list()
            both_teams.append(k)  # site_id
            cursor.execute("SELECT match_info_html FROM matches_info_html WHERE site_id=?", (k,))
            match_info_soup = bs4.BeautifulSoup(cursor.fetchall()[0][0], 'html.parser')
            cursor.execute("SELECT match_history FROM matches_info_json WHERE site_id=?", (k,))
            match_history_json = pickle.loads(cursor.fetchall()[0][0])

            cursor.execute("SELECT match_timeline FROM matches_info_json WHERE site_id=?", (k,))
            match_timeline_json = pickle.loads(cursor.fetchall()[0][0])

            if (
                    match_history_json != "Null" and match_timeline_json != "Null" and k != 15524 and k != 16017 and k != 16034) or \
                    match_info_soup.find_all('div', class_='col-xs-7')[0].text.split()[-1][1:-1] == 'CN':
                # print(k)
                if len(match_info_soup.find_all('table')) > 1:
                    both_teams.append(
                        match_info_soup.find_all('div', class_='col-xs-7 text-left')[0].find('a').text)  # championship
                    both_teams.append(match_info_soup.find_all('div', class_='col-xs-7 text-left')[0].text.split()[-1][
                                      1:-1])  # server
                    both_teams.append(
                        match_info_soup.find_all('div', class_='col-xs-5 text-right')[0].text.split()[0])  # date
                    both_teams.append(float(
                        match_info_soup.find_all('table')[1].find('tr').find_all('td')[2].text.strip()[
                        1:]))  # version game
                    both_teams.append(
                        match_info_soup.find_all('table')[1].find('tr').find_all('td')[1].find('span').text)  # time
                    if match_info_soup.find_all('div', class_='col-xs-7')[0].text.split()[-1][1:-1] != 'CN' and \
                            match_info_soup.find_all('table')[1].find('tr').find_all('td')[1].find(
                                    'span').text != '0:00' and \
                            len(match_info_soup.find_all('table')) > 6:
                        # print(both_teams)
                        teams = {'blue': list(), 'red': list()}
                        for team in teams:
                            teams[team].append(match_info_soup.find_all('table')[1].find_all('tr')[1].find('td',
                                                                                                           class_=team + "_line").text.strip())  # name
                            teams[team].append(
                                "true" if re.findall('<.*?>', str(
                                    match_info_soup.find_all('table')[1].find('tr').find_all('td')[1]))[1][
                                          1:4] == "img" and team == 'blue'
                                else "true" if
                                re.findall('<.*?>',
                                           str(match_info_soup.find_all('table')[1].find('tr').find_all('td')[1]))[1][
                                1:4] != "img" and team == 'red' else "false")
                            teams[team].append(team)
                            teams[team].append(match_info_soup.find_all('table')[1].find_all('tr')[1].find_all('td')[
                                                   1 if team == 'blue' else 0].text.strip())
                            [teams[team].append(
                                'true' if match_info_soup.find_all('table')[1].find_all('tr')[2].find('td',
                                                                                                      class_=team + "_line").find(
                                    'img', alt='First ' + objective) is not None else 'false') for objective in
                                ['Blood', 'Tower']]  # fb ft

                            teams[team].append(re.sub('[\[\]\'\,]', '', str(
                                [re.findall('champions_icon\/([A-Za-z]{1,30})', str(col)) for col in
                                 match_info_soup.find_all('table')[2].find_all('tr')[1].find_all('td',
                                                                                                 class_=team + "_line")])[
                                                                        1:-1]))  # bans

                        for team in teams:
                            if team == 'blue':
                                alies = range(1, 6)
                            else:
                                alies = range(6, 11)
                            nicknames = list()
                            try:
                                for elem in match_history_json['participantIdentities']:
                                    if elem['participantId'] in alies:
                                        if len(re.findall('.*? (.*)', elem['player']['summonerName'])) == 1:
                                            nicknames.append(re.findall('.*? (.*)', elem['player']['summonerName'])[0])
                                        else:
                                            raise Exception('Ошибка Проблема с ником')
                            except KeyError:

                                nicknames = [match_info_soup.find_all('table')[3].find('td',
                                                                                       class_=team + '_player_bar').find_all(
                                    'a', class_='black_link')]  # nicks

                                nicknames = [nickname.text for nickname in nicknames[0]]
                            # print(nicknames)
                            [teams[team].append(elem) for elem in nicknames]
                            champions = list()
                            cursor.execute("SELECT champions FROM champions_info")
                            champions_info = pickle.loads(cursor.fetchall()[0][0])
                            for elem in match_history_json['participants']:
                                if elem['participantId'] in alies:
                                    try:
                                        champions.append(champions_info[str(elem['championId'])])
                                    except KeyError:
                                        if elem['championId'] == 555: champions.append('Pyke')
                                        if elem['championId'] == 518: champions.append('Neeko')
                            [teams[team].append(elem) for elem in champions]
                        # minions get
                        for team in teams:
                            if team == 'blue':
                                alies = range(1, 6)
                                enemies = range(6, 11)
                            else:
                                alies = range(6, 11)
                                enemies = range(1, 6)
                            # minions ally
                            for elem in alies:
                                elems = list()
                                for j in range(0, len(match_timeline_json['frames'])):
                                    elems.append(int(match_timeline_json['frames'][j]['participantFrames'][str(elem)][
                                                         'minionsKilled']))
                                teams[team].append(pickle.dumps(elems))
                            # minions enemy
                            for elem in enemies:
                                elems = list()
                                for j in range(0, len(match_timeline_json['frames'])):
                                    elems.append(int(match_timeline_json['frames'][j]['participantFrames'][str(elem)][
                                                         'minionsKilled']))
                                teams[team].append(pickle.dumps(elems))
                            # jungle minions ally
                            for elem in alies:
                                elems = list()
                                for j in range(0, len(match_timeline_json['frames'])):
                                    elems.append(int(match_timeline_json['frames'][j]['participantFrames'][str(elem)][
                                                         'jungleMinionsKilled']))
                                teams[team].append(pickle.dumps(elems))
                            # jungle minions enemy
                            for elem in enemies:
                                elems = list()
                                for j in range(0, len(match_timeline_json['frames'])):
                                    elems.append(int(match_timeline_json['frames'][j]['participantFrames'][str(elem)][
                                                         'jungleMinionsKilled']))
                                teams[team].append(pickle.dumps(elems))
                            # gold ally
                            for elem in alies:
                                elems = list()
                                for j in range(0, len(match_timeline_json['frames'])):
                                    elems.append(int(
                                        match_timeline_json['frames'][j]['participantFrames'][str(elem)]['totalGold']))
                                teams[team].append(pickle.dumps(elems))
                            # gold enemy
                            for elem in enemies:
                                elems = list()
                                for j in range(0, len(match_timeline_json['frames'])):
                                    elems.append(int(
                                        match_timeline_json['frames'][j]['participantFrames'][str(elem)]['totalGold']))
                                teams[team].append(pickle.dumps(elems))
                            # xp ally
                            for elem in alies:
                                elems = list()
                                for j in range(0, len(match_timeline_json['frames'])):
                                    elems.append(
                                        int(match_timeline_json['frames'][j]['participantFrames'][str(elem)]['xp']))
                                teams[team].append(pickle.dumps(elems))
                            # xp enemy
                            for elem in enemies:
                                elems = list()
                                for j in range(0, len(match_timeline_json['frames'])):
                                    elems.append(
                                        int(match_timeline_json['frames'][j]['participantFrames'][str(elem)]['xp']))
                                teams[team].append(pickle.dumps(elems))
                            # lvl ally
                            for elem in alies:
                                elems = list()
                                for j in range(0, len(match_timeline_json['frames'])):
                                    elems.append(
                                        int(match_timeline_json['frames'][j]['participantFrames'][str(elem)]['level']))
                                teams[team].append(pickle.dumps(elems))
                            # lvl enemy
                            for elem in enemies:
                                elems = list()
                                for j in range(0, len(match_timeline_json['frames'])):
                                    elems.append(
                                        int(match_timeline_json['frames'][j]['participantFrames'][str(elem)]['level']))
                                teams[team].append(pickle.dumps(elems))

                        elems = list()
                        for j in range(0, len(match_timeline_json['frames'])):
                            # тут только турели и ингибиторы
                            [elems.append(elem) if elem['type'] == 'BUILDING_KILL' else None for elem in
                             match_timeline_json['frames'][j]['events']]
                        for team in teams:
                            team_id = 200 if team == 'blue' else 100
                            # towers get
                            lines = ['TOP_LANE', 'MID_LANE', 'BOT_LANE']
                            for line in lines:
                                times = list()
                                for elem in elems:
                                    if int(elem['teamId']) == int(team_id):
                                        if elem['towerType'] != 'NEXUS_TURRET':
                                            if elem['towerType'] != 'UNDEFINED_TURRET':
                                                if elem['laneType'] == line:
                                                    times.append(int(elem['timestamp']) / 60000)
                                teams[team].append(pickle.dumps(times))
                            times = list()
                            for elem in elems:
                                if int(elem['teamId']) == int(team_id) and elem['towerType'] == 'NEXUS_TURRET':
                                    times.append(int(elem['timestamp']) / 60000)
                            teams[team].append(pickle.dumps(times))
                            # towers lost
                            for line in lines:
                                times = list()
                                for elem in elems:
                                    if int(elem['teamId']) != int(team_id):
                                        if elem['towerType'] != 'NEXUS_TURRET':
                                            if elem['towerType'] != 'UNDEFINED_TURRET':
                                                if elem['laneType'] == line:
                                                    times.append(int(elem['timestamp']) / 60000)
                                teams[team].append(pickle.dumps(times))
                            times = list()
                            for elem in elems:
                                if int(elem['teamId']) != int(team_id) and elem['towerType'] == 'NEXUS_TURRET':
                                    times.append(int(elem['timestamp']) / 60000)
                            teams[team].append(pickle.dumps(times))
                            # inhib get
                            lines = ['TOP_LANE', 'MID_LANE', 'BOT_LANE']
                            for line in lines:
                                times = list()
                                for elem in elems:
                                    if int(elem['teamId']) == int(team_id):
                                        if elem['towerType'] == 'UNDEFINED_TURRET':
                                            if elem['laneType'] == line:
                                                times.append(int(elem['timestamp']) / 60000)
                                teams[team].append(pickle.dumps(times))
                            times = list()
                            # inhib lost
                            lines = ['TOP_LANE', 'MID_LANE', 'BOT_LANE']
                            for line in lines:
                                times = list()
                                for elem in elems:
                                    if int(elem['teamId']) != int(team_id):
                                        if elem['towerType'] == 'UNDEFINED_TURRET':
                                            if elem['laneType'] == line:
                                                times.append(int(elem['timestamp']) / 60000)
                                teams[team].append(pickle.dumps(times))
                        monsters = list()
                        for j in range(0, len(match_timeline_json['frames'])):
                            # тут только эпик монстры
                            [monsters.append(elem) if elem['type'] == 'ELITE_MONSTER_KILL' else None for elem in
                             match_timeline_json['frames'][j]['events']]
                        for team in teams:
                            if team == 'blue':
                                alies = range(1, 6)
                                enemies = range(6, 11)
                            else:
                                alies = range(6, 11)
                                enemies = range(1, 6)
                            # dragons ally
                            elems = list()
                            for monster in monsters:
                                if str(monster['monsterType']) == 'DRAGON':
                                    if int(monster['killerId']) in alies:
                                        elems.append(int(monster['timestamp']) / 60000)
                            teams[team].append(pickle.dumps(elems))
                            # dragons enemy
                            elems = list()
                            for monster in monsters:
                                if str(monster['monsterType']) == 'DRAGON':
                                    if int(monster['killerId']) in enemies:
                                        elems.append(int(monster['timestamp']) / 60000)
                            teams[team].append(pickle.dumps(elems))
                            # barons ally
                            elems = list()
                            for monster in monsters:
                                if str(monster['monsterType']) == 'BARON_NASHOR':
                                    if int(monster['killerId']) in alies:
                                        elems.append(int(monster['timestamp']) / 60000)
                            teams[team].append(pickle.dumps(elems))
                            # barons enemy
                            elems = list()
                            for monster in monsters:
                                if str(monster['monsterType']) == 'BARON_NASHOR':
                                    if int(monster['killerId']) in enemies:
                                        elems.append(int(monster['timestamp']) / 60000)
                            teams[team].append(pickle.dumps(elems))
                            # herald ally
                            elems = list()
                            for monster in monsters:
                                if str(monster['monsterType']) == 'RIFTHERALD':
                                    if int(monster['killerId']) in alies:
                                        elems.append(int(monster['timestamp']) / 60000)
                            teams[team].append(pickle.dumps(elems))
                            # herald enemy
                            elems = list()
                            for monster in monsters:
                                if str(monster['monsterType']) == 'RIFTHERALD':
                                    if int(monster['killerId']) in enemies:
                                        elems.append(int(monster['timestamp']) / 60000)
                            teams[team].append(pickle.dumps(elems))
                        kills_info = list()
                        for j in range(0, len(match_timeline_json['frames'])):
                            # тут киллы, ассисты
                            [kills_info.append(elem) if elem['type'] == 'CHAMPION_KILL' else None for elem in
                             match_timeline_json['frames'][j]['events']]
                        for team in teams:
                            if team == 'blue':
                                alies = range(1, 6)
                                enemies = range(6, 11)
                            else:
                                alies = range(6, 11)
                                enemies = range(1, 6)
                            # кда союззников
                            for player in alies:
                                kills = list()
                                deaths = list()
                                assists = list()
                                for kill_info in kills_info:
                                    if int(player) == int(kill_info['killerId']):
                                        kills.append(int(kill_info['timestamp']) / 60000)
                                    if int(player) == int(kill_info['victimId']):
                                        deaths.append(int(kill_info['timestamp']) / 60000)
                                    if int(player) in kill_info['assistingParticipantIds']:
                                        assists.append(int(kill_info['timestamp']) / 60000)

                                teams[team].append(pickle.dumps(kills))
                                teams[team].append(pickle.dumps(deaths))
                                teams[team].append(pickle.dumps(assists))
                            # кда врагов
                            for player in enemies:
                                kills = list()
                                deaths = list()
                                assists = list()
                                for kill_info in kills_info:
                                    if int(player) == int(kill_info['killerId']):
                                        kills.append(int(kill_info['timestamp']) / 60000)
                                    if int(player) == int(kill_info['victimId']):
                                        deaths.append(int(kill_info['timestamp']) / 60000)
                                    if int(player) in kill_info['assistingParticipantIds']:
                                        assists.append(int(kill_info['timestamp']) / 60000)

                                teams[team].append(pickle.dumps(kills))
                                teams[team].append(pickle.dumps(deaths))
                                teams[team].append(pickle.dumps(assists))
                        wards = list()
                        for j in range(0, len(match_timeline_json['frames'])):
                            # тут только варды
                            [wards.append(elem) if elem['type'] == 'WARD_PLACED' else None for elem in
                             match_timeline_json['frames'][j]['events']]
                        for team in teams:
                            simple_wards_ally = list()
                            vision_wards_ally = list()
                            simple_wards_enemy = list()
                            vision_wards_enemy = list()
                            if team == 'blue':
                                alies = range(1, 6)
                                enemies = range(6, 11)
                            else:
                                alies = range(6, 11)
                                enemies = range(1, 6)
                            for ward in wards:
                                if int(ward['creatorId']) in alies:
                                    if str(ward['wardType']) == 'CONTROL_WARD':
                                        vision_wards_ally.append(ward['timestamp'])
                                    else:
                                        simple_wards_ally.append(ward['timestamp'])
                                if int(ward['creatorId']) in enemies:
                                    if str(ward['wardType']) == 'CONTROL_WARD':
                                        simple_wards_enemy.append(ward['timestamp'])
                                    else:
                                        vision_wards_enemy.append(ward['timestamp'])
                            teams[team].append(pickle.dumps(simple_wards_ally))
                            teams[team].append(pickle.dumps(vision_wards_ally))
                            teams[team].append(pickle.dumps(simple_wards_enemy))
                            teams[team].append(pickle.dumps(vision_wards_enemy))
                        ward_kills = list()
                        for j in range(0, len(match_timeline_json['frames'])):
                            # тут только вард киллы
                            [ward_kills.append(elem) if elem['type'] == 'WARD_KILL' else None for elem in
                             match_timeline_json['frames'][j]['events']]
                        for team in teams:
                            kill_simple_wards_ally = list()
                            kill_vision_wards_ally = list()
                            kill_simple_wards_enemy = list()
                            kill_vision_wards_enemy = list()
                            if team == 'blue':
                                alies = range(1, 6)
                                enemies = range(6, 11)
                            else:
                                alies = range(6, 11)
                                enemies = range(1, 6)
                            for ward in ward_kills:
                                if int(ward['killerId']) in alies:
                                    if str(ward['wardType']) == 'CONTROL_WARD':
                                        kill_vision_wards_ally.append(ward['timestamp'])
                                    else:
                                        kill_simple_wards_ally.append(ward['timestamp'])
                                if int(ward['killerId']) in enemies:
                                    if str(ward['wardType']) == 'CONTROL_WARD':
                                        kill_simple_wards_enemy.append(ward['timestamp'])
                                    else:
                                        kill_vision_wards_enemy.append(ward['timestamp'])
                            teams[team].append(pickle.dumps(kill_simple_wards_ally))
                            teams[team].append(pickle.dumps(kill_vision_wards_ally))
                            teams[team].append(pickle.dumps(kill_simple_wards_enemy))
                            teams[team].append(pickle.dumps(kill_vision_wards_enemy))
                        for team in teams:
                            if team == 'blue':
                                alies = range(1, 6)
                                enemies = range(6, 11)
                            else:
                                alies = range(6, 11)
                                enemies = range(1, 6)
                            for player in match_history_json['participants']:
                                if player['participantId'] in alies:
                                    teams[team].append(int(player['stats']['longestTimeSpentLiving']) / 60)
                                    teams[team].append(player['stats']['totalDamageDealt'])
                                    teams[team].append(player['stats']['magicDamageDealt'])
                                    teams[team].append(player['stats']['physicalDamageDealt'])
                                    teams[team].append(player['stats']['trueDamageDealt'])
                                    teams[team].append(player['stats']['totalDamageDealtToChampions'])
                                    teams[team].append(player['stats']['magicDamageDealtToChampions'])
                                    teams[team].append(player['stats']['physicalDamageDealtToChampions'])
                                    teams[team].append(player['stats']['trueDamageDealtToChampions'])
                                    teams[team].append(player['stats']['totalHeal'])
                                    teams[team].append(player['stats']['totalDamageTaken'])
                                    teams[team].append(player['stats']['magicalDamageTaken'])
                                    teams[team].append(player['stats']['physicalDamageTaken'])
                                    teams[team].append(player['stats']['trueDamageTaken'])
                                    teams[team].append(player['stats']['goldEarned'])
                                    teams[team].append(player['stats']['totalMinionsKilled'])
                                    teams[team].append(player['stats']['neutralMinionsKilled'])
                                    teams[team].append(player['stats']['neutralMinionsKilledTeamJungle'])
                                    teams[team].append(player['stats']['neutralMinionsKilledEnemyJungle'])
                                    teams[team].append(player['stats']['totalTimeCrowdControlDealt'])
                                    teams[team].append(player['stats']['wardsPlaced'])
                                    teams[team].append(player['stats']['wardsKilled'])
                                    teams[team].append(player['timeline']['creepsPerMinDeltas']['0-10'])
                                    teams[team].append(player['timeline']['creepsPerMinDeltas']['10-20'] if int(
                                        re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 20 and int(
                                        re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    teams[team].append(player['timeline']['creepsPerMinDeltas']['20-30'] if int(
                                        re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 30 and int(
                                        re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')

                                    teams[team].append(player['timeline']['creepsPerMinDeltas']['30-end'] if int(
                                        re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 40 and int(
                                        re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    teams[team].append(player['timeline']['xpPerMinDeltas']['0-10'])
                                    teams[team].append(player['timeline']['xpPerMinDeltas']['10-20'] if int(
                                        re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 20 and int(
                                        re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    teams[team].append(player['timeline']['xpPerMinDeltas']['20-30'] if int(
                                        re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 30 and int(
                                        re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    teams[team].append(player['timeline']['xpPerMinDeltas']['30-end'] if int(
                                        re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 40 and int(
                                        re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    teams[team].append(player['timeline']['goldPerMinDeltas']['0-10'])
                                    teams[team].append(player['timeline']['goldPerMinDeltas']['10-20'] if int(
                                        re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 20 and int(
                                        re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    teams[team].append(player['timeline']['goldPerMinDeltas']['20-30'] if int(
                                        re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 30 and int(
                                        re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    teams[team].append(player['timeline']['goldPerMinDeltas']['30-end'] if int(
                                        re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 40 and int(
                                        re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    try:
                                        teams[team].append(player['timeline']['csDiffPerMinDeltas']['0-10'])
                                    except KeyError:
                                        teams[team].append('Null')
                                    try:
                                        teams[team].append(player['timeline']['csDiffPerMinDeltas']['10-20'] if int(
                                            re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 20 and int(
                                            re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    except KeyError:
                                        teams[team].append('Null')
                                    try:
                                        teams[team].append(player['timeline']['csDiffPerMinDeltas']['20-30'] if int(
                                            re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 30 and int(
                                            re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    except KeyError:
                                        teams[team].append('Null')
                                    try:
                                        teams[team].append(player['timeline']['csDiffPerMinDeltas']['30-end'] if int(
                                            re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 40 and int(
                                            re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    except KeyError:
                                        teams[team].append('Null')
                                    try:
                                        teams[team].append(player['timeline']['xpDiffPerMinDeltas']['0-10'])
                                    except KeyError:
                                        teams[team].append('Null')
                                    try:
                                        teams[team].append(player['timeline']['xpDiffPerMinDeltas']['10-20'] if int(
                                            re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 20 and int(
                                            re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    except KeyError:
                                        teams[team].append('Null')
                                    try:
                                        teams[team].append(player['timeline']['xpDiffPerMinDeltas']['20-30'] if int(
                                            re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 30 and int(
                                            re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    except KeyError:
                                        teams[team].append('Null')
                                    try:
                                        teams[team].append(player['timeline']['xpDiffPerMinDeltas']['30-end'] if int(
                                            re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 40 and int(
                                            re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    except KeyError:
                                        teams[team].append('Null')
                                    teams[team].append(player['timeline']['damageTakenPerMinDeltas']['0-10'])
                                    teams[team].append(player['timeline']['damageTakenPerMinDeltas']['10-20'] if int(
                                        re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 20 and int(
                                        re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    teams[team].append(player['timeline']['damageTakenPerMinDeltas']['20-30'] if int(
                                        re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 30 and int(
                                        re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    teams[team].append(player['timeline']['damageTakenPerMinDeltas']['30-end'] if int(
                                        re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 40 and int(
                                        re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    try:
                                        teams[team].append(player['timeline']['damageTakenDiffPerMinDeltas']['0-10'])
                                    except KeyError:
                                        teams[team].append('Null')
                                    try:
                                        teams[team].append(
                                            player['timeline']['damageTakenDiffPerMinDeltas']['10-20'] if int(
                                                re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 20 and int(
                                                re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    except KeyError:
                                        teams[team].append('Null')
                                    try:
                                        teams[team].append(
                                            player['timeline']['damageTakenDiffPerMinDeltas']['20-30'] if int(
                                                re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 30 and int(
                                                re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    except KeyError:
                                        teams[team].append('Null')
                                    try:
                                        teams[team].append(
                                            player['timeline']['damageTakenDiffPerMinDeltas']['30-end'] if int(
                                                re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 40 and int(
                                                re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    except KeyError:
                                        teams[team].append('Null')
                            for player in match_history_json['participants']:
                                if player['participantId'] in enemies:
                                    teams[team].append(int(player['stats']['longestTimeSpentLiving']) / 60)
                                    teams[team].append(player['stats']['totalDamageDealt'])
                                    teams[team].append(player['stats']['magicDamageDealt'])
                                    teams[team].append(player['stats']['physicalDamageDealt'])
                                    teams[team].append(player['stats']['trueDamageDealt'])
                                    teams[team].append(player['stats']['totalDamageDealtToChampions'])
                                    teams[team].append(player['stats']['magicDamageDealtToChampions'])
                                    teams[team].append(player['stats']['physicalDamageDealtToChampions'])
                                    teams[team].append(player['stats']['trueDamageDealtToChampions'])
                                    teams[team].append(player['stats']['totalHeal'])
                                    teams[team].append(player['stats']['totalDamageTaken'])
                                    teams[team].append(player['stats']['magicalDamageTaken'])
                                    teams[team].append(player['stats']['physicalDamageTaken'])
                                    teams[team].append(player['stats']['trueDamageTaken'])
                                    teams[team].append(player['stats']['goldEarned'])
                                    teams[team].append(player['stats']['totalMinionsKilled'])
                                    teams[team].append(player['stats']['neutralMinionsKilled'])
                                    teams[team].append(player['stats']['neutralMinionsKilledTeamJungle'])
                                    teams[team].append(player['stats']['neutralMinionsKilledEnemyJungle'])
                                    teams[team].append(player['stats']['totalTimeCrowdControlDealt'])
                                    teams[team].append(player['stats']['wardsPlaced'])
                                    teams[team].append(player['stats']['wardsKilled'])
                                    teams[team].append(player['timeline']['creepsPerMinDeltas']['0-10'])
                                    teams[team].append(player['timeline']['creepsPerMinDeltas']['10-20'] if int(
                                        re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 20 and int(
                                        re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    teams[team].append(player['timeline']['creepsPerMinDeltas']['20-30'] if int(
                                        re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 30 and int(
                                        re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')

                                    teams[team].append(player['timeline']['creepsPerMinDeltas']['30-end'] if int(
                                        re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 40 and int(
                                        re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    teams[team].append(player['timeline']['xpPerMinDeltas']['0-10'])
                                    teams[team].append(player['timeline']['xpPerMinDeltas']['10-20'] if int(
                                        re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 20 and int(
                                        re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    teams[team].append(player['timeline']['xpPerMinDeltas']['20-30'] if int(
                                        re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 30 and int(
                                        re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    teams[team].append(player['timeline']['xpPerMinDeltas']['30-end'] if int(
                                        re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 40 and int(
                                        re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    teams[team].append(player['timeline']['goldPerMinDeltas']['0-10'])
                                    teams[team].append(player['timeline']['goldPerMinDeltas']['10-20'] if int(
                                        re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 20 and int(
                                        re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    teams[team].append(player['timeline']['goldPerMinDeltas']['20-30'] if int(
                                        re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 30 and int(
                                        re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    teams[team].append(player['timeline']['goldPerMinDeltas']['30-end'] if int(
                                        re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 40 and int(
                                        re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    try:
                                        teams[team].append(player['timeline']['csDiffPerMinDeltas']['0-10'])
                                    except KeyError:
                                        teams[team].append('Null')
                                    try:
                                        teams[team].append(player['timeline']['csDiffPerMinDeltas']['10-20'] if int(
                                            re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 20 and int(
                                            re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    except KeyError:
                                        teams[team].append('Null')
                                    try:
                                        teams[team].append(player['timeline']['csDiffPerMinDeltas']['20-30'] if int(
                                            re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 30 and int(
                                            re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    except KeyError:
                                        teams[team].append('Null')
                                    try:
                                        teams[team].append(player['timeline']['csDiffPerMinDeltas']['30-end'] if int(
                                            re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 40 and int(
                                            re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    except KeyError:
                                        teams[team].append('Null')
                                    try:
                                        teams[team].append(player['timeline']['xpDiffPerMinDeltas']['0-10'])
                                    except KeyError:
                                        teams[team].append('Null')
                                    try:
                                        teams[team].append(player['timeline']['xpDiffPerMinDeltas']['10-20'] if int(
                                            re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 20 and int(
                                            re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    except KeyError:
                                        teams[team].append('Null')
                                    try:
                                        teams[team].append(player['timeline']['xpDiffPerMinDeltas']['20-30'] if int(
                                            re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 30 and int(
                                            re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    except KeyError:
                                        teams[team].append('Null')
                                    try:
                                        teams[team].append(player['timeline']['xpDiffPerMinDeltas']['30-end'] if int(
                                            re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 40 and int(
                                            re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    except KeyError:
                                        teams[team].append('Null')
                                    teams[team].append(player['timeline']['damageTakenPerMinDeltas']['0-10'])
                                    teams[team].append(player['timeline']['damageTakenPerMinDeltas']['10-20'] if int(
                                        re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 20 and int(
                                        re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    teams[team].append(player['timeline']['damageTakenPerMinDeltas']['20-30'] if int(
                                        re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 30 and int(
                                        re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    teams[team].append(player['timeline']['damageTakenPerMinDeltas']['30-end'] if int(
                                        re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 40 and int(
                                        re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    try:
                                        teams[team].append(player['timeline']['damageTakenDiffPerMinDeltas']['0-10'])
                                    except KeyError:
                                        teams[team].append('Null')
                                    try:
                                        teams[team].append(
                                            player['timeline']['damageTakenDiffPerMinDeltas']['10-20'] if int(
                                                re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 20 and int(
                                                re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    except KeyError:
                                        teams[team].append('Null')
                                    try:
                                        teams[team].append(
                                            player['timeline']['damageTakenDiffPerMinDeltas']['20-30'] if int(
                                                re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 30 and int(
                                                re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    except KeyError:
                                        teams[team].append('Null')
                                    try:
                                        teams[team].append(
                                            player['timeline']['damageTakenDiffPerMinDeltas']['30-end'] if int(
                                                re.findall('([0-9]{1,100}):', both_teams[-1])[0]) >= 40 and int(
                                                re.findall(':([0-9]{1,100})', both_teams[-1])[0]) >= 1 else 'None')
                                    except KeyError:
                                        teams[team].append('Null')
                        # cursor.execute('select * from matches_info_parsed')
                        # names = [description[0] for description in cursor.description]
                        # for team in teams:
                        #     print(team, ":")
                        #     for i in range(0,20):
                        #         print(i,
                        #               names[i+6],
                        #               teams[team][i])
                        #     print('\n\n\n')
                        # [print(teams[team]) for team in teams]
                        # [print(sum([both_teams + teams[team]], [])) for team in teams]
                        [cursor.execute('''
                            INSERT INTO matches_info_parsed (                    
                            site_id,
                            championship, 
                            server, 
                            match_date, 
                            game_patch, 
                            match_time, 
                            team, 
                            is_winner, 
                            side, 
                            enemy_team, 
                            first_blood,
                            first_tower,
                            bans,
                            top_nick, 
                            jungle_nick, 
                            mid_nick,
                            adc_nick,
                            sup_nick,
                            top_pick, 
                            jungle_pick, 
                            mid_pick, 
                            adc_pick, 
                            sup_pick,
                            top_cs, 
                            mid_cs, 
                            jungle_cs,  
                            bot_cs,  
                            sup_cs, 
                            enemy_top_cs, 
                            enemy_mid_cs, 
                            enemy_jungle_cs, 
                            enemy_bot_cs,  
                            enemy_sup_cs,
                            top_cs_jungle, 
                            mid_cs_jungle,
                            jungle_cs_jungle,
                            bot_cs_jungle,
                            sup_cs_jungle,
                            enemy_top_cs_jungle,
                            enemy_mid_cs_jungle, 
                            enemy_jungle_cs_jungle, 
                            enemy_bot_cs_jungle,  
                            enemy_sup_cs_jungle,
                            top_gold, 
                            mid_gold, 
                            jungle_gold,  
                            bot_gold,  
                            sup_gold, 
                            enemy_top_gold, 
                            enemy_mid_gold, 
                            enemy_jungle_gold, 
                            enemy_bot_gold, 
                            enemy_sup_gold,
                            top_xp, 
                            mid_xp, 
                            jungle_xp, 
                            bot_xp,  
                            sup_xp, 
                            enemy_top_xp, 
                            enemy_mid_xp, 
                            enemy_jungle_xp,
                            enemy_bot_xp,  
                            enemy_sup_xp,
                            top_lvl, 
                            mid_lvl, 
                            jungle_lvl,  
                            bot_lvl,  
                            sup_lvl, 
                            enemy_top_lvl, 
                            enemy_mid_lvl, 
                            enemy_jungle_lvl, 
                            enemy_bot_lvl,  
                            enemy_sup_lvl,
                            top_tower_get,
                            mid_tower_get,
                            bot_tower_get,
                            nexus_tower_get,
                            top_tower_lost,
                            mid_tower_lost,
                            bot_tower_lost,
                            nexus_tower_lost,
                            top_ingib_get,
                            mid_ingib_get,
                            bot_ingib_get,
                            top_ingib_lost,
                            mid_ingib_lost,
                            bot_ingib_lost,
                            dragon_get,
                            dragon_lost,
                            baron_get,
                            baron_lost,
                            herold_get,
                            herold_lost,
                            kill_top_ally,
                            death_top_ally,
                            assists_top_ally,
                            kill_jng_ally,
                            death_jng_ally,
                            assists_jng_ally,
                            kill_mid_ally,
                            death_mid_ally,
                            assists_mid_ally,
                            kill_adc_ally,
                            death_adc_ally,
                            assists_adc_ally,
                            kill_sup_ally,
                            death_sup_ally,
                            assists_sup_ally,
                            kill_top_enemy,
                            death_top_enemy,
                            assists_top_enemy,
                            kill_jng_enemy,
                            death_jng_enemy,
                            assists_jng_enemy,
                            kill_mid_enemy,
                            death_mid_enemy,
                            assists_mid_enemy,
                            kill_adc_enemy,
                            death_adc_enemy,
                            assists_adc_enemy,
                            kill_sup_enemy,
                            death_sup_enemy,
                            assists_sup_enemy,
                            simple_wards_ally, 
                            vision_wards_ally,
                            simple_wards_enemy, 
                            vision_wards_enemy,
                            kill_simple_wards_ally, 
                            kill_vision_wards_ally,
                            kill_simple_wards_enemy, 
                            kill_vision_wards_enemy,
                            ally_top_longestTimeSpentLiving,
                            ally_top_totalDamageDealt,
                            ally_top_magicDamageDealt,
                            ally_top_physicalDamageDealt,
                            ally_top_trueDamageDealt,
                            ally_top_totalDamageDealtToChampions,
                            ally_top_magicDamageDealtToChampions,
                            ally_top_physicalDamageDealtToChampions,
                            ally_top_trueDamageDealtToChampions,
                            ally_top_totalHeal,
                            ally_top_totalDamageTaken,
                            ally_top_magicalDamageTaken,
                            ally_top_physicalDamageTaken,
                            ally_top_trueDamageTaken,
                            ally_top_goldEarned,
                            ally_top_totalMinionsKilled,
                            ally_top_neutralMinionsKilled,
                            ally_top_neutralMinionsKilledTeamJungle,
                            ally_top_neutralMinionsKilledEnemyJungle,
                            ally_top_totalTimeCrowdControlDealt,
                            ally_top_wardsPlaced,
                            ally_top_wardsKilled,
                        ally_top_creepsPerMinDeltas0_10,
                        ally_top_creepsPerMinDeltas10_20,
                        ally_top_creepsPerMinDeltas20_30,
                        ally_top_creepsPerMinDeltas30_end,
                        ally_top_xpPerMinDeltas0_10,
                        ally_top_xpPerMinDeltas10_20,
                        ally_top_xpPerMinDeltas20_30,
                        ally_top_xpPerMinDeltas30_end,
                        ally_top_goldPerMinDeltas0_10,
                        ally_top_goldPerMinDeltas10_20,
                        ally_top_goldPerMinDeltas20_30,
                        ally_top_goldPerMinDeltas30_end,
                        ally_top_csDiffPerMinDeltas0_10,
                        ally_top_csDiffPerMinDeltas10_20,
                        ally_top_csDiffPerMinDeltas20_30,
                        ally_top_csDiffPerMinDeltas30_end,
                        ally_top_xpDiffPerMinDeltas0_10,
                        ally_top_xpDiffPerMinDeltas10_20,
                        ally_top_xpDiffPerMinDeltas20_30,
                        ally_top_xpDiffPerMinDeltas30_end,
                        ally_top_damageTakenPerMinDeltas0_10,
                        ally_top_damageTakenPerMinDeltas10_20,
                        ally_top_damageTakenPerMinDeltas20_30,
                        ally_top_damageTakenPerMinDeltas30_end,
                        ally_top_damageTakenDiffPerMinDeltas0_10,
                        ally_top_damageTakenDiffPerMinDeltas10_20,
                        ally_top_damageTakenDiffPerMinDeltas20_30,
                        ally_top_damageTakenDiffPerMinDeltas30_end,
                            ally_jng_longestTimeSpentLiving,
                            ally_jng_totalDamageDealt,
                            ally_jng_magicDamageDealt,
                            ally_jng_physicalDamageDealt,
                            ally_jng_trueDamageDealt,
                            ally_jng_totalDamageDealtToChampions,
                            ally_jng_magicDamageDealtToChampions,
                            ally_jng_physicalDamageDealtToChampions,
                            ally_jng_trueDamageDealtToChampions,
                            ally_jng_totalHeal,
                            ally_jng_totalDamageTaken,
                            ally_jng_magicalDamageTaken,
                            ally_jng_physicalDamageTaken,
                            ally_jng_trueDamageTaken,
                            ally_jng_goldEarned,
                            ally_jng_totalMinionsKilled,
                            ally_jng_neutralMinionsKilled,
                            ally_jng_neutralMinionsKilledTeamJungle,
                            ally_jng_neutralMinionsKilledEnemyJungle,
                            ally_jng_totalTimeCrowdControlDealt,
                            ally_jng_wardsPlaced,
                            ally_jng_wardsKilled,
                        ally_jng_creepsPerMinDeltas0_10,
                        ally_jng_creepsPerMinDeltas10_20,
                        ally_jng_creepsPerMinDeltas20_30,
                        ally_jng_creepsPerMinDeltas30_end,
                        ally_jng_xpPerMinDeltas0_10,
                        ally_jng_xpPerMinDeltas10_20,
                        ally_jng_xpPerMinDeltas20_30,
                        ally_jng_xpPerMinDeltas30_end,
                        ally_jng_goldPerMinDeltas0_10,
                        ally_jng_goldPerMinDeltas10_20,
                        ally_jng_goldPerMinDeltas20_30,
                        ally_jng_goldPerMinDeltas30_end,
                        ally_jng_csDiffPerMinDeltas0_10,
                        ally_jng_csDiffPerMinDeltas10_20,
                        ally_jng_csDiffPerMinDeltas20_30,
                        ally_jng_csDiffPerMinDeltas30_end,
                        ally_jng_xpDiffPerMinDeltas0_10,
                        ally_jng_xpDiffPerMinDeltas10_20,
                        ally_jng_xpDiffPerMinDeltas20_30,
                        ally_jng_xpDiffPerMinDeltas30_end,
                        ally_jng_damageTakenPerMinDeltas0_10,
                        ally_jng_damageTakenPerMinDeltas10_20,
                        ally_jng_damageTakenPerMinDeltas20_30,
                        ally_jng_damageTakenPerMinDeltas30_end,
                        ally_jng_damageTakenDiffPerMinDeltas0_10,
                        ally_jng_damageTakenDiffPerMinDeltas10_20,
                        ally_jng_damageTakenDiffPerMinDeltas20_30,
                        ally_jng_damageTakenDiffPerMinDeltas30_end,                 
                            ally_mid_longestTimeSpentLiving,
                            ally_mid_totalDamageDealt,
                            ally_mid_magicDamageDealt,
                            ally_mid_physicalDamageDealt,
                            ally_mid_trueDamageDealt,
                            ally_mid_totalDamageDealtToChampions,
                            ally_mid_magicDamageDealtToChampions,
                            ally_mid_physicalDamageDealtToChampions,
                            ally_mid_trueDamageDealtToChampions,
                            ally_mid_totalHeal,
                            ally_mid_totalDamageTaken,
                            ally_mid_magicalDamageTaken,
                            ally_mid_physicalDamageTaken,
                            ally_mid_trueDamageTaken,
                            ally_mid_goldEarned,
                            ally_mid_totalMinionsKilled,
                            ally_mid_neutralMinionsKilled,
                            ally_mid_neutralMinionsKilledTeamJungle,
                            ally_mid_neutralMinionsKilledEnemyJungle,
                            ally_mid_totalTimeCrowdControlDealt,
                            ally_mid_wardsPlaced,
                            ally_mid_wardsKilled,
                        ally_mid_creepsPerMinDeltas0_10,
                        ally_mid_creepsPerMinDeltas10_20,
                        ally_mid_creepsPerMinDeltas20_30,
                        ally_mid_creepsPerMinDeltas30_end,
                        ally_mid_xpPerMinDeltas0_10,
                        ally_mid_xpPerMinDeltas10_20,
                        ally_mid_xpPerMinDeltas20_30,
                        ally_mid_xpPerMinDeltas30_end,
                        ally_mid_goldPerMinDeltas0_10,
                        ally_mid_goldPerMinDeltas10_20,
                        ally_mid_goldPerMinDeltas20_30,
                        ally_mid_goldPerMinDeltas30_end,
                        ally_mid_csDiffPerMinDeltas0_10,
                        ally_mid_csDiffPerMinDeltas10_20,
                        ally_mid_csDiffPerMinDeltas20_30,
                        ally_mid_csDiffPerMinDeltas30_end,
                        ally_mid_xpDiffPerMinDeltas0_10,
                        ally_mid_xpDiffPerMinDeltas10_20,
                        ally_mid_xpDiffPerMinDeltas20_30,
                        ally_mid_xpDiffPerMinDeltas30_end,
                        ally_mid_damageTakenPerMinDeltas0_10,
                        ally_mid_damageTakenPerMinDeltas10_20,
                        ally_mid_damageTakenPerMinDeltas20_30,
                        ally_mid_damageTakenPerMinDeltas30_end,
                        ally_mid_damageTakenDiffPerMinDeltas0_10,
                        ally_mid_damageTakenDiffPerMinDeltas10_20,
                        ally_mid_damageTakenDiffPerMinDeltas20_30,
                        ally_mid_damageTakenDiffPerMinDeltas30_end,
                            ally_adc_longestTimeSpentLiving,
                            ally_adc_totalDamageDealt,
                            ally_adc_magicDamageDealt,
                            ally_adc_physicalDamageDealt,
                            ally_adc_trueDamageDealt,
                            ally_adc_totalDamageDealtToChampions,
                            ally_adc_magicDamageDealtToChampions,
                            ally_adc_physicalDamageDealtToChampions,
                            ally_adc_trueDamageDealtToChampions,
                            ally_adc_totalHeal,
                            ally_adc_totalDamageTaken,
                            ally_adc_magicalDamageTaken,
                            ally_adc_physicalDamageTaken,
                            ally_adc_trueDamageTaken,
                            ally_adc_goldEarned,
                            ally_adc_totalMinionsKilled,
                            ally_adc_neutralMinionsKilled,
                            ally_adc_neutralMinionsKilledTeamJungle,
                            ally_adc_neutralMinionsKilledEnemyJungle,
                            ally_adc_totalTimeCrowdControlDealt,
                            ally_adc_wardsPlaced,
                            ally_adc_wardsKilled,
                        ally_adc_creepsPerMinDeltas0_10,
                        ally_adc_creepsPerMinDeltas10_20,
                        ally_adc_creepsPerMinDeltas20_30,
                        ally_adc_creepsPerMinDeltas30_end,
                        ally_adc_xpPerMinDeltas0_10,
                        ally_adc_xpPerMinDeltas10_20,
                        ally_adc_xpPerMinDeltas20_30,
                        ally_adc_xpPerMinDeltas30_end,
                        ally_adc_goldPerMinDeltas0_10,
                        ally_adc_goldPerMinDeltas10_20,
                        ally_adc_goldPerMinDeltas20_30,
                        ally_adc_goldPerMinDeltas30_end,
                        ally_adc_csDiffPerMinDeltas0_10,
                        ally_adc_csDiffPerMinDeltas10_20,
                        ally_adc_csDiffPerMinDeltas20_30,
                        ally_adc_csDiffPerMinDeltas30_end,
                        ally_adc_xpDiffPerMinDeltas0_10,
                        ally_adc_xpDiffPerMinDeltas10_20,
                        ally_adc_xpDiffPerMinDeltas20_30,
                        ally_adc_xpDiffPerMinDeltas30_end,
                        ally_adc_damageTakenPerMinDeltas0_10,
                        ally_adc_damageTakenPerMinDeltas10_20,
                        ally_adc_damageTakenPerMinDeltas20_30,
                        ally_adc_damageTakenPerMinDeltas30_end,
                        ally_adc_damageTakenDiffPerMinDeltas0_10,
                        ally_adc_damageTakenDiffPerMinDeltas10_20,
                        ally_adc_damageTakenDiffPerMinDeltas20_30,
                        ally_adc_damageTakenDiffPerMinDeltas30_end,
                            ally_sup_longestTimeSpentLiving,
                            ally_sup_totalDamageDealt,
                            ally_sup_magicDamageDealt,
                            ally_sup_physicalDamageDealt,
                            ally_sup_trueDamageDealt,
                            ally_sup_totalDamageDealtToChampions,
                            ally_sup_magicDamageDealtToChampions,
                            ally_sup_physicalDamageDealtToChampions,
                            ally_sup_trueDamageDealtToChampions,
                            ally_sup_totalHeal,
                            ally_sup_totalDamageTaken,
                            ally_sup_magicalDamageTaken,
                            ally_sup_physicalDamageTaken,
                            ally_sup_trueDamageTaken,
                            ally_sup_goldEarned,
                            ally_sup_totalMinionsKilled,
                            ally_sup_neutralMinionsKilled,
                            ally_sup_neutralMinionsKilledTeamJungle,
                            ally_sup_neutralMinionsKilledEnemyJungle,
                            ally_sup_totalTimeCrowdControlDealt,
                            ally_sup_wardsPlaced,
                            ally_sup_wardsKilled,
                        ally_sup_creepsPerMinDeltas0_10,
                        ally_sup_creepsPerMinDeltas10_20,
                        ally_sup_creepsPerMinDeltas20_30,
                        ally_sup_creepsPerMinDeltas30_end,
                        ally_sup_xpPerMinDeltas0_10,
                        ally_sup_xpPerMinDeltas10_20,
                        ally_sup_xpPerMinDeltas20_30,
                        ally_sup_xpPerMinDeltas30_end,
                        ally_sup_goldPerMinDeltas0_10,
                        ally_sup_goldPerMinDeltas10_20,
                        ally_sup_goldPerMinDeltas20_30,
                        ally_sup_goldPerMinDeltas30_end,
                        ally_sup_csDiffPerMinDeltas0_10,
                        ally_sup_csDiffPerMinDeltas10_20,
                        ally_sup_csDiffPerMinDeltas20_30,
                        ally_sup_csDiffPerMinDeltas30_end,
                        ally_sup_xpDiffPerMinDeltas0_10,
                        ally_sup_xpDiffPerMinDeltas10_20,
                        ally_sup_xpDiffPerMinDeltas20_30,
                        ally_sup_xpDiffPerMinDeltas30_end,
                        ally_sup_damageTakenPerMinDeltas0_10,
                        ally_sup_damageTakenPerMinDeltas10_20,
                        ally_sup_damageTakenPerMinDeltas20_30,
                        ally_sup_damageTakenPerMinDeltas30_end,
                        ally_sup_damageTakenDiffPerMinDeltas0_10,
                        ally_sup_damageTakenDiffPerMinDeltas10_20,
                        ally_sup_damageTakenDiffPerMinDeltas20_30,
                        ally_sup_damageTakenDiffPerMinDeltas30_end,
                            enemy_top_longestTimeSpentLiving,
                            enemy_top_totalDamageDealt,
                            enemy_top_magicDamageDealt,
                            enemy_top_physicalDamageDealt,
                            enemy_top_trueDamageDealt,
                            enemy_top_totalDamageDealtToChampions,
                            enemy_top_magicDamageDealtToChampions,
                            enemy_top_physicalDamageDealtToChampions,
                            enemy_top_trueDamageDealtToChampions,
                            enemy_top_totalHeal,
                            enemy_top_totalDamageTaken,
                            enemy_top_magicalDamageTaken,
                            enemy_top_physicalDamageTaken,
                            enemy_top_trueDamageTaken,
                            enemy_top_goldEarned,
                            enemy_top_totalMinionsKilled,
                            enemy_top_neutralMinionsKilled,
                            enemy_top_neutralMinionsKilledTeamJungle,
                            enemy_top_neutralMinionsKilledEnemyJungle,
                            enemy_top_totalTimeCrowdControlDealt,
                            enemy_top_wardsPlaced,
                            enemy_top_wardsKilled,
                        enemy_top_creepsPerMinDeltas0_10,
                        enemy_top_creepsPerMinDeltas10_20,
                        enemy_top_creepsPerMinDeltas20_30,
                        enemy_top_creepsPerMinDeltas30_end,
                        enemy_top_xpPerMinDeltas0_10,
                        enemy_top_xpPerMinDeltas10_20,
                        enemy_top_xpPerMinDeltas20_30,
                        enemy_top_xpPerMinDeltas30_end,
                        enemy_top_goldPerMinDeltas0_10,
                        enemy_top_goldPerMinDeltas10_20,
                        enemy_top_goldPerMinDeltas20_30,
                        enemy_top_goldPerMinDeltas30_end,
                        enemy_top_csDiffPerMinDeltas0_10,
                        enemy_top_csDiffPerMinDeltas10_20,
                        enemy_top_csDiffPerMinDeltas20_30,
                        enemy_top_csDiffPerMinDeltas30_end,
                        enemy_top_xpDiffPerMinDeltas0_10,
                        enemy_top_xpDiffPerMinDeltas10_20,
                        enemy_top_xpDiffPerMinDeltas20_30,
                        enemy_top_xpDiffPerMinDeltas30_end,
                        enemy_top_damageTakenPerMinDeltas0_10,
                        enemy_top_damageTakenPerMinDeltas10_20,
                        enemy_top_damageTakenPerMinDeltas20_30,
                        enemy_top_damageTakenPerMinDeltas30_end,
                        enemy_top_damageTakenDiffPerMinDeltas0_10,
                        enemy_top_damageTakenDiffPerMinDeltas10_20,
                        enemy_top_damageTakenDiffPerMinDeltas20_30,
                        enemy_top_damageTakenDiffPerMinDeltas30_end,
                            enemy_jng_longestTimeSpentLiving,
                            enemy_jng_totalDamageDealt,
                            enemy_jng_magicDamageDealt,
                            enemy_jng_physicalDamageDealt,
                            enemy_jng_trueDamageDealt,
                            enemy_jng_totalDamageDealtToChampions,
                            enemy_jng_magicDamageDealtToChampions,
                            enemy_jng_physicalDamageDealtToChampions,
                            enemy_jng_trueDamageDealtToChampions,
                            enemy_jng_totalHeal,
                            enemy_jng_totalDamageTaken,
                            enemy_jng_magicalDamageTaken,
                            enemy_jng_physicalDamageTaken,
                            enemy_jng_trueDamageTaken,
                            enemy_jng_goldEarned,
                            enemy_jng_totalMinionsKilled,
                            enemy_jng_neutralMinionsKilled,
                            enemy_jng_neutralMinionsKilledTeamJungle,
                            enemy_jng_neutralMinionsKilledEnemyJungle,
                            enemy_jng_totalTimeCrowdControlDealt,
                            enemy_jng_wardsPlaced,
                            enemy_jng_wardsKilled,
                        enemy_jng_creepsPerMinDeltas0_10,
                        enemy_jng_creepsPerMinDeltas10_20,
                        enemy_jng_creepsPerMinDeltas20_30,
                        enemy_jng_creepsPerMinDeltas30_end,
                        enemy_jng_xpPerMinDeltas0_10,
                        enemy_jng_xpPerMinDeltas10_20,
                        enemy_jng_xpPerMinDeltas20_30,
                        enemy_jng_xpPerMinDeltas30_end,
                        enemy_jng_goldPerMinDeltas0_10,
                        enemy_jng_goldPerMinDeltas10_20,
                        enemy_jng_goldPerMinDeltas20_30,
                        enemy_jng_goldPerMinDeltas30_end,
                        enemy_jng_csDiffPerMinDeltas0_10,
                        enemy_jng_csDiffPerMinDeltas10_20,
                        enemy_jng_csDiffPerMinDeltas20_30,
                        enemy_jng_csDiffPerMinDeltas30_end,
                        enemy_jng_xpDiffPerMinDeltas0_10,
                        enemy_jng_xpDiffPerMinDeltas10_20,
                        enemy_jng_xpDiffPerMinDeltas20_30,
                        enemy_jng_xpDiffPerMinDeltas30_end,
                        enemy_jng_damageTakenPerMinDeltas0_10,
                        enemy_jng_damageTakenPerMinDeltas10_20,
                        enemy_jng_damageTakenPerMinDeltas20_30,
                        enemy_jng_damageTakenPerMinDeltas30_end,
                        enemy_jng_damageTakenDiffPerMinDeltas0_10,
                        enemy_jng_damageTakenDiffPerMinDeltas10_20,
                        enemy_jng_damageTakenDiffPerMinDeltas20_30,
                        enemy_jng_damageTakenDiffPerMinDeltas30_end,
                            enemy_mid_longestTimeSpentLiving,
                            enemy_mid_totalDamageDealt,
                            enemy_mid_magicDamageDealt,
                            enemy_mid_physicalDamageDealt,
                            enemy_mid_trueDamageDealt,
                            enemy_mid_totalDamageDealtToChampions,
                            enemy_mid_magicDamageDealtToChampions,
                            enemy_mid_physicalDamageDealtToChampions,
                            enemy_mid_trueDamageDealtToChampions,
                            enemy_mid_totalHeal,
                            enemy_mid_totalDamageTaken,
                            enemy_mid_magicalDamageTaken,
                            enemy_mid_physicalDamageTaken,
                            enemy_mid_trueDamageTaken,
                            enemy_mid_goldEarned,
                            enemy_mid_totalMinionsKilled,
                            enemy_mid_neutralMinionsKilled,
                            enemy_mid_neutralMinionsKilledTeamJungle,
                            enemy_mid_neutralMinionsKilledEnemyJungle,
                            enemy_mid_totalTimeCrowdControlDealt,
                            enemy_mid_wardsPlaced,
                            enemy_mid_wardsKilled,
                        enemy_mid_creepsPerMinDeltas0_10,
                        enemy_mid_creepsPerMinDeltas10_20,
                        enemy_mid_creepsPerMinDeltas20_30,
                        enemy_mid_creepsPerMinDeltas30_end,
                        enemy_mid_xpPerMinDeltas0_10,
                        enemy_mid_xpPerMinDeltas10_20,
                        enemy_mid_xpPerMinDeltas20_30,
                        enemy_mid_xpPerMinDeltas30_end,
                        enemy_mid_goldPerMinDeltas0_10,
                        enemy_mid_goldPerMinDeltas10_20,
                        enemy_mid_goldPerMinDeltas20_30,
                        enemy_mid_goldPerMinDeltas30_end,
                        enemy_mid_csDiffPerMinDeltas0_10,
                        enemy_mid_csDiffPerMinDeltas10_20,
                        enemy_mid_csDiffPerMinDeltas20_30,
                        enemy_mid_csDiffPerMinDeltas30_end,
                        enemy_mid_xpDiffPerMinDeltas0_10,
                        enemy_mid_xpDiffPerMinDeltas10_20,
                        enemy_mid_xpDiffPerMinDeltas20_30,
                        enemy_mid_xpDiffPerMinDeltas30_end,
                        enemy_mid_damageTakenPerMinDeltas0_10,
                        enemy_mid_damageTakenPerMinDeltas10_20,
                        enemy_mid_damageTakenPerMinDeltas20_30,
                        enemy_mid_damageTakenPerMinDeltas30_end,
                        enemy_mid_damageTakenDiffPerMinDeltas0_10,
                        enemy_mid_damageTakenDiffPerMinDeltas10_20,
                        enemy_mid_damageTakenDiffPerMinDeltas20_30,
                        enemy_mid_damageTakenDiffPerMinDeltas30_end,
                            enemy_adc_longestTimeSpentLiving,
                            enemy_adc_totalDamageDealt,
                            enemy_adc_magicDamageDealt,
                            enemy_adc_physicalDamageDealt,
                            enemy_adc_trueDamageDealt,
                            enemy_adc_totalDamageDealtToChampions,
                            enemy_adc_magicDamageDealtToChampions,
                            enemy_adc_physicalDamageDealtToChampions,
                            enemy_adc_trueDamageDealtToChampions,
                            enemy_adc_totalHeal,
                            enemy_adc_totalDamageTaken,
                            enemy_adc_magicalDamageTaken,
                            enemy_adc_physicalDamageTaken,
                            enemy_adc_trueDamageTaken,
                            enemy_adc_goldEarned,
                            enemy_adc_totalMinionsKilled,
                            enemy_adc_neutralMinionsKilled,
                            enemy_adc_neutralMinionsKilledTeamJungle,
                            enemy_adc_neutralMinionsKilledEnemyJungle,
                            enemy_adc_totalTimeCrowdControlDealt,
                            enemy_adc_wardsPlaced,
                            enemy_adc_wardsKilled,
                        enemy_adc_creepsPerMinDeltas0_10,
                        enemy_adc_creepsPerMinDeltas10_20,
                        enemy_adc_creepsPerMinDeltas20_30,
                        enemy_adc_creepsPerMinDeltas30_end,
                        enemy_adc_xpPerMinDeltas0_10,
                        enemy_adc_xpPerMinDeltas10_20,
                        enemy_adc_xpPerMinDeltas20_30,
                        enemy_adc_xpPerMinDeltas30_end,
                        enemy_adc_goldPerMinDeltas0_10,
                        enemy_adc_goldPerMinDeltas10_20,
                        enemy_adc_goldPerMinDeltas20_30,
                        enemy_adc_goldPerMinDeltas30_end,
                        enemy_adc_csDiffPerMinDeltas0_10,
                        enemy_adc_csDiffPerMinDeltas10_20,
                        enemy_adc_csDiffPerMinDeltas20_30,
                        enemy_adc_csDiffPerMinDeltas30_end,
                        enemy_adc_xpDiffPerMinDeltas0_10,
                        enemy_adc_xpDiffPerMinDeltas10_20,
                        enemy_adc_xpDiffPerMinDeltas20_30,
                        enemy_adc_xpDiffPerMinDeltas30_end,
                        enemy_adc_damageTakenPerMinDeltas0_10,
                        enemy_adc_damageTakenPerMinDeltas10_20,
                        enemy_adc_damageTakenPerMinDeltas20_30,
                        enemy_adc_damageTakenPerMinDeltas30_end,
                        enemy_adc_damageTakenDiffPerMinDeltas0_10,
                        enemy_adc_damageTakenDiffPerMinDeltas10_20,
                        enemy_adc_damageTakenDiffPerMinDeltas20_30,
                        enemy_adc_damageTakenDiffPerMinDeltas30_end,
                            enemy_sup_longestTimeSpentLiving,
                            enemy_sup_totalDamageDealt,
                            enemy_sup_magicDamageDealt,
                            enemy_sup_physicalDamageDealt,
                            enemy_sup_trueDamageDealt,
                            enemy_sup_totalDamageDealtToChampions,
                            enemy_sup_magicDamageDealtToChampions,
                            enemy_sup_physicalDamageDealtToChampions,
                            enemy_sup_trueDamageDealtToChampions,
                            enemy_sup_totalHeal,
                            enemy_sup_totalDamageTaken,
                            enemy_sup_magicalDamageTaken,
                            enemy_sup_physicalDamageTaken,
                            enemy_sup_trueDamageTaken,
                            enemy_sup_goldEarned,
                            enemy_sup_totalMinionsKilled,
                            enemy_sup_neutralMinionsKilled,
                            enemy_sup_neutralMinionsKilledTeamJungle,
                            enemy_sup_neutralMinionsKilledEnemyJungle,
                            enemy_sup_totalTimeCrowdControlDealt,
                            enemy_sup_wardsPlaced,
                            enemy_sup_wardsKilled,
                        enemy_sup_creepsPerMinDeltas0_10,
                        enemy_sup_creepsPerMinDeltas10_20,
                        enemy_sup_creepsPerMinDeltas20_30,
                        enemy_sup_creepsPerMinDeltas30_end,
                        enemy_sup_xpPerMinDeltas0_10,
                        enemy_sup_xpPerMinDeltas10_20,
                        enemy_sup_xpPerMinDeltas20_30,
                        enemy_sup_xpPerMinDeltas30_end,
                        enemy_sup_goldPerMinDeltas0_10,
                        enemy_sup_goldPerMinDeltas10_20,
                        enemy_sup_goldPerMinDeltas20_30,
                        enemy_sup_goldPerMinDeltas30_end,
                        enemy_sup_csDiffPerMinDeltas0_10,
                        enemy_sup_csDiffPerMinDeltas10_20,
                        enemy_sup_csDiffPerMinDeltas20_30,
                        enemy_sup_csDiffPerMinDeltas30_end,
                        enemy_sup_xpDiffPerMinDeltas0_10,
                        enemy_sup_xpDiffPerMinDeltas10_20,
                        enemy_sup_xpDiffPerMinDeltas20_30,
                        enemy_sup_xpDiffPerMinDeltas30_end,
                        enemy_sup_damageTakenPerMinDeltas0_10,
                        enemy_sup_damageTakenPerMinDeltas10_20,
                        enemy_sup_damageTakenPerMinDeltas20_30,
                        enemy_sup_damageTakenPerMinDeltas30_end,
                        enemy_sup_damageTakenDiffPerMinDeltas0_10,
                        enemy_sup_damageTakenDiffPerMinDeltas10_20,
                        enemy_sup_damageTakenDiffPerMinDeltas20_30,
                        enemy_sup_damageTakenDiffPerMinDeltas30_end) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                            ''', sum([both_teams + teams[team]], [])) for team in teams]

                        connect.commit()

            print('\r%3.6s%% (%s/%s)' % (k * 100 / (number_of_matches), str(k), str(number_of_matches)), end='')


def get_matches_info_parsed_cn(number_of_matches):
    with sqlite3.connect('Statistics_Analyzer.sqlite') as connect:
        cursor = connect.cursor()
        try:
            cursor.execute("""CREATE TABLE matches_info_parsed (                    
                        site_id INTEGER,
                        championship INTEGER, 
                        server VARCHAR, 
                        match_date timestring, 
                        game_patch VARCHAR, 
                        match_time timestring, 
                        team VARCHAR, 
                        is_winner VARCHAR, 
                        side VARCHAR, 
                        enemy_team VARCHAR, 
                        first_blood VARCHAR,
                        first_tower VARCHAR,
                        bans VARCHAR,
                        top_nick VARCHAR, 
                        jungle_nick VARCHAR, 
                        mid_nick VARCHAR,
                        adc_nick VARCHAR,
                        sup_nick VARCHAR,
                        top_pick VARCHAR, 
                        jungle_pick VARCHAR, 
                        mid_pick VARCHAR, 
                        adc_pick VARCHAR, 
                        sup_pick VARCHAR,
                        top_cs VARCHAR, 
                        mid_cs VARCHAR, 
                        jungle_cs VARCHAR,  
                        bot_cs VARCHAR,  
                        sup_cs VARCHAR, 
                        enemy_top_cs VARCHAR, 
                        enemy_mid_cs VARCHAR, 
                        enemy_jungle_cs VARCHAR, 
                        enemy_bot_cs VARCHAR,  
                        enemy_sup_cs VARCHAR,
                        top_cs_jungle VARCHAR, 
                        mid_cs_jungle VARCHAR,
                        jungle_cs_jungle VARCHAR,
                        bot_cs_jungle VARCHAR,
                        sup_cs_jungle VARCHAR,
                        enemy_top_cs_jungle VARCHAR,
                        enemy_mid_cs_jungle VARCHAR, 
                        enemy_jungle_cs_jungle VARCHAR, 
                        enemy_bot_cs_jungle VARCHAR,  
                        enemy_sup_cs_jungle VARCHAR,
                        top_gold VARCHAR, 
                        mid_gold VARCHAR, 
                        jungle_gold VARCHAR,  
                        bot_gold VARCHAR,  
                        sup_gold VARCHAR, 
                        enemy_top_gold VARCHAR, 
                        enemy_mid_gold VARCHAR, 
                        enemy_jungle_gold VARCHAR, 
                        enemy_bot_gold VARCHAR, 
                        enemy_sup_gold VARCHAR,
                        top_xp VARCHAR, 
                        mid_xp VARCHAR, 
                        jungle_xp VARCHAR, 
                        bot_xp VARCHAR,  
                        sup_xp VARCHAR, 
                        enemy_top_xp VARCHAR, 
                        enemy_mid_xp VARCHAR, 
                        enemy_jungle_xp VARCHAR,
                        enemy_bot_xp VARCHAR,  
                        enemy_sup_xp VARCHAR,
                        top_lvl VARCHAR, 
                        mid_lvl VARCHAR, 
                        jungle_lvl VARCHAR,  
                        bot_lvl VARCHAR,  
                        sup_lvl VARCHAR, 
                        enemy_top_lvl VARCHAR, 
                        enemy_mid_lvl VARCHAR, 
                        enemy_jungle_lvl VARCHAR, 
                        enemy_bot_lvl VARCHAR,  
                        enemy_sup_lvl VARCHAR,
                        top_tower_get VARCHAR,
                        mid_tower_get VARCHAR,
                        bot_tower_get VARCHAR,
                        nexus_tower_get VARCHAR,
                        top_tower_lost VARCHAR,
                        mid_tower_lost VARCHAR,
                        bot_tower_lost VARCHAR,
                        nexus_tower_lost VARCHAR,
                        top_ingib_get VARCHAR,
                        mid_ingib_get VARCHAR,
                        bot_ingib_get VARCHAR,
                        top_ingib_lost VARCHAR,
                        mid_ingib_lost VARCHAR,
                        bot_ingib_lost VARCHAR,
                        dragon_get VARCHAR,
                        dragon_lost VARCHAR,
                        baron_get VARCHAR,
                        baron_lost VARCHAR,
                        herold_get VARCHAR,
                        herold_lost VARCHAR,
                        kill_top_ally VARCHAR,
                        death_top_ally VARCHAR,
                        assists_top_ally VARCHAR,
                        kill_jng_ally VARCHAR,
                        death_jng_ally VARCHAR,
                        assists_jng_ally VARCHAR,
                        kill_mid_ally VARCHAR,
                        death_mid_ally VARCHAR,
                        assists_mid_ally VARCHAR,
                        kill_adc_ally VARCHAR,
                        death_adc_ally VARCHAR,
                        assists_adc_ally VARCHAR,
                        kill_sup_ally VARCHAR,
                        death_sup_ally VARCHAR,
                        assists_sup_ally VARCHAR,
                        kill_top_enemy VARCHAR,
                        death_top_enemy VARCHAR,
                        assists_top_enemy VARCHAR,
                        kill_jng_enemy VARCHAR,
                        death_jng_enemy VARCHAR,
                        assists_jng_enemy VARCHAR,
                        kill_mid_enemy VARCHAR,
                        death_mid_enemy VARCHAR,
                        assists_mid_enemy VARCHAR,
                        kill_adc_enemy VARCHAR,
                        death_adc_enemy VARCHAR,
                        assists_adc_enemy VARCHAR,
                        kill_sup_enemy VARCHAR,
                        death_sup_enemy VARCHAR,
                        assists_sup_enemy VARCHAR,
                        simple_wards_ally VARCHAR, 
                        vision_wards_ally VARCHAR,
                        simple_wards_enemy VARCHAR, 
                        vision_wards_enemy VARCHAR,
                        kill_simple_wards_ally VARCHAR, 
                        kill_vision_wards_ally VARCHAR,
                        kill_simple_wards_enemy VARCHAR, 
                        kill_vision_wards_enemy VARCHAR,
                        ally_top_longestTimeSpentLiving VARCHAR,
                        ally_top_totalDamageDealt VARCHAR,
                        ally_top_magicDamageDealt VARCHAR,
                        ally_top_physicalDamageDealt VARCHAR,
                        ally_top_trueDamageDealt VARCHAR,
                        ally_top_totalDamageDealtToChampions VARCHAR,
                        ally_top_magicDamageDealtToChampions VARCHAR,
                        ally_top_physicalDamageDealtToChampions VARCHAR,
                        ally_top_trueDamageDealtToChampions VARCHAR,
                        ally_top_totalHeal VARCHAR,
                        ally_top_totalDamageTaken VARCHAR,
                        ally_top_magicalDamageTaken VARCHAR,
                        ally_top_physicalDamageTaken VARCHAR,
                        ally_top_trueDamageTaken VARCHAR,
                        ally_top_goldEarned VARCHAR,
                        ally_top_totalMinionsKilled VARCHAR,
                        ally_top_neutralMinionsKilled VARCHAR,
                        ally_top_neutralMinionsKilledTeamJungle VARCHAR,
                        ally_top_neutralMinionsKilledEnemyJungle VARCHAR,
                        ally_top_totalTimeCrowdControlDealt VARCHAR,
                        ally_top_wardsPlaced VARCHAR,
                        ally_top_wardsKilled VARCHAR,
                    ally_top_creepsPerMinDeltas0_10 VARCHAR,
                    ally_top_creepsPerMinDeltas10_20 VARCHAR,
                    ally_top_creepsPerMinDeltas20_30 VARCHAR,
                    ally_top_creepsPerMinDeltas30_end VARCHAR,
                    ally_top_xpPerMinDeltas0_10 VARCHAR,
                    ally_top_xpPerMinDeltas10_20 VARCHAR,
                    ally_top_xpPerMinDeltas20_30 VARCHAR,
                    ally_top_xpPerMinDeltas30_end VARCHAR,
                    ally_top_goldPerMinDeltas0_10 VARCHAR,
                    ally_top_goldPerMinDeltas10_20 VARCHAR,
                    ally_top_goldPerMinDeltas20_30 VARCHAR,
                    ally_top_goldPerMinDeltas30_end VARCHAR,
                    ally_top_csDiffPerMinDeltas0_10 VARCHAR,
                    ally_top_csDiffPerMinDeltas10_20 VARCHAR,
                    ally_top_csDiffPerMinDeltas20_30 VARCHAR,
                    ally_top_csDiffPerMinDeltas30_end VARCHAR,
                    ally_top_xpDiffPerMinDeltas0_10 VARCHAR,
                    ally_top_xpDiffPerMinDeltas10_20 VARCHAR,
                    ally_top_xpDiffPerMinDeltas20_30 VARCHAR,
                    ally_top_xpDiffPerMinDeltas30_end VARCHAR,
                    ally_top_damageTakenPerMinDeltas0_10 VARCHAR,
                    ally_top_damageTakenPerMinDeltas10_20 VARCHAR,
                    ally_top_damageTakenPerMinDeltas20_30 VARCHAR,
                    ally_top_damageTakenPerMinDeltas30_end VARCHAR,
                    ally_top_damageTakenDiffPerMinDeltas0_10 VARCHAR,
                    ally_top_damageTakenDiffPerMinDeltas10_20 VARCHAR,
                    ally_top_damageTakenDiffPerMinDeltas20_30 VARCHAR,
                    ally_top_damageTakenDiffPerMinDeltas30_end VARCHAR,
                        ally_jng_longestTimeSpentLiving VARCHAR,
                        ally_jng_totalDamageDealt VARCHAR,
                        ally_jng_magicDamageDealt VARCHAR,
                        ally_jng_physicalDamageDealt VARCHAR,
                        ally_jng_trueDamageDealt VARCHAR,
                        ally_jng_totalDamageDealtToChampions VARCHAR,
                        ally_jng_magicDamageDealtToChampions VARCHAR,
                        ally_jng_physicalDamageDealtToChampions VARCHAR,
                        ally_jng_trueDamageDealtToChampions VARCHAR,
                        ally_jng_totalHeal VARCHAR,
                        ally_jng_totalDamageTaken VARCHAR,
                        ally_jng_magicalDamageTaken VARCHAR,
                        ally_jng_physicalDamageTaken VARCHAR,
                        ally_jng_trueDamageTaken VARCHAR,
                        ally_jng_goldEarned VARCHAR,
                        ally_jng_totalMinionsKilled VARCHAR,
                        ally_jng_neutralMinionsKilled VARCHAR,
                        ally_jng_neutralMinionsKilledTeamJungle VARCHAR,
                        ally_jng_neutralMinionsKilledEnemyJungle VARCHAR,
                        ally_jng_totalTimeCrowdControlDealt VARCHAR,
                        ally_jng_wardsPlaced VARCHAR,
                        ally_jng_wardsKilled VARCHAR,
                    ally_jng_creepsPerMinDeltas0_10 VARCHAR,
                    ally_jng_creepsPerMinDeltas10_20 VARCHAR,
                    ally_jng_creepsPerMinDeltas20_30 VARCHAR,
                    ally_jng_creepsPerMinDeltas30_end VARCHAR,
                    ally_jng_xpPerMinDeltas0_10 VARCHAR,
                    ally_jng_xpPerMinDeltas10_20 VARCHAR,
                    ally_jng_xpPerMinDeltas20_30 VARCHAR,
                    ally_jng_xpPerMinDeltas30_end VARCHAR,
                    ally_jng_goldPerMinDeltas0_10 VARCHAR,
                    ally_jng_goldPerMinDeltas10_20 VARCHAR,
                    ally_jng_goldPerMinDeltas20_30 VARCHAR,
                    ally_jng_goldPerMinDeltas30_end VARCHAR,
                    ally_jng_csDiffPerMinDeltas0_10 VARCHAR,
                    ally_jng_csDiffPerMinDeltas10_20 VARCHAR,
                    ally_jng_csDiffPerMinDeltas20_30 VARCHAR,
                    ally_jng_csDiffPerMinDeltas30_end VARCHAR,
                    ally_jng_xpDiffPerMinDeltas0_10 VARCHAR,
                    ally_jng_xpDiffPerMinDeltas10_20 VARCHAR,
                    ally_jng_xpDiffPerMinDeltas20_30 VARCHAR,
                    ally_jng_xpDiffPerMinDeltas30_end VARCHAR,
                    ally_jng_damageTakenPerMinDeltas0_10 VARCHAR,
                    ally_jng_damageTakenPerMinDeltas10_20 VARCHAR,
                    ally_jng_damageTakenPerMinDeltas20_30 VARCHAR,
                    ally_jng_damageTakenPerMinDeltas30_end VARCHAR,
                    ally_jng_damageTakenDiffPerMinDeltas0_10 VARCHAR,
                    ally_jng_damageTakenDiffPerMinDeltas10_20 VARCHAR,
                    ally_jng_damageTakenDiffPerMinDeltas20_30 VARCHAR,
                    ally_jng_damageTakenDiffPerMinDeltas30_end VARCHAR,                 
                        ally_mid_longestTimeSpentLiving VARCHAR,
                        ally_mid_totalDamageDealt VARCHAR,
                        ally_mid_magicDamageDealt VARCHAR,
                        ally_mid_physicalDamageDealt VARCHAR,
                        ally_mid_trueDamageDealt VARCHAR,
                        ally_mid_totalDamageDealtToChampions VARCHAR,
                        ally_mid_magicDamageDealtToChampions VARCHAR,
                        ally_mid_physicalDamageDealtToChampions VARCHAR,
                        ally_mid_trueDamageDealtToChampions VARCHAR,
                        ally_mid_totalHeal VARCHAR,
                        ally_mid_totalDamageTaken VARCHAR,
                        ally_mid_magicalDamageTaken VARCHAR,
                        ally_mid_physicalDamageTaken VARCHAR,
                        ally_mid_trueDamageTaken VARCHAR,
                        ally_mid_goldEarned VARCHAR,
                        ally_mid_totalMinionsKilled VARCHAR,
                        ally_mid_neutralMinionsKilled VARCHAR,
                        ally_mid_neutralMinionsKilledTeamJungle VARCHAR,
                        ally_mid_neutralMinionsKilledEnemyJungle VARCHAR,
                        ally_mid_totalTimeCrowdControlDealt VARCHAR,
                        ally_mid_wardsPlaced VARCHAR,
                        ally_mid_wardsKilled VARCHAR,
                    ally_mid_creepsPerMinDeltas0_10 VARCHAR,
                    ally_mid_creepsPerMinDeltas10_20 VARCHAR,
                    ally_mid_creepsPerMinDeltas20_30 VARCHAR,
                    ally_mid_creepsPerMinDeltas30_end VARCHAR,
                    ally_mid_xpPerMinDeltas0_10 VARCHAR,
                    ally_mid_xpPerMinDeltas10_20 VARCHAR,
                    ally_mid_xpPerMinDeltas20_30 VARCHAR,
                    ally_mid_xpPerMinDeltas30_end VARCHAR,
                    ally_mid_goldPerMinDeltas0_10 VARCHAR,
                    ally_mid_goldPerMinDeltas10_20 VARCHAR,
                    ally_mid_goldPerMinDeltas20_30 VARCHAR,
                    ally_mid_goldPerMinDeltas30_end VARCHAR,
                    ally_mid_csDiffPerMinDeltas0_10 VARCHAR,
                    ally_mid_csDiffPerMinDeltas10_20 VARCHAR,
                    ally_mid_csDiffPerMinDeltas20_30 VARCHAR,
                    ally_mid_csDiffPerMinDeltas30_end VARCHAR,
                    ally_mid_xpDiffPerMinDeltas0_10 VARCHAR,
                    ally_mid_xpDiffPerMinDeltas10_20 VARCHAR,
                    ally_mid_xpDiffPerMinDeltas20_30 VARCHAR,
                    ally_mid_xpDiffPerMinDeltas30_end VARCHAR,
                    ally_mid_damageTakenPerMinDeltas0_10 VARCHAR,
                    ally_mid_damageTakenPerMinDeltas10_20 VARCHAR,
                    ally_mid_damageTakenPerMinDeltas20_30 VARCHAR,
                    ally_mid_damageTakenPerMinDeltas30_end VARCHAR,
                    ally_mid_damageTakenDiffPerMinDeltas0_10 VARCHAR,
                    ally_mid_damageTakenDiffPerMinDeltas10_20 VARCHAR,
                    ally_mid_damageTakenDiffPerMinDeltas20_30 VARCHAR,
                    ally_mid_damageTakenDiffPerMinDeltas30_end VARCHAR,
                        ally_adc_longestTimeSpentLiving VARCHAR,
                        ally_adc_totalDamageDealt VARCHAR,
                        ally_adc_magicDamageDealt VARCHAR,
                        ally_adc_physicalDamageDealt VARCHAR,
                        ally_adc_trueDamageDealt VARCHAR,
                        ally_adc_totalDamageDealtToChampions VARCHAR,
                        ally_adc_magicDamageDealtToChampions VARCHAR,
                        ally_adc_physicalDamageDealtToChampions VARCHAR,
                        ally_adc_trueDamageDealtToChampions VARCHAR,
                        ally_adc_totalHeal VARCHAR,
                        ally_adc_totalDamageTaken VARCHAR,
                        ally_adc_magicalDamageTaken VARCHAR,
                        ally_adc_physicalDamageTaken VARCHAR,
                        ally_adc_trueDamageTaken VARCHAR,
                        ally_adc_goldEarned VARCHAR,
                        ally_adc_totalMinionsKilled VARCHAR,
                        ally_adc_neutralMinionsKilled VARCHAR,
                        ally_adc_neutralMinionsKilledTeamJungle VARCHAR,
                        ally_adc_neutralMinionsKilledEnemyJungle VARCHAR,
                        ally_adc_totalTimeCrowdControlDealt VARCHAR,
                        ally_adc_wardsPlaced VARCHAR,
                        ally_adc_wardsKilled VARCHAR,
                    ally_adc_creepsPerMinDeltas0_10 VARCHAR,
                    ally_adc_creepsPerMinDeltas10_20 VARCHAR,
                    ally_adc_creepsPerMinDeltas20_30 VARCHAR,
                    ally_adc_creepsPerMinDeltas30_end VARCHAR,
                    ally_adc_xpPerMinDeltas0_10 VARCHAR,
                    ally_adc_xpPerMinDeltas10_20 VARCHAR,
                    ally_adc_xpPerMinDeltas20_30 VARCHAR,
                    ally_adc_xpPerMinDeltas30_end VARCHAR,
                    ally_adc_goldPerMinDeltas0_10 VARCHAR,
                    ally_adc_goldPerMinDeltas10_20 VARCHAR,
                    ally_adc_goldPerMinDeltas20_30 VARCHAR,
                    ally_adc_goldPerMinDeltas30_end VARCHAR,
                    ally_adc_csDiffPerMinDeltas0_10 VARCHAR,
                    ally_adc_csDiffPerMinDeltas10_20 VARCHAR,
                    ally_adc_csDiffPerMinDeltas20_30 VARCHAR,
                    ally_adc_csDiffPerMinDeltas30_end VARCHAR,
                    ally_adc_xpDiffPerMinDeltas0_10 VARCHAR,
                    ally_adc_xpDiffPerMinDeltas10_20 VARCHAR,
                    ally_adc_xpDiffPerMinDeltas20_30 VARCHAR,
                    ally_adc_xpDiffPerMinDeltas30_end VARCHAR,
                    ally_adc_damageTakenPerMinDeltas0_10 VARCHAR,
                    ally_adc_damageTakenPerMinDeltas10_20 VARCHAR,
                    ally_adc_damageTakenPerMinDeltas20_30 VARCHAR,
                    ally_adc_damageTakenPerMinDeltas30_end VARCHAR,
                    ally_adc_damageTakenDiffPerMinDeltas0_10 VARCHAR,
                    ally_adc_damageTakenDiffPerMinDeltas10_20 VARCHAR,
                    ally_adc_damageTakenDiffPerMinDeltas20_30 VARCHAR,
                    ally_adc_damageTakenDiffPerMinDeltas30_end VARCHAR,
                        ally_sup_longestTimeSpentLiving VARCHAR,
                        ally_sup_totalDamageDealt VARCHAR,
                        ally_sup_magicDamageDealt VARCHAR,
                        ally_sup_physicalDamageDealt VARCHAR,
                        ally_sup_trueDamageDealt VARCHAR,
                        ally_sup_totalDamageDealtToChampions VARCHAR,
                        ally_sup_magicDamageDealtToChampions VARCHAR,
                        ally_sup_physicalDamageDealtToChampions VARCHAR,
                        ally_sup_trueDamageDealtToChampions VARCHAR,
                        ally_sup_totalHeal VARCHAR,
                        ally_sup_totalDamageTaken VARCHAR,
                        ally_sup_magicalDamageTaken VARCHAR,
                        ally_sup_physicalDamageTaken VARCHAR,
                        ally_sup_trueDamageTaken VARCHAR,
                        ally_sup_goldEarned VARCHAR,
                        ally_sup_totalMinionsKilled VARCHAR,
                        ally_sup_neutralMinionsKilled VARCHAR,
                        ally_sup_neutralMinionsKilledTeamJungle VARCHAR,
                        ally_sup_neutralMinionsKilledEnemyJungle VARCHAR,
                        ally_sup_totalTimeCrowdControlDealt VARCHAR,
                        ally_sup_wardsPlaced VARCHAR,
                        ally_sup_wardsKilled VARCHAR,
                    ally_sup_creepsPerMinDeltas0_10 VARCHAR,
                    ally_sup_creepsPerMinDeltas10_20 VARCHAR,
                    ally_sup_creepsPerMinDeltas20_30 VARCHAR,
                    ally_sup_creepsPerMinDeltas30_end VARCHAR,
                    ally_sup_xpPerMinDeltas0_10 VARCHAR,
                    ally_sup_xpPerMinDeltas10_20 VARCHAR,
                    ally_sup_xpPerMinDeltas20_30 VARCHAR,
                    ally_sup_xpPerMinDeltas30_end VARCHAR,
                    ally_sup_goldPerMinDeltas0_10 VARCHAR,
                    ally_sup_goldPerMinDeltas10_20 VARCHAR,
                    ally_sup_goldPerMinDeltas20_30 VARCHAR,
                    ally_sup_goldPerMinDeltas30_end VARCHAR,
                    ally_sup_csDiffPerMinDeltas0_10 VARCHAR,
                    ally_sup_csDiffPerMinDeltas10_20 VARCHAR,
                    ally_sup_csDiffPerMinDeltas20_30 VARCHAR,
                    ally_sup_csDiffPerMinDeltas30_end VARCHAR,
                    ally_sup_xpDiffPerMinDeltas0_10 VARCHAR,
                    ally_sup_xpDiffPerMinDeltas10_20 VARCHAR,
                    ally_sup_xpDiffPerMinDeltas20_30 VARCHAR,
                    ally_sup_xpDiffPerMinDeltas30_end VARCHAR,
                    ally_sup_damageTakenPerMinDeltas0_10 VARCHAR,
                    ally_sup_damageTakenPerMinDeltas10_20 VARCHAR,
                    ally_sup_damageTakenPerMinDeltas20_30 VARCHAR,
                    ally_sup_damageTakenPerMinDeltas30_end VARCHAR,
                    ally_sup_damageTakenDiffPerMinDeltas0_10 VARCHAR,
                    ally_sup_damageTakenDiffPerMinDeltas10_20 VARCHAR,
                    ally_sup_damageTakenDiffPerMinDeltas20_30 VARCHAR,
                    ally_sup_damageTakenDiffPerMinDeltas30_end VARCHAR,
                        enemy_top_longestTimeSpentLiving VARCHAR,
                        enemy_top_totalDamageDealt VARCHAR,
                        enemy_top_magicDamageDealt VARCHAR,
                        enemy_top_physicalDamageDealt VARCHAR,
                        enemy_top_trueDamageDealt VARCHAR,
                        enemy_top_totalDamageDealtToChampions VARCHAR,
                        enemy_top_magicDamageDealtToChampions VARCHAR,
                        enemy_top_physicalDamageDealtToChampions VARCHAR,
                        enemy_top_trueDamageDealtToChampions VARCHAR,
                        enemy_top_totalHeal VARCHAR,
                        enemy_top_totalDamageTaken VARCHAR,
                        enemy_top_magicalDamageTaken VARCHAR,
                        enemy_top_physicalDamageTaken VARCHAR,
                        enemy_top_trueDamageTaken VARCHAR,
                        enemy_top_goldEarned VARCHAR,
                        enemy_top_totalMinionsKilled VARCHAR,
                        enemy_top_neutralMinionsKilled VARCHAR,
                        enemy_top_neutralMinionsKilledTeamJungle VARCHAR,
                        enemy_top_neutralMinionsKilledEnemyJungle VARCHAR,
                        enemy_top_totalTimeCrowdControlDealt VARCHAR,
                        enemy_top_wardsPlaced VARCHAR,
                        enemy_top_wardsKilled VARCHAR,
                    enemy_top_creepsPerMinDeltas0_10 VARCHAR,
                    enemy_top_creepsPerMinDeltas10_20 VARCHAR,
                    enemy_top_creepsPerMinDeltas20_30 VARCHAR,
                    enemy_top_creepsPerMinDeltas30_end VARCHAR,
                    enemy_top_xpPerMinDeltas0_10 VARCHAR,
                    enemy_top_xpPerMinDeltas10_20 VARCHAR,
                    enemy_top_xpPerMinDeltas20_30 VARCHAR,
                    enemy_top_xpPerMinDeltas30_end VARCHAR,
                    enemy_top_goldPerMinDeltas0_10 VARCHAR,
                    enemy_top_goldPerMinDeltas10_20 VARCHAR,
                    enemy_top_goldPerMinDeltas20_30 VARCHAR,
                    enemy_top_goldPerMinDeltas30_end VARCHAR,
                    enemy_top_csDiffPerMinDeltas0_10 VARCHAR,
                    enemy_top_csDiffPerMinDeltas10_20 VARCHAR,
                    enemy_top_csDiffPerMinDeltas20_30 VARCHAR,
                    enemy_top_csDiffPerMinDeltas30_end VARCHAR,
                    enemy_top_xpDiffPerMinDeltas0_10 VARCHAR,
                    enemy_top_xpDiffPerMinDeltas10_20 VARCHAR,
                    enemy_top_xpDiffPerMinDeltas20_30 VARCHAR,
                    enemy_top_xpDiffPerMinDeltas30_end VARCHAR,
                    enemy_top_damageTakenPerMinDeltas0_10 VARCHAR,
                    enemy_top_damageTakenPerMinDeltas10_20 VARCHAR,
                    enemy_top_damageTakenPerMinDeltas20_30 VARCHAR,
                    enemy_top_damageTakenPerMinDeltas30_end VARCHAR,
                    enemy_top_damageTakenDiffPerMinDeltas0_10 VARCHAR,
                    enemy_top_damageTakenDiffPerMinDeltas10_20 VARCHAR,
                    enemy_top_damageTakenDiffPerMinDeltas20_30 VARCHAR,
                    enemy_top_damageTakenDiffPerMinDeltas30_end VARCHAR,
                        enemy_jng_longestTimeSpentLiving VARCHAR,
                        enemy_jng_totalDamageDealt VARCHAR,
                        enemy_jng_magicDamageDealt VARCHAR,
                        enemy_jng_physicalDamageDealt VARCHAR,
                        enemy_jng_trueDamageDealt VARCHAR,
                        enemy_jng_totalDamageDealtToChampions VARCHAR,
                        enemy_jng_magicDamageDealtToChampions VARCHAR,
                        enemy_jng_physicalDamageDealtToChampions VARCHAR,
                        enemy_jng_trueDamageDealtToChampions VARCHAR,
                        enemy_jng_totalHeal VARCHAR,
                        enemy_jng_totalDamageTaken VARCHAR,
                        enemy_jng_magicalDamageTaken VARCHAR,
                        enemy_jng_physicalDamageTaken VARCHAR,
                        enemy_jng_trueDamageTaken VARCHAR,
                        enemy_jng_goldEarned VARCHAR,
                        enemy_jng_totalMinionsKilled VARCHAR,
                        enemy_jng_neutralMinionsKilled VARCHAR,
                        enemy_jng_neutralMinionsKilledTeamJungle VARCHAR,
                        enemy_jng_neutralMinionsKilledEnemyJungle VARCHAR,
                        enemy_jng_totalTimeCrowdControlDealt VARCHAR,
                        enemy_jng_wardsPlaced VARCHAR,
                        enemy_jng_wardsKilled VARCHAR,
                    enemy_jng_creepsPerMinDeltas0_10 VARCHAR,
                    enemy_jng_creepsPerMinDeltas10_20 VARCHAR,
                    enemy_jng_creepsPerMinDeltas20_30 VARCHAR,
                    enemy_jng_creepsPerMinDeltas30_end VARCHAR,
                    enemy_jng_xpPerMinDeltas0_10 VARCHAR,
                    enemy_jng_xpPerMinDeltas10_20 VARCHAR,
                    enemy_jng_xpPerMinDeltas20_30 VARCHAR,
                    enemy_jng_xpPerMinDeltas30_end VARCHAR,
                    enemy_jng_goldPerMinDeltas0_10 VARCHAR,
                    enemy_jng_goldPerMinDeltas10_20 VARCHAR,
                    enemy_jng_goldPerMinDeltas20_30 VARCHAR,
                    enemy_jng_goldPerMinDeltas30_end VARCHAR,
                    enemy_jng_csDiffPerMinDeltas0_10 VARCHAR,
                    enemy_jng_csDiffPerMinDeltas10_20 VARCHAR,
                    enemy_jng_csDiffPerMinDeltas20_30 VARCHAR,
                    enemy_jng_csDiffPerMinDeltas30_end VARCHAR,
                    enemy_jng_xpDiffPerMinDeltas0_10 VARCHAR,
                    enemy_jng_xpDiffPerMinDeltas10_20 VARCHAR,
                    enemy_jng_xpDiffPerMinDeltas20_30 VARCHAR,
                    enemy_jng_xpDiffPerMinDeltas30_end VARCHAR,
                    enemy_jng_damageTakenPerMinDeltas0_10 VARCHAR,
                    enemy_jng_damageTakenPerMinDeltas10_20 VARCHAR,
                    enemy_jng_damageTakenPerMinDeltas20_30 VARCHAR,
                    enemy_jng_damageTakenPerMinDeltas30_end VARCHAR,
                    enemy_jng_damageTakenDiffPerMinDeltas0_10 VARCHAR,
                    enemy_jng_damageTakenDiffPerMinDeltas10_20 VARCHAR,
                    enemy_jng_damageTakenDiffPerMinDeltas20_30 VARCHAR,
                    enemy_jng_damageTakenDiffPerMinDeltas30_end VARCHAR,
                        enemy_mid_longestTimeSpentLiving VARCHAR,
                        enemy_mid_totalDamageDealt VARCHAR,
                        enemy_mid_magicDamageDealt VARCHAR,
                        enemy_mid_physicalDamageDealt VARCHAR,
                        enemy_mid_trueDamageDealt VARCHAR,
                        enemy_mid_totalDamageDealtToChampions VARCHAR,
                        enemy_mid_magicDamageDealtToChampions VARCHAR,
                        enemy_mid_physicalDamageDealtToChampions VARCHAR,
                        enemy_mid_trueDamageDealtToChampions VARCHAR,
                        enemy_mid_totalHeal VARCHAR,
                        enemy_mid_totalDamageTaken VARCHAR,
                        enemy_mid_magicalDamageTaken VARCHAR,
                        enemy_mid_physicalDamageTaken VARCHAR,
                        enemy_mid_trueDamageTaken VARCHAR,
                        enemy_mid_goldEarned VARCHAR,
                        enemy_mid_totalMinionsKilled VARCHAR,
                        enemy_mid_neutralMinionsKilled VARCHAR,
                        enemy_mid_neutralMinionsKilledTeamJungle VARCHAR,
                        enemy_mid_neutralMinionsKilledEnemyJungle VARCHAR,
                        enemy_mid_totalTimeCrowdControlDealt VARCHAR,
                        enemy_mid_wardsPlaced VARCHAR,
                        enemy_mid_wardsKilled VARCHAR,
                    enemy_mid_creepsPerMinDeltas0_10 VARCHAR,
                    enemy_mid_creepsPerMinDeltas10_20 VARCHAR,
                    enemy_mid_creepsPerMinDeltas20_30 VARCHAR,
                    enemy_mid_creepsPerMinDeltas30_end VARCHAR,
                    enemy_mid_xpPerMinDeltas0_10 VARCHAR,
                    enemy_mid_xpPerMinDeltas10_20 VARCHAR,
                    enemy_mid_xpPerMinDeltas20_30 VARCHAR,
                    enemy_mid_xpPerMinDeltas30_end VARCHAR,
                    enemy_mid_goldPerMinDeltas0_10 VARCHAR,
                    enemy_mid_goldPerMinDeltas10_20 VARCHAR,
                    enemy_mid_goldPerMinDeltas20_30 VARCHAR,
                    enemy_mid_goldPerMinDeltas30_end VARCHAR,
                    enemy_mid_csDiffPerMinDeltas0_10 VARCHAR,
                    enemy_mid_csDiffPerMinDeltas10_20 VARCHAR,
                    enemy_mid_csDiffPerMinDeltas20_30 VARCHAR,
                    enemy_mid_csDiffPerMinDeltas30_end VARCHAR,
                    enemy_mid_xpDiffPerMinDeltas0_10 VARCHAR,
                    enemy_mid_xpDiffPerMinDeltas10_20 VARCHAR,
                    enemy_mid_xpDiffPerMinDeltas20_30 VARCHAR,
                    enemy_mid_xpDiffPerMinDeltas30_end VARCHAR,
                    enemy_mid_damageTakenPerMinDeltas0_10 VARCHAR,
                    enemy_mid_damageTakenPerMinDeltas10_20 VARCHAR,
                    enemy_mid_damageTakenPerMinDeltas20_30 VARCHAR,
                    enemy_mid_damageTakenPerMinDeltas30_end VARCHAR,
                    enemy_mid_damageTakenDiffPerMinDeltas0_10 VARCHAR,
                    enemy_mid_damageTakenDiffPerMinDeltas10_20 VARCHAR,
                    enemy_mid_damageTakenDiffPerMinDeltas20_30 VARCHAR,
                    enemy_mid_damageTakenDiffPerMinDeltas30_end VARCHAR,
                        enemy_adc_longestTimeSpentLiving VARCHAR,
                        enemy_adc_totalDamageDealt VARCHAR,
                        enemy_adc_magicDamageDealt VARCHAR,
                        enemy_adc_physicalDamageDealt VARCHAR,
                        enemy_adc_trueDamageDealt VARCHAR,
                        enemy_adc_totalDamageDealtToChampions VARCHAR,
                        enemy_adc_magicDamageDealtToChampions VARCHAR,
                        enemy_adc_physicalDamageDealtToChampions VARCHAR,
                        enemy_adc_trueDamageDealtToChampions VARCHAR,
                        enemy_adc_totalHeal VARCHAR,
                        enemy_adc_totalDamageTaken VARCHAR,
                        enemy_adc_magicalDamageTaken VARCHAR,
                        enemy_adc_physicalDamageTaken VARCHAR,
                        enemy_adc_trueDamageTaken VARCHAR,
                        enemy_adc_goldEarned VARCHAR,
                        enemy_adc_totalMinionsKilled VARCHAR,
                        enemy_adc_neutralMinionsKilled VARCHAR,
                        enemy_adc_neutralMinionsKilledTeamJungle VARCHAR,
                        enemy_adc_neutralMinionsKilledEnemyJungle VARCHAR,
                        enemy_adc_totalTimeCrowdControlDealt VARCHAR,
                        enemy_adc_wardsPlaced VARCHAR,
                        enemy_adc_wardsKilled VARCHAR,
                    enemy_adc_creepsPerMinDeltas0_10 VARCHAR,
                    enemy_adc_creepsPerMinDeltas10_20 VARCHAR,
                    enemy_adc_creepsPerMinDeltas20_30 VARCHAR,
                    enemy_adc_creepsPerMinDeltas30_end VARCHAR,
                    enemy_adc_xpPerMinDeltas0_10 VARCHAR,
                    enemy_adc_xpPerMinDeltas10_20 VARCHAR,
                    enemy_adc_xpPerMinDeltas20_30 VARCHAR,
                    enemy_adc_xpPerMinDeltas30_end VARCHAR,
                    enemy_adc_goldPerMinDeltas0_10 VARCHAR,
                    enemy_adc_goldPerMinDeltas10_20 VARCHAR,
                    enemy_adc_goldPerMinDeltas20_30 VARCHAR,
                    enemy_adc_goldPerMinDeltas30_end VARCHAR,
                    enemy_adc_csDiffPerMinDeltas0_10 VARCHAR,
                    enemy_adc_csDiffPerMinDeltas10_20 VARCHAR,
                    enemy_adc_csDiffPerMinDeltas20_30 VARCHAR,
                    enemy_adc_csDiffPerMinDeltas30_end VARCHAR,
                    enemy_adc_xpDiffPerMinDeltas0_10 VARCHAR,
                    enemy_adc_xpDiffPerMinDeltas10_20 VARCHAR,
                    enemy_adc_xpDiffPerMinDeltas20_30 VARCHAR,
                    enemy_adc_xpDiffPerMinDeltas30_end VARCHAR,
                    enemy_adc_damageTakenPerMinDeltas0_10 VARCHAR,
                    enemy_adc_damageTakenPerMinDeltas10_20 VARCHAR,
                    enemy_adc_damageTakenPerMinDeltas20_30 VARCHAR,
                    enemy_adc_damageTakenPerMinDeltas30_end VARCHAR,
                    enemy_adc_damageTakenDiffPerMinDeltas0_10 VARCHAR,
                    enemy_adc_damageTakenDiffPerMinDeltas10_20 VARCHAR,
                    enemy_adc_damageTakenDiffPerMinDeltas20_30 VARCHAR,
                    enemy_adc_damageTakenDiffPerMinDeltas30_end VARCHAR,
                        enemy_sup_longestTimeSpentLiving VARCHAR,
                        enemy_sup_totalDamageDealt VARCHAR,
                        enemy_sup_magicDamageDealt VARCHAR,
                        enemy_sup_physicalDamageDealt VARCHAR,
                        enemy_sup_trueDamageDealt VARCHAR,
                        enemy_sup_totalDamageDealtToChampions VARCHAR,
                        enemy_sup_magicDamageDealtToChampions VARCHAR,
                        enemy_sup_physicalDamageDealtToChampions VARCHAR,
                        enemy_sup_trueDamageDealtToChampions VARCHAR,
                        enemy_sup_totalHeal VARCHAR,
                        enemy_sup_totalDamageTaken VARCHAR,
                        enemy_sup_magicalDamageTaken VARCHAR,
                        enemy_sup_physicalDamageTaken VARCHAR,
                        enemy_sup_trueDamageTaken VARCHAR,
                        enemy_sup_goldEarned VARCHAR,
                        enemy_sup_totalMinionsKilled VARCHAR,
                        enemy_sup_neutralMinionsKilled VARCHAR,
                        enemy_sup_neutralMinionsKilledTeamJungle VARCHAR,
                        enemy_sup_neutralMinionsKilledEnemyJungle VARCHAR,
                        enemy_sup_totalTimeCrowdControlDealt VARCHAR,
                        enemy_sup_wardsPlaced VARCHAR,
                        enemy_sup_wardsKilled VARCHAR,
                    enemy_sup_creepsPerMinDeltas0_10 VARCHAR,
                    enemy_sup_creepsPerMinDeltas10_20 VARCHAR,
                    enemy_sup_creepsPerMinDeltas20_30 VARCHAR,
                    enemy_sup_creepsPerMinDeltas30_end VARCHAR,
                    enemy_sup_xpPerMinDeltas0_10 VARCHAR,
                    enemy_sup_xpPerMinDeltas10_20 VARCHAR,
                    enemy_sup_xpPerMinDeltas20_30 VARCHAR,
                    enemy_sup_xpPerMinDeltas30_end VARCHAR,
                    enemy_sup_goldPerMinDeltas0_10 VARCHAR,
                    enemy_sup_goldPerMinDeltas10_20 VARCHAR,
                    enemy_sup_goldPerMinDeltas20_30 VARCHAR,
                    enemy_sup_goldPerMinDeltas30_end VARCHAR,
                    enemy_sup_csDiffPerMinDeltas0_10 VARCHAR,
                    enemy_sup_csDiffPerMinDeltas10_20 VARCHAR,
                    enemy_sup_csDiffPerMinDeltas20_30 VARCHAR,
                    enemy_sup_csDiffPerMinDeltas30_end VARCHAR,
                    enemy_sup_xpDiffPerMinDeltas0_10 VARCHAR,
                    enemy_sup_xpDiffPerMinDeltas10_20 VARCHAR,
                    enemy_sup_xpDiffPerMinDeltas20_30 VARCHAR,
                    enemy_sup_xpDiffPerMinDeltas30_end VARCHAR,
                    enemy_sup_damageTakenPerMinDeltas0_10 VARCHAR,
                    enemy_sup_damageTakenPerMinDeltas10_20 VARCHAR,
                    enemy_sup_damageTakenPerMinDeltas20_30 VARCHAR,
                    enemy_sup_damageTakenPerMinDeltas30_end VARCHAR,
                    enemy_sup_damageTakenDiffPerMinDeltas0_10 VARCHAR,
                    enemy_sup_damageTakenDiffPerMinDeltas10_20 VARCHAR,
                    enemy_sup_damageTakenDiffPerMinDeltas20_30 VARCHAR,
                    enemy_sup_damageTakenDiffPerMinDeltas30_end VARCHAR)""")
            connect.commit()
            print('\nСоздание таблицы (matches_info_parsed)')
            cursor.execute('SELECT  (site_id) FROM matches_info_json')
            ids = ([int(str(elem).replace(",", "").replace(")", "").replace("(", "")) for elem in cursor.fetchall()])
        except sqlite3.OperationalError:
            print('\nТаблица существует (matches_info_parsed)')
            cursor.execute('SELECT  (site_id) FROM matches_info_json')
            ids = ([int(str(elem).replace(",", "").replace(")", "").replace("(", "")) for elem in cursor.fetchall()])
            cursor.execute('SELECT  MAX(site_id) FROM matches_info_parsed')
            old_ids = range(15915, 18048)
            for old_id in old_ids:
                try:
                    ids.remove(old_id)
                except ValueError:
                    list()
        for k in old_ids:
            both_teams = list()
            both_teams.append(k)  # site_id
            cursor.execute("SELECT match_info_html FROM matches_info_html WHERE site_id=?", (k,))
            match_info_soup = bs4.BeautifulSoup(cursor.fetchall()[0][0], 'html.parser')
            # print(match_info_soup.find_all('div', class_='col-xs-7')[0].text)
            if len(match_info_soup.find_all('table')) > 1 and \
                    match_info_soup.find_all('div', class_='col-xs-7')[0].text.split()[-1][1:-1] == 'CN' and \
                    match_info_soup.find_all('table')[1].find('tr').find_all('td')[1].find(
                        'span').text != '0:00' and len(match_info_soup.find_all('table')) > 1:
                both_teams.append(
                    match_info_soup.find_all('div', class_='col-xs-7 text-left')[0].find('a').text)  # championship
                both_teams.append(
                    match_info_soup.find_all('div', class_='col-xs-7 text-left')[0].text.split()[-1][1:-1])  # server
                both_teams.append(
                    match_info_soup.find_all('div', class_='col-xs-5 text-right')[0].text.split()[0])  # date
                both_teams.append(float(
                    match_info_soup.find_all('table')[1].find('tr').find_all('td')[2].text.strip()[1:]))  # version game
                both_teams.append(
                    match_info_soup.find_all('table')[1].find('tr').find_all('td')[1].find('span').text)  # time
                # print(both_teams)
                teams = {'blue': list(), 'red': list()}
                for team in teams:
                    teams[team].append(match_info_soup.find_all('table')[1].find_all('tr')[1].find('td',
                                                                                                   class_=team + "_line").text.strip())  # name
                    teams[team].append(
                        "true" if
                        re.findall('<.*?>', str(match_info_soup.find_all('table')[1].find('tr').find_all('td')[1]))[1][
                        1:4] == "img" and team == 'blue'
                        else "true" if
                        re.findall('<.*?>', str(match_info_soup.find_all('table')[1].find('tr').find_all('td')[1]))[1][
                        1:4] != "img" and team == 'red' else "false")
                    teams[team].append(team)
                    teams[team].append(match_info_soup.find_all('table')[1].find_all('tr')[1].find_all('td')[
                                           1 if team == 'blue' else 0].text.strip())
                    [teams[team].append(
                        'true' if match_info_soup.find_all('table')[1].find_all('tr')[2].find('td',
                                                                                              class_=team + "_line").find(
                            'img', alt='First ' + objective) is not None else 'false') for objective in
                        ['Blood', 'Tower']]  # fb ft

                    teams[team].append(re.sub('[\[\]\'\,]', '', str(
                        [re.findall('champions_icon\/([A-Za-z]{1,30})', str(col)) for col in
                         match_info_soup.find_all('table')[2].find_all('tr')[1].find_all('td', class_=team + "_line")])[
                                                                1:-1]))  # bans
                    teams[team].append(re.sub('[\[\]\'\,]', '', str(
                        [re.findall('champions_icon\/([A-Za-z]{1,30})', str(col)) for col in
                         match_info_soup.find_all('table')[2].find_all('tr')[1].find_all('td', class_=team + "_line")])[
                                                                1:-1]))  # bans
                    kills = [re.findall('([0-9]{1,3})\/', elem.find_all('td')[1 if team == 'blue' else -2].text)[0] for
                             elem in match_info_soup.find('td', class_=team + '_player_bar').find_all('tr')[1:]]
                    deaths = [re.findall('([0-9]{1,3})\/', elem.find_all('td')[1 if team == 'blue' else -2].text)[0] for
                              elem in match_info_soup.find('td', class_=team + '_player_bar').find_all('tr')[1:]]
                    for elem in range(0, 79):
                        teams[team].append(0)
                    for elem in kills:
                        kill_massiv = list()
                        for el in range(0, int(elem)):
                            kill_massiv.append(1)
                        teams[team].append(pickle.dumps(kill_massiv))
                        teams[team].append(0)
                        teams[team].append(0)
                    for elem in deaths:
                        kill_massiv = list()
                        for el in range(0, int(elem)):
                            kill_massiv.append(1)
                        teams[team].append(pickle.dumps(kill_massiv))
                        teams[team].append(0)
                        teams[team].append(0)
                    for elem in range(0, 508):
                        teams[team].append(0)

                # [print(sum([both_teams + teams[team]], [])) for team in teams]
                [cursor.execute('''
                    INSERT INTO matches_info_parsed (                    
                    site_id,
                    championship, 
                    server, 
                    match_date, 
                    game_patch, 
                    match_time, 
                    team, 
                    is_winner, 
                    side, 
                    enemy_team, 
                    first_blood,
                    first_tower,
                    bans,
                    top_nick, 
                    jungle_nick, 
                    mid_nick,
                    adc_nick,
                    sup_nick,
                    top_pick, 
                    jungle_pick, 
                    mid_pick, 
                    adc_pick, 
                    sup_pick,
                    top_cs, 
                    mid_cs, 
                    jungle_cs,  
                    bot_cs,  
                    sup_cs, 
                    enemy_top_cs, 
                    enemy_mid_cs, 
                    enemy_jungle_cs, 
                    enemy_bot_cs,  
                    enemy_sup_cs,
                    top_cs_jungle, 
                    mid_cs_jungle,
                    jungle_cs_jungle,
                    bot_cs_jungle,
                    sup_cs_jungle,
                    enemy_top_cs_jungle,
                    enemy_mid_cs_jungle, 
                    enemy_jungle_cs_jungle, 
                    enemy_bot_cs_jungle,  
                    enemy_sup_cs_jungle,
                    top_gold, 
                    mid_gold, 
                    jungle_gold,  
                    bot_gold,  
                    sup_gold, 
                    enemy_top_gold, 
                    enemy_mid_gold, 
                    enemy_jungle_gold, 
                    enemy_bot_gold, 
                    enemy_sup_gold,
                    top_xp, 
                    mid_xp, 
                    jungle_xp, 
                    bot_xp,  
                    sup_xp, 
                    enemy_top_xp, 
                    enemy_mid_xp, 
                    enemy_jungle_xp,
                    enemy_bot_xp,  
                    enemy_sup_xp,
                    top_lvl, 
                    mid_lvl, 
                    jungle_lvl,  
                    bot_lvl,  
                    sup_lvl, 
                    enemy_top_lvl, 
                    enemy_mid_lvl, 
                    enemy_jungle_lvl, 
                    enemy_bot_lvl,  
                    enemy_sup_lvl,
                    top_tower_get,
                    mid_tower_get,
                    bot_tower_get,
                    nexus_tower_get,
                    top_tower_lost,
                    mid_tower_lost,
                    bot_tower_lost,
                    nexus_tower_lost,
                    top_ingib_get,
                    mid_ingib_get,
                    bot_ingib_get,
                    top_ingib_lost,
                    mid_ingib_lost,
                    bot_ingib_lost,
                    dragon_get,
                    dragon_lost,
                    baron_get,
                    baron_lost,
                    herold_get,
                    herold_lost,
                    kill_top_ally,
                    death_top_ally,
                    assists_top_ally,
                    kill_jng_ally,
                    death_jng_ally,
                    assists_jng_ally,
                    kill_mid_ally,
                    death_mid_ally,
                    assists_mid_ally,
                    kill_adc_ally,
                    death_adc_ally,
                    assists_adc_ally,
                    kill_sup_ally,
                    death_sup_ally,
                    assists_sup_ally,
                    kill_top_enemy,
                    death_top_enemy,
                    assists_top_enemy,
                    kill_jng_enemy,
                    death_jng_enemy,
                    assists_jng_enemy,
                    kill_mid_enemy,
                    death_mid_enemy,
                    assists_mid_enemy,
                    kill_adc_enemy,
                    death_adc_enemy,
                    assists_adc_enemy,
                    kill_sup_enemy,
                    death_sup_enemy,
                    assists_sup_enemy,
                    simple_wards_ally, 
                    vision_wards_ally,
                    simple_wards_enemy, 
                    vision_wards_enemy,
                    kill_simple_wards_ally, 
                    kill_vision_wards_ally,
                    kill_simple_wards_enemy, 
                    kill_vision_wards_enemy,
                    ally_top_longestTimeSpentLiving,
                    ally_top_totalDamageDealt,
                    ally_top_magicDamageDealt,
                    ally_top_physicalDamageDealt,
                    ally_top_trueDamageDealt,
                    ally_top_totalDamageDealtToChampions,
                    ally_top_magicDamageDealtToChampions,
                    ally_top_physicalDamageDealtToChampions,
                    ally_top_trueDamageDealtToChampions,
                    ally_top_totalHeal,
                    ally_top_totalDamageTaken,
                    ally_top_magicalDamageTaken,
                    ally_top_physicalDamageTaken,
                    ally_top_trueDamageTaken,
                    ally_top_goldEarned,
                    ally_top_totalMinionsKilled,
                    ally_top_neutralMinionsKilled,
                    ally_top_neutralMinionsKilledTeamJungle,
                    ally_top_neutralMinionsKilledEnemyJungle,
                    ally_top_totalTimeCrowdControlDealt,
                    ally_top_wardsPlaced,
                    ally_top_wardsKilled,
                ally_top_creepsPerMinDeltas0_10,
                ally_top_creepsPerMinDeltas10_20,
                ally_top_creepsPerMinDeltas20_30,
                ally_top_creepsPerMinDeltas30_end,
                ally_top_xpPerMinDeltas0_10,
                ally_top_xpPerMinDeltas10_20,
                ally_top_xpPerMinDeltas20_30,
                ally_top_xpPerMinDeltas30_end,
                ally_top_goldPerMinDeltas0_10,
                ally_top_goldPerMinDeltas10_20,
                ally_top_goldPerMinDeltas20_30,
                ally_top_goldPerMinDeltas30_end,
                ally_top_csDiffPerMinDeltas0_10,
                ally_top_csDiffPerMinDeltas10_20,
                ally_top_csDiffPerMinDeltas20_30,
                ally_top_csDiffPerMinDeltas30_end,
                ally_top_xpDiffPerMinDeltas0_10,
                ally_top_xpDiffPerMinDeltas10_20,
                ally_top_xpDiffPerMinDeltas20_30,
                ally_top_xpDiffPerMinDeltas30_end,
                ally_top_damageTakenPerMinDeltas0_10,
                ally_top_damageTakenPerMinDeltas10_20,
                ally_top_damageTakenPerMinDeltas20_30,
                ally_top_damageTakenPerMinDeltas30_end,
                ally_top_damageTakenDiffPerMinDeltas0_10,
                ally_top_damageTakenDiffPerMinDeltas10_20,
                ally_top_damageTakenDiffPerMinDeltas20_30,
                ally_top_damageTakenDiffPerMinDeltas30_end,
                    ally_jng_longestTimeSpentLiving,
                    ally_jng_totalDamageDealt,
                    ally_jng_magicDamageDealt,
                    ally_jng_physicalDamageDealt,
                    ally_jng_trueDamageDealt,
                    ally_jng_totalDamageDealtToChampions,
                    ally_jng_magicDamageDealtToChampions,
                    ally_jng_physicalDamageDealtToChampions,
                    ally_jng_trueDamageDealtToChampions,
                    ally_jng_totalHeal,
                    ally_jng_totalDamageTaken,
                    ally_jng_magicalDamageTaken,
                    ally_jng_physicalDamageTaken,
                    ally_jng_trueDamageTaken,
                    ally_jng_goldEarned,
                    ally_jng_totalMinionsKilled,
                    ally_jng_neutralMinionsKilled,
                    ally_jng_neutralMinionsKilledTeamJungle,
                    ally_jng_neutralMinionsKilledEnemyJungle,
                    ally_jng_totalTimeCrowdControlDealt,
                    ally_jng_wardsPlaced,
                    ally_jng_wardsKilled,
                ally_jng_creepsPerMinDeltas0_10,
                ally_jng_creepsPerMinDeltas10_20,
                ally_jng_creepsPerMinDeltas20_30,
                ally_jng_creepsPerMinDeltas30_end,
                ally_jng_xpPerMinDeltas0_10,
                ally_jng_xpPerMinDeltas10_20,
                ally_jng_xpPerMinDeltas20_30,
                ally_jng_xpPerMinDeltas30_end,
                ally_jng_goldPerMinDeltas0_10,
                ally_jng_goldPerMinDeltas10_20,
                ally_jng_goldPerMinDeltas20_30,
                ally_jng_goldPerMinDeltas30_end,
                ally_jng_csDiffPerMinDeltas0_10,
                ally_jng_csDiffPerMinDeltas10_20,
                ally_jng_csDiffPerMinDeltas20_30,
                ally_jng_csDiffPerMinDeltas30_end,
                ally_jng_xpDiffPerMinDeltas0_10,
                ally_jng_xpDiffPerMinDeltas10_20,
                ally_jng_xpDiffPerMinDeltas20_30,
                ally_jng_xpDiffPerMinDeltas30_end,
                ally_jng_damageTakenPerMinDeltas0_10,
                ally_jng_damageTakenPerMinDeltas10_20,
                ally_jng_damageTakenPerMinDeltas20_30,
                ally_jng_damageTakenPerMinDeltas30_end,
                ally_jng_damageTakenDiffPerMinDeltas0_10,
                ally_jng_damageTakenDiffPerMinDeltas10_20,
                ally_jng_damageTakenDiffPerMinDeltas20_30,
                ally_jng_damageTakenDiffPerMinDeltas30_end,                 
                    ally_mid_longestTimeSpentLiving,
                    ally_mid_totalDamageDealt,
                    ally_mid_magicDamageDealt,
                    ally_mid_physicalDamageDealt,
                    ally_mid_trueDamageDealt,
                    ally_mid_totalDamageDealtToChampions,
                    ally_mid_magicDamageDealtToChampions,
                    ally_mid_physicalDamageDealtToChampions,
                    ally_mid_trueDamageDealtToChampions,
                    ally_mid_totalHeal,
                    ally_mid_totalDamageTaken,
                    ally_mid_magicalDamageTaken,
                    ally_mid_physicalDamageTaken,
                    ally_mid_trueDamageTaken,
                    ally_mid_goldEarned,
                    ally_mid_totalMinionsKilled,
                    ally_mid_neutralMinionsKilled,
                    ally_mid_neutralMinionsKilledTeamJungle,
                    ally_mid_neutralMinionsKilledEnemyJungle,
                    ally_mid_totalTimeCrowdControlDealt,
                    ally_mid_wardsPlaced,
                    ally_mid_wardsKilled,
                ally_mid_creepsPerMinDeltas0_10,
                ally_mid_creepsPerMinDeltas10_20,
                ally_mid_creepsPerMinDeltas20_30,
                ally_mid_creepsPerMinDeltas30_end,
                ally_mid_xpPerMinDeltas0_10,
                ally_mid_xpPerMinDeltas10_20,
                ally_mid_xpPerMinDeltas20_30,
                ally_mid_xpPerMinDeltas30_end,
                ally_mid_goldPerMinDeltas0_10,
                ally_mid_goldPerMinDeltas10_20,
                ally_mid_goldPerMinDeltas20_30,
                ally_mid_goldPerMinDeltas30_end,
                ally_mid_csDiffPerMinDeltas0_10,
                ally_mid_csDiffPerMinDeltas10_20,
                ally_mid_csDiffPerMinDeltas20_30,
                ally_mid_csDiffPerMinDeltas30_end,
                ally_mid_xpDiffPerMinDeltas0_10,
                ally_mid_xpDiffPerMinDeltas10_20,
                ally_mid_xpDiffPerMinDeltas20_30,
                ally_mid_xpDiffPerMinDeltas30_end,
                ally_mid_damageTakenPerMinDeltas0_10,
                ally_mid_damageTakenPerMinDeltas10_20,
                ally_mid_damageTakenPerMinDeltas20_30,
                ally_mid_damageTakenPerMinDeltas30_end,
                ally_mid_damageTakenDiffPerMinDeltas0_10,
                ally_mid_damageTakenDiffPerMinDeltas10_20,
                ally_mid_damageTakenDiffPerMinDeltas20_30,
                ally_mid_damageTakenDiffPerMinDeltas30_end,
                    ally_adc_longestTimeSpentLiving,
                    ally_adc_totalDamageDealt,
                    ally_adc_magicDamageDealt,
                    ally_adc_physicalDamageDealt,
                    ally_adc_trueDamageDealt,
                    ally_adc_totalDamageDealtToChampions,
                    ally_adc_magicDamageDealtToChampions,
                    ally_adc_physicalDamageDealtToChampions,
                    ally_adc_trueDamageDealtToChampions,
                    ally_adc_totalHeal,
                    ally_adc_totalDamageTaken,
                    ally_adc_magicalDamageTaken,
                    ally_adc_physicalDamageTaken,
                    ally_adc_trueDamageTaken,
                    ally_adc_goldEarned,
                    ally_adc_totalMinionsKilled,
                    ally_adc_neutralMinionsKilled,
                    ally_adc_neutralMinionsKilledTeamJungle,
                    ally_adc_neutralMinionsKilledEnemyJungle,
                    ally_adc_totalTimeCrowdControlDealt,
                    ally_adc_wardsPlaced,
                    ally_adc_wardsKilled,
                ally_adc_creepsPerMinDeltas0_10,
                ally_adc_creepsPerMinDeltas10_20,
                ally_adc_creepsPerMinDeltas20_30,
                ally_adc_creepsPerMinDeltas30_end,
                ally_adc_xpPerMinDeltas0_10,
                ally_adc_xpPerMinDeltas10_20,
                ally_adc_xpPerMinDeltas20_30,
                ally_adc_xpPerMinDeltas30_end,
                ally_adc_goldPerMinDeltas0_10,
                ally_adc_goldPerMinDeltas10_20,
                ally_adc_goldPerMinDeltas20_30,
                ally_adc_goldPerMinDeltas30_end,
                ally_adc_csDiffPerMinDeltas0_10,
                ally_adc_csDiffPerMinDeltas10_20,
                ally_adc_csDiffPerMinDeltas20_30,
                ally_adc_csDiffPerMinDeltas30_end,
                ally_adc_xpDiffPerMinDeltas0_10,
                ally_adc_xpDiffPerMinDeltas10_20,
                ally_adc_xpDiffPerMinDeltas20_30,
                ally_adc_xpDiffPerMinDeltas30_end,
                ally_adc_damageTakenPerMinDeltas0_10,
                ally_adc_damageTakenPerMinDeltas10_20,
                ally_adc_damageTakenPerMinDeltas20_30,
                ally_adc_damageTakenPerMinDeltas30_end,
                ally_adc_damageTakenDiffPerMinDeltas0_10,
                ally_adc_damageTakenDiffPerMinDeltas10_20,
                ally_adc_damageTakenDiffPerMinDeltas20_30,
                ally_adc_damageTakenDiffPerMinDeltas30_end,
                    ally_sup_longestTimeSpentLiving,
                    ally_sup_totalDamageDealt,
                    ally_sup_magicDamageDealt,
                    ally_sup_physicalDamageDealt,
                    ally_sup_trueDamageDealt,
                    ally_sup_totalDamageDealtToChampions,
                    ally_sup_magicDamageDealtToChampions,
                    ally_sup_physicalDamageDealtToChampions,
                    ally_sup_trueDamageDealtToChampions,
                    ally_sup_totalHeal,
                    ally_sup_totalDamageTaken,
                    ally_sup_magicalDamageTaken,
                    ally_sup_physicalDamageTaken,
                    ally_sup_trueDamageTaken,
                    ally_sup_goldEarned,
                    ally_sup_totalMinionsKilled,
                    ally_sup_neutralMinionsKilled,
                    ally_sup_neutralMinionsKilledTeamJungle,
                    ally_sup_neutralMinionsKilledEnemyJungle,
                    ally_sup_totalTimeCrowdControlDealt,
                    ally_sup_wardsPlaced,
                    ally_sup_wardsKilled,
                ally_sup_creepsPerMinDeltas0_10,
                ally_sup_creepsPerMinDeltas10_20,
                ally_sup_creepsPerMinDeltas20_30,
                ally_sup_creepsPerMinDeltas30_end,
                ally_sup_xpPerMinDeltas0_10,
                ally_sup_xpPerMinDeltas10_20,
                ally_sup_xpPerMinDeltas20_30,
                ally_sup_xpPerMinDeltas30_end,
                ally_sup_goldPerMinDeltas0_10,
                ally_sup_goldPerMinDeltas10_20,
                ally_sup_goldPerMinDeltas20_30,
                ally_sup_goldPerMinDeltas30_end,
                ally_sup_csDiffPerMinDeltas0_10,
                ally_sup_csDiffPerMinDeltas10_20,
                ally_sup_csDiffPerMinDeltas20_30,
                ally_sup_csDiffPerMinDeltas30_end,
                ally_sup_xpDiffPerMinDeltas0_10,
                ally_sup_xpDiffPerMinDeltas10_20,
                ally_sup_xpDiffPerMinDeltas20_30,
                ally_sup_xpDiffPerMinDeltas30_end,
                ally_sup_damageTakenPerMinDeltas0_10,
                ally_sup_damageTakenPerMinDeltas10_20,
                ally_sup_damageTakenPerMinDeltas20_30,
                ally_sup_damageTakenPerMinDeltas30_end,
                ally_sup_damageTakenDiffPerMinDeltas0_10,
                ally_sup_damageTakenDiffPerMinDeltas10_20,
                ally_sup_damageTakenDiffPerMinDeltas20_30,
                ally_sup_damageTakenDiffPerMinDeltas30_end,
                    enemy_top_longestTimeSpentLiving,
                    enemy_top_totalDamageDealt,
                    enemy_top_magicDamageDealt,
                    enemy_top_physicalDamageDealt,
                    enemy_top_trueDamageDealt,
                    enemy_top_totalDamageDealtToChampions,
                    enemy_top_magicDamageDealtToChampions,
                    enemy_top_physicalDamageDealtToChampions,
                    enemy_top_trueDamageDealtToChampions,
                    enemy_top_totalHeal,
                    enemy_top_totalDamageTaken,
                    enemy_top_magicalDamageTaken,
                    enemy_top_physicalDamageTaken,
                    enemy_top_trueDamageTaken,
                    enemy_top_goldEarned,
                    enemy_top_totalMinionsKilled,
                    enemy_top_neutralMinionsKilled,
                    enemy_top_neutralMinionsKilledTeamJungle,
                    enemy_top_neutralMinionsKilledEnemyJungle,
                    enemy_top_totalTimeCrowdControlDealt,
                    enemy_top_wardsPlaced,
                    enemy_top_wardsKilled,
                enemy_top_creepsPerMinDeltas0_10,
                enemy_top_creepsPerMinDeltas10_20,
                enemy_top_creepsPerMinDeltas20_30,
                enemy_top_creepsPerMinDeltas30_end,
                enemy_top_xpPerMinDeltas0_10,
                enemy_top_xpPerMinDeltas10_20,
                enemy_top_xpPerMinDeltas20_30,
                enemy_top_xpPerMinDeltas30_end,
                enemy_top_goldPerMinDeltas0_10,
                enemy_top_goldPerMinDeltas10_20,
                enemy_top_goldPerMinDeltas20_30,
                enemy_top_goldPerMinDeltas30_end,
                enemy_top_csDiffPerMinDeltas0_10,
                enemy_top_csDiffPerMinDeltas10_20,
                enemy_top_csDiffPerMinDeltas20_30,
                enemy_top_csDiffPerMinDeltas30_end,
                enemy_top_xpDiffPerMinDeltas0_10,
                enemy_top_xpDiffPerMinDeltas10_20,
                enemy_top_xpDiffPerMinDeltas20_30,
                enemy_top_xpDiffPerMinDeltas30_end,
                enemy_top_damageTakenPerMinDeltas0_10,
                enemy_top_damageTakenPerMinDeltas10_20,
                enemy_top_damageTakenPerMinDeltas20_30,
                enemy_top_damageTakenPerMinDeltas30_end,
                enemy_top_damageTakenDiffPerMinDeltas0_10,
                enemy_top_damageTakenDiffPerMinDeltas10_20,
                enemy_top_damageTakenDiffPerMinDeltas20_30,
                enemy_top_damageTakenDiffPerMinDeltas30_end,
                    enemy_jng_longestTimeSpentLiving,
                    enemy_jng_totalDamageDealt,
                    enemy_jng_magicDamageDealt,
                    enemy_jng_physicalDamageDealt,
                    enemy_jng_trueDamageDealt,
                    enemy_jng_totalDamageDealtToChampions,
                    enemy_jng_magicDamageDealtToChampions,
                    enemy_jng_physicalDamageDealtToChampions,
                    enemy_jng_trueDamageDealtToChampions,
                    enemy_jng_totalHeal,
                    enemy_jng_totalDamageTaken,
                    enemy_jng_magicalDamageTaken,
                    enemy_jng_physicalDamageTaken,
                    enemy_jng_trueDamageTaken,
                    enemy_jng_goldEarned,
                    enemy_jng_totalMinionsKilled,
                    enemy_jng_neutralMinionsKilled,
                    enemy_jng_neutralMinionsKilledTeamJungle,
                    enemy_jng_neutralMinionsKilledEnemyJungle,
                    enemy_jng_totalTimeCrowdControlDealt,
                    enemy_jng_wardsPlaced,
                    enemy_jng_wardsKilled,
                enemy_jng_creepsPerMinDeltas0_10,
                enemy_jng_creepsPerMinDeltas10_20,
                enemy_jng_creepsPerMinDeltas20_30,
                enemy_jng_creepsPerMinDeltas30_end,
                enemy_jng_xpPerMinDeltas0_10,
                enemy_jng_xpPerMinDeltas10_20,
                enemy_jng_xpPerMinDeltas20_30,
                enemy_jng_xpPerMinDeltas30_end,
                enemy_jng_goldPerMinDeltas0_10,
                enemy_jng_goldPerMinDeltas10_20,
                enemy_jng_goldPerMinDeltas20_30,
                enemy_jng_goldPerMinDeltas30_end,
                enemy_jng_csDiffPerMinDeltas0_10,
                enemy_jng_csDiffPerMinDeltas10_20,
                enemy_jng_csDiffPerMinDeltas20_30,
                enemy_jng_csDiffPerMinDeltas30_end,
                enemy_jng_xpDiffPerMinDeltas0_10,
                enemy_jng_xpDiffPerMinDeltas10_20,
                enemy_jng_xpDiffPerMinDeltas20_30,
                enemy_jng_xpDiffPerMinDeltas30_end,
                enemy_jng_damageTakenPerMinDeltas0_10,
                enemy_jng_damageTakenPerMinDeltas10_20,
                enemy_jng_damageTakenPerMinDeltas20_30,
                enemy_jng_damageTakenPerMinDeltas30_end,
                enemy_jng_damageTakenDiffPerMinDeltas0_10,
                enemy_jng_damageTakenDiffPerMinDeltas10_20,
                enemy_jng_damageTakenDiffPerMinDeltas20_30,
                enemy_jng_damageTakenDiffPerMinDeltas30_end,
                    enemy_mid_longestTimeSpentLiving,
                    enemy_mid_totalDamageDealt,
                    enemy_mid_magicDamageDealt,
                    enemy_mid_physicalDamageDealt,
                    enemy_mid_trueDamageDealt,
                    enemy_mid_totalDamageDealtToChampions,
                    enemy_mid_magicDamageDealtToChampions,
                    enemy_mid_physicalDamageDealtToChampions,
                    enemy_mid_trueDamageDealtToChampions,
                    enemy_mid_totalHeal,
                    enemy_mid_totalDamageTaken,
                    enemy_mid_magicalDamageTaken,
                    enemy_mid_physicalDamageTaken,
                    enemy_mid_trueDamageTaken,
                    enemy_mid_goldEarned,
                    enemy_mid_totalMinionsKilled,
                    enemy_mid_neutralMinionsKilled,
                    enemy_mid_neutralMinionsKilledTeamJungle,
                    enemy_mid_neutralMinionsKilledEnemyJungle,
                    enemy_mid_totalTimeCrowdControlDealt,
                    enemy_mid_wardsPlaced,
                    enemy_mid_wardsKilled,
                enemy_mid_creepsPerMinDeltas0_10,
                enemy_mid_creepsPerMinDeltas10_20,
                enemy_mid_creepsPerMinDeltas20_30,
                enemy_mid_creepsPerMinDeltas30_end,
                enemy_mid_xpPerMinDeltas0_10,
                enemy_mid_xpPerMinDeltas10_20,
                enemy_mid_xpPerMinDeltas20_30,
                enemy_mid_xpPerMinDeltas30_end,
                enemy_mid_goldPerMinDeltas0_10,
                enemy_mid_goldPerMinDeltas10_20,
                enemy_mid_goldPerMinDeltas20_30,
                enemy_mid_goldPerMinDeltas30_end,
                enemy_mid_csDiffPerMinDeltas0_10,
                enemy_mid_csDiffPerMinDeltas10_20,
                enemy_mid_csDiffPerMinDeltas20_30,
                enemy_mid_csDiffPerMinDeltas30_end,
                enemy_mid_xpDiffPerMinDeltas0_10,
                enemy_mid_xpDiffPerMinDeltas10_20,
                enemy_mid_xpDiffPerMinDeltas20_30,
                enemy_mid_xpDiffPerMinDeltas30_end,
                enemy_mid_damageTakenPerMinDeltas0_10,
                enemy_mid_damageTakenPerMinDeltas10_20,
                enemy_mid_damageTakenPerMinDeltas20_30,
                enemy_mid_damageTakenPerMinDeltas30_end,
                enemy_mid_damageTakenDiffPerMinDeltas0_10,
                enemy_mid_damageTakenDiffPerMinDeltas10_20,
                enemy_mid_damageTakenDiffPerMinDeltas20_30,
                enemy_mid_damageTakenDiffPerMinDeltas30_end,
                    enemy_adc_longestTimeSpentLiving,
                    enemy_adc_totalDamageDealt,
                    enemy_adc_magicDamageDealt,
                    enemy_adc_physicalDamageDealt,
                    enemy_adc_trueDamageDealt,
                    enemy_adc_totalDamageDealtToChampions,
                    enemy_adc_magicDamageDealtToChampions,
                    enemy_adc_physicalDamageDealtToChampions,
                    enemy_adc_trueDamageDealtToChampions,
                    enemy_adc_totalHeal,
                    enemy_adc_totalDamageTaken,
                    enemy_adc_magicalDamageTaken,
                    enemy_adc_physicalDamageTaken,
                    enemy_adc_trueDamageTaken,
                    enemy_adc_goldEarned,
                    enemy_adc_totalMinionsKilled,
                    enemy_adc_neutralMinionsKilled,
                    enemy_adc_neutralMinionsKilledTeamJungle,
                    enemy_adc_neutralMinionsKilledEnemyJungle,
                    enemy_adc_totalTimeCrowdControlDealt,
                    enemy_adc_wardsPlaced,
                    enemy_adc_wardsKilled,
                enemy_adc_creepsPerMinDeltas0_10,
                enemy_adc_creepsPerMinDeltas10_20,
                enemy_adc_creepsPerMinDeltas20_30,
                enemy_adc_creepsPerMinDeltas30_end,
                enemy_adc_xpPerMinDeltas0_10,
                enemy_adc_xpPerMinDeltas10_20,
                enemy_adc_xpPerMinDeltas20_30,
                enemy_adc_xpPerMinDeltas30_end,
                enemy_adc_goldPerMinDeltas0_10,
                enemy_adc_goldPerMinDeltas10_20,
                enemy_adc_goldPerMinDeltas20_30,
                enemy_adc_goldPerMinDeltas30_end,
                enemy_adc_csDiffPerMinDeltas0_10,
                enemy_adc_csDiffPerMinDeltas10_20,
                enemy_adc_csDiffPerMinDeltas20_30,
                enemy_adc_csDiffPerMinDeltas30_end,
                enemy_adc_xpDiffPerMinDeltas0_10,
                enemy_adc_xpDiffPerMinDeltas10_20,
                enemy_adc_xpDiffPerMinDeltas20_30,
                enemy_adc_xpDiffPerMinDeltas30_end,
                enemy_adc_damageTakenPerMinDeltas0_10,
                enemy_adc_damageTakenPerMinDeltas10_20,
                enemy_adc_damageTakenPerMinDeltas20_30,
                enemy_adc_damageTakenPerMinDeltas30_end,
                enemy_adc_damageTakenDiffPerMinDeltas0_10,
                enemy_adc_damageTakenDiffPerMinDeltas10_20,
                enemy_adc_damageTakenDiffPerMinDeltas20_30,
                enemy_adc_damageTakenDiffPerMinDeltas30_end,
                    enemy_sup_longestTimeSpentLiving,
                    enemy_sup_totalDamageDealt,
                    enemy_sup_magicDamageDealt,
                    enemy_sup_physicalDamageDealt,
                    enemy_sup_trueDamageDealt,
                    enemy_sup_totalDamageDealtToChampions,
                    enemy_sup_magicDamageDealtToChampions,
                    enemy_sup_physicalDamageDealtToChampions,
                    enemy_sup_trueDamageDealtToChampions,
                    enemy_sup_totalHeal,
                    enemy_sup_totalDamageTaken,
                    enemy_sup_magicalDamageTaken,
                    enemy_sup_physicalDamageTaken,
                    enemy_sup_trueDamageTaken,
                    enemy_sup_goldEarned,
                    enemy_sup_totalMinionsKilled,
                    enemy_sup_neutralMinionsKilled,
                    enemy_sup_neutralMinionsKilledTeamJungle,
                    enemy_sup_neutralMinionsKilledEnemyJungle,
                    enemy_sup_totalTimeCrowdControlDealt,
                    enemy_sup_wardsPlaced,
                    enemy_sup_wardsKilled,
                enemy_sup_creepsPerMinDeltas0_10,
                enemy_sup_creepsPerMinDeltas10_20,
                enemy_sup_creepsPerMinDeltas20_30,
                enemy_sup_creepsPerMinDeltas30_end,
                enemy_sup_xpPerMinDeltas0_10,
                enemy_sup_xpPerMinDeltas10_20,
                enemy_sup_xpPerMinDeltas20_30,
                enemy_sup_xpPerMinDeltas30_end,
                enemy_sup_goldPerMinDeltas0_10,
                enemy_sup_goldPerMinDeltas10_20,
                enemy_sup_goldPerMinDeltas20_30,
                enemy_sup_goldPerMinDeltas30_end,
                enemy_sup_csDiffPerMinDeltas0_10,
                enemy_sup_csDiffPerMinDeltas10_20,
                enemy_sup_csDiffPerMinDeltas20_30,
                enemy_sup_csDiffPerMinDeltas30_end,
                enemy_sup_xpDiffPerMinDeltas0_10,
                enemy_sup_xpDiffPerMinDeltas10_20,
                enemy_sup_xpDiffPerMinDeltas20_30,
                enemy_sup_xpDiffPerMinDeltas30_end,
                enemy_sup_damageTakenPerMinDeltas0_10,
                enemy_sup_damageTakenPerMinDeltas10_20,
                enemy_sup_damageTakenPerMinDeltas20_30,
                enemy_sup_damageTakenPerMinDeltas30_end,
                enemy_sup_damageTakenDiffPerMinDeltas0_10,
                enemy_sup_damageTakenDiffPerMinDeltas10_20,
                enemy_sup_damageTakenDiffPerMinDeltas20_30,
                enemy_sup_damageTakenDiffPerMinDeltas30_end) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ''', sum([both_teams + teams[team]], [])) for team in teams]

                connect.commit()

            print('\r%3.6s%% (%s/%s)' % (k * 100 / (number_of_matches), str(k), str(number_of_matches)), end='')


def get_odds_archive_championships(url):
    abs_url = 'https://www.oddsportal.com'
    html = get_html_code(url)
    soup = bs4.BeautifulSoup(html, 'html.parser')
    championships = soup.find('table', class_='table-main sport').find_all('td')
    championships_lol = [elem for elem in championships if re.match('League of Legends', elem.text) != None]
    names = [elem.text for elem in championships_lol]
    hrefs = ['https://www.oddsportal.com' + elem.find('a')['href'] for elem in championships_lol]
    with sqlite3.connect('Statistics_Analyzer.sqlite') as connect:
        cursor = connect.cursor()
        try:
            cursor.execute("DROP TABLE odds_archive_championships")
        except:
            pass
        cursor.execute("CREATE TABLE odds_archive_championships (championship LONGTEXT, year LONGTEXT, url LONGTEXT)")
        connect.commit()
        print('Создание таблицы (odds_archive_championships)')
        for i in range(0, len(hrefs)):
            html = get_html_code(hrefs[i])
            soup = bs4.BeautifulSoup(html, 'html.parser')
            if soup.find('h1').text != 'Page not found':
                year_hrefs = ['https://www.oddsportal.com' + elem['href'] for elem in
                              soup.find('div', class_='main-menu2 main-menu-gray').find('ul',
                                                                                        class_="main-filter").find_all(
                                  'a')]
                years = [elem.text for elem in
                         soup.find('div', class_='main-menu2 main-menu-gray').find('ul', class_="main-filter").find_all(
                             'a')]
                for j in range(0, len(year_hrefs)):
                    cursor.execute("INSERT INTO odds_archive_championships (championship,year,url) VALUES (?,?,?)",
                                   (names[i], years[j], year_hrefs[j]))
                    connect.commit()


def get_odds_archive_urls():
    abs_url = 'https://www.oddsportal.com'
    with sqlite3.connect('Statistics_Analyzer.sqlite') as connect:
        j = 0
        cursor = connect.cursor()
        cursor.execute("SELECT url from odds_archive_championships")
        championships = [elem[0] for elem in cursor.fetchall()]
        try:
            cursor.execute("DROP TABLE odds_archive_list_of_mathes")
        except:
            pass
        cursor.execute("CREATE TABLE odds_archive_list_of_mathes (id INTEGER, url LONGTEXT)")
        connect.commit()
        print('Создание таблицы (odds_archive_list_of_mathes)')
    for championship_url in championships:
        html = get_js_html(championship_url)
        soup = bs4.BeautifulSoup(html, 'html.parser')
        print(championship_url)
        if soup.find('div', id='tournamentTable').text != 'No data available':
            try:
                pages = [championship_url + elem['href'] for elem in soup.find('div', id='pagination').find_all('a')]
            except AttributeError:
                pages = [championship_url]
            for page in pages:
                html = get_js_html(page)
                soup = bs4.BeautifulSoup(html, 'html.parser')
                matches = soup.find('div', id='tournamentTable').find_all('td', class_='name table-participant')
                matches = [abs_url + elem.find('a')['href'] for elem in matches]
                for i in range(0, len(matches)):
                    cursor.execute("INSERT INTO odds_archive_list_of_mathes VALUES (?,?)",
                                   (j, matches[i]))
                    j += 1
                    connect.commit()


def get_odds_archive_match(url):
    months = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
              'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
    regions = {
        'League of Legends Oceanic Pro League': 'OCE',
        'League of Legends Circuito Brasileiro de League of Legends': 'BR',
        'League of Legends LoL Pro League': 'CN',
        'League of Legends European Championship': 'EUW',
        'League of Legends IEM - Katowice': 'WR',
        'League of Legends LoL Continental League': 'CIS',
        'League of Legends Champions Korea': 'KR',
        'League of Legends IEM Season XI - Gyeonggi': 'WR',
        'League of Legends KeSPA Cup': 'KR',
        'League of Legends Lol Master Series': 'TW',
        'League of Legends IEM Season XI - Oakland': 'WR',
        'League of Legends Sea Tour': 'SEA',
        'League of Legends All-Star': 'WR',
        'League of Legends Championship Series': 'NA',
        'League of Legends International Wildcard': 'WR',
        'League of Legends Mid Season Invitational': 'WR',
        'League of Legends Rift Rivals': 'WR',
        'League of Legends World Championship': 'WR'
    }

    html = get_js_html(url)
    soup = bs4.BeautifulSoup(html, 'html.parser')
    team1 = soup.find('h1').text.split(' - ')[0].strip()
    team2 = soup.find('h1').text.split(' - ')[1].strip()
    result1 = soup.find(class_='result').find('strong').text.split(':')[0]
    result2 = soup.find(class_='result').find('strong').text.split(':')[1]
    date = soup.find('p', class_='datet').text.split(',')[1].strip().split(' ')
    date = date[3] + '-' + months[date[1]] + '-' + date[0]
    odds = soup.find('table', class_='table-main detail-odds sortable').find('tbody').find_all('tr')[:-1]
    odds = [elem.find_all('td')[1:-2] for elem in odds]
    odd1 = list()
    odd2 = list()
    for elem in odds:
        if len(elem) != 0:
            if (elem[0].text) != '':
                odd1.append(float(elem[0].text))
            if (elem[1].text) != '':
                odd2.append(float(elem[1].text))
    odd1 = (sorted(odd1))[-2] if len(odd1) > 1 else max(odd1)
    odd2 = (sorted(odd2))[-2] if len(odd2) > 1 else max(odd2)
    region = regions[
        re.sub(r"\d+", "", re.findall('"([0-9a-zA-Z.\- ]{1,199})"', soup.find(id='bookmarks-link').text)[0]).strip()]
    return [date, region, team1, team2, result1, result2, odd1, odd2]


def get_odds_archive_matches():
    times = list()
    with sqlite3.connect('Statistics_Analyzer.sqlite') as connect:
        cursor = connect.cursor()
        cursor.execute("SELECT  MAX(id) FROM odds_archive_list_of_mathes")
        number_of_matches = cursor.fetchall()[0][0]
        try:
            cursor.execute(
                "CREATE TABLE odds_arhive_matches (id INTEGER, match_date timestring, region LONGTEXT, team1 LONGTEXT, team2 LONGTEXT, result1 LONGTEXT, result2 LONGTEXT, odd1 LONGTEXT, odd2 LONGTEXT)")
            connect.commit()
            start_id = 0
            print('\nСоздание таблицы (get_odds_archive_matches)')
        except sqlite3.OperationalError:
            cursor.execute("SELECT  MAX(id) FROM odds_arhive_matches")
            start_id = cursor.fetchall()[0][0] + 1
            print('\nТаблица существует (get_odds_archive_matches)')
        for i in range(start_id, number_of_matches + 1):
            cursor.execute("SELECT url FROM odds_archive_list_of_mathes WHERE id=?", (i,))
            time1 = time.time()
            match_info = get_odds_archive_match(cursor.fetchall()[0][0])
            match_info.insert(0, i)
            cursor.execute("INSERT INTO odds_arhive_matches VALUES (?,?,?,?,?,?,?,?,?)", match_info)
            connect.commit()
            # time.sleep(random.randint(8, 15) / 10)
            time2 = time.time()
            times.append(time2 - time1)
            print('\r%3.6s%% (%s/%s) Время на один шаг: %s cек. Времени осталось: %s ч. ' % (
            i * 100 / (number_of_matches), str(i), str(number_of_matches), sum(times) / len(times),
            (number_of_matches - i) * (sum(times) / len(times)) / 3600), end='')

        cursor.close()

from dataclasses import dataclass
import numpy as np
@dataclass
class GameMetadata:
    championship : str
    team_1 : str
    team_2 : str
    date :  np.datetime64
    time : np.datetime64
    patch : str
    win_1 : bool
    win_2 : bool
    gol_id : str
    json : str
    json_timeline : str

    @classmethod
    def init_from_html(cls,url):
        html = get_html_code(url)
        soup = bs4.BeautifulSoup(html, 'html.parser')
        championship = soup.find('div',class_='col-12 col-sm-7').find('a').text
        team_1 = soup.find('div',class_='row rowbreak pb-4').find_all(class_='col-12 col-sm-6')[0].find('a').text
        team_2 = soup.find('div', class_='row rowbreak pb-4').find_all(class_='col-12 col-sm-6')[1].find('a').text
        win_1 = soup.find('div',class_='row rowbreak pb-4').find_all(class_='col-12 blue-line-header')[0].text.split('-')[-1]
        win_2 = soup.find('div',class_='row rowbreak pb-4').find_all(class_='col-12 blue-line-header')[1].text.split('-')[-1]
        time = pd.to_datetime(soup.find('div', class_='col-6 text-center').find('h1').text).time()
        json = soup.find(title='Riot Match History').attrs['href']




def main():
    chmap_data = ChampionData('8.16')
    df2 = chmap_data.data

    chmap_data.current_patch = '10.16'
    df1 = chmap_data.update_data()
    a =GameMetadata.init_from_html('https://gol.gg/game/stats/26503/page-game/')
    a = GolGG()
    a.champion_data('9.21')
    get_champions_info('9.21')
    # get_odds_archive_championships('https://www.oddsportal.com/results/#esports')
    # get_odds_archive_urls()
    # get_odds_archive_matches()
    # get_champions_info('https://ddragon.leagueoflegends.com/cdn/9.11.1/data/en_US/champion.json')
    # url_home='https://gol.gg/esports/home/'Statistics_Analyzer
    # url_matches='http://gol.gg/game/gameshow.php?id='
    # number_of_matches=get_number_of_matches(url_home)
    # get_matches_info_parsed_cn(number_of_matches)
    # # get_matches_info_html(url_matches,number_of_matches)
    # get_matches_info_json(number_of_matches)
    # get_matches_info_parsed(number_of_matches)


if __name__ == '__main__':
    main()
