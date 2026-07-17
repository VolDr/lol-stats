import sqlite3
import pickle
import datetime
import re
import numpy as np
import csv
import random
import matplotlib.pyplot as plt
import MySQLdb
import sys
import time
import scipy
from math import floor, ceil
DATA_for_team = "between  strftime('%Y-%m-%d', '2017-11-10') and  strftime('%Y-%m-%d', '2020-05-20')"
DATA_for_all= "between  strftime('%Y-%m-%d', '2015-12-18') and  strftime('%Y-%m-%d', '2020-05-20')"
# DATA = ""
import warnings
import math
warnings.filterwarnings("ignore")
import csaps
from scipy import stats
from collections import Counter
from scipy.interpolate import interp1d
from scipy import interpolate
from datetime import timedelta, date

def trueround(x):
    x = float(x)
    if x - floor(x) < 0.5:
        x = floor(x)
    else:
        x = ceil(x)
    return x


def get_teams_win_rate():
    with sqlite3.connect('Statistics_Analyzer.sqlite') as sqliteconn:
        cursor = sqliteconn.cursor()
        try:
            cursor.execute("DROP TABLE winrate")
        except sqlite3.OperationalError:
            pass
    for elem in get_team_names():
        get_team_win_rate(elem)

def get_team_win_rate(team):

    total_games = 0
    win_games = 0
    with sqlite3.connect('Statistics_Analyzer.sqlite') as sqliteconn:
        cursor = sqliteconn.cursor()
        cursor.execute("SELECT is_winner FROM matches_info_parsed WHERE team=? and match_date " + DATA_for_team, (team,))
        sqliteconn.commit()
        team = re.sub(' ', '_', team)
        team = re.sub('-', '', team)
        team = re.sub('\.', '', team)
        team = re.sub('!', '', team)
        for elem in cursor:
            total_games+=1
            if elem[0] == 'true':win_games+=1
        try:
            cursor.execute("CREATE TABLE winrate (team LONGTEXT, win_rate LONGTEXT)")
        except sqlite3.OperationalError:
            pass
        winrate=win_games/total_games
        cursor.execute("INSERT INTO winrate VALUES (?,?)",(team,winrate,))





def get_rois_global(parametr_list, team,server):
    P=list()
    for parametr in parametr_list:
        P.append(get_roi_global(parametr, team,server))
    return P




def is_normal(x,alpha=0.05):
    x=list(x)
    rw, p = stats.normaltest(list(x), axis=0)
    print(p)
    if p < 0.01:
       pass
       # print('distribution is not normal')
    else:
        pass
        #  print('distribution is normal')
    rw, p = stats.normaltest([np.exp(elem) for elem in x], axis=0)
    if p < 0.01:
        pass
        #   print('distribution is not log-normal')
    else:
        pass
        #  print('distribution is log-normal')
def cdf(pdf):
    pdf=sorted(pdf)
    cumulative_func=list()
    cumulative_func.append(0)
    cumulative_pdf=0
    new_pdf=list()
    for i in range(0,len(pdf)):
        if i>0:
            if pdf[i]==new_pdf[-1]:
                number_of_elem=cumulative_func[-1]
                cumulative_func.pop()
                cumulative_func.append(number_of_elem+1)
                cumulative_pdf+=1
            else:
                cumulative_pdf += 1
                cumulative_func.append(cumulative_pdf)
                new_pdf.append(pdf[i])
        else:
            cumulative_pdf += 1
            cumulative_func.append(cumulative_pdf)
            new_pdf.append(pdf[i])
    cumulative_func=cumulative_func[:-1]
    cumulative_func=[elem/max(cumulative_func) for elem in cumulative_func]
    # plt.plot(new_pdf, cumulative_func, '-')
    #    plt.show()
   # print('x=',new_pdf)
    #print('y=',cumulative_func)
    return [new_pdf,cumulative_func]
def generate_random_value(probability_distribution,length):
    random_uniform = np.random.uniform(0, 1, length)
    random_custom_distribution=list()
  #  probability_distribution[1]=[elem-probability_distribution[1][0] for elem in probability_distribution[1]]
    for elem in random_uniform:
        for i in range(0,len(probability_distribution[0])-1):
            if elem == probability_distribution[1][i]:
                random_custom_distribution.append((probability_distribution[0][i]))
            elif elem==probability_distribution[1][i+1]:
                random_custom_distribution.append((probability_distribution[0][i+1]))
            elif elem>probability_distribution[1][i] and elem<probability_distribution[1][i+1]:
                    koef=(elem-probability_distribution[1][i])/(probability_distribution[1][i+1]-probability_distribution[1][i])
                    random_custom_distribution.append(koef*(probability_distribution[0][i+1]-probability_distribution[0][i])+probability_distribution[0][i])


 #   print(len(random_uniform),'=',len(random_custom_distribution))
    return random_custom_distribution
def get_freq(x):
    x = sorted(x)
    n = 1 + int(math.log2(len(x)))
    lengh = (max(x) - min(x)) / n
    for i in range(0, len(x)):
        pass
    intervals = [min(x) + lengh * elem for elem in range(0, n + 1)]
    frequens = list()
    for i in range(0, len(intervals) - 1):
        freq = 0
        for elem in x:
            if elem >= intervals[i] and elem < intervals[i + 1] + 0.0001:
                freq = freq + 1
        frequens.append(freq)
    return frequens
def plot_freq(parameter_list):
    parameter_list.sort()
    # print(str(min(parameter_list))+" "+str(max(parameter_list)))
    number_of_intervals = trueround(1 + 3.322 * float(np.log10(len(parameter_list))))
    # number_of_intervals = 100
    interval_len = (max(parameter_list) - min(parameter_list)) / number_of_intervals


    current_x = min(parameter_list)
    X_intervals = list()
    while current_x <= max(parameter_list) + interval_len:
        X_intervals.append(current_x)
        current_x += interval_len

    # print(str(int(X_intervals[-1]))+" "+str(len(str(int(X_intervals[-1])))))
    if interval_len != 1:
        X_intervals[-1] = trueround(X_intervals[-1]) + float(int(X_intervals[-1])) / 500
    else:
        if len(X_intervals) != 2: X_intervals[-1] = trueround(X_intervals[-1]) + 0.00001
    if len(X_intervals) == 2: X_intervals.append(max(X_intervals) + interval_len)
    P = list()
    # print(X_intervals)
    for i in range(0, len(X_intervals) - 1):
        test_log = list()
        frec_all_games = 0
        for x_i in parameter_list:
            if x_i >= X_intervals[i] and x_i < X_intervals[i + 1]:
                frec_all_games += 1
                test_log.append(x_i)
        try:
            P.append(frec_all_games / len(parameter_list))
            # print("["+str(X_intervals[i])+" : "+str((X_intervals[i+1]))+")  = "+str(frec_all_games/len(parameter_list)))
            # print(test_log)
        except ZeroDivisionError:
            P.append(999)
    # print("Накопленная вероятность:  "+str(sum(P)))
    fig, ax = plt.subplots(1, 1)
    ax.set_xticks(X_intervals + [max(X_intervals) + interval_len])
    # Set ticks labels for x-axis
    # X_intervals = X_intervals[:-1]
    # X_intervals.insert(0, min(X_intervals) - interval_len)
    plt.bar([elem + interval_len / 2 for elem in X_intervals[:-1]], P, interval_len / 1.1, color='c', align='center')
    plt.grid(False)
    plt.axis([min(X_intervals), max(X_intervals), 0, max(P)+0.01])
    plt.show()
    return [ax, X_intervals, P]



