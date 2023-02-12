# -*- coding: utf-8 -*-
"""
Created on Dec Nov 26 09:13:23 2022

Here i automated BOC 145 strategy, we request you please run this setup in paper trade mode first and after result confirmation proceed for Live Trade.

TradeMode : Live (In you want to take real trade)
TradeMode : Paper (In you want to take paper trade)

BOC strategy expalined by BOC : https://www.youtube.com/watch?v=MLjaMzBKzcg&t=149s&ab_channel=BaapofChart

Contact details :
Telegram Channel:  https://t.me/pythontrader
Youtube Channel : https://youtube.com/@pythontraders
Developer Telegram ID : https://t.me/pythontrader_admin
Other tool folder : tinyurl.com/pythontrader
Gmail ID:   mnkumar2020@gmail.com 
Whatsapp : 9470669031 

Disclaimer: The information provided by the Python Traders channel is for educational purposes only, so please contact your financial adviser before placing your trade. Developer is not responsible for any profit/loss happened due to coding, logical or any type of error.
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

Timestamp = dt.now().strftime("%d%m%Y")
LogFile  = "BOC_145_" + str(Timestamp)  + str('.log') 

logging.basicConfig(filename=LogFile, format='%(asctime)s %(message)s', filemode='w')
logger = logging.getLogger() 
logger.setLevel(logging.INFO)

logger.info("Logger started")

api = None

def Config_reading():
    print("reading Config file\n\n")
    global sleeptime, AlgoSetupFolder
    global userid
    global password, LogginThroughToken, TokenFile, TwoFA, vendor_code, api_secret,imei
    global quantity, TradeSymbol, option_lower_range ,option_upper_range ,OptionSnapShotTime ,Trade_Squareoff_Time ,BuyWhen ,Target ,SL, TradeMode
    
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
            Trade_Squareoff_Time = databaseConfig['Algo_Setup']['Trade_Squareoff_Time']
            BuyWhen = databaseConfig['Algo_Setup']['BuyWhen']
            Target = databaseConfig['Algo_Setup']['Target']
            SL = databaseConfig['Algo_Setup']['SL']

            Message = "User Config details : \nTradeMode = "+str(TradeMode)+"\nquantity = "+str(quantity)+"\nTradeSymbol = "+str(TradeSymbol)+"\noption_lower_range = "+str(option_lower_range)+"\noption_upper_range = "+str(option_upper_range)+"\nOptionSnapShotTime = "+str(OptionSnapShotTime)+"\nTrade_Squareoff_Time = "+str(Trade_Squareoff_Time)+"\nBuyWhen = "+str(BuyWhen)+"\nTarget = "+str(Target)+"\nSL = "+str(SL)+"\nuserid = "+str(userid)+ "\npassword = " + str(password)+"\nLogginThroughToken = "+str(LogginThroughToken)+"\nTokenFile = "+str(TokenFile)+"\nTwoFA = "+str(TwoFA)+"\nvendor_code = "+str(vendor_code)+"\napi_secret = "+str(api_secret)+"\nimei = "+str(imei)

            print(Message)
            logger.info(Message)
            

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
                print(f"userid {userid} password {password} usertoken {usertoken}")
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

def LoadToken():
    Message = "I am inside LoadToken"
    print(Message)
    logger.info(Message)
    global df_intrument
    zip_file = "NFO_symbols.txt.zip"
    try:
        url = f"https://shoonya.finvasia.com/{zip_file}"
        r = requests.get(f"{url}", allow_redirects=True)
        open(zip_file, "wb").write(r.content)
        Message = "Latest intrument files downloaded"
        print(Message)
        logger.info(Message)
        df_intrument = pd.read_csv(zip_file)
    except Exception as e:
        print(f"Exception occur while downloading token from net: {e}")
        df_intrument = pd.read_csv(zip_file)
        Message = "intrument files loaded from local folder"
        print(Message)
        logger.info(Message)

    df_intrument['Expiry'] = pd.to_datetime(df_intrument['Expiry']).apply(lambda x: x.date())  
    #print(df_intrument)

def GetOptionChain(Symbol, Expiry = 'currentweek'):
    Message = "I am inside GetOptionChain"
    print(Message)
    logger.info(Message)
    global df_intrument
    
    try:
        if Expiry == 'currentweek':
            df_selected_instrument = df_intrument[(df_intrument.Symbol == Symbol) & (df_intrument.Instrument == 'OPTIDX')]
            Expiry
            df_selected_instrument.sort_values(by = 'Expiry',inplace = True)
            WeeklyExpiryDate = df_selected_instrument.iloc[0]['Expiry']
            
            df_selected_instrument = df_selected_instrument[df_selected_instrument.Expiry == WeeklyExpiryDate]
            
        else:
            df_selected_instrument = df_intrument[(df_intrument.Symbol == Symbol) & (df_intrument.Instrument == 'OPTIDX')& (df_intrument.Expiry == Expiry) ]

        strikeList = []
        for i in df_selected_instrument.index:
            try:
                #print(df_selected_instrument.loc[i])
                strikeInfo = df_selected_instrument.loc[i]
                res = api.get_quotes(exchange='NFO', token=str(strikeInfo.Token))
                #print(res)    
                res = {'symbol': res['tsym'], 'ltp': float(res['lp']),'lot_size':strikeInfo.LotSize,'token':res['token'], 'option_type':res['optt'],'expiry':res['exd'],'strike':res['strprc']}
                strikeList.append(res)
            except Exception as e:
                #print(f"Exception occur in GetOptionChain for {df_selected_instrument.loc[i]}")
                pass
        df_oc = pd.DataFrame(strikeList)
        df_oc['expiry'] = pd.to_datetime(df_oc['expiry']).apply(lambda x: x.date())  
        
        
    except Exception as e:
        Message = str(e) + ": Exception occur in GetOptionChain, while calculating optionchain for " + str(Symbol) + " symbol and " + str(Expiry) + " Expiry"
        print(Message)
        logger.info(Message)
    
    return df_oc

    
def strategy():
    Message = "I am inside strategy"
    print(Message)
    logger.info(Message)
    LoadToken()
    global quantity, TradeSymbol, option_lower_range ,option_upper_range ,OptionSnapShotTime ,Trade_Squareoff_Time ,BuyWhen ,Target ,SL, TradeMode
    
    start_hour, start_minute, start_second = OptionSnapShotTime.split(':')

    if dt.now(timezone("Asia/Kolkata")).time() > time(int(start_hour),int(start_minute),int(start_second)):
        Message = "Option lookup time (" + str (OptionSnapShotTime) +") is already over, do you want to proceed now"
        print(Message)
        logger.info(Message)
        
        Userchoice = input("Type Yes/No :").upper()
        #print(Userchoice)
        logger.info(Userchoice)
        
        
        if (Userchoice[0] != 'Y'):
            Message = "Please run algo on next day before " + str(OptionSnapShotTime)
            print(Message)
            logger.info(Message)
            sys.exit()
        
    while dt.now(timezone("Asia/Kolkata")).time() < time(int(start_hour),int(start_minute),int(start_second)):
        Message = "Waiting for start time " + OptionSnapShotTime 
        logger.info(Message)
        print(Message)
                
    df_oc = GetOptionChain(TradeSymbol)
    df_oc = df_oc[ (df_oc['ltp'] < option_upper_range ) & (df_oc['ltp'] > option_lower_range)]
    print(f"\n\nSelected strike based on given option price range\n{df_oc}") 
    if(len(df_oc) > 0):
        
        df_pe_oc = df_oc[df_oc.option_type == 'PE']
        strikeList = []
        if len(df_pe_oc) > 0:
            df_pe_oc.sort_values(by = 'ltp',inplace = True,ascending=False)
            res = {'symbol': df_pe_oc.iloc[0]['symbol'],'token':df_pe_oc.iloc[0]['token'], 'strike':df_pe_oc.iloc[0]['strike'],'option_type':df_pe_oc.iloc[0]['option_type'],'initial_ltp': df_pe_oc.iloc[0]['ltp'],'current_ltp': df_pe_oc.iloc[0]['ltp']}
            strikeList.append(res)
        
        df_ce_oc = df_oc[df_oc.option_type == 'CE']
        if len(df_ce_oc) > 0:
            df_ce_oc.sort_values(by = 'ltp',inplace = True,ascending=False)
            res = {'symbol': df_ce_oc.iloc[0]['symbol'],'token':df_ce_oc.iloc[0]['token'], 'strike':df_ce_oc.iloc[0]['strike'],'option_type':df_ce_oc.iloc[0]['option_type'],'initial_ltp': df_ce_oc.iloc[0]['ltp'],'current_ltp': df_ce_oc.iloc[0]['ltp']}
            strikeList.append(res)
            
        df_trade_option = pd.DataFrame(strikeList)
        df_trade_option['quantity'] = quantity
        df_trade_option['TradeMode'] = TradeMode
        df_trade_option['TradeStatus'] = 'Wait'
        df_trade_option['EntryPrice'] = 0.0
        df_trade_option['ExitPrice'] = 0.0
        df_trade_option['PnL'] = 0.0
        print(f"\n\nSelected strike based on probability to execute\n{df_trade_option}") 
        
        end_hour, end_minute, end_second = Trade_Squareoff_Time.split(':')        
        while True:
            try:
                if dt.now(timezone("Asia/Kolkata")).time() >= time(int(end_hour),int(end_minute),int(end_second)):
                    Message ='Its time to autosquareoff if any active trade found'
                    print(Message)
                    logger.info(Message)
                    for ind in df_trade_option.index:
                        if(df_trade_option['TradeStatus'][ind] == 'Active'):
                            Message ="Going to squareoff " + str(df_trade_option['strike'][ind]) + df_trade_option['option_type'][ind]
                            print(Message)
                            logger.info(Message)
                            if TradeMode == 'LIVE':
                                Ltp = place_trade(df_trade_option['symbol'][ind], df_trade_option['quantity'][ind], 'SELL')
                            else:
                                Ltp = GetLTP(exchange='NFO', token=df_trade_option['token'][ind])
                                
                            df_trade_option['ExitPrice'][ind] = Ltp
                            df_trade_option['TradeStatus'][ind] = 'Closed'
                        
                            PnL = (Ltp - df_trade_option['EntryPrice'][ind] ) * df_trade_option['quantity'][ind]
                            df_trade_option['PnL'][ind] = PnL
                    print(df_trade_option)          
                    break
                else:
                    for ind in df_trade_option.index:
                        Ltp = GetLTP(exchange='NFO', token=df_trade_option['token'][ind])
                        df_trade_option['current_ltp'][ind] = Ltp
                        if(df_trade_option['TradeStatus'][ind] == 'Wait'):
                            if Ltp > BuyWhen:
                                Message ="Entry condition meet for " + str(df_trade_option['strike'][ind]) + df_trade_option['option_type'][ind]
                                print(Message)
                                logger.info(Message)
                                if TradeMode == 'LIVE':
                                    Ltp = place_trade(df_trade_option['symbol'][ind], df_trade_option['quantity'][ind], 'BUY')
                                
                                df_trade_option['EntryPrice'][ind] = Ltp
                                df_trade_option['TradeStatus'][ind] = 'Active'
                        elif(df_trade_option['TradeStatus'][ind] == 'Active'):
                            if Ltp > Target or Ltp < SL :
                                Message ="Target/SL hit for " + str(df_trade_option['strike'][ind]) + df_trade_option['option_type'][ind]
                                print(Message)
                                logger.info(Message)
                                if TradeMode == 'LIVE':
                                    Ltp = place_trade(df_trade_option['symbol'][ind], df_trade_option['quantity'][ind], 'SELL')
                                
                                df_trade_option['ExitPrice'][ind] = Ltp
                                df_trade_option['TradeStatus'][ind] = 'Closed'
                            
                            PnL = (Ltp - df_trade_option['EntryPrice'][ind] ) * df_trade_option['quantity'][ind]
                            df_trade_option['PnL'][ind] = PnL
                print(f"\n\n{df_trade_option}")  
                sleep(5)
                
                if len(df_trade_option[df_trade_option.TradeStatus == 'Closed']) == 2:
                    #now no more trade waiting so its time to exit
                    break
            except Exception as e:
                Message ="Exception occur while analysing trade :" + str(e)
                print(Message)
                logger.info(Message)
    else:
        Message = "No strike find based on your desired premium price range, so closing the algo. You may change the value and restart the algo"
        print(Message)
        logger.info(Message)

def place_trade(tradingsymbol, quantity, buy_or_sell):
    global api
    
    ExecutedPrice = 0
    try:
        orderId = api.place_order(
            buy_or_sell=buy_or_sell[0],
            product_type='I',
            exchange='NFO',
            tradingsymbol=tradingsymbol,
            quantity=quantity,
            discloseqty=0,
            price_type="MKT",
            price=0.0,
            trigger_price=None,
            retention="DAY",
            remarks="Python_Trader_BOC",
        ).get("norenordno")

        filled_quantity, ExecutedPrice = order_status(orderId)

        Message = "Placed order id :" + orderId + ", Executed @ " + str(ExecutedPrice)
        print(Message)
    except Exception as e:
        Message ="Exception occur in order placement : " + str(e)
        print(Message)
        logger.info(Message)
    return ExecutedPrice

def order_status (orderid):
    Message = "I am inside order_status for " + str(orderid)
    #print(Message)
    logger.info(Message)
    global api
    filled_quantity = 0
    AverageExecutedPrice = 0
    try:
        order_book = api.get_order_book()
        order_book = pd.DataFrame(order_book)
        
        order_book = order_book[order_book.norenordno == str(orderid)]
        #print(order_book)
        
        status = order_book.iloc[0]['status']
        if(status == 'COMPLETE'):
            filled_quantity = 1
            AverageExecutedPrice = order_book.iloc[0]['avgprc']
    except Exception as e:
        Message = str(e) + " : Exception occur in order_status while fetching status for orderid #" + str(orderid)
        print(Message)
        logger.info(Message)
    return filled_quantity, float(AverageExecutedPrice)
    
def GetLTP(exchange, token):
    global api
    LTP = 0
    try:
        LTP = float(api.get_quotes(exchange=exchange, token=str(token))['lp'])
    
    except Exception as e:
        Message = str(e) + ": Exception occur in GetLTP, while fetching LTP for exchange " + str(exchange) + " token = " + str(token)
        print(Message)
        logger.info(Message)
    return LTP
    
if __name__ == '__main__':  
    
    WelcomeMessage = "\n\nBOC 145 algo started for " + userid
    print(WelcomeMessage)
    if ConnectApi() == 1:
        print("Logging successful")
        strategy()
        print("Algo closed successful")
    else:
        Message = "Please check your credential and start program again"
        print(Message)
    
    
