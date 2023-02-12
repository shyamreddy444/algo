# -*- coding: utf-8 -*-
"""
Created on Dec 29 09:13:23 2022

Here i automated BOC 200X strategy, we request you please run this setup in paper trade mode first and after result confirmation proceed for Live Trade.

TradeMode : Live (In you want to take real trade)
TradeMode : Paper (In you want to take paper trade)

BOC strategy expalined by BOC : https://drive.google.com/file/d/1Hi0B369_-3A3wbzUbzPJV0D0Cgy3lb-E/view?usp=share_link

Contact details :
Telegram Channel:  https://t.me/pythontrader
Youtube Channel : https://youtube.com/@pythontraders
Developer Telegram ID : https://t.me/pythontrader_admin
Other tool folder : tinyurl.com/pythontrader
Gmail ID:   mnkumar2020@gmail.com 
Whatsapp : 9470669031 

Disclaimer: The information provided by the Python Traders channel is for educational purposes only, so please contact your financial adviser before placing your trade. Developer is not responsible for any profit/loss happened due to strategy, coding, logical or any type of error.
"""

from NorenRestApiPy.NorenApi import  NorenApi
import json
from datetime import datetime as dt
from datetime import time,timedelta as td
import logging
import requests
import warnings
from time import sleep
warnings.filterwarnings("ignore")
from pytz import timezone
import sys
import os
import platform

try:
    import yaml
except Exception as e:
    os.system('python -m pip install pyyaml')
    import yaml
try:
    import pyotp
except Exception as e:
    os.system('python -m pip install pyotp')
    import pyotp
try:
    import pandas as pd
except Exception as e:
    os.system('python -m pip install pandas') 
    import pandas as pd    

os_name = platform.system()
if(os_name == 'Windows'):
    LogsFolder = "logs\\"
else:
    LogsFolder = "logs/"

if not os.path.exists('logs'): os.mkdir('logs')

Timestamp = dt.now().strftime("%d%m%Y_%H_%M")
LogFile  = LogsFolder + "BOC_200X_" + str(Timestamp)  + str('.log') 

logging.basicConfig(filename=LogFile, format='%(asctime)s %(message)s', filemode='w')
logger = logging.getLogger() 
logger.setLevel(logging.INFO)

logger.info("Logger started")

api = None

def Config_reading():
    print("reading Config file\n\n")
    global userid
    global password, LogginThroughToken, TokenFile, TwoFA, vendor_code, api_secret,imei
    global quantity, TradeSymbol, option_lower_range ,option_upper_range ,OptionSnapShotTime ,EntryTime,  Trade_Squareoff_Time ,BuyAbove ,Target_Point ,SL_Point, TradeMode
    
    with open('Config.yaml') as file:
        try:
            databaseConfig = yaml.safe_load(file)   
            #print(databaseConfig)
            
            userid = databaseConfig['userid']
            
            password = databaseConfig['Credential']['password']
            LogginThroughToken = databaseConfig['Credential']['LogginThroughToken']
            TokenFile = databaseConfig['Credential']['TokenFile']
            TwoFA = databaseConfig['Credential']['TwoFA']
            vendor_code = databaseConfig['Credential']['vendor_code']
            api_secret = databaseConfig['Credential']['api_secret']
            imei = databaseConfig['Credential']['imei']
            
            TradeMode = databaseConfig['Algo_Setup']['TradeMode'].upper()
            quantity = databaseConfig['Algo_Setup']['quantity']
            TradeSymbol = databaseConfig['Algo_Setup']['TradeSymbol']
            option_lower_range = databaseConfig['Algo_Setup']['option_lower_range']
            option_upper_range = databaseConfig['Algo_Setup']['option_upper_range']
            OptionSnapShotTime = databaseConfig['Algo_Setup']['OptionSnapShotTime']
            EntryTime = databaseConfig['Algo_Setup']['EntryTime']
            Trade_Squareoff_Time = databaseConfig['Algo_Setup']['Trade_Squareoff_Time']
            BuyAbove = databaseConfig['Algo_Setup']['BuyAbove']
            Target_Point = databaseConfig['Algo_Setup']['Target_Point']
            SL_Point = databaseConfig['Algo_Setup']['SL_Point']
            
            
            #print(databaseConfig)
            logger.info(databaseConfig)
            

        except yaml.YAMLError as exc:
            Message = str(exc) + " :Exception occur in Config_reading()"
            print(Message)
            logger.info(Message)
        

Config_reading()