def get_P_win_in_match(server,team1,team2,start_date,last_date,table_name):
    kills_in_game_team1 = list()
    times_team1 = list()
    kills_in_game_team2 = list()
    times_team2 = list()
    kills_per_min_team1 = list()
    kills_per_min_team2 = list()
    times_team1_team2 = list()
    with sqlite3.connect('Statistics_Analyzer.sqlite') as connect:
        cursor = connect.cursor()
        cursor.execute(
            "SELECT kill_adc_ally,kill_sup_ally,kill_jng_ally,kill_mid_ally,kill_top_ally,match_time FROM "+table_name+" WHERE team='"+team1+"' "
            "and server='"+server+"'"
            "  and match_date BETWEEN '"+start_date.strftime("%Y-%m-%d")+"' and '"+last_date.strftime("%Y-%m-%d")+"'")
        for elem in cursor.fetchall():
            kills = 0
            for i in range(0, 5):
                kills += len(pickle.loads(elem[i]))
            kills_in_game_team1.append(kills)
            time = re.findall('([0-9]{1,3}):([0-9]{1,3})', elem[5])
            times_team1.append(int(time[0][0]) + int((time[0][1])) / 60)
            times_team1_team2.append(int(time[0][0]) + int((time[0][1])) / 60)
        cursor.execute(
            "SELECT kill_adc_ally,kill_sup_ally,kill_jng_ally,kill_mid_ally,kill_top_ally, match_time,enemy_team FROM "+table_name+" WHERE team='"+team2+"' "
            "and server='"+server+"'"
            "  and match_date BETWEEN '"+start_date.strftime("%Y-%m-%d")+"' and '"+last_date.strftime("%Y-%m-%d")+"'")
        for elem in cursor.fetchall():
            kills = 0
            for i in range(0, 5):
                kills += len(pickle.loads(elem[i]))
            kills_in_game_team2.append(kills)
            time = re.findall('([0-9]{1,3}):([0-9]{1,3})', elem[5])
            times_team2.append(int(time[0][0]) + int((time[0][1])) / 60)
            if elem[6] != team1:
                times_team1_team2.append(int(time[0][0]) + int((time[0][1])) / 60)
    for i in range(0, len(times_team1)):
        kill_per_min = kills_in_game_team1[i] / times_team1[i]
        kills_per_min_team1.append(kill_per_min)
    for i in range(0, len(times_team2)):
        kill_per_min = kills_in_game_team2[i] / times_team2[i]
        kills_per_min_team2.append(kill_per_min)

    number_of_mathes = 1
    numbers_of_P= 1
    P=list()

    times_team1_team2_cdf = cdf(times_team1_team2)
    kills_per_min_team1_cdf = cdf(kills_per_min_team1)
    kills_per_min_team2_cdf = cdf(kills_per_min_team2)





    for number in range(0, numbers_of_P):
    #     for number in range(0,numbers_of_P):
    #         new_times = generate_random_value(times_team1_team2_cdf, number_of_mathes)
    #     team1_results = list()
    #     team2_results = list()
    #     for i in range(0, len(new_times)):
    #         rand_for_team_1 = generate_random_value(kills_per_min_team1_cdf, (int(new_times[i])))
    #         team1_results.append(sum(rand_for_team_1))
    #         rand_for_team_2 = generate_random_value(kills_per_min_team2_cdf, (int(new_times[i])))
    #         team2_results.append(sum(rand_for_team_2))
    #     match_result = list()
    #     for i in range(0, len(team2_results)):
    #         if team1_results[i] > team2_results[i]:
    #             match_result.append([1, 0, 0])
    #         elif team1_results[i] == team2_results[i]:
    #             match_result.append([0, 1, 0])
    #         elif team1_results[i] < team2_results[i]:
    #             match_result.append([0, 0, 1])
        new_times = generate_random_value(times_team1_team2_cdf,int(number_of_mathes))
        team1_score = list()
        team2_score = list()
        match_result = list()
        rand_for_team_1=list()
        rand_for_team_2 = list()
        for time in new_times:
            r1=(np.random.randint(0, 1000, size=(int(time))) / 1000)
            r2=(np.random.randint(0, 1000, size=(int(time))) / 1000)
            rand_for_team_1.append(r1)
            rand_for_team_2.append(r2)
        for j in range(0,len(new_times)):
            new_kills_per_min_team1 = list()
            new_kills_per_min_team2 = list()
            kills_per_min_for_team1=generate_random_value(kills_per_min_team1_cdf, int(new_times[j]))
            for i in range(0,len(rand_for_team_1[j])):
                new_kills_per_min_team1.append(1 if rand_for_team_1[j][i]<kills_per_min_for_team1[i] else 0)
            kills_per_min_for_team2=generate_random_value(kills_per_min_team2_cdf, int(new_times[j]))
            for i in range(0,len(rand_for_team_2[j])):
                new_kills_per_min_team2.append(1 if rand_for_team_2[j][i]<kills_per_min_for_team2[i] else 0)
            team1_score.append(sum(new_kills_per_min_team1))
            team2_score.append(sum(new_kills_per_min_team2))
        for i in range(0, len(team1_score)):
            if team1_score[i] > team2_score[i]:
                match_result.append([1, 0, 0])
            elif team1_score[i] == team2_score[i]:
                match_result.append([0, 1, 0])
            elif team1_score[i] < team2_score[i]:
                match_result.append([0, 0, 1])
        P.append([sum([row[0] for row in match_result]) / len(match_result),sum([row[2] for row in match_result]) / len(match_result)])

    return P


def get_match_roi_from_archive(server,team1,team2,start_date,last_date,match_date,table_name):
    prize_team_1=list()
    prize_team_2=list()
    with sqlite3.connect('Statistics_Analyzer.sqlite') as connect:
        cursor = connect.cursor()
        cursor.execute("SELECT odd1,odd2 FROM odds_arhive_matches WHERE team1 like ? and team2 like ? and match_date=?",(team1, team2, match_date.strftime("%Y-%m-%d")))
        data=cursor.fetchall()
        if len(data)!=0:
            for elem in data:
                odd1=float(elem[0])
                odd2=float(elem[1])
        else:
            cursor.execute("SELECT odd1,odd2 FROM odds_arhive_matches WHERE team1 like ? and team2 like ? and match_date=?",(team2, team1, match_date.strftime("%Y-%m-%d")))
            data = cursor.fetchall()
            if len(data)!=0:
                for elem in data:
                    odd1=float(elem[1])
                    odd2=float(elem[0])
            else:
               print(team2, team1, last_date)
    P=get_P_win_in_match(server, team1, team2, start_date, last_date,table_name)
    for p in P:
        prize_team_1.append(p[0]*odd1)
        prize_team_2.append(p[1] * odd2)
    return prize_team_1,prize_team_2


def daterange(date1, date2):
    dates=list()
    for n in range(int((date2 - date1).days) + 1):
        dates.append(date1 + timedelta(n))
    return dates

def get_rois(table_name,out_table):
    absolute_start_date = date(2019, 1, 1)
    PT_date_start=date(2019,2,12)
    EUW_date_start=date(2019,2,2)
    TR_date_start=date(2019,2,3)
    OCE_date_start=date(2019,2,2)
    VN_date_start = date(2019,2,17)
    BR_date_start = date(2019,1,27)
    CIS_date_start = date(2019,2,24)
    NA_date_start = date(2019,2,10)
    UK_date_start = date(2019,2,22)
    TW_date_start = date(2019,2,16)
    KR_date_start = date(2019,2,3)
    CN_date_start = date(2019,1,28)
    start_dt = date(2019, 2, 1)
    end_dt = date(2019, 5, 19)
    dates=daterange(start_dt, end_dt)
    times=list()
    timer=0
    numer_of_datas=len(dates)
    with sqlite3.connect('Statistics_Analyzer.sqlite') as connect:
        cursor = connect.cursor()
        for current_date in range(0, len(dates)):
            time1 = time.time()
            timer+=1
            cursor.execute("SELECT server,team,enemy_team,championship FROM "+table_name+" WHERE match_date='"+dates[current_date].strftime("%Y-%m-%d")+"' GROUP BY site_id")
            data=cursor.fetchall()
            for j in range(0,len(data)):
                if len(re.findall('Playoffs', data[j][3])) != 1 and data[j][0] != 'ES' and data[j][0] != 'WR' and \
                                data[j][0] != 'VN' and data[j][0] != 'PT' and data[j][0] != 'FR' and data[j][
                    0] != 'PL' and data[j][0] != 'IT' and data[j][0] != 'JP' and data[j][0] != 'LAT' and data[j][
                    3] != 'NA Academy Spring 2019' and data[j][3] != 'EU Master 2019 Spring Play-In' and data[j][
                    3] != 'LCK Summer Promotion 2019' and data[j][3] != 'EU Master Spring 2019' and data[j][
                    3] != 'LST Spring 2019':
                    if (data[j][0] == 'PT' and dates[current_date] > PT_date_start) or (
                            data[j][0] == 'EUW' and dates[current_date] > EUW_date_start) or (
                            data[j][0] == 'TR' and dates[current_date] > TR_date_start) or (
                            data[j][0] == 'OCE' and dates[current_date] > OCE_date_start) or (
                            data[j][0] == 'VN' and dates[current_date] > VN_date_start) or (
                            data[j][0] == 'BR' and dates[current_date] > BR_date_start) or (
                            data[j][0] == 'CIS' and dates[current_date] > CIS_date_start) or (
                            data[j][0] == 'NA' and dates[current_date] > NA_date_start) or (
                            data[j][0] == 'UK' and dates[current_date] > UK_date_start) or (
                            data[j][0] == 'TW' and dates[current_date] > TW_date_start) or (
                            data[j][0] == 'KR' and dates[current_date] > KR_date_start) or (
                            data[j][0] == 'CN' and dates[current_date] > CN_date_start):
                        if  data[j][0]!='SK Gaming' and data[j][1]!='FC Schalke 04' and dates[current_date]!=date(2019,3, 16):
                            if  data[j][0]!='ahq e-Sports Club' and data[j][1]!='J Team' and dates[current_date]!=date(2019,3, 31):
                                roi1,roi2=get_match_roi_from_archive(data[j][0],data[j][1],data[j][2],absolute_start_date,dates[current_date-1],
                                                           dates[current_date],table_name)
                                try:
                                    # cursor.execute("CREATE TABLE "+out_table+" (date datestring, team1 LONGTEXT,team2 LONGTEXT,roi_massive LONGTEXT, roi_m REAL,roi_g REAL, roi_v REAL, roi_s REAL, roi_k REAL)")
                                    cursor.execute("CREATE TABLE " + out_table + " (date datestring,team1 LONGTEXT,team2 LONGTEXT, roi_m REAL)")
                                except sqlite3.OperationalError:
                                    pass
                                roi1_m=np.mean(roi1)
                                roi2_m=np.mean(roi2)
                                cursor.execute("INSERT INTO " + out_table + " VALUES (?,?,?,?)", (
                                dates[current_date].strftime("%Y-%m-%d"), data[j][1], data[j][2],
                                roi1_m))
                                cursor.execute("INSERT INTO " + out_table + " VALUES (?,?,?,?)", (
                                dates[current_date].strftime("%Y-%m-%d"), data[j][2], data[j][1],
                                roi2_m))
                                connect.commit()
            time2 = time.time()
            times.append(time2 - time1)
            print('\r%3.6s%% (%s/%s) Время на один шаг: %s cек. Времени осталось: %s ч. ' % (
                timer * 100 / (numer_of_datas), str(timer), str(numer_of_datas), sum(times) / len(times),
                (numer_of_datas - timer) * (sum(times) / len(times)) / 3600), end='')







