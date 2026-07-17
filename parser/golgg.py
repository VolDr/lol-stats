from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import sessionmaker
from parser import web
from bs4 import BeautifulSoup
import os
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
import datetime
from parser import utils
from typing import Iterable
#
path_to_db = '../data'
if not os.path.exists(path_to_db):
    os.mkdir(path_to_db)
engine = create_engine(os.path.join('sqlite:///', path_to_db, 'statistics_analyzer.sqlite?check_same_thread=false'),
                       echo=False)
base = declarative_base()
# session = sessionmaker(bind=engine)()
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)
session = Session()

# from parser.database import base, session, engine

site_address = 'https://gol.gg'
tournament_address = os.path.join(site_address, 'tournament/')
tournament_list_address = os.path.join(tournament_address, 'list/')
game_page_address = lambda id: f'https://gol.gg/game/stats/{id}/page-game/'
old_proxies = web.get_proxy_list(local=True, use_your_ip=True, path = '../data/old_proxies.html')
proxies = web.get_proxy_list(local=True, use_your_ip=True)


def match_details_local_address(bs):
    if bs.find('div', class_='col-3').find('a') is None:
        return None
    return bs.find('div', class_='col-3').find('a')['href'].split('match-details')[-1].strip()[1:]


def match_date(bs):
    return datetime.datetime.strptime(bs.find('div', class_='col-12 col-sm-5 text-right').text.split()[0],
                                      '%Y-%m-%d').date()


def match_country(bs):
    return bs.find('div', class_='col-12 col-sm-7').text.split('(')[1].strip()[:-1]


def match_tournament(bs):
    return bs.find('div', class_='col-12 col-sm-7').text.split('(')[0].strip()


def match_team(bs, side: str):
    return bs.find('div', class_=f'{side}-line-header').text.split('-')[0].strip()


def match_exists(match_page_source_code):
    return True if not match_page_source_code.find(text='Oops ! Page not found.') else False


def last_game_id(indent=0):
    match_ids = []
    target_class = 'table_list footable toggle-square-filled'
    for proxy in web.get_proxy_list():
        last_matches_list = web.html_code(site_address, js=True, proxy=proxy, loaded_element_class=target_class)

    [match_ids.append(int(row.findAll('td')[2].find('a')['href'][2:].split('/')[-3])) for row in
     BeautifulSoup(last_matches_list).findAll('tr')[1:]]

    tournament_list = web.html_code(tournament_list_address, js=True, loaded_element_class=target_class)
    tournament_list_addresses = [os.path.join(tournament_address, a['href'][2:]) for a in
                                 BeautifulSoup(tournament_list).find('tbody').find_all('a')]

    for tournament in tournament_list_addresses:
        table = BeautifulSoup(web.html_code(tournament)).find('h1', text='Last games').nextSibling.nextSibling
        [match_ids.append(int(a['href'][2:].split('/')[-3])) for a in table.find_all('a')]
    return max(match_ids) + indent


class Match_not_available(base):
    __tablename__ = 'gol_not_available'
    id = Column(Integer, primary_key=True)

    def __init__(self, *args, **kwargs):
        base.metadata.create_all(engine)
        base.__init__(self, *args, **kwargs)
        session.add(self)
        session.commit()


class Match_not_exist(base):
    __tablename__ = 'gol_not_exist'
    id = Column(Integer, primary_key=True)

    def __init__(self, *args, **kwargs):
        base.metadata.create_all(engine)
        base.__init__(self, *args, **kwargs)
        session.add(self)
        session.commit()


class Match_not_detal_address(base):
    __tablename__ = 'gol_not_detal_address'
    id = Column(Integer, primary_key=True)
    url = Column(String)
    team_blue = Column(String)
    team_red = Column(String)
    tournament = Column(String)
    country = Column(String)
    date = Column(Date)

    def __init__(self, *args, **kwargs):
        base.metadata.create_all(engine)
        base.__init__(self, *args, **kwargs)
        session.add(self)
        session.commit()

    @classmethod
    def init_from_page_code(cls, bs, url, match_id):
        return cls(id=match_id, url=url, team_blue=match_team(bs, 'blue'), team_red=match_team(bs, 'red'),
                   tournament=match_tournament(bs),
                   country=match_country(bs), date=match_date(bs))