def ConnectApi():
    global api
    global userid
    global password, LogginThroughToken, TokenFile, TwoFA, vendor_code, api_secret, imei
    
    
    Message = "Going to initialise finvasia session"
    print(Message)
    logger.info(Message)
    isConnected = 1
    
    try:
        class ShoonyaApiPy(NorenApi):
            def __init__(self):
                NorenApi.__init__(self, host='https://api.shoonya.com/NorenWClientTP/', websocket='wss://api.shoonya.com/NorenWSTP/', eodhost='https://api.shoonya.com/chartApi/getdata/')
        api = ShoonyaApiPy()
    except Exception as e:
        class ShoonyaApiPy(NorenApi):
            def __init__(self):
                NorenApi.__init__(self, host='https://api.shoonya.com/NorenWClientTP/', websocket='wss://api.shoonya.com/NorenWSTP/')
        api = ShoonyaApiPy()

    if(LogginThroughToken == 0):
        Message = "Going to generate new token"
        print(Message)
        logger.info(Message)
        try:
            
            twoFA  = pyotp.TOTP(TwoFA).now()
            twoFA = f"{int(twoFA):06d}" if len(twoFA) <=5 else twoFA
            
            
            login_status = api.login(userid=userid, password=password, twoFA=twoFA, vendor_code=vendor_code, api_secret=api_secret, imei=imei)

            login_status_msg = login_status.get('uname') + " login:" + login_status.get('stat')+ " token = " +login_status.get('susertoken')
            username = login_status.get('uname')
            
            susertoken = login_status.get('susertoken')

            TokenFile = 'token.txt'
            
            with open(TokenFile, 'w') as wr:
                wr.write(susertoken)
        except Exception as e:
            isConnected = 0
            login_status_msg = "Session not set for " + userid
            
            Message =  str(e) + " : Exception occur in generating new access token for = " + str(userid)
            
            print(Message) 
            logger.info(Message)
            
    else:
        Message = "Going to login through already generated token using file " + str(TokenFile)
        print(Message)
        logger.info(Message)
        
        try:
            with open(TokenFile, 'r') as wr:
                usertoken = wr.read()
        
            if(len(usertoken) != 0):
                #print(f"userid {userid} password {password} usertoken {usertoken}")
                api = ShoonyaApiPy()
                login_status = api.set_session(userid=userid, password=password,usertoken=usertoken)
                get_limits = api.get_limits()
                #print(get_limits)
                if(get_limits['stat'] != 'Ok'):
                    isConnected = 0
                    login_status_msg = "Session not set with error " + str(get_limits['emsg'])
                else:
                    login_status_msg = "Session set for " + userid 
                
            else:
                isConnected = 0
                login_status_msg = "Session token not found for " + userid
                
                print(login_status_msg) 
                logger.info(login_status_msg)

            print(login_status_msg)    
            logger.info(login_status_msg)
                
        except Exception as e:
            Message =  str(e) + " : Exception occur in setting access token for = " + str(userid)
            isConnected = 0
            print(Message) 
            logger.info(Message)
        
    return isConnected

ConnectApi()
master_contract = pd.read_csv('https://shoonya.finvasia.com/NFO_symbols.txt.zip', compression='zip', engine='python',
                              delimiter=',')
master_contract['Expiry'] = pd.to_datetime(master_contract['Expiry'])
master_contract['StrikePrice'] = master_contract['StrikePrice'].astype(float)
master_contract.sort_values('Expiry', inplace=True)
master_contract.reset_index(drop=True, inplace=True)


def get_instrument(Symbol, strike_price, optiontype, expiry_offset):
    # to get a intstrument token from the master contract downloaded from shoonya website
    return (master_contract[(master_contract['Symbol'] == Symbol) & (master_contract['OptionType'] == optiontype) & (
    master_contract['StrikePrice'] == strike_price)].iloc[expiry_offset])


def get_atm_strike():
    bnspot_token = api.searchscrip(exchange='NSE', searchtext='Nifty bank')['values'][0]['token']
    while True:
        bnflp = float(api.get_quotes(exchange='NSE', token=bnspot_token)['lp'])
        if bnflp != None:
            break
    atmprice = round(bnflp / base) * base
    return atmprice


def place_order(BS, tradingsymbol, quantity, product_type='I', price_type='MKT', exchange='NFO', price=0,
                trigger_price=None):
    order_place = api.place_order(buy_or_sell=BS, product_type=product_type,
                                  exchange=exchange, tradingsymbol=tradingsymbol,
                                  quantity=quantity, discloseqty=0, price_type=price_type, price=price,
                                  trigger_price=trigger_price)  # M for NRML AND I For intraday in product type
    return order_place['norenordno']


def stop_loss_order(qty, tradingsymbol, price, sl):
    stop_price = round(price-10)
    price = stop_price - 5
    trigger_price = stop_price
    stop_loss_orderid = place_order(BS='S', tradingsymbol=tradingsymbol, quantity=qty, price_type='SL-LMT', price=price,
                                    trigger_price=trigger_price)
    return stop_loss_orderid