def get_real_prize(rois_table_name_roi, match_info_table,odds_table):
    roi_gs=[0.21]
    # roi_gs=list()
    # for num in range(2, 60):
    #     roi_gs.append(num / 100)
    # roi_test4 = list()
    # roi_test5 = list()
    # roi_test6 = list()

    for roi_g in roi_gs:
        start_dt = date(2019, 1, 26)
        end_dt = date(2019, 5, 19)
        dates=daterange(start_dt, end_dt)
        numer_of_datas=len(dates)
       # roi_g = 0.2
        bankroll=100
        bankroll_strategy_bigger_then_m_prop_brm=list()
        bankroll_strategy_bigger_then_m_prop_smaller_then_g_prop_brm=list()
        bankroll_strategy_max1_brm=list()
        bankroll_strategy_max1_and_g_brm=list()

        bankroll_strategy_bigger_then_m_ravn_10=list()
        bankroll_strategy_max1_10=list()
        bankroll_strategy_max2_ravn_10=list()
        bankroll_strategy_max3_ravn_10=list()
        bankroll_strategy_max2_prop_10=list()
        bankroll_strategy_max3_prop_10=list()
        bankroll_strategy_bigger_then_m_prop_10=list()
        bankroll_strategy_bigger_then_m_prop_smaller_then_g_prop_10=list()
        bankroll_strategy_bigger_then_m_prop_smaller_then_g_ravn_10=list()
        bankroll_strategy_max1_and_g_10=list()
        bankroll_strategy_max2_ravn_and_g_10=list()
        bankroll_strategy_max3_ravn_and_g_10=list()
        bankroll_strategy_max2_prop_and_g_10=list()
        bankroll_strategy_max3_prop_and_g_10=list()
        bankroll_strategy_bigger_then_m_prop_brm.append([bankroll,0])
        bankroll_strategy_bigger_then_m_prop_smaller_then_g_prop_brm.append([bankroll,0])
        bankroll_strategy_max1_brm.append([bankroll,0])
        bankroll_strategy_max1_and_g_brm.append([bankroll,0])
        bankroll_strategy_bigger_then_m_ravn_10.append([bankroll,0])
        bankroll_strategy_max1_10.append([bankroll,0])
        bankroll_strategy_max2_ravn_10.append([bankroll,0])
        bankroll_strategy_max3_ravn_10.append([bankroll,0])
        bankroll_strategy_max2_prop_10.append([bankroll,0])
        bankroll_strategy_max3_prop_10.append([bankroll,0])
        bankroll_strategy_bigger_then_m_prop_10.append([bankroll,0])
        bankroll_strategy_bigger_then_m_prop_smaller_then_g_prop_10.append([bankroll,0])
        bankroll_strategy_bigger_then_m_prop_smaller_then_g_ravn_10.append([bankroll, date(2019, 1, 25).strftime("%d-%m")])
        bankroll_strategy_max1_and_g_10.append([bankroll,0])
        bankroll_strategy_max2_ravn_and_g_10.append([bankroll,0])
        bankroll_strategy_max3_ravn_and_g_10.append([bankroll,0])
        bankroll_strategy_max2_prop_and_g_10.append([bankroll,0])
        bankroll_strategy_max3_prop_and_g_10.append([bankroll,0])


        bankroll_strategy_bigger_then_m_ravn_9=list()
        bankroll_strategy_max1_9=list()
        bankroll_strategy_max2_ravn_9=list()
        bankroll_strategy_max3_ravn_9=list()
        bankroll_strategy_max2_prop_9=list()
        bankroll_strategy_max3_prop_9=list()
        bankroll_strategy_bigger_then_m_prop_9=list()
        bankroll_strategy_bigger_then_m_prop_smaller_then_g_prop_9=list()
        bankroll_strategy_bigger_then_m_prop_smaller_then_g_ravn_9=list()
        bankroll_strategy_max1_and_g_9=list()
        bankroll_strategy_max2_ravn_and_g_9=list()
        bankroll_strategy_max3_ravn_and_g_9=list()
        bankroll_strategy_max2_prop_and_g_9=list()
        bankroll_strategy_max3_prop_and_g_9=list()
        bankroll_strategy_bigger_then_m_ravn_9.append([bankroll,0])
        bankroll_strategy_max1_9.append([bankroll,0])
        bankroll_strategy_max2_ravn_9.append([bankroll,0])
        bankroll_strategy_max3_ravn_9.append([bankroll,0])
        bankroll_strategy_max2_prop_9.append([bankroll,0])
        bankroll_strategy_max3_prop_9.append([bankroll,0])
        bankroll_strategy_bigger_then_m_prop_9.append([bankroll,0])
        bankroll_strategy_bigger_then_m_prop_smaller_then_g_prop_9.append([bankroll,0])
        bankroll_strategy_bigger_then_m_prop_smaller_then_g_ravn_9.append([bankroll, date(2019, 1, 25).strftime("%d-%m")])
        bankroll_strategy_max1_and_g_9.append([bankroll,0])
        bankroll_strategy_max2_ravn_and_g_9.append([bankroll,0])
        bankroll_strategy_max3_ravn_and_g_9.append([bankroll,0])
        bankroll_strategy_max2_prop_and_g_9.append([bankroll,0])
        bankroll_strategy_max3_prop_and_g_9.append([bankroll,0])

        bankroll_strategy_bigger_then_m_ravn_8=list()
        bankroll_strategy_max1_8=list()
        bankroll_strategy_max2_ravn_8=list()
        bankroll_strategy_max3_ravn_8=list()
        bankroll_strategy_max2_prop_8=list()
        bankroll_strategy_max3_prop_8=list()
        bankroll_strategy_bigger_then_m_prop_8=list()
        bankroll_strategy_bigger_then_m_prop_smaller_then_g_prop_8=list()
        bankroll_strategy_bigger_then_m_prop_smaller_then_g_ravn_8=list()
        bankroll_strategy_max1_and_g_8=list()
        bankroll_strategy_max2_ravn_and_g_8=list()
        bankroll_strategy_max3_ravn_and_g_8=list()
        bankroll_strategy_max2_prop_and_g_8=list()
        bankroll_strategy_max3_prop_and_g_8=list()
        bankroll_strategy_bigger_then_m_ravn_8.append([bankroll,0])
        bankroll_strategy_max1_8.append([bankroll,0])
        bankroll_strategy_max2_ravn_8.append([bankroll,0])
        bankroll_strategy_max3_ravn_8.append([bankroll,0])
        bankroll_strategy_max2_prop_8.append([bankroll,0])
        bankroll_strategy_max3_prop_8.append([bankroll,0])
        bankroll_strategy_bigger_then_m_prop_8.append([bankroll,0])
        bankroll_strategy_bigger_then_m_prop_smaller_then_g_prop_8.append([bankroll,0])
        bankroll_strategy_bigger_then_m_prop_smaller_then_g_ravn_8.append([bankroll, date(2018, 1, 25).strftime("%d-%m")])
        bankroll_strategy_max1_and_g_8.append([bankroll,0])
        bankroll_strategy_max2_ravn_and_g_8.append([bankroll,0])
        bankroll_strategy_max3_ravn_and_g_8.append([bankroll,0])
        bankroll_strategy_max2_prop_and_g_8.append([bankroll,0])
        bankroll_strategy_max3_prop_and_g_8.append([bankroll,0])



        size_of_bet_on_one_day=0.03
        day=0
        with sqlite3.connect('Statistics_Analyzer.sqlite') as connect:
            cursor = connect.cursor()
            for current_date in range(0, len(dates)):
                bets = list()
                odds_of_bets = list()
                result_of_bets = list()
                cur_date=dates[current_date]
                if cur_date!=date(2019, 5, 19):
                    next_date=dates[current_date+1]
                day+=1
                cursor.execute(
                    "SELECT date, team1,team2, roi_m,roi_g FROM "+rois_table_name_roi+" WHERE date='" + cur_date.strftime("%Y-%m-%d") + "' GROUP by team1,team2, date order by roi_m")
                data= cursor.fetchall()
                if len(data)!=0:

                    for match in data:
                        if match[3]>0: bets.append(match)
                    for match in bets:
                        cursor.execute("SELECT odd1 from "+odds_table+" where team1 like (?) and team2 like (?) and match_date=(?)",(match[1],match[2],cur_date))
                        odd1=cursor.fetchall()
                        if len(odd1)!=0:
                            odds_of_bets.append(float(odd1[0][0]))
                        else:
                            cursor.execute("SELECT odd2 from "+odds_table+" where team2 like (?) and team1 like (?) and match_date=(?)", (match[1],match[2],cur_date))
                            odd2 = cursor.fetchall()
                            if len(odd2) != 0:
                                odds_of_bets.append("---")
                                print("????")
                    for match in bets:
                        cursor.execute("SELECT is_winner FROM " + match_info_table + " WHERE team like '" + match[
                            1] + "' " "and enemy_team like '" + match[2] + "'""  and match_date = '" + match[
                                           0] + "' order by site_id")

                        win=cursor.fetchall()[0][0]
                        if win=='true':
                            result_of_bets.append(1)
                        else:
                            result_of_bets.append(0)
                    if len(bets)==len(result_of_bets) and len(bets)==len(odds_of_bets) and len(odds_of_bets)==len(result_of_bets):
                        bankroll_strategy_bigger_then_m_prop_brm.append([strategy_bigger_then_m_prop_brm(bankroll_strategy_bigger_then_m_prop_brm[-1][0], bets, odds_of_bets, result_of_bets), day])
                        bankroll_strategy_bigger_then_m_prop_smaller_then_g_prop_brm.append([strategy_bigger_then_m_prop_smaller_then_g_prop_brm(bankroll_strategy_bigger_then_m_prop_smaller_then_g_prop_brm[-1][0], bets, odds_of_bets, result_of_bets,roi_g), day])
                        bankroll_strategy_max1_brm.append([strategy_max1_brm(bankroll_strategy_max1_brm[-1][0], bets, odds_of_bets, result_of_bets), day])
                        bankroll_strategy_max1_and_g_brm.append([strategy_max1_and_g_brm(bankroll_strategy_max1_and_g_brm[-1][0], bets, odds_of_bets, result_of_bets,roi_g), day])
                        bankroll_strategy_bigger_then_m_ravn_10.append([strategy_bigger_then_m_ravn(1/10,bankroll_strategy_bigger_then_m_ravn_10[-1][0], bets, odds_of_bets, result_of_bets), day])
                        bankroll_strategy_max1_10.append([strategy_max1(1/10,bankroll_strategy_max1_10[-1][0], bets, odds_of_bets, result_of_bets), day])
                        bankroll_strategy_max2_ravn_10.append([strategy_max2_ravn(1/10,bankroll_strategy_max2_ravn_10[-1][0], bets, odds_of_bets, result_of_bets), day])
                        bankroll_strategy_max3_ravn_10.append([strategy_max3_ravn(1/10,bankroll_strategy_max3_ravn_10[-1][0], bets, odds_of_bets, result_of_bets), day])
                        bankroll_strategy_max2_prop_10.append([strategy_max2_prop(1/10,bankroll_strategy_max2_prop_10[-1][0], bets, odds_of_bets, result_of_bets), day])
                        bankroll_strategy_max3_prop_10.append([strategy_max3_prop(1/10,bankroll_strategy_max3_prop_10[-1][0], bets, odds_of_bets, result_of_bets), day])
                        bankroll_strategy_bigger_then_m_prop_10.append([strategy_bigger_then_m_prop(1/10,bankroll_strategy_bigger_then_m_prop_10[-1][0], bets, odds_of_bets, result_of_bets), day])
                        bankroll_strategy_bigger_then_m_prop_smaller_then_g_prop_10.append([strategy_bigger_then_m_prop_smaller_then_g_prop(1/10,bankroll_strategy_bigger_then_m_prop_smaller_then_g_prop_10[-1][0], bets, odds_of_bets, result_of_bets,roi_g), day])
                        bankroll_strategy_bigger_then_m_prop_smaller_then_g_ravn_10.append([strategy_bigger_then_m_prop_smaller_then_g_ravn(1/10,bankroll_strategy_bigger_then_m_prop_smaller_then_g_ravn_10[-1][0], bets, odds_of_bets, result_of_bets,roi_g), date(2019, 1, 25).strftime("%d-%m")])
                        bankroll_strategy_max1_and_g_10.append([strategy_max1_and_g(1/10,bankroll_strategy_max1_and_g_10[-1][0], bets, odds_of_bets, result_of_bets,roi_g), day])
                        bankroll_strategy_max2_ravn_and_g_10.append([strategy_max2_ravn_and_g(1/10,bankroll_strategy_max2_ravn_and_g_10[-1][0], bets, odds_of_bets, result_of_bets,roi_g), day])
                        bankroll_strategy_max3_ravn_and_g_10.append([strategy_max3_ravn_and_g(1/10,bankroll_strategy_max3_ravn_and_g_10[-1][0], bets, odds_of_bets, result_of_bets,roi_g), day])
                        bankroll_strategy_max2_prop_and_g_10.append([strategy_max2_prop_and_g(1/10,bankroll_strategy_max2_prop_and_g_10[-1][0], bets, odds_of_bets, result_of_bets,roi_g), day])
                        bankroll_strategy_max3_prop_and_g_10.append([strategy_max3_prop_and_g(1/10,bankroll_strategy_max3_prop_and_g_10[-1][0], bets, odds_of_bets, result_of_bets,roi_g), day])
                        bankroll_strategy_bigger_then_m_ravn_9.append([strategy_bigger_then_m_ravn(1/9,bankroll_strategy_bigger_then_m_ravn_9[-1][0], bets, odds_of_bets, result_of_bets), day])
                        bankroll_strategy_max1_9.append([strategy_max1(1/9,bankroll_strategy_max1_9[-1][0], bets, odds_of_bets, result_of_bets), day])
                        bankroll_strategy_max2_ravn_9.append([strategy_max2_ravn(1/9,bankroll_strategy_max2_ravn_9[-1][0], bets, odds_of_bets, result_of_bets), day])
                        bankroll_strategy_max3_ravn_9.append([strategy_max3_ravn(1/9,bankroll_strategy_max3_ravn_9[-1][0], bets, odds_of_bets, result_of_bets), day])
                        bankroll_strategy_max2_prop_9.append([strategy_bigger_then_m_prop(1/9,bankroll_strategy_max2_prop_9[-1][0], bets, odds_of_bets, result_of_bets), day])
                        bankroll_strategy_max3_prop_9.append([strategy_max3_prop(1/9,bankroll_strategy_max3_prop_9[-1][0], bets, odds_of_bets, result_of_bets), day])
                        bankroll_strategy_bigger_then_m_prop_9.append([strategy_bigger_then_m_prop(1/9,bankroll_strategy_bigger_then_m_prop_9[-1][0], bets, odds_of_bets, result_of_bets), day])
                        bankroll_strategy_bigger_then_m_prop_smaller_then_g_prop_9.append([strategy_bigger_then_m_prop_smaller_then_g_prop(1/9,bankroll_strategy_bigger_then_m_prop_smaller_then_g_prop_9[-1][0], bets, odds_of_bets, result_of_bets,roi_g), day])
                        bankroll_strategy_bigger_then_m_prop_smaller_then_g_ravn_9.append([strategy_bigger_then_m_prop_smaller_then_g_ravn(1/9,bankroll_strategy_bigger_then_m_prop_smaller_then_g_ravn_9[-1][0], bets, odds_of_bets, result_of_bets,roi_g), date(2019, 1, 25).strftime("%d-%m")])
                        bankroll_strategy_max1_and_g_9.append([strategy_max1_and_g(1/9,bankroll_strategy_max1_and_g_9[-1][0], bets, odds_of_bets, result_of_bets,roi_g), day])
                        bankroll_strategy_max2_ravn_and_g_9.append([strategy_max2_ravn_and_g(1/9,bankroll_strategy_max2_ravn_and_g_9[-1][0], bets, odds_of_bets, result_of_bets,roi_g), day])
                        bankroll_strategy_max3_ravn_and_g_9.append([strategy_max3_ravn_and_g(1/9,bankroll_strategy_max3_ravn_and_g_9[-1][0], bets, odds_of_bets, result_of_bets,roi_g), day])
                        bankroll_strategy_max2_prop_and_g_9.append([strategy_max2_prop_and_g(1/9,bankroll_strategy_max2_prop_and_g_9[-1][0], bets, odds_of_bets, result_of_bets,roi_g), day])
                        bankroll_strategy_max3_prop_and_g_9.append([strategy_max3_prop_and_g(1/9,bankroll_strategy_max3_prop_and_g_9[-1][0], bets, odds_of_bets, result_of_bets,roi_g), day])
                        bankroll_strategy_bigger_then_m_ravn_8.append([strategy_bigger_then_m_ravn(1/8,bankroll_strategy_bigger_then_m_ravn_8[-1][0], bets, odds_of_bets, result_of_bets), day])
                        bankroll_strategy_max1_8.append([strategy_max1(1/8,bankroll_strategy_max1_8[-1][0], bets, odds_of_bets, result_of_bets), day])
                        bankroll_strategy_max2_ravn_8.append([strategy_max2_ravn(1/8,bankroll_strategy_max2_ravn_8[-1][0], bets, odds_of_bets, result_of_bets), day])
                        bankroll_strategy_max3_ravn_8.append([strategy_max3_ravn(1/8,bankroll_strategy_max3_ravn_8[-1][0], bets, odds_of_bets, result_of_bets), day])
                        bankroll_strategy_max2_prop_8.append([strategy_max2_prop(1/8,bankroll_strategy_max2_prop_8[-1][0], bets, odds_of_bets, result_of_bets), day])
                        bankroll_strategy_max3_prop_8.append([strategy_max3_prop(1/8,bankroll_strategy_max3_prop_8[-1][0], bets, odds_of_bets, result_of_bets), day])
                        bankroll_strategy_bigger_then_m_prop_8.append([strategy_bigger_then_m_prop(1/8,bankroll_strategy_bigger_then_m_prop_8[-1][0], bets, odds_of_bets, result_of_bets), day])
                        bankroll_strategy_bigger_then_m_prop_smaller_then_g_prop_8.append([strategy_bigger_then_m_prop_smaller_then_g_prop(1/8,bankroll_strategy_bigger_then_m_prop_smaller_then_g_prop_8[-1][0], bets, odds_of_bets, result_of_bets,roi_g), day])
                        bankroll_strategy_bigger_then_m_prop_smaller_then_g_ravn_8.append([strategy_bigger_then_m_prop_smaller_then_g_ravn(1/8,bankroll_strategy_bigger_then_m_prop_smaller_then_g_ravn_8[-1][0], bets, odds_of_bets, result_of_bets,roi_g), date(2019, 1, 25).strftime("%d-%m")])
                        bankroll_strategy_max1_and_g_8.append([strategy_max1_and_g(1/8,bankroll_strategy_max1_and_g_8[-1][0], bets, odds_of_bets, result_of_bets,roi_g), day])
                        bankroll_strategy_max2_ravn_and_g_8.append([strategy_max2_ravn_and_g(1/8,bankroll_strategy_max2_ravn_and_g_8[-1][0], bets, odds_of_bets, result_of_bets,roi_g), day])
                        bankroll_strategy_max3_ravn_and_g_8.append([strategy_max3_ravn_and_g(1/8,bankroll_strategy_max3_ravn_and_g_8[-1][0], bets, odds_of_bets, result_of_bets,roi_g), day])
                        bankroll_strategy_max2_prop_and_g_8.append([strategy_max2_prop_and_g(1/8,bankroll_strategy_max2_prop_and_g_8[-1][0], bets, odds_of_bets, result_of_bets,roi_g), day])
                        bankroll_strategy_max3_prop_and_g_8.append([strategy_max3_prop_and_g(1/8,bankroll_strategy_max3_prop_and_g_8[-1][0], bets, odds_of_bets, result_of_bets,roi_g), day])


                    else:
                        print('???')
            # roi_test4.append(bankroll_strategy_bigger_then_m_prop_smaller_then_g_prop_10[-1][0])
            # roi_test5.append(bankroll_strategy_bigger_then_m_prop_smaller_then_g_ravn_10[-1][0])
            # roi_test6.append(bankroll_strategy_max1_and_g_10[-1][0])

    # return [elem[0] for elem in bankroll_strategy_max1_and_g_brm]
    # plt.subplot(311)
    # plt.plot(roi_gs,roi_test4, '-')
    # plt.subplot(312)
    # plt.plot(roi_gs,roi_test5, '-')
    # plt.subplot(313)
    # plt.plot(roi_gs,roi_test6, '-')

        plt.subplot(3,2,1)
        plt.plot([elem[1] for elem in bankroll_strategy_max1_8], [elem[0] for elem in bankroll_strategy_max1_9], '-')
        plt.subplot(3,2,2)
        plt.plot([elem[1] for elem in bankroll_strategy_max1_brm], [elem[0] for elem in bankroll_strategy_max1_brm], '-')
        plt.subplot(3,2,3)
        plt.plot([elem[1] for elem in bankroll_strategy_bigger_then_m_prop_8], [elem[0] for elem in bankroll_strategy_bigger_then_m_prop_brm], '-')
        plt.subplot(3,2,4)
        plt.plot([elem[1] for elem in bankroll_strategy_bigger_then_m_prop_brm], [elem[0] for elem in bankroll_strategy_bigger_then_m_prop_8], '-')
        plt.subplot(3,2,5)
        plt.plot([elem[1] for elem in bankroll_strategy_bigger_then_m_prop_smaller_then_g_prop_8], [elem[0] for elem in bankroll_strategy_bigger_then_m_prop_smaller_then_g_prop_8], '-')
        plt.subplot(3,2,6)
        plt.plot([elem[1] for elem in bankroll_strategy_bigger_then_m_prop_smaller_then_g_prop_brm], [elem[0] for elem in bankroll_strategy_bigger_then_m_prop_smaller_then_g_prop_brm], '-')


    plt.show()

    pass


