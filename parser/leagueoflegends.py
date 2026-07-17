import os
from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer, Date, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from parser import golgg
from typing import Iterable
from parser import web
from parser import utils
path_to_db = '../data'
if not os.path.exists(path_to_db):
    os.mkdir(path_to_db)
engine = create_engine(os.path.join('sqlite:///', path_to_db, 'statistics_analyzer.sqlite?check_same_thread=false'),
                       echo=False)
base = declarative_base()
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)
session = Session()

cookies = {'__cfduid': 'd5f87f54337b4681f2b21a81ce6d30c6a1605357097',
           'ping_session_id': '3af727e8-d316-4289-9e35-48da99543025',
           'id_hint': 'sub%3Da14e603e-1c86-5d0e-99ea-a18b708f535b%26lang%3Den%26game_name%3DE%252016%26tag_line%3DAASC%26id%3D32514157%26summoner%3DE%252016%26region%3DEUW1%26tag%3Deuw',
           'PVPNET_LANG': 'en_US',
           'notice_behavior': 'none',
           'id_token': 'eyJraWQiOiJzMSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiJhMTRlNjAzZS0xYzg2LTVkMGUtOTllYS1hMThiNzA4ZjUzNWIiLCJjb3VudHJ5IjoicnVzIiwicGxheWVyX3Bsb2NhbGUiOiJlbi1VUyIsImFtciI6WyJwYXNzd29yZCJdLCJpc3MiOiJodHRwczpcL1wvYXV0aC5yaW90Z2FtZXMuY29tIiwibG9sIjpbeyJjdWlkIjozMjUxNDE1NywiY3BpZCI6IkVVVzEiLCJ1aWQiOjMyNTE0MTU3LCJ1bmFtZSI6ImUxNmFhc2MiLCJwdHJpZCI6bnVsbCwicGlkIjoiRVVXMSIsInN0YXRlIjoiRU5BQkxFRCJ9XSwibG9jYWxlIjoiZW5fVVMiLCJhdWQiOiJyc28td2ViLWNsaWVudC1wcm9kIiwiYWNyIjoidXJuOnJpb3Q6YnJvbnplIiwicGxheWVyX2xvY2FsZSI6ImVuLVVTIiwiZXhwIjoxNjA1NDQzNDk0LCJpYXQiOjE2MDUzNTcwOTQsImFjY3QiOnsiZ2FtZV9uYW1lIjoiRSAxNiIsInRhZ19saW5lIjoiQUFTQyJ9LCJqdGkiOiJlaHVKbGNOUFc1TSIsImxvZ2luX2NvdW50cnkiOiJydXMifQ.WNaNOokC9BAQmeWFVCxn5-2_dNX4Sh8ZfduLWRDp0RVt2BVJKhgv_wUWtQsxd_Uol2O1Zfu9ads2tDbMm75EA48xllxQAbucmvoPS9rZfqdh5DXZZF34hAlEArTqBxtNomdUgWkBd95LYf1HchvCkeANKpo2MMY6K0Ph9h5zTcM',
           'PVPNET_REGION': 'euw',
           'PVPNET_ID_EUW': '32514157',
           'PVPNET_TOKEN_EUW': 'eyJkYXRlX3RpbWUiOjE2MDUzNTcwOTU3MTAsImdhc19hY2NvdW50X2lkIjozMjUxNDE1NywicHZwbmV0X2FjY291bnRfaWQiOjMyNTE0MTU3LCJzdW1tb25lcl9uYW1lIjoiRSAxNiIsInZvdWNoaW5nX2tleV9pZCI6IjkwMzQ3NTJiMmI0NTYwNDRhZTg3ZjI1OTgyZGFkMDdkIiwic2lnbmF0dXJlIjoiRGNGL1U0dDVBRWh6ZU4rYWIyUjNtZDhCSU1SYUR5dU9WMkZodEJ5UlAvbWZKcmFOeWUxd2hCTnl2cW52Tjl5bjU2cFdYZnE1T3BNUE9ubzhYM0ZxL3RaNTIyZm5sWWxObzZ4NEJCNzA5emJRQjRWSklHTnZmREx1VWdOUkxTckJveVh5SW9NU1puYTE2eVplQWF6OW9tak9hNGRUcGthTlRDd09hdHJvay93PSJ9',
           'PVPNET_ACCT_EUW': 'E+16',
           '_gat': '1',
           '_gid': 'GA1.2.1836652518.1605353993',
           '_ga': 'GA1.2.1888463085.1605353993',
           'ajs_user_id': 'null',
           'ajs_group_id': 'null'
           }


