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

##INPUT DATA
API = IQ_Option('your_account', 'your_pass')
API.connect()
API.change_balance("PRACTICE")

#Config vars
lucro_total = 0
nivel_soros = 2
mao = 1
lucro = 0
perca = 0

entrada = 10
stoploss = entrada + entrada * 0.4  # 40% do valor da entrada
stopgain = entrada * 0.6  # 60% do valor da entrada


#TODO: implementar logica para verificar nivel de sorosgale
def soros_gale(perca, pair, acao, lucro_total, nivel_soros, mao, lucro):
    entrada_soros = (perca) / 2 + lucro

    status, data_id = API.buy_digital_spot(pair, entrada_soros, acao)

    if status:
        print("Entrada realizada com sucesso, aguardando resultado..")

        while True:
            status, lucro = API.check_win_digital_v2(data_id)

            if status:
                if lucro > 0:
                    lucro_total += lucro
                    mao += 1
                    print("WIN" + str(lucro))

                else:
                    lucro_total = 0
                    mao = 1
                    perca += perca/2
                    nivel_soros += 1
                    print("LOSS" + str(lucro))
                break

    return perca, lucro_total, nivel_soros, mao, lucro


def normal_hand(acao, pair, perca, lucro_total):
    status, data_id = API.buy_digital_spot(pair, 2.0, acao)

    if status:
        print("Entrada realizada com sucesso, aguardando resultado..")

    while True:

        status, valor = API.check_win_digital_v2(data_id)

        if status:
            if valor > 0:
                print("WIN" + str(valor))
                lucro_total += valor
            else:
                print("LOSS" + str(valor))
                perca += valor
            break

    return perca, lucro_total, 0, 0, valor


def create_data_treated(vela, vela_size):
    dado_tratado = {
        'open': np.empty(vela_size),
        'high': np.empty(vela_size),
        'low': np.empty(vela_size),
        'close': np.empty(vela_size),
        'volume': np.empty(vela_size)
    }

    for x in range(0, vela_size):
        dado_tratado['open'][x] = vela[x]['open']
        dado_tratado['high'][x] = vela[x]['max']
        dado_tratado['low'][x] = vela[x]['min']
        dado_tratado['close'][x] = vela[x]['close']
        dado_tratado['volume'][x] = vela[x]['volume']

    return dado_tratado


def calculate_ema(dado_tratado):
    return TA.EMA(dado_tratado, period=100)


def calculate_bb(dado_tratado):
    return TA.BBANDS(dado_tratado, period=20, std_multiplier=2.5)


def strategy(ema, bb_up, bb_low, velas, pair, perca, lucro_total, nivel_soros, mao, lucro):
    #round data
    up = round(bb_up[len(bb_up) - 2], 5)
    low = round(bb_low[len(low) - 2], 5)
    ema_data = round(ema[len(ema) - 2], 5)
    close = round(velas[-1]['close'], 5)

    if close <= low and close > ema_data:
        perca, lucro_total, nivel_soros, mao, lucro = soros_gale(
            perca, 'call', pair, lucro_total, nivel_soros, mao, lucro) if perca > 0 else normal_hand('call', pair, perca, lucro_total)
    elif close >= up and close < ema:
        perca, lucro_total, nivel_soros, mao, lucro = soros_gale(
            perca, 'put', pair, lucro_total, nivel_soros, mao, lucro) if perca > 0 else normal_hand('put', pair, perca, lucro_total)

    return perca, lucro_total, nivel_soros, mao, lucro


def create_bot(pair, period, vela_size, ):

    while True:
        velas = API.get_candles(pair, period, vela_size, time())

        dado_tratado = create_data_treated(velas, vela_size)

        ema = calculate_ema(dado_tratado)
        up, mid, low = calculate_bb(dado_tratado)

        perca, lucro_total, nivel_soros, mao, lucro = strategy(
            ema, up, low, velas, pair, perca, lucro_total, nivel_soros, mao, lucro)


        if perca >= stoploss or lucro_total >= stopgain:
            break


def execute_trade():

    execute_trade = False
    while True:
        if API.check_connect() == False:
            print("Erro ao se conectar")
            API.reconnect()
        else:
            print("Conectado com sucesso!")
            execute_trade = True
            break

        sleep(1)

    if execute_trade:
        create_bot("EURUSD", 60, 100)  # execute bot


execute_trade()