def strategy_bigger_then_m_ravn(size_of_bet_on_one_day,bankroll,bets,odds_of_bets,result_of_bets):
    new_bankroll=bankroll
    number_of_odds = 0
    list_of_bets=list()
    for bet in range(0, len(bets)):
        if bets[bet][3] >= 1:
            number_of_odds += 1
    if number_of_odds != 0:
        size_of_bet_on_one_match = size_of_bet_on_one_day / number_of_odds
    elif number_of_odds==0:
        size_of_bet_on_one_match=0
    for bet in range(0, len(bets)):
        if bets[bet][3] >= 1:
            new_bankroll += odds_of_bets[bet] * result_of_bets[bet] * size_of_bet_on_one_match * bankroll
            list_of_bets.append(size_of_bet_on_one_match * bankroll)
    new_bankroll = new_bankroll - sum(list_of_bets)
    return new_bankroll
def strategy_max1(size_of_bet_on_one_day,bankroll,bets,odds_of_bets,result_of_bets):
    new_bankroll=bankroll
    size_of_bet_on_one_match = size_of_bet_on_one_day
    list_of_bets=list()
    max_m = max([elem[3] for elem in bets])
    for bet in range(0, len(bets)):
        if bets[bet][3] == max_m and bets[bet][3] >=1:
            new_bankroll += odds_of_bets[bet] * result_of_bets[bet] * size_of_bet_on_one_match * bankroll
            list_of_bets.append(size_of_bet_on_one_match * bankroll)
    new_bankroll = new_bankroll - sum(list_of_bets)
    return new_bankroll
