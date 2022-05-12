from iqoptionapi.stable_api import IQ_Option
from time import time, sleep
import json
from finta import TA
import pandas as pd
from datetime import datetime
import signal
import sys
from threading import Thread, Lock
import numpy as np

API = IQ_Option('your_account', 'your_pass')
API.connect()

API.change_balance("PRACTICE")

value = 2.0
direcao = 'call'
timeframe = 1


def signal_handler(sig, frame):
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def get_data(par, timeframe, periods=200):
    velas = API.get_candles(par, timeframe * 60, periods, time())
    df = pd.DataFrame(velas)
    df.rename(columns={"max": "high", "min": "low"}, inplace=True)

    return df


def thread_function(par):
    print("thread with pair: {}".format(par))

    while True:
        chinese_strategy(par, value, timeframe)
        sleep(0.5)


def mov_av_dev(df):
    src = TA.SSMA(df, 20)
    calc = df.iloc[-1]['close'] - src.iloc[-1]

    return calc, 'green' if calc >= (df.iloc[-2]['close'] - src.iloc[-2]) else 'red'


def oportunity_window(ssma_3, ssma_50, ssma3_pos, ssma_50_pos, window, color, par):

    if window != 0:

        time_frame_ssma3 = ssma_3.iloc[:].values.tolist(
        )[int(-window):int(-ssma3_pos)]

        time_frame_ssma50 = ssma_50.iloc[:].values.tolist(
        )[int(-window):int(-ssma_50_pos)]

        time_frame_ssma3_second = ssma_3.iloc[:].values.tolist(
        )[int(-(2 * window)):int(-ssma3_pos-window)]

        time_frame_ssma50_second = ssma_50.iloc[:].values.tolist(
        )[int(-(2 * window)):int(-ssma_50_pos-window)]

        if np.all(np.asarray(time_frame_ssma3)
                  < np.asarray(time_frame_ssma50)) and np.all(np.asarray(time_frame_ssma3_second)
                                                              > np.asarray(time_frame_ssma50_second)) and color == 'red':
            entrada_digital(par, value, 'put', timeframe)
        elif np.all(np.asarray(time_frame_ssma3)
                    > np.asarray(time_frame_ssma50)) and np.all(np.asarray(time_frame_ssma3_second)
                                                                < np.asarray(time_frame_ssma50_second)) and color == 'green':
            entrada_digital(par, value, 'call', timeframe)
    else:
        greater_equal_than = ssma_3.iloc[-1] >= ssma_50.iloc[-1]
        lesser_equal_than = ssma_3.iloc[-1] <= ssma_50.iloc[-1]

        greater_than = ssma_3.iloc[-2] > ssma_50.iloc[-2]
        lesser_than = ssma_3.iloc[-2] < ssma_50.iloc[-2]

        if lesser_equal_than and greater_than and color == 'red':
            entrada_digital(par, value, 'put', timeframe)
        elif greater_equal_than and lesser_than and color == 'green':
            entrada_digital(par, value, 'call', timeframe)


def chinese_strategy(par, value, timeframe):

    #get dataframe from candles
    mutex.acquire()
    df = get_data(par, timeframe, 200)
    mutex.release()

    #calculate the SSMA of period 20
    tax, color = mov_av_dev(df)

    #calculate indicators for chinese strategy
    ssma_3 = TA.SSMA(df, 3)
    ssma_50 = TA.SSMA(df, 50)

    #get oportunity window and do the job
    oportunity_window(ssma_3, ssma_50, 1, 1, 5, color, par)


def entrada_digital(par, value, op, timeframe):

    print("Abrindo operação no par {} com valor de R${} com direção {} no timeframe de {} min".format(
        par, value, op, timeframe))

    status, id_data = API.buy_digital_spot_v2(par, value, op, timeframe)

    if status:
        status = False

        while status == False:
            status, lucro = API.check_win_digital_v2(id_data)
            sleep(0.05)

        if lucro > 0:
            print("WIN: R${}".format(lucro))

        else:
            print("LOSS: R${}".format(lucro))


def execute_trade():

    while True:
        if API.check_connect() == False:
            print("Erro ao se conectar")
            API.reconnect()
        else:
            print("Conectado com sucesso!")
            thread1.start()
            thread2.start()
            thread3.start()
            thread4.start()
            thread5.start()
            thread6.start()
            break

        sleep(1)


mutex = Lock()

thread1 = Thread(target=thread_function, args=("EURUSD",))
thread2 = Thread(target=thread_function, args=("EURGBP",))
thread3 = Thread(target=thread_function, args=("EURJPY",))
thread4 = Thread(target=thread_function, args=("GBPUSD",))
thread5 = Thread(target=thread_function, args=("GBPJPY",))
thread6 = Thread(target=thread_function, args=("AUDCAD",))


execute_trade()