def single_order_history(orderid, req):
    ''''stat','norenordno', 'uid', 'src_uid', 'actid', 'exch', 'tsym', 'q 'trantyty',pe', 'prctyp', 'ret', 'rejby', 'kidid',
       'pan', 'ordersource', 'token', 'pp', 'ls', 'ti', 'prc', 'dscqty', 'prd', 'status', 'rpt', 'ordenttm', 'norentm', 'rejreason','exch_tm'''
    # this required to made to avoid unnecesary making a lof of Dataframes
    # dl=pd.DataFrame(api.single_order_history(orderid))
    # sleep(1)
    # return dl[req].iloc[0]

    while True:
        json_data = api.single_order_history(orderid)
        if json_data != None:
            break

    for id in json_data:
        value_return = id[req]
        break

    return value_return



# while dt.datetime.now(timezone("Asia/Kolkata")).time() < dt.time(9,20,0):
#    sleep(1)

#while dt.datetime.now(timezone("Asia/Kolkata")).time() < dt.time(6,20,0):
   #   sleep(1)

base = 100
symbol = "BANKNIFTY"
sl = 30
qty = 50
target = 80
def exit():
    while dt.datetime.now(timezone("Asia/Kolkata")).time() > dt.time(15, 5, 0):
        while True:
            try:
                a = api.get_positions()
                a = pd.DataFrame(a)
                ob = api.get_order_book()
                ob = pd.DataFrame(ob)
                break
            except Exception:
                print('uni_exit error fetching positions/orders')
                time.sleep(1)
                continue

        for i in a.itertuples():

            if int(i.netqty) < 0: api.place_order(buy_or_sell='B', product_type=i.prd, exchange=i.exch,
                                                  tradingsymbol=i.tsym, quantity=abs(int(i.netqty)), discloseqty=0,
                                                  price_type='MKT', price=0, trigger_price=None,
                                                  retention='DAY', remarks='killswitch_buy')

            if int(i.netqty) > 0: api.place_order(buy_or_sell='S', product_type=i.prd, exchange=i.exch,
                                                  tradingsymbol=i.tsym, quantity=int(i.netqty), discloseqty=0,
                                                  price_type='MKT', price=0, trigger_price=None,
                                                  retention='DAY', remarks='killswitch_sell')

            #     ob = api.get_order_book()
            #     ob = pd.DataFrame(ob)
        for i in ob.itertuples():

            if i.status == 'TRIGGER_PENDING': ret = api.cancel_order(i.norenordno)
            if i.status == 'OPEN': ret = api.cancel_order(i.norenordno)

def callbuy():
    atm_strike = get_atm_strike()
    ce_tradingsymbol = get_instrument(symbol, atm_strike-100, 'CE', 0)['TradingSymbol']
    atmcetoken = api.searchscrip(exchange='NFO', searchtext=ce_tradingsymbol)['values'][0]['token']
    ce_orderid = place_order('B', ce_tradingsymbol, qty)
    sleep(3)
    ce_price = float(single_order_history(ce_orderid, 'avgprc'))
    ce_slorderid = stop_loss_order(qty, ce_tradingsymbol, ce_price, sl)
    entry = ce_price


    while True:
        try:
            close = float(api.get_quotes(exchange='NFO', token=atmcetoken)['lp'])


        except:
            continue


        if close > entry + target:
            api.modify_order(exchange='NFO', tradingsymbol=ce_tradingsymbol, orderno=ce_slorderid,
                             newquantity=qty, newprice_type='MKT', newprice=0.00)
            print('target hit : ', close )
            break


        time.sleep(5)

def putbuy():
    atm_strike = get_atm_strike()
    pe_tradingsymbol = get_instrument(symbol, atm_strike+100, 'PE', 0)['TradingSymbol']
    atmpetoken = api.searchscrip(exchange='NFO', searchtext=pe_tradingsymbol)['values'][0]['token']
    pe_orderid = place_order('B', pe_tradingsymbol, qty)
    sleep(3)
    pe_price = float(single_order_history(pe_orderid, 'avgprc'))
    pe_slorderid = stop_loss_order(qty, pe_tradingsymbol, pe_price, sl)
    entry = pe_price


    while True:
        try:
            close = float(api.get_quotes(exchange='NFO', token=atmpetoken)['lp'])


        except:
            continue


        if close > entry + target:
            api.modify_order(exchange='NFO', tradingsymbol=pe_tradingsymbol, orderno=pe_slorderid,
                             newquantity=qty, newprice_type='MKT', newprice=0.00)
            print('target hit : ', close)
            break


        time.sleep(5)

while True:
    # take input from the user
    choice = input("Enter choice 1 for LONG & 2 for SHORT: ")

    # check if choice is one of the four options
    if choice in ('1', '2'):

        if choice == '1':
            callbuy()

        elif choice == '2':
            putbuy()