def strategy_max2_ravn(size_of_bet_on_one_day,bankroll,bets,odds_of_bets,result_of_bets):
    new_bankroll=bankroll
    list_of_bets=list()
    size_of_bet_on_one_match = size_of_bet_on_one_day/2
    max_m1 = max(sorted([elem[3] for elem in bets]))
    max_m2 = max(sorted([elem[3] for elem in bets][:-1]))
    if max_m2==max_m1:
        print('pook')
        max_m2=max(sorted([elem[3] for elem in bets][:-2]))
        if max_m2==max_m1:
            max_m2=max(sorted([elem[3] for elem in bets][:-3]))
    for bet in range(0, len(bets)):
        if (bets[bet][3] == max_m1 or bets[bet][3] == max_m2) and bets[bet][3] >=1:
            new_bankroll += odds_of_bets[bet] * result_of_bets[bet] * size_of_bet_on_one_match * bankroll
            list_of_bets.append(size_of_bet_on_one_match * bankroll)
    new_bankroll = new_bankroll - sum(list_of_bets)
    return new_bankroll
def strategy_max3_ravn(size_of_bet_on_one_day,bankroll,bets,odds_of_bets,result_of_bets):
    new_bankroll=bankroll
    list_of_bets=list()
    size_of_bet_on_one_match = size_of_bet_on_one_day/3
    max_m1 = max(sorted([elem[3] for elem in bets]))
    max_m2 = max(sorted([elem[3] for elem in bets][:-1]))
    try:
        max_m3 = max(sorted([elem[3] for elem in bets][:-2]))
    except ValueError:
        max_m3=max_m2
    if max_m2==max_m1:
        max_m2=max(sorted([elem[3] for elem in bets][:-2]))
        try:
            max_m3 = max(sorted([elem[3] for elem in bets][:-3]))
        except ValueError:
            max_m3 = max_m2
        if max_m2==max_m1:
            max_m2=max(sorted([elem[3] for elem in bets][:-3]))
            try:
                max_m3 = max(sorted([elem[3] for elem in bets][:-4]))
            except ValueError:
                max_m3 = max_m2


    for bet in range(0, len(bets)):
        if (bets[bet][3] == max_m1 or bets[bet][3]== max_m2 or bets[bet][3] == max_m3) and bets[bet][3] >=1:
            new_bankroll += odds_of_bets[bet] * result_of_bets[bet] * size_of_bet_on_one_match * bankroll
            list_of_bets.append(size_of_bet_on_one_match * bankroll)
    new_bankroll = new_bankroll - sum(list_of_bets)
    return new_bankroll
def strategy_max2_prop(size_of_bet_on_one_day,bankroll,bets,odds_of_bets,result_of_bets):
    new_bankroll = bankroll
    actual_bets = list()
    size_of_bet_on_one_match = size_of_bet_on_one_day/2
    max_m1 = max(sorted([elem[3] for elem in bets]))
    max_m2 = max(sorted([elem[3] for elem in bets][:-1]))
    list_of_bets = list()
    for bet in range(0, len(bets)):
        if (bets[bet][3] == max_m1 or bets[bet][3]== max_m2) and bets[bet][3] >=1:
            actual_bets.append(bets[bet])
    for bet in range(0, len(bets)):
        if (bets[bet][3] == max_m1 or bets[bet][3] == max_m2) and bets[bet][3] >=1:
            new_bankroll += odds_of_bets[bet] * result_of_bets[bet] * size_of_bet_on_one_match * bankroll
            list_of_bets.append(size_of_bet_on_one_match * bankroll)
    new_bankroll = new_bankroll - sum(list_of_bets)
    return new_bankroll
def strategy_max3_prop(size_of_bet_on_one_day,bankroll,bets,odds_of_bets,result_of_bets):
    new_bankroll=bankroll
    actual_bets=list()
    size_of_bet_on_one_match = size_of_bet_on_one_day/3
    max_m1 = max(sorted([elem[3] for elem in bets]))
    max_m2 = max(sorted([elem[3] for elem in bets][:-1]))
    try:
        max_m3 = max(sorted([elem[3] for elem in bets][:-2]))
    except ValueError:
        max_m3=max_m2
    list_of_bets = list()
    for bet in range(0, len(bets)):
        if (bets[bet][3] == max_m1 or bets[bet][3]== max_m2 or bets[bet][3] == max_m3) and bets[bet][3] >=1:
            actual_bets.append(bets[bet])
    sum_m = sum([elem[3] for elem in actual_bets])
    for bet in range(0, len(bets)):
        if (bets[bet][3] == max_m1 or bets[bet][3] == max_m2 or bets[bet][3] == max_m3) and bets[bet][3] >= 1:
            size_of_bet_on_one_match=(bets[bet][3] / sum_m)
            new_bankroll += odds_of_bets[bet] * result_of_bets[bet] * size_of_bet_on_one_match * bankroll
            list_of_bets.append(size_of_bet_on_one_match * bankroll)
    new_bankroll = new_bankroll - sum(list_of_bets)
    return new_bankroll
def strategy_bigger_then_m_prop(size_of_bet_on_one_day,bankroll,bets,odds_of_bets,result_of_bets):
    new_bankroll=bankroll
    actual_bets=list()
    for bet in range(0, len(bets)):
        if bets[bet][3] >= 1:
            actual_bets.append(bets[bet])
    sum_m = sum([elem[3] for elem in actual_bets])
    list_of_bets=list()
    for bet in range (0,len(bets)):
        if bets[bet][3]>=1:
            size_of_bet_on_one_match=(bets[bet][3] / sum_m)
            new_bankroll+=odds_of_bets[bet]*result_of_bets[bet]*size_of_bet_on_one_day*bankroll*size_of_bet_on_one_match
            list_of_bets.append(size_of_bet_on_one_day*bankroll*size_of_bet_on_one_match)
    new_bankroll = new_bankroll - sum(list_of_bets)
    return new_bankroll