class Game(base):
    __tablename__ = 'gol_game_data'
    id = Column(Integer, primary_key=True)
    url = Column(String)
    team_blue = Column(String)
    team_red = Column(String)
    tournament = Column(String)
    country = Column(String)
    date = Column(Date)
    match_details = Column(String)
    timeline = Column(String)

    def __init__(self, *args, **kwargs):
        base.metadata.create_all(engine)
        base.__init__(self, *args, **kwargs)
        session.add(self)
        session.commit()

    @classmethod
    def init_from_page_code(cls, bs, url, match_id):
        match_details = os.path.join('https://acs.leagueoflegends.com/v1/stats/game', match_details_local_address(bs))
        timeline = match_details.replace('?gameHash', '/timeline?gameHash')
        return cls(id=match_id, url=url, team_blue=match_team(bs, 'blue'), team_red=match_team(bs, 'red'),
                   tournament=match_tournament(bs), country=match_country(bs), date=match_date(bs),
                   match_details=match_details, timeline=timeline)


def save_game_info(id):
    if id in not_exist_ids or id in exist_ids or id in not_detail_adreccess_ids:
        return
    try:
        code = web.proxy_loop(game_page_address(id), proxies, too_many_requests)
        page = BeautifulSoup(code)
        # if web.Proxy.all_proxies_bad(proxies):
        #     web.Proxy.reset_proxies(proxies)
        # for proxy in proxies:
        #     if not proxy.is_bad:
        #         try:
        #             code = web.html_code(game_page_address(id), proxy=proxy)
        #         except web.ProxyError:
        #             proxy.is_bad = True
        #             return save_game_info(id)
        #         if code is not None:
        #             break
        # page = BeautifulSoup(code)
        # if too_many_requests(page):
        #     proxy.is_bad = True
        #     return save_game_info(id)
    except RuntimeError as e:
        print(e)
    else:
        if match_exists(page):
            if match_details_local_address(page) is not None:
                Game.init_from_page_code(page, game_page_address(id), id)
            else:
                Match_not_detal_address.init_from_page_code(page, game_page_address(id), id)
        else:
            Match_not_exist(id=id)
        # time.sleep(random.randint(10, 50)/10)


def table_exist(table_name):
    return engine.dialect.has_table(engine, table_name)


def ids_from_table(table_class):
    if table_exist(table_class.__tablename__):
        return [q.id for q in session.query(table_class).all()]
    else:
        return []


def too_many_requests(match_page_source_code):
    return False if not BeautifulSoup(match_page_source_code).find(
        text='too many requests. Try again in a few minutes.') else True


def game_data() -> Iterable[Game]:
    for game in session.query(Game):
        yield game

if __name__ == '__main__':
    # last_id = last_game_id(indent=10)
    not_exist_ids = ids_from_table(Match_not_exist)
    exist_ids = ids_from_table(Game)
    not_detail_adreccess_ids = ids_from_table(Match_not_detal_address)
    # for id in range(1000):
    #     save_game_info(id)
    utils.work_parallel(save_game_info, range(26000), thread_number=16)

    # for id in range(1000):
    #     if id in not_exist_ids or id in exist_ids:
    #         continue
    #     try:
    #         page = BeautifulSoup(web.html_code(game_page_address(id)))
    #     except RuntimeError as e:
    #         print(e)
    #         Match_not_available(id=id)
    #     else:
    #         if match_exists(page):
    #             Game.init_from_page_code(page, game_page_address(id), id)
    #         else:
    #             Match_not_exist(id=id)
    #     pass
    # a = Game.init_from_site('https://gol.gg/game/stats/4534/page-game/')