class LolGameData(base):
    __tablename__ = 'leagueoflegends_game_data'
    id = Column(Integer, primary_key=True)
    gameId = Column(Integer)
    platformId = Column(String)
    gameCreation = Column(Integer)
    gameDuration = Column(Integer)
    queueId = Column(Integer)
    mapId = Column(Integer)
    seasonId = Column(Integer)
    gameVersion = Column(String)
    gameMode = Column(String)
    gameType = Column(String)

    def __init__(self, *args, **kwargs):
        base.metadata.create_all(engine)
        base.__init__(self, *args, **kwargs)
        session.add(self)
        session.commit()

    @classmethod
    def init_from_json(cls, json):
        json = utils.remove_dict_and_lists_from_dict(json)
        return cls(**json)


class LolGameTeamData(base):
    __tablename__ = 'leagueoflegends_team_data'
    id = Column(Integer, primary_key=True)
    gameId = Column(Integer)
    teamId = Column(Integer)
    win = Column(String)
    firstBlood = Column(Boolean)
    firstTower = Column(Boolean)
    firstInhibitor = Column(Boolean)
    firstBaron = Column(Boolean)
    firstDragon = Column(Boolean)
    firstRiftHerald = Column(Boolean)
    towerKills = Column(Integer)
    inhibitorKills = Column(Integer)
    baronKills = Column(Integer)
    dragonKills = Column(Integer)
    vilemawKills = Column(Integer)
    riftHeraldKills = Column(Integer)
    dominionVictoryScore = Column(Integer)

    def __init__(self, *args, **kwargs):
        base.metadata.create_all(engine)
        base.__init__(self, *args, **kwargs)
        session.add(self)
        session.commit()

    @classmethod
    def init_from_json(cls, id,json):
        teams_db = list()
        for team in json['teams']:
            team = utils.remove_dict_and_lists_from_dict(team)
            teams_db.append(cls(id = id, gameId = json['gameId'],**team))
        return teams_db

class LolGameTeamBansData(base):
    __tablename__ = 'leagueoflegends_team_bans_data'
    id = Column(Integer, primary_key=True)
    gameId = Column(Integer)
    teamId = Column(Integer)
    championId = Column(Integer)
    pickTurn = Column(Integer)

    def __init__(self, *args, **kwargs):
        base.metadata.create_all(engine)
        base.__init__(self, *args, **kwargs)
        session.add(self)
        session.commit()

    @classmethod
    def init_from_json(cls, json):
        teams_db = list()
        for team in json['teams']:
            for bans in team['bans']:
                bans = dict(bans)
                teams_db.append(cls(gameId = json['gameId'],teamId = team['teamId'], **bans))
        return teams_db



class LolGameTeamParticipantsData(base):
    __tablename__ = 'leagueoflegends_team_participants_data'
    id = Column(Integer, primary_key=True)
    gameId = Column(Integer)
    participantId = Column(Integer)
    teamId = Column(Integer)
    championId = Column(Integer)
    spell1Id = Column(Integer)
    spell2Id = Column(Integer)
    role = Column(String)
    lane = Column(String)

    def __init__(self, *args, **kwargs):
        base.metadata.create_all(engine)
        base.__init__(self, *args, **kwargs)
        session.add(self)
        session.commit()

    @classmethod
    def init_from_json(cls, json):
        participants = list()
        for participant in json['participants']:
            participant = utils.remove_dict_and_lists_from_dict(participant)
            participant.update(utils.remove_dict_and_lists_from_dict(participant['timeline']))
            participants.append(cls(gameId = json['gameId'], **participant))
        return participants