def strategy_bigger_then_m_prop_smaller_then_g_prop(size_of_bet_on_one_day,bankroll,bets,odds_of_bets,result_of_bets,roi_g):
    list_of_bets=list()
    new_bankroll=bankroll
    actual_bets = list()
    for bet in range(0, len(bets)):
        if bets[bet][3] > 1 and bets[bet][4] <= roi_g:
            actual_bets.append(bets[bet])
    sum_m = sum([elem[3] for elem in actual_bets])
    for bet in range(0, len(bets)):
        if bets[bet][3] > 1 and bets[bet][4] <= roi_g:
            size_of_bet_on_one_match = (bets[bet][3] / sum_m)
            new_bankroll += odds_of_bets[bet] * result_of_bets[bet] * size_of_bet_on_one_day * bankroll * size_of_bet_on_one_match
            list_of_bets.append(size_of_bet_on_one_day*bankroll*size_of_bet_on_one_match)
    new_bankroll = new_bankroll - sum(list_of_bets)
    return new_bankroll
def strategy_bigger_then_m_prop_smaller_then_g_ravn(size_of_bet_on_one_day,bankroll,bets,odds_of_bets,result_of_bets,roi_g):
    new_bankroll=bankroll
    number_of_odds = 0
    list_of_bets=list()
    for bet in range(0, len(bets)):
        if bets[bet][3] >= 1 and bets[bet][4] <= roi_g:
            number_of_odds += 1
    if number_of_odds != 0:
        size_of_bet_on_one_match = size_of_bet_on_one_day / number_of_odds
    elif number_of_odds==0:
        size_of_bet_on_one_match=0
    for bet in range(0, len(bets)):
        if bets[bet][3] >= 1 and bets[bet][4] <= roi_g:
            new_bankroll += odds_of_bets[bet] * result_of_bets[bet] * size_of_bet_on_one_match * bankroll
            list_of_bets.append(size_of_bet_on_one_match * bankroll)
    new_bankroll = new_bankroll - sum(list_of_bets)
    return new_bankroll
def strategy_max1_and_g(size_of_bet_on_one_day,bankroll,bets,odds_of_bets,result_of_bets,roi_g):
    new_bankroll=bankroll
    size_of_bet_on_one_match = size_of_bet_on_one_day
    list_of_bets=list()
    max_m = max([elem[3] for elem in bets])
    for bet in range(0, len(bets)):
        if bets[bet][3] == max_m and bets[bet][3] >=1  and bets[bet][4] <= roi_g:
            new_bankroll += odds_of_bets[bet] * result_of_bets[bet] * size_of_bet_on_one_match * bankroll
            list_of_bets.append(size_of_bet_on_one_match * bankroll)
    new_bankroll = new_bankroll - sum(list_of_bets)
    return new_bankroll
def strategy_max2_ravn_and_g(size_of_bet_on_one_day,bankroll,bets,odds_of_bets,result_of_bets,roi_g):
    new_bankroll=bankroll
    list_of_bets=list()
    size_of_bet_on_one_match = size_of_bet_on_one_day/2
    max_m1 = max(sorted([elem[3] for elem in bets]))
    max_m2 = max(sorted([elem[3] for elem in bets][:-1]))
    for bet in range(0, len(bets)):
        if (bets[bet][3] == max_m1 or bets[bet][3] == max_m2) and bets[bet][3] >=1 and bets[bet][4] <= roi_g:
            new_bankroll += odds_of_bets[bet] * result_of_bets[bet] * size_of_bet_on_one_match * bankroll
            list_of_bets.append(size_of_bet_on_one_match * bankroll)
    new_bankroll = new_bankroll - sum(list_of_bets)
    return new_bankroll
def strategy_max3_ravn_and_g(size_of_bet_on_one_day,bankroll,bets,odds_of_bets,result_of_bets,roi_g):
    new_bankroll=bankroll
    list_of_bets=list()
    size_of_bet_on_one_match = size_of_bet_on_one_day/3
    max_m1 = max(sorted([elem[3] for elem in bets]))
    max_m2 = max(sorted([elem[3] for elem in bets][:-1]))
    try:
        max_m3 = max(sorted([elem[3] for elem in bets][:-2]))
    except ValueError:
        max_m3=max_m2
    for bet in range(0, len(bets)):
        if (bets[bet][3] == max_m1 or bets[bet][3]== max_m2 or bets[bet][3] == max_m3) and bets[bet][3] >=1 and bets[bet][4] <= roi_g:
            new_bankroll += odds_of_bets[bet] * result_of_bets[bet] * size_of_bet_on_one_match * bankroll
            list_of_bets.append(size_of_bet_on_one_match * bankroll)
    new_bankroll = new_bankroll - sum(list_of_bets)
    return new_bankroll
def strategy_max2_prop_and_g(size_of_bet_on_one_day,bankroll,bets,odds_of_bets,result_of_bets,roi_g):
    new_bankroll = bankroll
    actual_bets = list()
    size_of_bet_on_one_match = size_of_bet_on_one_day/2
    max_m1 = max(sorted([elem[3] for elem in bets]))
    max_m2 = max(sorted([elem[3] for elem in bets][:-1]))
    list_of_bets = list()
    for bet in range(0, len(bets)):
        if (bets[bet][3] == max_m1 or bets[bet][3]== max_m2) and bets[bet][3] >=1  and bets[bet][4] <= roi_g:
            actual_bets.append(bets[bet])
    for bet in range(0, len(bets)):
        if (bets[bet][3] == max_m1 or bets[bet][3] == max_m2) and bets[bet][3] >=1  and bets[bet][4] <= roi_g:
            new_bankroll += odds_of_bets[bet] * result_of_bets[bet] * size_of_bet_on_one_match * bankroll
            list_of_bets.append(size_of_bet_on_one_match * bankroll)
    new_bankroll = new_bankroll - sum(list_of_bets)
    return new_bankroll
def strategy_max3_prop_and_g(size_of_bet_on_one_day,bankroll,bets,odds_of_bets,result_of_bets,roi_g):
    new_bankroll=bankroll
    actual_bets=list()
    size_of_bet_on_one_match = size_of_bet_on_one_day/3
    max_m1 = max(sorted([elem[3] for elem in bets]))
    max_m2 = max(sorted([elem[3] for elem in bets][:-1]))
    try:
        max_m3 = max(sorted([elem[3] for elem in bets][:-2]))
    except ValueError:
        max_m3=max_m2
    list_of_bets = list()
    for bet in range(0, len(bets)):
        if (bets[bet][3] == max_m1 or bets[bet][3]== max_m2 or bets[bet][3] == max_m3) and bets[bet][3] >=1 and bets[bet][4] <= roi_g:
            actual_bets.append(bets[bet])
    sum_m = sum([elem[3] for elem in actual_bets])
    for bet in range(0, len(bets)):
        if (bets[bet][3] == max_m1 or bets[bet][3] == max_m2 or bets[bet][3] == max_m3) and bets[bet][3] >= 1 and bets[bet][4] <= roi_g:
            size_of_bet_on_one_match=(bets[bet][3] / sum_m)
            new_bankroll += odds_of_bets[bet] * result_of_bets[bet] * size_of_bet_on_one_match * bankroll
            list_of_bets.append(size_of_bet_on_one_match * bankroll)
    new_bankroll = new_bankroll - sum(list_of_bets)
    return new_bankroll
def strategy_bigger_then_m_prop_brm(bankroll,bets,odds_of_bets,result_of_bets):
    new_bankroll=bankroll
    if bankroll<100:
        size_of_bet_on_one_day= 12
    elif bankroll>=100 and bankroll<200:
        size_of_bet_on_one_day= 24
    elif bankroll>=200 and bankroll<400:
        size_of_bet_on_one_day= 48
    elif bankroll >= 400 and bankroll < 800:
        size_of_bet_on_one_day = 48
    elif bankroll >= 800 and bankroll < 1600:
        size_of_bet_on_one_day = 96
    elif bankroll >= 1600:
        size_of_bet_on_one_day = 192
    actual_bets=list()
    for bet in range(0, len(bets)):
        if bets[bet][3] >= 1:
            actual_bets.append(bets[bet])
    sum_m = sum([elem[3] for elem in actual_bets])
    list_of_bets=list()
    for bet in range (0,len(bets)):
        if bets[bet][3]>=1:
            size_of_bet_on_one_match=(bets[bet][3] / sum_m)
            new_bankroll+=odds_of_bets[bet]*result_of_bets[bet]*size_of_bet_on_one_day*size_of_bet_on_one_match
            list_of_bets.append(size_of_bet_on_one_day*size_of_bet_on_one_match)
    new_bankroll = new_bankroll - sum(list_of_bets)
    return new_bankroll
def strategy_bigger_then_m_prop_smaller_then_g_prop_brm(bankroll,bets,odds_of_bets,result_of_bets,roi_g):
    list_of_bets=list()
    new_bankroll=bankroll
    if bankroll<100:
        size_of_bet_on_one_day= 12
    elif bankroll>=100 and bankroll<200:
        size_of_bet_on_one_day= 24
    elif bankroll>=200 and bankroll<400:
        size_of_bet_on_one_day= 48
    elif bankroll >= 400 and bankroll < 800:
        size_of_bet_on_one_day = 48
    elif bankroll >= 800 and bankroll < 1600:
        size_of_bet_on_one_day = 96
    elif bankroll >= 1600:
        size_of_bet_on_one_day = 192
    list_of_bets = list()
    actual_bets = list()
    for bet in range(0, len(bets)):
        if bets[bet][3] > 1 and bets[bet][4] <= roi_g:
            actual_bets.append(bets[bet])
    sum_m = sum([elem[3] for elem in actual_bets])
    for bet in range(0, len(bets)):
        if bets[bet][3] > 1 and bets[bet][4] <= roi_g:
            size_of_bet_on_one_match = (bets[bet][3] / sum_m)
            new_bankroll += odds_of_bets[bet] * result_of_bets[
                bet] * size_of_bet_on_one_day  * size_of_bet_on_one_match
            list_of_bets.append(size_of_bet_on_one_day  * size_of_bet_on_one_match)
    new_bankroll = new_bankroll - sum(list_of_bets)
    return new_bankroll
def strategy_max1_brm(bankroll,bets,odds_of_bets,result_of_bets):
    new_bankroll=bankroll
    if bankroll<100:
        size_of_bet_on_one_day= 12
    elif bankroll>=100 and bankroll<200:
        size_of_bet_on_one_day= 24
    elif bankroll>=200 and bankroll<400:
        size_of_bet_on_one_day= 48
    elif bankroll >= 400 and bankroll < 800:
        size_of_bet_on_one_day = 48
    elif bankroll >= 800 and bankroll < 1600:
        size_of_bet_on_one_day = 96
    elif bankroll >= 1600:
        size_of_bet_on_one_day = 192
    new_bankroll = bankroll
    size_of_bet_on_one_match = size_of_bet_on_one_day
    list_of_bets = list()
    max_m = max([elem[3] for elem in bets])
    for bet in range(0, len(bets)):
        if bets[bet][3] == max_m and bets[bet][3] >= 1:
            new_bankroll += odds_of_bets[bet] * result_of_bets[bet] * size_of_bet_on_one_match
            list_of_bets.append(size_of_bet_on_one_match )
    new_bankroll = new_bankroll - sum(list_of_bets)
    return new_bankroll
def strategy_max1_and_g_brm(bankroll,bets,odds_of_bets,result_of_bets,roi_g):
    new_bankroll=bankroll
    if bankroll < 100:
        size_of_bet_on_one_day = 12
    elif bankroll >= 100 and bankroll < 200:
        size_of_bet_on_one_day = 24
    elif bankroll >= 200 and bankroll < 400:
        size_of_bet_on_one_day = 48
    elif bankroll >= 400 and bankroll < 800:
        size_of_bet_on_one_day = 48
    elif bankroll >= 800 and bankroll < 1600:
        size_of_bet_on_one_day = 96
    elif bankroll >= 1600:
        size_of_bet_on_one_day = 192
    size_of_bet_on_one_match = size_of_bet_on_one_day
    list_of_bets = list()
    max_m = max([elem[3] for elem in bets])
    for bet in range(0, len(bets)):
        if bets[bet][3] == max_m and bets[bet][3] >= 1 and bets[bet][4] <= roi_g:
            new_bankroll += odds_of_bets[bet] * result_of_bets[bet] * size_of_bet_on_one_match
            list_of_bets.append(size_of_bet_on_one_match)
    new_bankroll = new_bankroll - sum(list_of_bets)
    return new_bankroll
def strategy_v5_brm(bankroll,bets,odds_of_bets,result_of_bets,roi_g):
    new_bankroll=bankroll
    if bankroll<100:
        size_of_bet_on_match= 12
    elif bankroll>=100 and bankroll<200:
        size_of_bet_on_match= 24
    elif bankroll>=200 and bankroll<400:
        size_of_bet_on_match= 48
    elif bankroll >= 400 and bankroll < 800:
        size_of_bet_on_match = 48
    elif bankroll >= 800 and bankroll < 1600:
        size_of_bet_on_match = 96
    elif bankroll >= 1600:
        size_of_bet_on_match = 192
    number_of_odds = 0

    actual_bets = list()
    for bet in range(0, len(bets)):
        m=bets[bet][3]
        g=bets[bet][4]
        if bets[bet][3] > 1 and bets[bet][4] <= roi_g:
            actual_bets.append(bets[bet])
    sum_m = sum([elem[3] for elem in actual_bets])
    for bet in range(0, len(bets)):
        if bets[bet][3] > 1 and bets[bet][4] <= roi_g:
            size_of_bet_on_one_match = (bets[bet][3] / sum_m)
            number_of_odds += 1
            new_bankroll += odds_of_bets[bet] * result_of_bets[bet]*size_of_bet_on_match
    new_bankroll=new_bankroll-number_of_odds*size_of_bet_on_match
    return new_bankroll
def strategy_v5_kelly(bankroll,bets,odds_of_bets,result_of_bets,roi_g):
    new_bankroll=bankroll
    size_of_odds=list()
    size_of_bet_on_one_day=0.1
    number_of_odds = 0
    for bet in range(0, len(bets)):
        if bets[bet][3] > 1 and bets[bet][4] <= roi_g:
            number_of_odds += 1
            new_bankroll += odds_of_bets[bet] * result_of_bets[bet]*((bets[bet][3] -1)/(odds_of_bets[bet]-1))*bankroll*size_of_bet_on_one_day
            size_of_odds.append(((bets[bet][3] -1)/(odds_of_bets[bet]-1))*bankroll*size_of_bet_on_one_day)
    if number_of_odds!=0:
        new_bankroll=new_bankroll-sum(size_of_odds)
    return new_bankroll
def strategy_v6_brm(bankroll,bets,odds_of_bets,result_of_bets,roi_g):
    new_bankroll=bankroll
    if bankroll<100:
        size_of_bet_on_match= 12
    elif bankroll>=100 and bankroll<200:
        size_of_bet_on_match= 24
    elif bankroll>=200 and bankroll<400:
        size_of_bet_on_match= 48
    elif bankroll >= 400 and bankroll < 800:
        size_of_bet_on_match = 48
    elif bankroll >= 800 and bankroll < 1600:
        size_of_bet_on_match = 96
    elif bankroll >= 1600:
        size_of_bet_on_match = 192

    number_of_odds = 0
    actual_bets = list()
    max_m = max([elem[3] for elem in bets])
    for bet in range(0, len(bets)):
        if bets[bet][3] == max_m and bets[bet][4] <= roi_g:
            number_of_odds += 1
            new_bankroll += odds_of_bets[bet] * result_of_bets[bet] * size_of_bet_on_match
    new_bankroll=new_bankroll-number_of_odds*size_of_bet_on_match
    return new_bankroll


def team_selection_strategy(strategy_name,rois_list):
    pass





def main():
    get_rois('matches_info_parsed','roi_10000_2')
    get_real_prize('rois4','matches_info_parsed','odds_arhive_mathes')



    # get_match_roi_from_archive('EUW', 'Splyce', 'G2 Esports', '2019-01-10', '2019-03-07', '2019-03-08', '2019-03-09')
    #  test=get_P_win_in_match('NA','TSM','CLG','2019-01-01','2019-03-01','matches_info_parsed')
    # get_real_prize('rois_for_test_fantasy1', 'matches_info_parsed_fantasy1','odds_arhive_mathes_fantasy')




    # for i in range(66,88):
    #     get_new_rois_fantasy_for_test('matches_info_parsed_fantasy_ravnie_'+str(i))
    #     get_rois('matches_info_parsed_fantasy_ravnie_' + str(i),'rois_for_test_fantasy_ravnie_'+str(i))
        # print('matches_info_parsed_for_test' + str(i))



    # for i in range(33,66):
    #     get_rois_fantasy_bigger_fois('matches_info_parsed_for_test'+str(i),'rois_for_test_fantasy_bigger_fois_'+str(i))


    # get_new_odds_arhive_mathes_for_test('odds_arhive_mathes_fantasy')
    # for i in range(1,100):
    #     get_new_rois_fantasy_for_test('matches_info_parsed_fantasy' + str(i))

    # start_date = date(2019, 1, 1).strftime("%Y-%m-%d")
    # last_date = '2019-05-15'
    # with sqlite3.connect('Statistics_Analyzer.sqlite') as connect:
    #     cursor = connect.cursor()
    #     cursor.execute(
    #                 "SELECT team, enemy_team, championship, server, kill_adc_ally,kill_sup_ally,kill_jng_ally,kill_mid_ally,kill_top_ally, match_time,match_date FROM matches_info_parsed WHERE match_date BETWEEN '" + start_date + "' and '" + last_date + "'")
    #     for elem in cursor.fetchall():
    #         team_kills=0
    #         team_kills+=(len(pickle.loads(elem[4])))
    #         team_kills +=(len(pickle.loads(elem[5])))
    #         team_kills +=(len(pickle.loads(elem[6])))
    #         team_kills +=(len(pickle.loads(elem[7])))
    #         team_kills +=(len(pickle.loads(elem[8])))
    #         try:
    #             cursor.execute("CREATE TABLE inf_mathes ( match_date timestring, team VARCHAR,enemy_team VARCHAR,server VARCHAR, match_time timestring,score VARCHAR)")
    #         except:
    #             pass
    #         if elem[3]=='EUW' or elem[3]=='NA' or elem[3]=="KR" or elem[3]=='OCE' or elem[3]=='CIS':
    #             cursor.execute("INSERT INTO inf_mathes ( match_date,  team, enemy_team, server, match_time,score) values (?,?,?,?,?,?)", (elem[10],elem[0],elem[1],elem[3],elem[9],team_kills))

    #
    # get_real_prize('rois4','matches_info_parsed')