class LolGameTeamParticipantsStatsData(base):
    __tablename__ = 'leagueoflegends_team_participants_stats_data'
    id = Column(Integer, primary_key=True)
    gameId = Column(Integer)
    participantId = Column(Integer)
    win = Column(Boolean)
    item0 = Column(Integer)
    item1 = Column(Integer)
    item2 = Column(Integer)
    item3 = Column(Integer)
    item4 = Column(Integer)
    item5 = Column(Integer)
    item6 = Column(Integer)
    kills = Column(Integer)
    deaths = Column(Integer)
    assists = Column(Integer)
    largestKillingSpree = Column(Integer)
    largestMultiKill = Column(Integer)
    killingSprees = Column(Integer)
    longestTimeSpentLiving = Column(Integer)
    doubleKills = Column(Integer)
    tripleKills = Column(Integer)
    quadraKills = Column(Integer)
    pentaKills = Column(Integer)
    unrealKills = Column(Integer)
    totalDamageDealt = Column(Integer)
    magicDamageDealt = Column(Integer)
    physicalDamageDealt = Column(Integer)
    trueDamageDealt = Column(Integer)
    largestCriticalStrike = Column(Integer)
    totalDamageDealtToChampions = Column(Integer)
    magicDamageDealtToChampions = Column(Integer)
    physicalDamageDealtToChampions = Column(Integer)
    trueDamageDealtToChampions = Column(Integer)
    totalHeal = Column(Integer)
    totalUnitsHealed = Column(Integer)
    damageSelfMitigated = Column(Integer)
    damageDealtToObjectives = Column(Integer)
    damageDealtToTurrets = Column(Integer)
    visionScore = Column(Integer)
    timeCCingOthers = Column(Integer)
    totalDamageTaken = Column(Integer)
    magicalDamageTaken = Column(Integer)
    physicalDamageTaken = Column(Integer)
    trueDamageTaken = Column(Integer)
    goldEarned = Column(Integer)
    goldSpent = Column(Integer)
    turretKills = Column(Integer)
    inhibitorKills = Column(Integer)
    totalMinionsKilled = Column(Integer)
    neutralMinionsKilled = Column(Integer)
    neutralMinionsKilledTeamJungle = Column(Integer)
    neutralMinionsKilledEnemyJungle = Column(Integer)
    totalTimeCrowdControlDealt = Column(Integer)
    champLevel = Column(Integer)
    visionWardsBoughtInGame = Column(Integer)
    sightWardsBoughtInGame = Column(Integer)
    wardsPlaced = Column(Integer)
    wardsKilled = Column(Integer)
    firstBloodKill = Column(Boolean)
    firstBloodAssist = Column(Boolean)
    firstTowerKill = Column(Boolean)
    firstTowerAssist = Column(Boolean)
    firstInhibitorKill = Column(Boolean)
    firstInhibitorAssist = Column(Boolean)
    combatPlayerScore = Column(Integer)
    objectivePlayerScore = Column(Integer)
    totalPlayerScore = Column(Integer)
    totalScoreRank = Column(Integer)
    playerScore0 = Column(Integer)
    playerScore1 = Column(Integer)
    playerScore2 = Column(Integer)
    playerScore3 = Column(Integer)
    playerScore4 = Column(Integer)
    playerScore5 = Column(Integer)
    playerScore6 = Column(Integer)
    playerScore7 = Column(Integer)
    playerScore8 = Column(Integer)
    playerScore9 = Column(Integer)
    perk0 = Column(Integer)
    perk0Var1 = Column(Integer)
    perk0Var2 = Column(Integer)
    perk0Var3 = Column(Integer)
    perk1 = Column(Integer)
    perk1Var1 = Column(Integer)
    perk1Var2 = Column(Integer)
    perk1Var3 = Column(Integer)
    perk2 = Column(Integer)
    perk2Var1 = Column(Integer)
    perk2Var2 = Column(Integer)
    perk2Var3 = Column(Integer)
    perk3 = Column(Integer)
    perk3Var1 = Column(Integer)
    perk3Var2 = Column(Integer)
    perk3Var3 = Column(Integer)
    perk4 = Column(Integer)
    perk4Var1 = Column(Integer)
    perk4Var2 = Column(Integer)
    perk4Var3 = Column(Integer)
    perk5 = Column(Integer)
    perk5Var1 = Column(Integer)
    perk5Var2 = Column(Integer)
    perk5Var3 = Column(Integer)
    perkPrimaryStyle = Column(Integer)
    perkSubStyle = Column(Integer)
    statPerk0 = Column(Integer)
    statPerk1 = Column(Integer)
    statPerk2 = Column(Integer)

    def __init__(self, *args, **kwargs):
        base.metadata.create_all(engine)
        base.__init__(self, *args, **kwargs)
        session.add(self)
        session.commit()


    @classmethod
    def init_from_json(cls, json):
        stats = list()
        for participant in json['participants']:
            stat = utils.remove_dict_and_lists_from_dict(participant['stats'])
            stats.append(cls(gameId = json['gameId'], participantId = participant['participantId'], **stat))
        return stats