# get_rois('matches_info_parsed_for_test1', 'rois_for_test1')
#     get_P_win_in_match('EUW', 'Misfits', 'G2 Esports', '2017-01-01', '2019-01-01', 'matches_info_parsed')

    srednee=list()
    Srednee=list()
    Maximalnoe=list()
    Minimalnoe=list()
    last_prize=list()
    for i in range(1, 26):
        srednee.append(get_real_prize('rois_for_test_fantasy_bigger_fois_'+str(i),'matches_info_parsed_for_test'+str(i),'odds_arhive_mathes'))
    plot_freq(sorted([elem[-1] for elem in srednee])[3:-3])
    for i in range(0, 25):
        sred=sum(sorted([elem[i] for elem in srednee])[1:-1])/len(sorted([elem[i] for elem in srednee])[1:-1])
        maxi=max(sorted([elem[i] for elem in srednee])[:-1])
        mini=min(sorted([elem[i] for elem in srednee])[1:])
        Srednee.append([sred,i])
        Maximalnoe.append([maxi,i])
        Minimalnoe.append([mini, i])
        if i==(len(srednee[0])-1):
            last_prize.append(elem[i] for elem in srednee)


    ax1=plt.subplot(111)
    plt.plot([elem[1] for elem in Srednee], [elem[0] for elem in Srednee], '-')
    plt.plot([elem[1] for elem in Minimalnoe], [elem[0] for elem in Minimalnoe], '-')
    plt.plot([elem[1] for elem in Maximalnoe], [elem[0] for elem in Maximalnoe], '-')
    print(Srednee[-1],Minimalnoe[-1],Maximalnoe[-1])
    # ax1.set_yscale('log')
    plt.show()





    #get_match_roi_from_archive('KR','SK Telecom T1','Afreeca Freecs','2019-01-10','2019-03-29','2019-03-30')
    # kills_in_game=list()
    # times=list()
    # kills_per_min=list()
    # with sqlite3.connect('Statistics_Analyzer.sqlite') as connect:
    #     elems=list()
    #     cursor = connect.cursor()
    #     cursor.execute("SELECT kill_adc_ally,kill_sup_ally,kill_jng_ally,kill_mid_ally,kill_top_ally,kill_adc_enemy,kill_sup_enemy,kill_jng_enemy,kill_mid_enemy,kill_top_enemy,match_date FROM matches_info_parsed WHERE team='Kingzone DragonX' "
    #                    #"and server='KR'"
    #                    "  and match_date BETWEEN '2019-01-07' and '2019-03-26'")
    #     for elem in cursor.fetchall():
    #         kills=0
    #         for i in range(0,10):
    #             kills+=len(pickle.loads(elem[i]))
    #         kills_in_game.append(kills)
    #
    #
    #     cursor.execute("SELECT match_time FROM matches_info_parsed WHERE team='Kingzone DragonX' "
    #                    #"and server='KR'"
    #                    "  and match_date BETWEEN '2019-01-07' and '2019-03-26'")
    #     for elem in cursor.fetchall():
    #         time=re.findall('([0-9]{1,3}):([0-9]{1,3})',elem[0])
    #         times.append(int(time[0][0])+int((time[0][1]))/60)
    # print(len(times))
    # print(len(kills_in_game))
    # for i in range(0,len(times)):
    #     kill_per_min=kills_in_game[i]/times[i]
    #     kills_per_min.append(kill_per_min)
    #
    # print(kills_per_min)
    # print(len(kills_per_min))
    # avg_kills_per_game_in_min=(sum(kills_per_min)/len(kills_per_min))
    # avg_match_time = (sum(times) / len(times))
    # print('отклонение',np.std(times))
    # print(avg_kills_per_game_in_min)
    # print(avg_match_time)
    # number_of_mathes=4
    # new_times=list()
    # for i in range (0,number_of_mathes):
    #     new_times.append(random.normalvariate(avg_match_time, np.std(times)))
    # #print(new_times)
    # matches=list()
    # for time in new_times:
    #     matches.append(np.random.randint(0, 1000, size=(int(time)))/1000)
    # print(matches)
    # new_matches=list()
    # for match in matches:
    #     new_match=list()
    #     [new_match.append(1 if elem>avg_kills_per_game_in_min else 0) for elem in match]
    #     new_matches.append(new_match)
    # total_kills_in_new_matches=([sum(new_match) for new_match in new_matches])
    # print(total_kills_in_new_matches)
    # print(sum(total_kills_in_new_matches)/len(total_kills_in_new_matches))











    # #plot_freq(times_team1_team2)  # sorted
    # rand_for_team_1=list()
    # for time in new_times:
    #     rand_for_team_1.append(np.random.randint(0, 1000, size=(int(time)))/1000)
    #     new_kills_per_min_team1.append(np.random.normal(avg_kills_per_game_in_min_team1, np.std(kills_per_min_team1), size=(int(time))))
    # rand_for_team_2 = list()
    # for time in new_times:
    #     rand_for_team_2.append(np.random.randint(0, 1000, size=(int(time))) / 1000)
    #     new_kills_per_min_team2.append(np.random.normal(avg_kills_per_game_in_min_team2, np.std(kills_per_min_team2), size=(int(time))))
    # #print(new_kills_per_min_team2)
    # match_result=list()
    # team1_score=list()
    # team2_score = list()
    # # for match in rand_for_team_1:
    # #     match_score=list()
    # #     [match_score.append(1 if elem<avg_kills_per_game_in_min_team1 else 0) for elem in match]
    # #     team1_score.append(sum(match_score))
    # # for match in rand_for_team_2:
    # #     match_score=list()
    # #     [match_score.append(1 if elem < avg_kills_per_game_in_min_team2 else 0) for elem in match]
    # #     team2_score.append(sum(match_score))
    #
    # for j in range(0,len(rand_for_team_1)):
    #     match_score=list()
    #     for i in range(0,len(rand_for_team_1[j])):
    #         #print(rand_for_team_1[j][i],new_kills_per_min_team1[j][i])
    #         match_score.append(new_kills_per_min_team1[j][i])
    #     team1_score.append(sum(match_score))
    # for match in range(0,len(rand_for_team_2)):
    #     match_score=list()
    #     for i in range(0,len(rand_for_team_2[j])):
    #         match_score.append( new_kills_per_min_team2[j][i] )
    #     team2_score.append(sum(match_score))
    #
    #
    # #print(team1_score)
    # #print(team2_score)
    # for i in range(0,len(team1_score)):
    #     if team1_score[i]>team2_score[i]:
    #         match_result.append([1,0,0])
    #     elif team1_score[i]==team2_score[i]:
    #         match_result.append([0,1,0])
    #     elif team1_score[i]<team2_score[i]:
    #         match_result.append([0,0,1])
    # #print(match_result)
    # print(sum([row[0] for row in match_result])/len(match_result),sum([row[1] for row in match_result])/len(match_result),sum([row[2] for row in match_result])/len(match_result))
    #



    #
# connect.commit()





    #remove_negative_from_avg_data()
    #return 0
    # teams=['hanwha_life_esports','geng_esports']
    # parametr_list=['gold_diff_all_20_10min','kda','gold_diff_all_20_15min','gold_diff_all_15_10min','xp_diff_per_minute_all','ka_total','first_baron_get']
    # print(get_probability_of_victory_for_two_teams(teams,parametr_list))
    # print()
    # return 0
    # probability_of_victory_from_avg_stat('bausupermassive','all_tower_get_total','standart')
    # probability_of_victory_from_avg_stat('bausupermassive', 'kda','standart')
    # get_average_basic_teams_stat_standardized()

    # get_team_names()
    # get_teams_win_rate()
    # print('Винрейт подсчитан')
    # get_basic_team_stat('global')
    # print('Общая статистика подсчитана')
    # get_basic_teams_stats()
    # print('Статистика команд подсчитана')
    # get_average_basic_teams_stats()
    # get_average_basic_teams_stats_standardized()
    # print('Средние статистики команд подсчитаны')
    # # team1= sys.argv[2]
    # k1= float(sys.argv[3])
    # team2= sys.argv[4]
    # k2= float(sys.argv[5])
    # server=sys.argv[1]
    # parametr_list=['gold_diff_all_20_10min','gold_diff_all_20_15min','gold_diff_all_15_10min','kda']
    # team1_Ps = get_rois_global(parametr_list, team1,server)
    # team2_Ps = get_rois_global(parametr_list, team2,server)
    # team1_Ps_w=list()
    # team2_Ps_w=list()
    # for i in range(0,len(team1_Ps)):
    #     w=team1_Ps[i]+team2_Ps[i]
    #     team1_Ps_w.append(team1_Ps[i]/w)
    #     team2_Ps_w.append(team2_Ps[i]/w)
    # print(team1)
    # for i in range(0,len(team1_Ps_w)):
    #     print(parametr_list[i]+"\t\t\t\tP="+str(round(team1_Ps[i],3))+"\tPw="+str(round(team1_Ps_w[i],3))+"\troi="+str(round(100*team1_Ps[i]*k1-100,3))+"\troi_w="+str(round(100*team1_Ps_w[i]*k1-100,3)))
    # print('-------')
    # print(str(round(sum(team1_Ps_w)/len(team1_Ps_w),3)) + " " + str(round(100 * (sum(team1_Ps_w)/len(team1_Ps_w)) * k1 - 100,3)))
    # print('=============================')
    # print()
    # print(team2)
    # for i in range(0,len(team2_Ps_w)):
    #     print(parametr_list[i] + "\t\t\t\tP=" +str(round(team2_Ps[i],3))+"\tPw="+str(round(team2_Ps_w[i],3))+"\troi="+str(round(100*team2_Ps[i]*k2-100,3))+"\troi_w="+str(round(100*team2_Ps_w[i]*k2-100,3)))
    # print('-------')
    # print(str(round(sum(team2_Ps_w)/len(team2_Ps_w),3)) + " " + str(round(100 * (sum(team2_Ps_w)/len(team2_Ps_w)) * k2 - 100,3)))
    # print('==============================')
    # print()
    #
    #
    #



    #  get_rois_global(parametr_list, team2, k2)
    # plt.show()



    # fig2 = probability_of_victory('global', 'ally_sup_totalDamageDealt', 'modern')
    # plt.show()
    # print(80*get_average_match_time()/100)

if __name__== '__main__':
    main()