class LolGameTeamParticipantsCreepsPerMinDeltasData(base):
    __tablename__ = 'leagueoflegends_team_participants_creeps_per_min_deltas_data'
    id = Column(Integer, primary_key=True)
    gameId = Column(Integer)
    participantId = Column(Integer)
    minutes0_10 = Column(Float)
    minutes10_20 = Column(Float)
    minutes20_30 = Column(Float)
    minutes30_end = Column(Float)

    def __init__(self, *args, **kwargs):
        base.metadata.create_all(engine)
        base.__init__(self, *args, **kwargs)
        session.add(self)
        session.commit()

    @classmethod
    def init_from_json(cls, json):
        creeps_per_min_deltas_list = list()
        for participant in json['participants']:
            creeps_per_min_deltas = utils.remove_dict_and_lists_from_dict(participant['timeline']['creepsPerMinDeltas'])
            utils.remove_dict_and_lists_from_dict(creeps_per_min_deltas)
            creeps_per_min_deltas_list.append(cls(gameId=json['gameId'], participantId=participant['participantId'], **creeps_per_min_deltas))
        return creeps_per_min_deltas_list





class LolGameTeamParticipantsXpPerMinDeltasData(base):
    __tablename__ = 'leagueoflegends_team_participants_xp_per_min_deltas_data'
    id = Column(Integer, primary_key=True)
    gameId = Column(Integer)
    participantId = Column(Integer)
    minutes0_10 = Column(Float)
    minutes10_20 = Column(Float)
    minutes20_30 = Column(Float)
    minutes30_end = Column(Float)

    def __init__(self, *args, **kwargs):
        base.metadata.create_all(engine)
        base.__init__(self, *args, **kwargs)
        session.add(self)
        session.commit()


class LolGameTeamParticipantsGoldPerMinDeltasData(base):
    __tablename__ = 'leagueoflegends_team_participants_gold_per_min_deltas_data'
    id = Column(Integer, primary_key=True)
    gameId = Column(Integer)
    participantId = Column(Integer)
    minutes0_10 = Column(Float)
    minutes10_20 = Column(Float)
    minutes20_30 = Column(Float)
    minutes30_end = Column(Float)

    def __init__(self, *args, **kwargs):
        base.metadata.create_all(engine)
        base.__init__(self, *args, **kwargs)
        session.add(self)
        session.commit()

class LolGameTeamParticipantsDamageTakenfPerMinDeltasData(base):
    __tablename__ = 'leagueoflegends_team_participants_damage_taken_per_min_deltas_data'
    id = Column(Integer, primary_key=True)
    gameId = Column(Integer)
    participantId = Column(Integer)
    minutes0_10 = Column(Float)
    minutes10_20 = Column(Float)
    minutes20_30 = Column(Float)
    minutes30_end = Column(Float)

    def __init__(self, *args, **kwargs):
        base.metadata.create_all(engine)
        base.__init__(self, *args, **kwargs)
        session.add(self)
        session.commit()

def print_dict_keys(d, indent=''):
    for key, elem in d.items():
        if isinstance(elem, dict):
            print(f'{indent[:-1]}\t\t***{key}***')
            print_dict_keys(elem, indent + '\t')
        elif isinstance(elem, list):
            print(f'{indent[:-1]}\t\t***{key}***')
            if isinstance(elem[0], dict):
                print_dict_keys(elem[0], indent + '\t')
        else:
            typ = 'Integer' if type(elem) == int else 'String' if type(elem) == str  else 'Boolean' if type(elem) == bool  else "Float" if type(elem) == float else f"******{type(elem)}"
            try:
                int(key.split('-')[0])
            except:
                key_ = key
            else:
                key_ = f'minutes{key}'
            key_ = key_.replace('-', '_')
            print(f'\t{indent}{key_} = Column({typ})')
    indent = ''


def main():
    proxies = web.get_proxy_list(local=True)
    for game in golgg.game_data():
        # js = web.proxy_loop(game.match_details, proxies, json=True, cookies=cookies)
        js = web.html_code('https://acs.leagueoflegends.com/v1/stats/game/ESPORTSTMNT03/1443415?gameHash=4f3b0e46db9a870f&tab=overview', json=True, cookies=cookies)
        print_dict_keys(js)
        l = LolGameData.init_from_json(js)
        teams = LolGameTeamData.init_from_json(game.id, js)
        bans = LolGameTeamBansData.init_from_json(js)
        part = LolGameTeamParticipantsData.init_from_json(js)
        tm = LolGameTeamParticipantsCreepsPerMinDeltasData.init_from_json(js)
        # master = LolGameTeamParticipantsMasteriesData.init_from_json(js)
        # run = LolGameTeamParticipantsMasteriesData.init_from_json(js)


        pass


if __name__ == '__main__':
    main()
