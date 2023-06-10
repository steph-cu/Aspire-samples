#==================================================================================================================================
#
#   OpenADR Server for EMS Management
#
#==================================================================================================================================
#
#   Uses Openleadr, Logger, _thread, and mysql 
#   Runs functions on multiple threads
#=================================================================================================================================
"""
#=================================================================================================================================
#                           <<< Functions >>>
#   Clear_old_reports(Folder):
#   Logger_setup(name):
----------------------------------------------------------------------------------------------------------------------------------
#   on_create_party_registration(registration_info):
#   on_register_report(ven_id, resource_id, measurement, unit, scale, min_sampling_interval, max_sampling_interval):
----------------------------------------------------------------------------------------------------------------------------------
#   FroniusCheckStatus(Value):
#   SMACheckStatus(Value):
#   YaskawaCheckStatus(Value):
----------------------------------------------------------------------------------------------------------------------------------
#   on_update_report(data, ven_id, resource_id, measurement):
#   event_response_callback(ven_id, event_id, opt_type):
----------------------------------------------------------------------------------------------------------------------------------
#   RMP_update(mode) <---------------------------------------------------------------------------------- This is a temporary event until we can get the real rmp client
#   update_regatron(voltage, current, power, res, over_voltage, over_current, state):
#   update_mxCom(current, voltage_type, onOff, ACVolt, DCVolt):
#   update_nhr(range, bdv, mode):
#   update_nhr_2(range, bdv, mode):
#   update_nhr_3(range, bdv, mode):
#       battery_logic[class]
#   update_battery_power(power)
#   update_battery_schedule(alter)
#   Emergency_OFF(Name, mode):
#   update_IP(ID)
#   update_yaskawa(amount_temp, amount_perm):
#   update_SMA7(amount):
#   update_SMA750(amount):
#   update_Fronius76(amount):
#   update_Fronius20(amount):
#   update_Grizl(name, amount=0)
----------------------------------------------------------------------------------------------------------------------------------
#   State_convert(ID, State)
#   reference_check(name)
#   manage_sql():
#   machine_Check(t):
#   Lock_out(ID):
#   Limit_Check(ID, reference, equipment):
#   auto_Control(name)
#   Decode_RMP(value)
#   
#   on_create_party_registration()      assign a ven_id for every piece of equipment that will be reporting
#   on_register_report()                assign a callback and sampling interval for recieving the reports
#   FroniusCheckStatus()                status value definitions for Fronius
#   SMACheckStatus()                    status value definitions for SMA
#   YaskawaCheckStatus()                status value definitions for Yaskawa
#   log()                               update Log with reported value, time and piece of equipment
#   on_update_report()                  callback that recieves report data and handles it
#   event_response_callback()           callback that recieves the response from a VEN to an event
#   update_battery()                    ___ Not implemented currently ___
#   RMP_update()      <--------------- This is a temporary event until we can get the real rmp client
#   update_regatron()                   defines events for updating the regatron, signal type, payload, and interval
#   update_mxCom()                      defines events for updating the mx-30, signal type, payload, and interval
#   update_nhr()                        defines events for updating the nhr1, signal type, payload, and interval
#   update_nhr_2()                      defines events for updating the nhr2, signal type, payload, and interval
#   update_nhr_3()                      defines events for updating the nhr3, signal type, payload, and interval
#   update_battery_power()              defines events for overriding battery power, signal type, payload, and interval
#   update_battery_schedule()           sets events for alternate batter power schedules
#   Emergency_OFF()                     
#   update_yaskawa()                    defines events for updating the yaskawa, signal type, payload, and interval
#   update_SMA7()                       defines events for updating the SMA7, signal type, payload, and interval
#   update_SMA50()                      defines events for updating the SMA50, signal type, payload, and interval
#   update_Fronius76()                  defines events for updating the Fronius76, signal type, payload, and interval
#   update_Fronius20()                  defines events for updating the Fronius20, signal type, payload, and interval
#   Update_Grizl()                      set charging profile, send change configuration, send reset
#   State_convert()                     converts state to int value for the event
#   reference_check()                   checks to make sure the equipment is running within parameters set in the SQL table, makes corrections if they are not; runs in a seperate thread
#  
#   manage_sql()                        commands to read, update, or delete values from the SQL management table                      
#   machine_Check()                     checks for scheduled events and makes sure user does not exceed limits; if an event is not scheduled, lockout power supply
#   Lock_out()                          sends an emergency off signal to power supplies 
#   Limit_Check()                       checks real time data to ensure the user does not exceed scheduled limits
#   auto_control()                      function to control the Logix battery
#   Decode_RMP()                        update SMA50 power limit
#
# -----------------------------------------------------------------------------------------------------------------
#                           
#   Server Setup functions and Infinite runtime loop setup
#
#==================================================================================================================================
"""

import asyncio
import logging
import mysql.connector
import openleadr
import os
import shutil
import time as TIME
import _thread
import threading
import re
import sys
sys.path.insert(0, '../Lib')
from datetime import *
from datetime import datetime, timezone, timedelta, time
from functools import partial
from mysql.connector import Error
from MySQL import *
from openleadr import OpenADRServer, enable_default_logging
from openleadr.objects import Event, EventDescriptor, EventSignal, Target, Interval
from functools import partial
from array import *


class prompt_thread(threading.Thread):
    def __init__(self) :
        threading.Thread.__init__(self)
        self.runnable = manage_sql
        self.daemon = True
    
    def run(self) :
        self.runnable()


#=========================================================================
#---- Logger setup ------------------------------------------------

string = datetime.now()
filePath=os.path.expanduser('~')

if not os.path.exists("Logs"): # If the file path does not exsist create it
    os.mkdir("Logs")
os.chdir("Logs")

def Clear_old_reports(Folder):
    print("\nClear old files in ",os.getcwd()) # get the current working directory
    Folder = Folder.split("-")
    #print(Folder)
    
    if os.getcwd() == "/home/microgrid/EMS/evr-ems-communication/testSQL/Exec/Logs": # <-- will need to update the directory path once the server is in final place
        if Folder[2] > '07':    # Find the logs for the last 7 days
            Folder[2] = (int(Folder[2])-7)
        else:
            if(int(Folder[1]) == 1 ): # if beginning of January 
                Folder[0] = int(Folder[0])-1 # change the year
                Folder[2] = (20 + int(Folder[2])) # change the day
                Folder[1] = int(Folder[1]) -1 # change the month
            else:
                Folder[2] = (20 + int(Folder[2])) #change the day
                Folder[1] = int(Folder[1]) -1 #change the month

                if int(Folder[1]) < 10: # if the month is less then 10 add a 0 in front ex. 1 -> 01
                    Folder[1] = "0" + str(Folder[1])

        if int(Folder[2]) < 10: # if the number is less then 10 add a 0 in front ex. 1 -> 01
            Folder[2] = "0" + str(Folder[2])
        #print(Folder[2])
        Folder = str(Folder[0]) + "-" +str(Folder[1])+"-"+str(Folder[2])
        print(Folder)
        
        for dir in os.walk("./"):   # Get directories and if they are older than a week delete the logs
            if str(dir[0]) != "./":
                dir = str(dir[0]).replace("./", "")
                if dir < Folder:
                    print("\n",dir)
                    print("less than ", Folder)
                    shutil.rmtree(dir)
    else:
        print("Can not clear files. You are in ", os.getcwd())
            

def Logger_setup(name): # Ran in a seperate thread, creates a new log file every hour
    global filePath
    global updateLogger # Logger for the update report logs
    oldinsidefolder = ''
    olddate = ''

    while True:
        datestring = str(date.today())+" "+str(datetime.now().hour)  # get current date and hour
        if olddate != datestring: # check the last time log files were updated   
            with Lock:
                olddate = datestring # set the date to the new datestring
                insideFolder = str(date.today()) # Check if it is a new day
                if not os.path.exists(insideFolder):
                    os.mkdir(insideFolder)
                if oldinsidefolder != insideFolder:
                    #print("Need new directory")
                    Clear_old_reports(insideFolder) # clear old reports
                    oldinsidefolder = insideFolder
                os.chdir(insideFolder)            

                filePath+="\Logs"+"\\"+insideFolder
                path = filePath+"\Logs"
                final=path
                path=path.replace("\\","") # Now the path exists
                fileName = "Log_ "+str(date.today())+" "+str(datetime.now().hour) + ".txt" # create a file 

                print("Created a new file", fileName)
                #openleadr.enable_default_logging(level=logging.INFO) # <--- This will log to console and is not the desired option
                logging.basicConfig(filename=fileName, level=logging.INFO) # Tell python to log to this file

                filehandler = logging.FileHandler(fileName) # Create filehandler
                logger = logging.getLogger('openleadr') # Get the Logger 
                logger.setLevel(logging.INFO)
                for hdlr in logger.handlers[:]:  # remove all old handlers
                    logger.removeHandler(hdlr)
                logger.addHandler(filehandler) # Add FileHandler, so the logger can write to the file that was created


                # Add logger for update reports 
                fileName2 = "Update_Report_Log_ "+str(date.today())+" "+str(datetime.now().hour) + ".txt" # create a file 

                print("Created a new file", fileName2)
                filehandler2 = logging.FileHandler(fileName2) # Create filehandler
                updateLogger = logging.getLogger('update_logger') # create logger
                updateLogger.setLevel(logging.INFO) # set logger level
                for hdlr in updateLogger.handlers[:]:  # remove all old handlers
                    updateLogger.removeHandler(hdlr)
                updateLogger.addHandler(filehandler2) # add file to logger

                #print("old: ",os.getcwd())
                os.chdir("..")
                #print("new: ",os.getcwd())
        TIME.sleep(1) # Wait then check the time


# Add thread to create logger
Lock = threading.Lock()   
_thread.start_new_thread(Logger_setup, ("t3",))

#--- End logger setup --------------------------------------------
#==============================================================================

#==============================================================================
#---- MYSQL ------------------------------------------------

try:
    #global connection
    connect = False
    timeout = 0
    while connect  == False and timeout < 3:
        #print("ready to connect to mysql \n\n")
        mySQL = SQL() # MySQL Library
        mySQL.sql_connect()

        if mySQL.connection.is_connected(): 
            connect = True
            print("\n Connected to MySQL\n")
            
            #mySQL.drop_table("equipment")
            #mySQL.drop_table("reference")
            #mySQL.drop_table("externalreference")
            #mySQL.drop_table("user")
            #mySQL.drop_table("battery")

            mySQL.createTable_equipment() # create equipment table
            mySQL.createTable_reference() # create reference value table for power supplies
            mySQL.createTable_External_reference() # create externalreference 
            mySQL.createTable_battery()   # create battery
        
            mySQL.Close()
            
        else:
            print("\t No Connection \n")
            timeout += 1
            if(timeout > 3):
                print("TIME OUT, Please try again")
            time.sleep(1)

except Error as err:
    print(f"\tError: '{err}'")

#=========================================================
#---- End MYSQL -----------------------------------------
#=========================================================

async def on_create_party_registration(registration_info):
    """
    Inspect the registration info and return a ven_id and registration_id.
    """
    print("REGISTERING", registration_info['ven_name'])
    if registration_info['ven_name'] == 'PowerSupply':
        ven_id = 'PowerSupplies'
        registration_id = 'PowerSupplies'
        return ven_id, registration_id
    elif registration_info['ven_name'] == 'GK':
        ven_id = 'gk'
        registration_id = 'gk'
        return ven_id, registration_id
    elif registration_info['ven_name'] == 'Fronius20':
        ven_id = 'fronius20'
        registration_id = 'fronius20'
        return ven_id, registration_id
    elif registration_info['ven_name'] == 'Fronius76':
        ven_id = 'fronius76'
        registration_id = 'fronius76'
        return ven_id, registration_id
    elif registration_info['ven_name'] == 'SMA50Client':
        ven_id = 'sma50'
        registration_id = 'sma50'
        return ven_id, registration_id
    elif registration_info['ven_name'] == 'SMA7Client':
        ven_id = 'sma7'
        registration_id = 'sma7'
        return ven_id, registration_id
    elif registration_info['ven_name'] == 'RMP': 
        ven_id = 'ven_id_228'
        registration_id = 'reg_id_228'
        return ven_id, registration_id
    elif registration_info['ven_name'] == 'Yaskawa':
        ven_id = 'ven_id_224'
        registration_id = 'reg_id_224'
        return ven_id, registration_id
    elif registration_info['ven_name'] == 'SMAClient':
        ven_id = 'ven_id_225'
        registration_id = 'reg_id_225'
        return ven_id, registration_id
    elif registration_info['ven_name'] == 'Grizl':
        ven_id = 'ven_id_300'
        registration_id = 'reg_id_300'
        return ven_id, registration_id
    elif registration_info['ven_name'] == 'ABB':
        ven_id = 'ABB'
        registration_id = 'ABB'
        return ven_id, registration_id
    elif registration_info['ven_name'] == 'logix':
        ven_id = 'logix_battery'
        registration_id = 'logix_battery'
        return ven_id, registration_id
    elif registration_info['ven_name'] == 'Leviton':
        ven_id = 'Leviton_ID'
        registration_id = 'Leviton_rID'
        return ven_id, registration_id
    else:
        print(registration_info['ven_name'])
        return False


async def on_register_report(ven_id, resource_id, measurement, unit, scale,
                             min_sampling_interval, max_sampling_interval):
    """
    Inspect a report offering from the VEN and return a callback and sampling interval for receiving the reports.
    """
    #print("We are in on register_report")
    callback = partial(on_update_report, ven_id=ven_id, resource_id=resource_id, measurement=measurement)
    sampling_interval = min_sampling_interval
    return callback, sampling_interval


   ## Interprets the status data for the inverters


#=============================================
#   Converts the response from int to string
#=============================================
def FroniusCheckStatus(Value):
    if(Value == 1):
        Value = "Off"
    elif(Value == 2):
        Value = "Auto Shutdown"
    elif(Value == 3):
        Value = "Starting"
    elif(Value == 4):
        Value = "Running"
    elif(Value == 5):
        Value = "Power Reduction"
    elif(Value == 6):
        Value = "Shutting Down"
    elif(Value == 7):
        Value = "Fault"
    elif(Value == 8):
        Value = "Standby"
    else:
        Value = "Status not found"
    return Value


#=============================================
#   Converts the response from int to string
#=============================================
def SMACheckStatus(Value):
    if(Value == 1):
        Value = "OFF"
    elif(Value == 2):
        Value = "Wait for PV Voltage"
    elif(Value == 3):
        Value = "Starting"
    elif(Value == 4):
        Value = "MPP (Running Normal)"
    elif(Value == 5):
        Value = "Regulated"
    elif(Value == 6):
        Value = "Shutting Down"
    elif(Value == 7):
        Value = "Fault"
    elif(Value == 8):
        Value = "Waiting for electric utility compamy"
    else:
        Value = "Status not found"
    return Value


#=============================================
#   Converts the response from int to string
#=============================================
def YaskawaCheckStatus(Value):
    if(Value == 0x1000):
        Value = "Running"
    elif(Value == 0x8000):
        Value = "Fault"
    elif(Value == 0x4000):
        Value = "Inverter is checking input and output Status"
    elif(Value == 0x2000):
        Value = "Standby"
    elif(Value == 0x0800):
        Value = "Derating"
    else:
        Value = "Status not found"
    return Value


#===============================================
#   writes the information to the update report
#===============================================
def log(time, value, ven_id, resource_id, measurement):
    global updateLogger

    if value != 0:
        updateLogger.info(f"{resource_id} reported {measurement} = {value} at time {time} from {ven_id}")

global actionPass
actionPass = True

async def on_update_report(data, ven_id, resource_id, measurement):
    """
    Callback that receives report data from the VEN and handles it.
    """
    for time, value in data:        
        #print(f"Ven {ven_id} reported {measurement} = {value} at time {time} for resource {ID}")

        with Lock: # Need to use lock because we will be writing to SQL tables
            if value != 0:
                log(time, value, ven_id, resource_id, measurement)

            mySQL.sql_connect() # Connect to SQL database
            ID = "" # ID for the sql table
            #print("\t\t >>>>>>>> " , ID, "   " , value, "  ",measurement) # here for debugging

            ID=resource_id

            if ID == 'battery_soc': # update the battery table ----------
                mySQL.update_battery(ID='Logix_Blue', SOC=value)
            elif ID == 'battery_report_power':
                mySQL.update_battery(ID='Logix_Blue', Power=value)
            elif ID == 'battery_desired_charge_rate':
                mySQL.update_battery(ID='Logix_Blue', charge=value)
            elif ID == 'battery_status':
                mySQL.update_battery(ID='Logix_Blue', Status=value)# -----------
            if ID == 'RMP':
                Decode_RMP(value)
                
            if measurement == 'Status':
                if (ID == 'SMA_SEVEN' or ID == 'SMA_FIFTY'):
                    status = SMACheckStatus(int(value))
                    mySQL.update_equipment(ID=ID, State = status)
                if (ID == 'Fronius_TWENTY' or ID == 'Fronius_SEVEN_SIX'):
                    status = FroniusCheckStatus(int(value))
                    mySQL.update_equipment(ID=ID, State = status)
                if ID == 'Yaskawa':
                    status = YaskawaCheckStatus(int(value))
                    mySQL.update_equipment(ID=ID, State = status)
            elif measurement == 'Mode':
                if ID == "MX_THIRTY":
                    if(value == -1.0):
                        mySQL.update_equipment(ID=ID, State = "OFF")
                    else:
                        mySQL.update_equipment(ID=ID, State = "ON")
                elif ID == "Grizl":
                    if(value == 1.0):
                        mySQL.update_equipment(ID=ID, State="Available")
                    elif (value == 2.0):
                        mySQL.update_equipment(ID=ID, State="Preparing")
                        # if (actionPass == True):
                        #     mySQL.update_reference(ID=ID, State="Ready")
                        #     actionPass = False
                        # mySQL.update_reference(ID=ID, State="Ready")
                    elif (value == 3.0):
                        mySQL.update_equipment(ID=ID, State="Charging")
                        mySQL.update_reference(ID=ID, State="Running")
                        # actionPass = True
                    elif (value == 4.0):
                        mySQL.update_equipment(ID=ID, State="Finishing")
                        mySQL.update_reference(ID=ID, State="Ready")
            elif measurement == 'output':
                if value == 0.0:
                    mySQL.update_equipment(ID=ID, State = 'OFF')
                else:
                        mySQL.update_equipment(ID=ID, State = str(value))
            elif measurement == 'Faults' or measurement == 'Flags':
                mySQL.update_equipment(ID=ID, Fault=str(value))
            elif measurement == 'Volts' or measurement == 'DCVoltage' or measurement == 'VoltageDC':
                if (ID == 'NHR_ONE' or ID == 'NHR_TWO' or ID == 'NHR_THREE' or ID == 'Regatron' or ID == 'GK'):
                    if(value != 0.0):
                        mySQL.update_equipment(ID=ID, State = "ON",Voltage=value )
                    else:
                        mySQL.update_equipment(ID=ID, State = "OFF",Voltage=value )
                elif ID == 'Logix_Blue' and value != 0.0:
                        mySQL.update_equipment(ID=ID, State = "Connected",Voltage=value )
                else:
                    mySQL.update_equipment(ID=ID, Voltage=value)
            elif measurement == 'Current' or measurement == 'TotalCurrent' or measurement == 'DCCurrent':
                mySQL.update_equipment(ID=ID, Current=value)
            elif measurement == 'Watts'or measurement == 'Power' or measurement == 'DailyEnergy' or measurement == 'PowerDC':
                mySQL.update_equipment(ID=ID, Power=value)
            elif measurement == 'SOC':
                mySQL.update_equipment(ID=ID, SOC=value)
            else:
                print("Error processing measurements")

            mySQL.Close() # close connection to SQL database

async def event_response_callback(ven_id, event_id, opt_type):
    """
    Callback that receives the response from a VEN to an Event.
    """
    print(f"VEN {ven_id} responded to Event {event_id} with: {opt_type}")

# message id
regatron_msg_id = 0
mx_msg_id = 0
nhr_one_msg_id = 0
nhr_two_msg_id = 0
nhr_three_msg_id = 0
yaskawa_msg_id = 0
sma_seven_msg_id = 0
sma_fifty_msg_id = 0
fronius_seventysix_msg_id = 0
fronius_twenty_msg_id = 0
grizl_id = 0
battery_power_msg_id = 0
Emergency_OFF_ID = 0
RMP_ID = 0
update_IP_ID = 0
update_battery_ID = 0
Gustav_Klein_msg_id = 0

#=========================================================================================
# add brians update_battery
#=========================================================================================

def RMP_update(mode):
    global RMP_ID
    RMP_ID += 1
    event_id_str = 'RMP ' + str(RMP_ID)
    event = Event(event_descriptor=EventDescriptor(event_id=event_id_str,
                                               modification_number=0,
                                               event_status='none',
                                               market_context='http://RMP'),
                event_signals=[EventSignal(signal_id='mode',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':mode,}]),],
              targets=[Target(ven_id='ven_id_228')])
    server.add_raw_event(ven_id='ven_id_228', event=event)

#===================================================================================
# Sends an event to client with the information needed to control the power supply
#===================================================================================
def update_regatron(voltage, current, power, res, over_voltage, over_current, state):
    print('update regatron')
    global regatron_msg_id
    regatron_msg_id += 1
    event_id_str = 'Regatron ' + str(regatron_msg_id)
    event = Event(event_descriptor=EventDescriptor(event_id=event_id_str,
                                               modification_number=0,
                                               event_status='none',
                                               market_context='http://regatron'),
                event_signals=[EventSignal(signal_id='voltage_ref',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':voltage,}]),
                            EventSignal(signal_id='current_ref',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':current,}]),
                            EventSignal(signal_id='power_ref',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':power,}]),
                            EventSignal(signal_id='internal_resistance',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':res,}]),
                            EventSignal(signal_id='over_voltage',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':over_voltage,}]),
                            EventSignal(signal_id='over_current',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':over_current,}]),
                            EventSignal(signal_id='state',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':state,}])],
              targets=[Target(ven_id='PowerSupplies')])
    server.add_raw_event(ven_id='PowerSupplies', event=event)

#===================================================================================
# Sends an event to client with the information needed to control the power supply
#===================================================================================
def update_mxCom(current, voltage_type, onOff, ACVolt, DCVolt, MXfreq, MXVR, MXOV, slewV, shape, clipL, Ores, Oimp, DCoffset, alc, cc, delay, Reset):
    print("updating")
    global mx_msg_id
    mx_msg_id += 1
    event_id_str = 'mxCom ' + str(mx_msg_id)
    event = Event(event_descriptor=EventDescriptor(event_id=event_id_str,
                                               modification_number=0,
                                               event_status='none',
                                               market_context='http://mxCom'),
                event_signals=[EventSignal(signal_id='current',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':current,}]),
                            EventSignal(signal_id='type',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':voltage_type,}]),
                            EventSignal(signal_id='on/off',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':onOff,}]),
                            EventSignal(signal_id='ACVolt',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':ACVolt,}]),
                            EventSignal(signal_id='DCVolt',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':DCVolt,}]),
                            EventSignal(signal_id='frequency',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':MXfreq,}]),
                            EventSignal(signal_id='VR',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':MXVR,}]),
                            EventSignal(signal_id='OV',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':MXOV,}]),
                            EventSignal(signal_id='slewV',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':slewV,}]),
                            EventSignal(signal_id='shape',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':shape,}]),
                            EventSignal(signal_id='clipL',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':clipL,}]),
                            EventSignal(signal_id='Ores',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':Ores,}]),
                            EventSignal(signal_id='Oimp',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':Oimp,}]),
                            EventSignal(signal_id='DCoffset',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':DCoffset,}]),
                            EventSignal(signal_id='alc',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':alc,}]),
                            EventSignal(signal_id='cc',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':cc,}]),
                            EventSignal(signal_id='ccdelay',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':delay,}]),
                            EventSignal(signal_id='Reset',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(Reset),}])],
              targets=[Target(ven_id='PowerSupplies')])
    server.add_raw_event(ven_id='PowerSupplies', event=event)

#===================================================================================
# Sends an event to client with the information needed to control the power supply
#===================================================================================
def update_nhr(range, bdv, State, mode, enable, voltage, current, power, resistance, OC, slewV, slewC, slewP, slewR, Rgain, parenable, aux, Reset):

    safety = OC.split(",")
    print(safety)


    global nhr_one_msg_id
    nhr_one_msg_id += 1
    event_id_str = 'nhr ' + str(nhr_one_msg_id)
    event = Event(event_descriptor=EventDescriptor(event_id=event_id_str,
                                               modification_number=0,
                                               event_status='none',
                                               market_context='http://nhr'),
                event_signals=[EventSignal(signal_id='range',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':range,}]),
                            EventSignal(signal_id='bdv',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':bdv,}]),
                            EventSignal(signal_id='mode',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':mode,}]),
                            EventSignal(signal_id='enable',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':enable,}]),
                            EventSignal(signal_id='voltage',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':voltage,}]),
                            EventSignal(signal_id='current',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':current,}]),
                            EventSignal(signal_id='power',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':power,}]),
                            EventSignal(signal_id='resistance',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':resistance,}]),
                            EventSignal(signal_id='State',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':State,}]),
                            EventSignal(signal_id='OC0',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[0]),}]),
                            EventSignal(signal_id='OC1',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[1]),}]),
                            EventSignal(signal_id='OC2',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[2]),}]),
                            EventSignal(signal_id='OC3',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[3]),}]),
                            EventSignal(signal_id='OC4',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[4]),}]),
                            EventSignal(signal_id='OC5',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[5]),}]),
                            EventSignal(signal_id='OC6',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[6]),}]),
                            EventSignal(signal_id='OC7',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[7]),}]),
                            EventSignal(signal_id='OC8',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[8]),}]),
                            EventSignal(signal_id='OC9',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[9]),}]),
                            EventSignal(signal_id='OC10',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[10]),}]),
                            EventSignal(signal_id='OC11',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[11]),}]),
                            EventSignal(signal_id='slewV',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(slewV),}]),
                            EventSignal(signal_id='slewC',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(slewC),}]),
                            EventSignal(signal_id='slewP',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(slewP),}]),
                            EventSignal(signal_id='slewR',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(slewR),}]),
                            EventSignal(signal_id='Rgain',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(Rgain),}]),
                            EventSignal(signal_id='parallel_enable',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(parenable),}]),
                            EventSignal(signal_id='auxilary',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(aux),}]),
                            EventSignal(signal_id='Reset',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(Reset),}]),],
              targets=[Target(ven_id='PowerSupplies')])
    server.add_raw_event(ven_id='PowerSupplies', event=event)

#===================================================================================
# Sends an event to client with the information needed to control the power supply
#===================================================================================
def update_nhr_2(range, bdv, State, mode, enable, voltage, current, power, resistance, OC, slewV, slewC, slewP, slewR, Rgain, parenable, aux, Reset):
    safety = OC.split(",")
    print(safety)

    global nhr_two_msg_id
    nhr_two_msg_id += 1
    event_id_str = 'nhr_2 ' + str(nhr_two_msg_id)
    event = Event(event_descriptor=EventDescriptor(event_id=event_id_str,
                                               modification_number=0,
                                               event_status='none',
                                               market_context='http://nhr'),
                event_signals=[EventSignal(signal_id='range',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':range,}]),
                            EventSignal(signal_id='bdv',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':bdv,}]),
                            EventSignal(signal_id='mode',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':mode,}]),
                            EventSignal(signal_id='enable',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':enable,}]),
                            EventSignal(signal_id='voltage',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':voltage,}]),
                            EventSignal(signal_id='current',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':current,}]),
                            EventSignal(signal_id='power',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':power,}]),
                            EventSignal(signal_id='resistance',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':resistance,}]),
                            EventSignal(signal_id='State',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':State,}]),
                            EventSignal(signal_id='OC0',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[0]),}]),
                            EventSignal(signal_id='OC1',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[1]),}]),
                            EventSignal(signal_id='OC2',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[2]),}]),
                            EventSignal(signal_id='OC3',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[3]),}]),
                            EventSignal(signal_id='OC4',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[4]),}]),
                            EventSignal(signal_id='OC5',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[5]),}]),
                            EventSignal(signal_id='OC6',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[6]),}]),
                            EventSignal(signal_id='OC7',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[7]),}]),
                            EventSignal(signal_id='OC8',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[8]),}]),
                            EventSignal(signal_id='OC9',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[9]),}]),
                            EventSignal(signal_id='OC10',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[10]),}]),
                            EventSignal(signal_id='OC11',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[11]),}]),
                            EventSignal(signal_id='slewV',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(slewV),}]),
                            EventSignal(signal_id='slewC',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(slewC),}]),
                            EventSignal(signal_id='slewP',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(slewP),}]),
                            EventSignal(signal_id='slewR',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(slewR),}]),
                            EventSignal(signal_id='Rgain',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(Rgain),}]),
                            EventSignal(signal_id='parallel_enable',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(parenable),}]),
                            EventSignal(signal_id='auxilary',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(aux),}]),
                            EventSignal(signal_id='Reset',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(Reset),}]),],
              targets=[Target(ven_id='PowerSupplies')])
    server.add_raw_event(ven_id='PowerSupplies', event=event)

#===================================================================================
# Sends an event to client with the information needed to control the power supply
#===================================================================================
def update_nhr_3(range, bdv, State, mode, enable, voltage, current, power, resistance, OC, slewV, slewC, slewP, slewR, Rgain, parenable, aux, Reset):
    safety = OC.split(",")
    print(safety)

    global nhr_three_msg_id
    nhr_three_msg_id += 1
    event_id_str = 'nhr_3 ' + str(nhr_three_msg_id)
    event = Event(event_descriptor=EventDescriptor(event_id=event_id_str,
                                               modification_number=0,
                                               event_status='none',
                                               market_context='http://nhr'),
                event_signals=[EventSignal(signal_id='range',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':range,}]),
                            EventSignal(signal_id='bdv',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':bdv,}]),
                            EventSignal(signal_id='mode',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':mode,}]),
                            EventSignal(signal_id='enable',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':enable,}]),
                            EventSignal(signal_id='voltage',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':voltage,}]),
                            EventSignal(signal_id='current',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':current,}]),
                            EventSignal(signal_id='power',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':power,}]),
                            EventSignal(signal_id='resistance',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':resistance,}]),
                            EventSignal(signal_id='State',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':State,}]),
                            EventSignal(signal_id='OC0',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[0]),}]),
                            EventSignal(signal_id='OC1',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[1]),}]),
                            EventSignal(signal_id='OC2',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[2]),}]),
                            EventSignal(signal_id='OC3',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[3]),}]),
                            EventSignal(signal_id='OC4',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[4]),}]),
                            EventSignal(signal_id='OC5',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[5]),}]),
                            EventSignal(signal_id='OC6',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[6]),}]),
                            EventSignal(signal_id='OC7',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[7]),}]),
                            EventSignal(signal_id='OC8',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[8]),}]),
                            EventSignal(signal_id='OC9',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[9]),}]),
                            EventSignal(signal_id='OC10',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[10]),}]),
                            EventSignal(signal_id='OC11',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(safety[11]),}]),
                            EventSignal(signal_id='slewV',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(slewV),}]),
                            EventSignal(signal_id='slewC',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(slewC),}]),
                            EventSignal(signal_id='slewP',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(slewP),}]),
                            EventSignal(signal_id='slewR',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(slewR),}]),
                            EventSignal(signal_id='Rgain',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(Rgain),}]),
                            EventSignal(signal_id='parallel_enable',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(parenable),}]),
                            EventSignal(signal_id='auxilary',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(aux),}]),
                            EventSignal(signal_id='Reset',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(Reset),}]),],
              targets=[Target(ven_id='PowerSupplies')])
    server.add_raw_event(ven_id='PowerSupplies', event=event)

def update_Gustav_Klein(state, voltage, source_current, sink_current, source_power, sink_power, internal_resistence, Reset, discharge_mode):
    print("GK is sent")
    global Gustav_Klein_msg_id
    Gustav_Klein_msg_id += 1
    event_id_str = 'GustavKlien ' + str(Gustav_Klein_msg_id)
    event = Event(event_descriptor=EventDescriptor(event_id=event_id_str,
                                               modification_number=0,
                                               event_status='none',
                                               market_context='http://GK'),
                event_signals=[EventSignal(signal_id='state',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(state),}]),
                            EventSignal(signal_id='voltage',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(voltage),}]),
                            EventSignal(signal_id='source_current',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(source_current),}]),
                            EventSignal(signal_id='sink_current',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(sink_current),}]),
                            EventSignal(signal_id='source_power',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(source_power),}]),
                            EventSignal(signal_id='sink_power',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(sink_power),}]),
                            EventSignal(signal_id='internal_resistence',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(internal_resistence),}]),
                            EventSignal(signal_id='Reset',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(Reset),}]),
                            EventSignal(signal_id='discharge_mode',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(discharge_mode),}]),],
              targets=[Target(ven_id='gk')])
    server.add_raw_event(ven_id='gk', event=event)

class battery_logic:
    power = 0

def update_battery_power(power):
    global battery_power_msg_id
    print("battery power override: " + str(power))
    battery_logic.power = power
#    server.events_updated['ven_id_139'] = True
    battery_power_msg_id += 1
    event_id_str = 'battery_power ' + str(battery_power_msg_id)
    event = Event(event_descriptor=EventDescriptor(event_id=event_id_str,
                                            modification_number=0,
                                            event_status ='none',
                                            market_context='http://battery_1'),
                event_signals=[EventSignal(signal_id='power',
                                        signal_type='level',
                                        signal_name='simple',
                                        intervals=[{'dtstart':datetime.now(),
                                                            'duration':timedelta(seconds=30),
                                                            'signal_payload':power,}]),],
            targets=[Target(ven_id='logix_battery')])
    server.add_raw_event(ven_id='logix_battery', event=event)

def update_battery_schedule(alter):
    global battery_power_msg_id
    #print("battery power schedule alternate: " + str(alter))
#    battery_logic. = alter
#    server.events_updated['ven_id_139'] = True
    battery_power_msg_id += 1
    event_id_str = 'alter_schedule ' + str(battery_power_msg_id)
    event = Event(event_descriptor=EventDescriptor(event_id=event_id_str,
                                            modification_number=0,
                                            event_status ='none',
                                            market_context='http://battery_1'),
                event_signals=[EventSignal(signal_id='power',
                                        signal_type='level',
                                        signal_name='simple',
                                        intervals=[{'dtstart':datetime.now(),
                                                            'duration':timedelta(seconds=30),
                                                            'signal_payload':float(alter),}]),],
            targets=[Target(ven_id='logix_battery')])
    server.add_raw_event(ven_id='logix_battery', event=event)

#===================================================================================
# Sends an event to client to turn off the power supply
#===================================================================================
def Emergency_OFF(Name, mode):
    print("Off for ", Name)
    global Emergency_OFF_ID
    Emergency_OFF_ID += 1
    event_id_str = Name +" "+ str(Emergency_OFF_ID)
    event = Event(event_descriptor=EventDescriptor(event_id=event_id_str,
                                               modification_number=0,
                                               event_status='none',
                                               market_context='http://eo'),
                event_signals=[EventSignal(signal_id='mode',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':mode,}]),],
              targets=[Target(ven_id='PowerSupplies')])
    server.add_raw_event(ven_id='PowerSupplies', event=event)

def Emergency_OFF_gk(Name, mode):
    global Emergency_OFF_ID
    Emergency_OFF_ID += 1
    event_id_str = Name +" "+ str(Emergency_OFF_ID)
    event = Event(event_descriptor=EventDescriptor(event_id=event_id_str,
                                               modification_number=0,
                                               event_status='none',
                                               market_context='http://eo'),
                event_signals=[EventSignal(signal_id='mode',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':mode,}]),],
              targets=[Target(ven_id='gk')])
    server.add_raw_event(ven_id='gk', event=event)
#===================================================================================
# Sends an event to client which will make the client update the IP address for the  power supply
#===================================================================================
def update_IP(ID):
    print(" update_IP ",ID)
    global update_IP_ID
    update_IP_ID += 1
    event_id_str = ID + "_IP " + str(update_IP_ID)

    if ID == "Logix_Blue" or ID == "Regatron" or ID == "NHR_ONE" or ID == "NHR_TWO" or ID == "NHR_THREE" or ID == "MX_THIRTY":
        VEN = 'PowerSupplies'
    elif ID == "GK":
        VEN = "gk"
    elif ID == "SMA_FIFTY":
        VEN = "sma50"
    elif ID == "SMA_SEVEN":
        VEN = "sma7"
    elif ID == "Fronius_TWENTY":
        VEN = "fronius20"
    elif ID == "Fronius_SEVEN_SIX":
        VEN = "fronius76"
    elif ID == "Yaskawa":
        VEN = "ven_id_224"
    else:
        print("invalid ID ", ID)
        return
 
    mode = 1
    #print(event_id_str) # here for debugging
        
    event = Event(event_descriptor=EventDescriptor(event_id=event_id_str,
                                               modification_number=0,
                                               event_status='none',
                                               market_context='http://update'),
                event_signals=[EventSignal(signal_id='mode',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':mode,}]),],
              targets=[Target(ven_id=VEN)])
    server.add_raw_event(ven_id=VEN, event=event)
        
def update_yaskawa(amount_temp, amount_perm):
    global yaskawa_msg_id
    yaskawa_msg_id += 1
    event_id_str = 'yaskawa ' + str(yaskawa_msg_id)
    event = Event(event_descriptor=EventDescriptor(event_id=event_id_str,
                                               modification_number=0,
                                               event_status='none',
                                               market_context='http://yaskawa'),
                event_signals=[EventSignal(signal_id='temp_curt',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':amount_temp,}]),
                            EventSignal(signal_id='perm_curt',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':amount_perm,}]),],
              targets=[Target(ven_id='ven_id_224')])
    server.add_raw_event(ven_id='ven_id_224', event=event)

def update_SMA7(amount):
    global sma_seven_msg_id
    sma_seven_msg_id += 1
    event_id_str = 'SMA7 ' + str(sma_seven_msg_id)
    event = Event(event_descriptor=EventDescriptor(event_id=event_id_str,
                                               modification_number=0,
                                               event_status='none',
                                               market_context='http://SMA7'),
                event_signals=[EventSignal(signal_id='percentage',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':float(amount),}]),],
              targets=[Target(ven_id='sma7')])
    server.add_raw_event(ven_id='sma7', event=event)

def update_SMA50(amount):
    global sma_fifty_msg_id
    sma_fifty_msg_id += 1
    event_id_str = 'SMA50 ' + str(sma_fifty_msg_id)
    event = Event(event_descriptor=EventDescriptor(event_id=event_id_str,
                                               modification_number=0,
                                               event_status='none',
                                               market_context='http://SMA50'),
                event_signals=[EventSignal(signal_id='percentage',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':amount,}]),],
              targets=[Target(ven_id='sma50')])
    server.add_raw_event(ven_id='sma50', event=event)

def update_Fronius76(amount):
    global fronius_seventysix_msg_id
    fronius_seventysix_msg_id += 1
    event_id_str = 'Fronius76 ' + str(fronius_seventysix_msg_id)
    event = Event(event_descriptor=EventDescriptor(event_id=event_id_str,
                                               modification_number=0,
                                               event_status='none',
                                               market_context='http://Fronius76'),
                event_signals=[EventSignal(signal_id='percentage',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':amount,}]),],
              targets=[Target(ven_id='fronius76')])
    server.add_raw_event(ven_id='fronius76', event=event)

def update_Fronius20(amount):
    global fronius_twenty_msg_id
    fronius_twenty_msg_id += 1
    event_id_str = 'FroniusTwenty ' + str(fronius_twenty_msg_id)
    event = Event(event_descriptor=EventDescriptor(event_id=event_id_str,
                                               modification_number=0,
                                               event_status='none',
                                               market_context='http://Fronius20'),
                event_signals=[EventSignal(signal_id='percentage',
                                         signal_type='level',
                                         signal_name='simple',
                                         intervals=[{'dtstart':datetime.now(),
                                                             'duration':timedelta(seconds=10),
                                                             'signal_payload':amount}])],
              targets=[Target(ven_id='fronius20')])
    server.add_raw_event(ven_id='fronius20', event=event)

def update_Grizl(name,duration, amount=0): # set charging profile, send change configuration, send reset
    global grizl_id
    grizl_id += 1
    event_id_str = 'Grizl ' + str(grizl_id)
    event = Event(event_descriptor=EventDescriptor(event_id=event_id_str,
                                                modification_number=0,
                                                event_status='none',
                                                market_context='http://Grizle'),
                    event_signals=[EventSignal(signal_id='duration',
                                             signal_type='level',
                                             signal_name='simple',
                                             intervals=[{'dtstart':datetime.now(),
                                                                'duration':timedelta(seconds=10),
                                                                'signal_payload':duration,}]),
                                EventSignal(signal_id=name,
                                             signal_type='level',
                                             signal_name='simple',
                                             intervals=[{'dtstart':datetime.now(),
                                                                'duration':timedelta(seconds=10),
                                                                'signal_payload':amount}])],
                    targets=[Target(ven_id='ven_id_300')])
    server.add_raw_event(ven_id='ven_id_300', event=event)

def update_ABB_East(name, duration, amount=0): # set charging profile, send change configuration, send reset
    global grizl_id
    grizl_id += 1
    event_id_str = 'ABB_East ' + str(grizl_id)
    event = Event(event_descriptor=EventDescriptor(event_id=event_id_str,
                                                modification_number=0,
                                                event_status='none',
                                                market_context='http://Grizle'),
                    event_signals=[EventSignal(signal_id='duration',
                                             signal_type='level',
                                             signal_name='simple',
                                             intervals=[{'dtstart':datetime.now(),
                                                                'duration':timedelta(seconds=10),
                                                                'signal_payload':duration}]),
                                EventSignal(signal_id=name,
                                             signal_type='level',
                                             signal_name='simple',
                                             intervals=[{'dtstart':datetime.now(),
                                                                'duration':timedelta(seconds=10),
                                                                'signal_payload':amount}])],
# need to change VEN to the right client
                    targets=[Target(ven_id='ABB')])
    server.add_raw_event(ven_id='ABB', event=event)


def update_ABB_West(name, duration, amount=0): # set charging profile, send change configuration, send reset
    global grizl_id
    grizl_id += 1
    event_id_str = 'ABB_West ' + str(grizl_id)
    event = Event(event_descriptor=EventDescriptor(event_id=event_id_str,
                                                modification_number=0,
                                                event_status='none',
                                                market_context='http://Grizle'),
                    event_signals=[EventSignal(signal_id='duration',
                                             signal_type='level',
                                             signal_name='simple',
                                             intervals=[{'dtstart':datetime.now(),
                                                                'duration':timedelta(seconds=10),
                                                                'signal_payload':duration}]),
                                EventSignal(signal_id=name,
                                             signal_type='level',
                                             signal_name='simple',
                                             intervals=[{'dtstart':datetime.now(),
                                                                'duration':timedelta(seconds=10),
                                                                'signal_payload':amount}])],
# need to change VEN to the right client
                    targets=[Target(ven_id='ABB')])
    server.add_raw_event(ven_id='ABB', event=event)


#=============================================
#   Converts from string to int
#=============================================
def State_convert(ID, State): # converts state to int value for the event

    #State =State.replace("'","")

    if ID == "MX_THIRTY":
        if State == 'ON':
            #print("state = ON(1)")
            State = 1
        else:
            #print("State = OFF(0)")
            State = 0
    else:
        if State == 'ON':
            #print("state = ON(1)")
            State = 1
        elif State == 'Standby':
            #print("State = Standby(2)")
            State = 2
        else:
            #print("State = OFF(0)")
            State = 0

    return State

    #---------------------------------------------------------------------------------------------------------------------
    # controls the powersupplies by checking the reference table and if there is a change send that change to the client
    #---------------------------------------------------------------------------------------------------------------------

def reference_check(name): # Runs as seperate thread

    TIME.sleep(.3)
    with Lock: # get the base value to compare 
        mySQL.sql_connect()
        oldRegtime = mySQL.get_from_table(Table="reference", ID="Regatron", Column='time') # get the time values from the reference table in order to check for later updates
        oldMXtime = mySQL.get_from_table(Table="reference", ID="MX_THIRTY", Column='time')
        oldNHR_1_time = mySQL.get_from_table(Table="reference", ID="NHR_ONE", Column='time')
        oldNHR_2_time = mySQL.get_from_table(Table="reference", ID="NHR_TWO", Column='time')
        oldNHR_3_time = mySQL.get_from_table(Table="reference", ID="NHR_THREE", Column='time')
        oldGKtime = mySQL.get_from_table(Table="reference", ID="GK", Column='time')

        ID = "Fronius_SEVEN_SIX"
        oldFronius_76_Power_Limit = mySQL.get_from_table(Table="externalreference", ID=ID, Column='Power_Limit') # Power Limit

        ID = "Fronius_TWENTY"
        oldFronius_20_Power_Limit = mySQL.get_from_table(Table="externalreference", ID=ID, Column='Power_Limit') # Power Limit

        ID = "SMA_FIFTY"
        oldSMA_50_Power_Limit = mySQL.get_from_table(Table="externalreference", ID=ID, Column='Power_Limit')    # Power Limit

        ID = "SMA_SEVEN"
        oldSMA_7_Power_Limit = mySQL.get_from_table(Table="externalreference", ID=ID, Column='Power_Limit')     # Power Limit

        ID = "Yaskawa"
        oldYaskawa_Power_Limit = mySQL.get_from_table(Table="externalreference", ID=ID, Column='Power_Limit')   # Power Limit

        ID = "Grizl"
        GrizlStatus = mySQL.get_from_table(Table="reference", ID=ID, Column='Mode_state') # Status from Mario
        oldabbeastID =  None
        oldabbwestID =  None
        oldgrizlID =    None


        mySQL.Close()

    while True:
        TIME.sleep(.2) # give the system time for the other threads or it runs really slow
        with Lock:
            mySQL.sql_connect()    

            ############################################################################################
            ########################## REGATRON ########################################################   
                 
            newRegtime = mySQL.get_from_table(Table="reference", ID="Regatron", Column='time')  # constant check for a different time value, aka an update

            try:
                if(oldRegtime != newRegtime): #if the time has changed in the reference table, than an update has been sent
                    print("regatron is updating")
                    ID = "Regatron"
                    regState = mySQL.get_from_table(Table="reference", ID=ID, Column='Mode_State')  # State
                    regVref = mySQL.get_from_table(Table="reference", ID=ID, Column='Voltage_AC')   # Voltage reference
                    regCref = mySQL.get_from_table(Table="reference", ID=ID, Column='Current')      # Current reference
                    regPref = mySQL.get_from_table(Table="reference", ID=ID, Column='Power')        # Power reference
                    regIRes = mySQL.get_from_table(Table="reference", ID=ID, Column='Internal_Resistance')  # internal_resistance
                    regOV = mySQL.get_from_table(Table="reference", ID=ID, Column='Voltage_DC')     # over_voltage
                    regOC = mySQL.get_from_table(Table="reference", ID=ID, Column='Over_Current')   # over_current
                    regState = State_convert(ID, regState)

                    if (regState != None and regVref != None and regCref != None and regPref != None and regIRes != None and regOV != None and regOC != None): # check we have valid arguments
                         update_regatron(regVref, regCref, regPref, regIRes, regOV, regOC, regState)
                         print("updating ", ID)
                    else:
                         print("\n There is an invalid value in reference table")

                    oldRegtime = newRegtime #update the old time variable to be ready for the next check

            except :
                    oldRegtime = newRegtime

            ##############################################################################################
            ########################### MX30 #############################################################

            newMXtime = mySQL.get_from_table(Table="reference", ID="MX_THIRTY", Column='time')   # constant check for a different time value, aka an update

            try :
                if(oldMXtime != newMXtime): #if the time has changed in the reference table, than an update has been sent
                    ID = "MX_THIRTY"
                    State = mySQL.get_from_table(Table="reference", ID=ID, Column='Mode_State')   # State
                    Vac = mySQL.get_from_table(Table="reference", ID=ID, Column='Voltage_AC')     # Voltage AC
                    Vdc = mySQL.get_from_table(Table="reference", ID=ID, Column='Voltage_DC')     # Votage DC 
                    Current = mySQL.get_from_table(Table="reference", ID=ID, Column='Current')    # Current
                    Mode = mySQL.get_from_table(Table="reference", ID=ID, Column='Range_Type')    # Mode 0 = DC , 1 = AC
                    MXfreq = mySQL.get_from_table(Table="reference", ID=ID, Column='Internal_Resistance')   # frequency maybe add to internal resistance
                    MXVR = mySQL.get_from_table(Table="reference", ID=ID, Column='Over_Current')  # Voltage range
                    MXOV = mySQL.get_from_table(Table="reference", ID=ID, Column='BDV_Minimum')   # user BDV_Minimum for OV
                    Reset = mySQL.get_from_table(Table="reference", ID=ID, Column='Reset')        #Reset
                    slewV = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_slewVolt') # MX_slewVolt
                    shape = mySQL.get_from_table(Table="reference", ID=ID, Column='MX_shape')     # Waveform
                    clipL = mySQL.get_from_table(Table="reference", ID=ID, Column='MX_cliplevel') # Waveform clip level
                    Ores = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_slewRes')   # Output resistance
                    Oimp = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_slewPower') # Output Impedance
                    DCoffset = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_slewCurr') # dc offset
                    alc = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_mode')       # Voltage alc
                    cc = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_enable')      # CC mode
                    delay = mySQL.get_from_table(Table="reference", ID=ID, Column='Power')        # CC Delay
                    State = State_convert(ID, State)

                    #check for non-null values
                    if(State != None and Vac != None and Current != None and Vdc != None and Mode != None and MXfreq != None and MXVR != None and MXOV != None  and int(Reset) != None and slewV != None and shape != None  and clipL != None and Ores != None and Oimp != None  and DCoffset != None and alc != None and cc != None and delay != None):
                        update_mxCom(Current, Mode, State, Vac, Vdc, MXfreq, MXVR, MXOV, slewV, shape, clipL, Ores, Oimp, DCoffset, alc, cc, delay, Reset)
                        print("updating ", ID)

                    oldMXtime = newMXtime # update the old time to be ready for the next update

            except:
                    oldMXtime = newMXtime

            ######################################################################################################
            ########################### NHR ONE ##################################################################

            newNHR1time = mySQL.get_from_table(Table="reference", ID="NHR_ONE", Column='time')           # the last time apply has been pressed

            try:
                if(oldNHR_1_time != newNHR1time): #  constant check for a different time value, aka an update
                    ID = "NHR_ONE" 
                    State = mySQL.get_from_table(Table="reference", ID=ID, Column='Mode_State')     # State
                    Range = mySQL.get_from_table(Table="reference", ID=ID, Column='Range_Type')     # range
                    BDV = mySQL.get_from_table(Table="reference", ID=ID, Column='BDV_Minimum')      # BDV
                    mode = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_mode')        # mode
                    enable = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_enable')    # enable
                    voltage = mySQL.get_from_table(Table="reference", ID=ID, Column='Voltage_AC')   # voltage
                    current = mySQL.get_from_table(Table="reference", ID=ID, Column='Current')      # current
                    power = mySQL.get_from_table(Table="reference", ID=ID, Column='Power')          # power
                    resistance = mySQL.get_from_table(Table="reference", ID=ID, Column='Internal_Resistance')  # resistance
                    OC = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_safety')        # Over_Current
                    slewV = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_slewVolt')   # NHR_slewVolt
                    slewC = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_slewCurr')   # NHR_slewCurr
                    slewP = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_slewPower')  # NHR_slewPower
                    slewR = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_slewRes')    # NHR_slewRes
                    Rgain = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_Rgain')      # NHR_Rgain
                    Reset = mySQL.get_from_table(Table="reference", ID=ID, Column='Reset')          #Reset
                    parenable = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_parallel') # parallel enable
                    aux = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_slaveunits')   # auxilaries
                    State = State_convert(ID, State)

                    #check for null values
                    if(State != None and Range != None and BDV != None and mode != None and enable != None and voltage != None and current != None and power != None and resistance != None and OC != None and slewV != None and slewC != None and slewP != None and slewR != None and Rgain != None and Reset != None and parenable != None and aux != None):
                        update_nhr(Range, BDV, int(State), mode, enable, voltage, current, power, resistance, OC, slewV, slewC, slewP, slewR, Rgain, parenable,aux, Reset)
                        print("updating ", ID) 

                    oldNHR_1_time = newNHR1time # get the old time variable ready for the next update

            except:
                    oldNHR_1_time = newNHR1time

            ######################################################################################################################
            ####################### NHR TWO ######################################################################################

            newNHR2time = mySQL.get_from_table(Table="reference", ID="NHR_TWO", Column='time')           # the last time apply has been pressed

            try:
                if(oldNHR_2_time != newNHR2time): # if the time has changed, an update has been sent
                    ID = "NHR_TWO"
                    State = mySQL.get_from_table(Table="reference", ID=ID, Column='Mode_State')     # State
                    Range = mySQL.get_from_table(Table="reference", ID=ID, Column='Range_Type')     # range
                    BDV = mySQL.get_from_table(Table="reference", ID=ID, Column='BDV_Minimum')      # BDV
                    mode = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_mode')        # mode
                    enable = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_enable')    # enable
                    voltage = mySQL.get_from_table(Table="reference", ID=ID, Column='Voltage_AC')   # voltage
                    current = mySQL.get_from_table(Table="reference", ID=ID, Column='Current')      # current
                    power = mySQL.get_from_table(Table="reference", ID=ID, Column='Power')          # power
                    resistance = mySQL.get_from_table(Table="reference", ID=ID, Column='Internal_Resistance')  # resistance
                    OC = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_safety')        # Over_Current
                    slewV = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_slewVolt')   # NHR_slewVolt
                    slewC = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_slewCurr')   # NHR_slewCurr
                    slewP = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_slewPower')  # NHR_slewPower
                    slewR = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_slewRes')    # NHR_slewRes
                    Rgain = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_Rgain')      # NHR_Rgain
                    Reset = mySQL.get_from_table(Table="reference", ID=ID, Column='Reset')          # Reset
                    parenable = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_parallel') # parallel enable
                    aux = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_slaveunits')   # auxilaries
                    State = State_convert(ID, State)

                    # check for null values in the table
                    if(State != None and Range != None and BDV != None and mode != None and enable != None and voltage != None and current != None and power != None and resistance != None and OC != None and slewV != None and slewC != None and slewP != None and slewR != None and Rgain != None and Reset != None and parenable != None and aux != None):
                        update_nhr_2(Range, BDV, int(State), mode, enable, voltage, current, power, resistance, OC, slewV, slewC, slewP, slewR, Rgain, parenable,aux, Reset)
                        print("updating ", ID)

                    oldNHR_2_time = newNHR2time # get the old time ready for the next update check

            except:
                    oldNHR_2_time = newNHR2time

            #############################################################################################################
            #################################### NHR THREE ##############################################################

            newNHR3time = mySQL.get_from_table(Table="reference", ID="NHR_THREE", Column='time')           # the last time apply has been pressed

            try:
                if(oldNHR_3_time != newNHR3time): # when the time value changes, an update is needed becasue an event has been sent
                    ID = "NHR_THREE"
                    State = mySQL.get_from_table(Table="reference", ID=ID, Column='Mode_State')     # State
                    Range = mySQL.get_from_table(Table="reference", ID=ID, Column='Range_Type')     # range
                    BDV = mySQL.get_from_table(Table="reference", ID=ID, Column='BDV_Minimum')      # BDV
                    mode = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_mode')        # mode
                    enable = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_enable')    # enable
                    voltage = mySQL.get_from_table(Table="reference", ID=ID, Column='Voltage_AC')   # voltage
                    current = mySQL.get_from_table(Table="reference", ID=ID, Column='Current')      # current
                    power = mySQL.get_from_table(Table="reference", ID=ID, Column='Power')          # power
                    resistance = mySQL.get_from_table(Table="reference", ID=ID, Column='Internal_Resistance')  # resistance
                    OC = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_safety')        # Over_Current
                    slewV = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_slewVolt')   # NHR_slewVolt
                    slewC = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_slewCurr')   # NHR_slewCurr
                    slewP = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_slewPower')  # NHR_slewPower
                    slewR = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_slewRes')    # NHR_slewRes
                    Rgain = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_Rgain')      # NHR_Rgain
                    Reset = mySQL.get_from_table(Table="reference", ID=ID, Column='Reset')          # Reset
                    parenable = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_parallel') # parallel enable
                    aux = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_slaveunits')   # auxilaries
                    State = State_convert(ID, State)

                    # check for null values
                    if(State != None and Range != None and BDV != None and mode != None and enable != None and voltage != None and current != None and power != None and resistance != None and OC != None and slewV != None and slewC != None and slewP != None and slewR != None and Rgain != None and Reset != None and parenable != None and aux != None):
                        update_nhr_3(Range, BDV, int(State), mode, enable, voltage, current, power, resistance, OC, slewV, slewC, slewP, slewR, Rgain, parenable,aux, Reset)
                        print("updating ", ID)   

                    oldNHR_3_time = newNHR3time # get the time value ready for the next update

            except:
                    oldNHR_3_time = newNHR3time

            ##########################################################################################################################
            ################################ GK ######################################################################################

            newGKtime = mySQL.get_from_table(Table="reference", ID="GK", Column='time')                   # the last time apply has been pressed

            try:
                if (oldGKtime != newGKtime): # if the time value has changed, an event has been sent
                    ID = "GK"
                    State = mySQL.get_from_table(Table="reference", ID=ID, Column='Mode_State')          # State
                    Voltage = mySQL.get_from_table(Table="reference", ID=ID, Column='Voltage_DC')        # Voltage
                    Source_Current = mySQL.get_from_table(Table="reference", ID=ID, Column='Current')    # Source Current
                    Sink_Current = mySQL.get_from_table(Table="reference", ID=ID, Column='Over_Current') # Sink Current
                    Source_Power = mySQL.get_from_table(Table="reference", ID=ID, Column='Power')        # Source Power
                    Sink_Power = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_slewPower')  # sink Power
                    Internal_Resistance = mySQL.get_from_table(Table="reference", ID=ID, Column='Internal_Resistance') # internal Resistance
                    Discharge_Mode = mySQL.get_from_table(Table="reference", ID=ID, Column='NHR_mode')   # Discharge Mode
                    Reset = mySQL.get_from_table(Table="reference", ID=ID, Column='Reset')                  # Reset

                    #check for null values
                    if(State != None and Voltage != None and Source_Current != None and Sink_Current != None and Source_Power != None and Sink_Power != None and Internal_Resistance != None and Discharge_Mode != None and Reset != None):
                        update_Gustav_Klein(State, Voltage, Source_Current, Sink_Current, Source_Power, Sink_Power, Internal_Resistance, Reset, Discharge_Mode)
                        print("updating ", ID)
                    oldGKtime = newGKtime

            except:
                    oldGKtime = newGKtime

            ###########################################################################################################################
            ############################## ABB EAST ###################################################################################

            try:
                    idabbeast = mySQL.get_active_event(Table="chargerscheduling", ID="ABB East", Column='id')
                    chargerstart_abbeast = mySQL.get_active_event(Table="chargerscheduling", ID="ABB East", Column='start')
                    chargerend_abbeast = mySQL.get_active_event(Table="chargerscheduling", ID="ABB East", Column='end')

                    # print("Charger start: ", chargerstart_abbeast)  # this is a timedelta variable
                    # print("End: ", chargerend_abbeast)  # this is also a time delta variable
                    now=datetime.now()  # this is a datetime variable
                    delta = timedelta(hours=now.hour, minutes=now.minute, seconds=now.second) #converting now to a time delta
                    # print("current time (delta): ", delta)
                    elapsed_start_abbeastt=delta-chargerstart_abbeast # current time - start should be positive to turn on
                    elapsed_end_abbeastt=delta-chargerend_abbeast  # current time - end Should be negative to turn on
                    # print(elapsed_start_abbeastt)
                    # print(elapsed_end_abbeastt)

                     # if conditions met above are correct, update reference table to turn on
                    #if(elapsed_start_abbeastt > timedelta(minutes=0) and elapsed_end_abbeastt < timedelta(minutes=0)):
                    if(chargerstart_abbeast != None and chargerend_abbeast != None and oldabbeastID != idabbeast):
                        mySQL.update_reference_charger("ABB_East", "ON")
                        chargerpower = mySQL.get_active_event(Table="chargerscheduling", ID="ABB East", Column='power')
                        start = chargerstart_abbeast.split(":")
                        end = chargerend_abbeast.split(":")

                        duration = ((end[0] *3600) + (end[1] * 60) + end[2]) - ((start[0] *3600) + (start[1] * 60) + start[2]) # duration in seconds
                        print(duration)
                        if(chargerpower != None):
                            update_ABB_East('ABB_East', duration, chargerpower)

                        # print("turning on") # turn mode_state on in reference
                    else:
                        mySQL.update_reference_charger("ABB_East", "OFF")

                        # print("turning off")    # turn mode_state off in reference
            except:
                    # if this fails it means there is no event
                    # print("no scheduled event, turning off")
                    mySQL.update_reference_charger("ABB_East", "OFF")

            ###########################################################################################################################
            ############################## ABB West ###################################################################################

            try:
                    idabbwest = mySQL.get_active_event(Table="chargerscheduling", ID="ABB West", Column='id')
                    chargerstart_abbwest = mySQL.get_active_event(Table="chargerscheduling", ID="ABB West", Column='start')
                    chargerend_abbwest = mySQL.get_active_event(Table="chargerscheduling", ID="ABB West", Column='end')
                    # print("Charger start: ", chargerstart_abbwest)  # this is a timedelta variable
                    # print("End: ", chargerend_abbwest)  # this is also a time delta variable
                    now=datetime.now()  # this is a datetime variable
                    delta = timedelta(hours=now.hour, minutes=now.minute, seconds=now.second) #converting now to a time delta
                    # print("current time (delta): ", delta)
                    elapsed_start_abbwestt=delta-chargerstart_abbwest # current time - start should be positive to turn on
                    elapsed_end_abbwestt=delta-chargerend_abbwest # current time - end should be negative to turn on
                    # print(elapsed_start_abbwestt)
                    # print(elapsed_end_abbwestt)

                    # if conditions are met, turn on the machine through the reference table
                    #if(elapsed_start_abbwestt > timedelta(minutes=0) and elapsed_end_abbwestt < timedelta(minutes=0)):
                    if(chargerstart_abbwest != None and chargerend_abbwest != None and oldabbwestID != idabbwest):
                        mySQL.update_reference_charger("ABB_West", "ON")

                        chargerpower = mySQL.get_from_schedule(Table="chargerscheduling", ID="ABB East", Column='power')
                        start = chargerstart_abbwest.split(":")
                        end = chargerend_abbwest.split(":")

                        duration = ((end[0] *3600) + (end[1] * 60) + end[2]) - ((start[0] *3600) + (start[1] * 60) + start[2]) # duration in seconds
                        print(duration)
                        if(chargerpower != None):
                            update_ABB_West('ABB_West', duration, chargerpower)

                        # print("turning on") # turn mode_state on in reference
                    else:
                        mySQL.update_reference_charger("ABB_West", "OFF")
                        # print("turning off") # turn mode_state off in reference
            except:
                    # if this fails it means there is no event
                    # print("no scheduled event, turning off")
                    mySQL.update_reference_charger("ABB_West", "OFF")

            ###########################################################################################################################
            ############################## GRIZL E ####################################################################################

            try:
                    idgrizl = mySQL.get_active_event(Table="chargerscheduling", ID="Grizl", Column='id')
                    chargerstart_grizl = mySQL.get_active_event(Table="chargerscheduling", ID="Grizel E", Column='start')
                    chargerend_grizl = mySQL.get_active_event(Table="chargerscheduling", ID="Grizel E", Column='end')
                    # print("Charger start: ", chargerstart_grizl)  # this is a timedelta variable
                    # print("End: ", chargerend_grizl)  # this is also a time delta variable
                    now=datetime.now()  # this is a datetime variable
                    delta = timedelta(hours=now.hour, minutes=now.minute, seconds=now.second) #converting now to a time delta
                    # print("current time (delta): ", delta)
                    elapsed_start_grizlt=delta-chargerstart_grizl # current time - start should be positive to turn on
                    elapsed_end_grizlt=delta-chargerend_grizl # current time - end should be negative to turn on
                    # print(elapsed_start_grizlt)
                    # print(elapsed_end_grizlt)

                    # if these conditions are met, turn on the machine
                    #if(elapsed_start_grizlt > timedelta(minutes=0) and elapsed_end_grizlt < timedelta(minutes=0)):
                    if(chargerstart_grizl != None and chargerend_grizl != None and oldgrizlID != idgrizl):
                        mySQL.update_reference_charger("Grizl", "ON")

                        chargerpower = mySQL.get_active_event(Table="chargerscheduling", ID="ABB East", Column='power')
                        start = chargerstart_abbwest.split(":")
                        end = chargerend_abbwest.split(":")

                        duration = ((end[0] *3600) + (end[1] * 60) + end[2]) - ((start[0] *3600) + (start[1] * 60) + start[2]) # duration in seconds
                        print(duration)
                        if(chargerpower != None):
                            update_Grizl('Grizl', duration, chargerpower)
                        # print("turning on") # turn mode_state on in reference
                    else:
                        mySQL.update_reference_charger("Grizl", "OFF")
                        # print("turning off") # turn mode_state off in reference
            except:
                    # if this fails it means there is no event
                    # print("no scheduled event, turning off")
                    mySQL.update_reference_charger("Grizl", "OFF")

            #===========================================================================================================================
            ############################################################################################################################
            #===========================================================================================================================
            ID = "Fronius_SEVEN_SIX"
            power_limit = mySQL.get_from_table(Table="externalreference", ID=ID, Column='Power_Limit')

            try:
                if(oldFronius_76_Power_Limit != power_limit):
                    print("Fronius 76 needs update")
                    if power_limit != None:
                        update_Fronius76(amount=power_limit)
                    oldFronius_76_Power_Limit = power_limit
            except:
                oldFronius_76_Power_Limit = power_limit

            ID = "Fronius_TWENTY"
            power_limit = mySQL.get_from_table(Table="externalreference", ID=ID, Column='Power_Limit')

            try:
                if(oldFronius_20_Power_Limit != power_limit):
                    print("Fronius 20 needs update")
                    if power_limit != None:
                        update_Fronius20(amount=power_limit)
                    oldFronius_20_Power_Limit = power_limit
            except:
                oldFronius_20_Power_Limit = power_limit

            ID = "SMA_FIFTY"
            power_limit = mySQL.get_from_table(Table="externalreference", ID=ID, Column='Power_Limit')

            try:
                if(oldSMA_50_Power_Limit != power_limit):
                    print("SMA 50 needs update")
                    if power_limit != None:
                        update_SMA50(amount=power_limit)
                    oldSMA_50_Power_Limit = power_limit
            except:
                oldSMA_50_Power_Limit = power_limit

            ID = "SMA_SEVEN"
            power_limit = mySQL.get_from_table(Table="externalreference", ID=ID, Column='Power_Limit')

            try:
                if(oldSMA_7_Power_Limit != power_limit):
                    print("SMA 7 needs update")
                    if power_limit != None:
                        update_SMA7(amount=power_limit)
                    oldSMA_7_Power_Limit = power_limit
            except:
                oldSMA_7_Power_Limit = power_limit

            ID ='Grizl'
            State = mySQL.get_from_table(Table="reference", ID=ID, Column='Mode_State')
            # print("WE HAVE GOTTEN TO CHECK THE STATE" + str(State))
            # print(State)
            if (State == "'ON'"):
                # print("Got to update Grizl")
                update_Grizl('start')
                # mySQL.update_reference(ID=ID, State='READY')
            elif (State == "'OFF'"):
                update_Grizl('stop')


            mySQL.Close()

#================================================
#   Allows user to control database using server
#================================================
def manage_sql():
    TIME.sleep(.2)
    print("Welcome to SQL Management\n\nAvaliable commands: 'update', 'read', 'delete', 'add'\nEnter 'help' for more information.\n")
    exit = False
    while(not exit):
        TIME.sleep(.1)
        try:
            with Lock:
                mySQL.sql_connect() # connect to sql
                commands = input("\nEnter a command: ")
                command = commands.split(" ")
                match command[0]:
                        case 'read': # read from the sql table, either all the tables, or data from a specific table
                            try:
                                match command[1]: #if the user types read, followed by something else, allow the display of other tables too
                                    case 'all':
                                        mySQL.show_tables()
                                    case 'battery':
                                        try:
                                            try:
                                                mySQL.read_table('battery', command[2], command[3]) #if there is a 4th command, read a single value
                                            except Exception as e:
                                                mySQL.read_table('battery', command[2], '') # if there is a 3rd command entered read value
                                        except Exception as e:
                                            mySQL.read_table('battery', '', '') #else, just put the whole table
                                    case 'chargerscheduling' | 'charger':
                                        try:
                                            try:
                                                mySQL.read_table('chargerscheduling', command[2], command[3])
                                            except Exception as e:
                                                mySQL.read_table('chargerscheduling', command[2], '')
                                        except Exception as e:
                                            mySQL.read_table('chargerscheduling', '', '')
                                    case 'equipment':
                                        try:
                                            try:
                                                mySQL.read_table('equipment', command[2], command[3])
                                            except Exception as e:
                                                mySQL.read_table('equipment', command[2], '')
                                        except Exception as e:
                                            mySQL.read_table('equipment', '', '')
                                    case 'events':
                                        try:
                                            try:
                                                mySQL.read_table('events', command[2], command[3])
                                            except Exception as e:
                                                mySQL.read_table('events', command[2], '')
                                        except Exception as e:
                                            mySQL.read_table('events', '', '')
                                    case 'externalreference' | 'external':
                                        try:
                                            try:
                                                mySQL.read_table('externalreference', command[2], command[3])
                                            except Exception as e:
                                                mySQL.read_table('externalreference', command[2], '')
                                        except Exception as e:
                                            mySQL.read_table('externalreference', '', '')
                                    case 'pwdReset' | 'pwdreset':
                                        try:
                                            try:
                                                mySQL.read_table('pwdReset', command[2], command[3])
                                            except Exception as e:
                                                mySQL.read_table('pwdReset', command[2], '')
                                        except Exception as e:
                                            mySQL.read_table('pwdReset', '', '')
                                    case 'reference':
                                        try:
                                            try:
                                                mySQL.read_table('reference', command[2], command[3])
                                            except Exception as e:
                                                mySQL.read_table('reference', command[2], '')
                                        except Exception as e:
                                            mySQL.read_table('reference', '', '')
                                    case 'scheduling':
                                        try:
                                            try:
                                                mySQL.read_table('scheduling', command[2], command[3])
                                            except Exception as e:
                                                mySQL.read_table('scheduling', command[2], '')
                                        except Exception as e:
                                            mySQL.read_table('scheduling', '', '')
                                    case 'users':
                                        try:
                                            try:
                                                mySQL.read_table('users', command[2], command[3])
                                            except Exception as e:
                                                mySQL.read_table('users', command[2], '')
                                        except Exception as e:
                                            mySQL.read_table('users', '', '')
                                    case default:
                                        print("\n'", command[1], "' is not a valid table.  Please try again.\nType 'read all' to view all tables, or 'help read' for more information.\n")
                            except Exception as e: #if there is no second command entered, the user wants to see all the tables
                                mySQL.show_tables()
                        case 'delete': # delete an entry from a specified table
                            try:
                                match command[1]: # specifies which table we want to delete an entry from
                                    case 'battery':
                                        try:
                                            temp = mySQL.get_from_table('battery', command[2], 'ID') # test to make sure the row exists in the table
                                            if temp == command[2]:
                                                mySQL.delete_entry('battery', command[2])  # if it exists delete it
                                            else:
                                                print("\n'", command[2], "' is not a valid ID.  Please try again.\nType 'read battery' to view all available IDs")                                
                                        except Exception as e:
                                            print("\nPlease enter the ID of the row you want to delete after 'battery'.\nType 'read battery' to view all available IDs")
                                    case 'chargerscheduling' | 'charger':
                                        try:
                                            temp = mySQL.get_from_table('chargerscheduling', command[2], 'id') # test to make sure the row exists in the table
                                            print(temp)
                                            if temp == int(command[2]):
                                                mySQL.delete_entry('chargerscheduling', command[2]) # if it exists delete it
                                            else:
                                                print("\n'", command[2], "' is not a valid ID.  Please try again.\nType 'read chargerscheduling' to view all available IDs")                                
                                        except Exception as e:
                                            print("\nPlease enter the ID of the row you want to delete after 'chargerscheduling'.\nType 'read chargerscheduling' to view all available IDs")
                                    case 'equipment':
                                        try:
                                            temp = mySQL.get_from_table('equipment', command[2], 'ID') # test to make sure the row exists in the table
                                            print(temp)
                                            if temp == command[2]:
                                                mySQL.delete_entry('equipment', command[2]) # if it exists delete it
                                            else:
                                                print("\n'", command[2], "' is not a valid ID.  Please try again.\nType 'read equipment' to view all available IDs")                                
                                        except Exception as e:
                                            print("\nPlease enter the ID of the row you want to delete after 'equipment'.\nType 'read equipment' to view all available IDs")
                                    case 'events':
                                        try:
                                            temp = mySQL.get_from_table('events', command[2], 'ID') # test to make sure the row exists in the table
                                            print(temp)
                                            if temp == int(command[2]):
                                                mySQL.delete_entry('events', command[2]) # if it exists delete it
                                            else:
                                                print("\n'", command[2], "' is not a valid ID.  Please try again.\nType 'read events' to view all available IDs")                                
                                        except Exception as e:
                                            print("\nPlease enter the ID of the row you want to delete after 'events'.\nType 'read events' to view all available IDs")    
                                    case 'externalreference' | 'external':
                                        try:
                                            temp = mySQL.get_from_table('externalreference', command[2], 'ID') # test to make sure the row exists in the table
                                            print(temp)
                                            if temp == command[2]:
                                                mySQL.delete_entry('externalreference', command[2]) # if it exists delete it
                                            else:
                                                print("\n'", command[2], "' is not a valid ID.  Please try again.\nType 'read externalreference' to view all available IDs")                                
                                        except Exception as e:
                                            print("\nPlease enter the ID of the row you want to delete after 'externalreference'.\nType 'read externalreference' to view all available IDs")
                                    case 'pwdReset' | 'pwdreset':
                                        try:
                                            temp = mySQL.get_from_table('pwdReset', command[2], 'id') # test to make sure the row exists in the table
                                            print(temp)
                                            if temp == int(command[2]):
                                                mySQL.delete_entry('pwdReset', command[2]) # if it exists delete it
                                            else:
                                                print("\n'", command[2], "' is not a valid ID.  Please try again.\nType 'read pwdReset' to view all available IDs")                                
                                        except Exception as e:
                                            print("\nPlease enter the ID of the row you want to delete after 'pwdReset'.\nType 'read pwdReset' to view all available IDs")
                                    case 'reference':
                                        try:
                                            temp = mySQL.get_from_table('reference', command[2], 'ID') # test to make sure the row exists in the table
                                            print(temp)
                                            if temp == command[2]:
                                                mySQL.delete_entry('reference', command[2]) # if it exists delete it
                                            else:
                                                print("\n'", command[2], "' is not a valid ID.  Please try again.\nType 'read reference' to view all available IDs")                                
                                        except Exception as e:
                                            print("\nPlease enter the ID of the row you want to delete after 'reference'.\nType 'read reference' to view all available IDs")
                                    case 'scheduling':
                                        try:
                                            temp = mySQL.get_from_table('scheduling', command[2], 'id') # test to make sure the row exists in the table
                                            print(temp)
                                            if temp == int(command[2]):
                                                mySQL.delete_entry('scheduling', command[2]) # if it exists delete it
                                            else:
                                                print("\n'", command[2], "' is not a valid ID.  Please try again.\nType 'read scheduling' to view all available IDs")                                
                                        except Exception as e:
                                            print("\nPlease enter the ID of the row you want to delete after 'scheduling'.\nType 'read scheduling' to view all available IDs")
                                    case 'users':
                                        try:
                                            temp = mySQL.get_from_table('users', command[2], 'id') # test to make sure the row exists in the table
                                            print(temp)
                                            if temp == int(command[2]):
                                                mySQL.delete_entry('users', command[2]) # if it exists delete it
                                            else:
                                                print("\n'", command[2], "' is not a valid ID.  Please try again.\nType 'read users' to view all available IDs")                                
                                        except Exception as e:
                                            print("\nPlease enter the ID of the row you want to delete after 'users'.\nType 'read users' to view all available IDs")
                                    case default:
                                        print("\n'", command[1], "' is not a valid table.  Please try again.\nType 'read all' to view all tables")                                        
                            except Exception as e:
                                print("\nPlease specify the name of a table after 'delete'.\nType 'read all' to view all available tables.")
                        case 'add': # not currently implemeted
                            print("\nPlease add to the SQL table through the ASPIRE website, or directly through the SQL table.\n")
                        case 'update': # lets the user update tables in sql
                            try:
                                match command[1]: 
                                    case 'equipment':
                                        try:
                                            match command[2]:
                                                case 'NHR_ONE' | 'nhr1' | 'nhr_one':
                                                    print("The current IP address for the NHR_ONE is: ")
                                                    print(mySQL.get_from_table('equipment', 'NHR_ONE', 'IP'))
                                                    newip = input("Enter the new IP address.  Type 'c' to cancel: ")
                                                    if newip != 'c':
                                                        mySQL.update_equipment(ID='NHR_ONE', IP=newip)
                                                        print("IP Address updated to: ", newip, "\n")
                                                    else:
                                                        print("Update canceled.\n") 
                                                case 'NHR_TWO' | 'nhr2' | 'nhr_two':
                                                    print("The current IP address for the NHR_TWO is: ")
                                                    print(mySQL.get_from_table('equipment', 'NHR_TWO', 'IP'))
                                                    newip = input("Enter the new IP address.  Type 'c' to cancel: ")
                                                    if newip != 'c':
                                                        mySQL.update_equipment(ID='NHR_TWO', IP=newip)
                                                        print("IP Address updated to: ", newip, "\n")
                                                    else:
                                                        print("Update canceled.\n")
                                                case 'NHR_THREE' | 'nhr3' | 'nhr_three':
                                                    print("The current IP address for the NHR_THREE is: ")
                                                    print(mySQL.get_from_table('equipment', 'NHR_THREE', 'IP'))
                                                    newip = input("Enter the new IP address.  Type 'c' to cancel: ")
                                                    if newip != 'c':
                                                        mySQL.update_equipment(ID='NHR_THREE', IP=newip)
                                                        print("IP Address updated to: ", newip, "\n")
                                                    else:
                                                        print("Update canceled.\n")
                                                case 'Grizl' | 'grizl':
                                                    print("The current IP address for the Grizl is: ")
                                                    print(mySQL.get_from_table('equipment', 'Grizl', 'IP'))
                                                    newip = input("Enter the new IP address.  Type 'c' to cancel: ")
                                                    if newip != 'c':
                                                        mySQL.update_equipment(ID='Grizl', IP=newip)
                                                        print("IP Address updated to: ", newip, "\n")
                                                    else:
                                                        print("Update canceled.\n")
                                                case 'Dynapower' | 'dynapower':
                                                    print("The current IP address for the Dynapower is: ")
                                                    print(mySQL.get_from_table('equipment', 'Dynapower', 'IP'))
                                                    newip = input("Enter the new IP address.  Type 'c' to cancel: ")
                                                    if newip != 'c':
                                                        mySQL.update_equipment(ID='Dynapower', IP=newip)
                                                        print("IP Address updated to: ", newip, "\n")
                                                    else:
                                                        print("Update canceled.\n")
                                                case 'SMA_SEVEN' | 'sma7' | 'smaseven' | 'SMA7' | 'SMASEVEN':
                                                    print("The current IP address for the SMA_SEVEN is: ")
                                                    print(mySQL.get_from_table('equipment', 'SMA_SEVEN', 'IP'))
                                                    newip = input("Enter the new IP address.  Type 'c' to cancel: ")
                                                    if newip != 'c':
                                                        mySQL.update_equipment(ID='SMA_SEVEN', IP=newip)
                                                        print("IP Address updated to: ", newip, "\n")
                                                    else:
                                                        print("Update canceled.\n")
                                                case 'Yaskawa' | 'yaskawa':
                                                    print("The current IP address for the Yaskawa is: ")
                                                    print(mySQL.get_from_table('equipment', 'Yaskawa', 'IP'))
                                                    newip = input("Enter the new IP address.  Type 'c' to cancel: ")
                                                    if newip != 'c':
                                                        mySQL.update_equipment(ID='Yaskawa', IP=newip)
                                                        print("IP Address updated to: ", newip, "\n")
                                                    else:
                                                        print("Update canceled.\n")
                                                case 'MX_THIRTY' | 'mx30' | 'mxthirty' | 'mx_thirty':
                                                    print("The current IP address for the MX_THIRTY is: ")
                                                    print(mySQL.get_from_table('equipment', 'MX_THIRTY', 'IP'))
                                                    newip = input("Enter the new IP address.  Type 'c' to cancel: ")
                                                    if newip != 'c':
                                                        mySQL.update_equipment(ID='MX_THIRTY', IP=newip)
                                                        print("IP Address updated to: ", newip, "\n")
                                                    else:
                                                        print("Update canceled.\n")
                                                case 'Regatron' | 'regatron':
                                                    print("The current IP address for the Regatron is: ")
                                                    print(mySQL.get_from_table('equipment', 'Regatron', 'IP'))
                                                    newip = input("Enter the new IP address.  Type 'c' to cancel: ")
                                                    if newip != 'c':
                                                        mySQL.update_equipment(ID='Regatron', IP=newip)
                                                        print("IP Address updated to: ", newip, "\n")
                                                    else:
                                                        print("Update canceled.\n")
                                                case 'Logix_Blue' | 'logix' | 'logixblue' | 'logix_blue' | 'Logix':
                                                    print("The current IP address for the Logix_Blue is: ")
                                                    print(mySQL.get_from_table('equipment', 'Logix_Blue', 'IP'))
                                                    newip = input("Enter the new IP address.  Type 'c' to cancel: ")
                                                    if newip != 'c':
                                                        mySQL.update_equipment(ID='Logix_Blue', IP=newip)
                                                        print("IP Address updated to: ", newip, "\n")
                                                    else:
                                                        print("Update canceled.\n")
                                                case 'SMA_FIFTY' | 'sma50' | 'smafifty' | 'SMA50' | 'SMAFIFTY':
                                                    print("The current IP address for the Yaskawa is: ")
                                                    print(mySQL.get_from_table('equipment', 'Yaskawa', 'IP'))
                                                    newip = input("Enter the new IP address.  Type 'c' to cancel: ")
                                                    if newip != 'c':
                                                        mySQL.update_equipment(ID='Yaskawa', IP=newip)
                                                        print("IP Address updated to: ", newip, "\n")
                                                    else:
                                                        print("Update canceled.\n")
                                                case 'GK' | 'gk':
                                                    print("The current IP address for the GK is: ")
                                                    print(mySQL.get_from_table('equipment', 'GK', 'IP'))
                                                    newip = input("Enter the new IP address.  Type 'c' to cancel: ")
                                                    if newip != 'c':
                                                        mySQL.update_equipment(ID='GK', IP=newip)
                                                        print("IP Address updated to: ", newip, "\n")
                                                    else:
                                                        print("Update canceled.\n")
                                                case 'Fronius_TWENTY' | 'Fronius20' | 'Fronius_20' | 'FroniusTwenty':
                                                    print("The current IP address for the Fronius_TWENTY is: ")
                                                    print(mySQL.get_from_table('equipment', 'Fronius_TWENTY', 'IP'))
                                                    newip = input("Enter the new IP address.  Type 'c' to cancel: ")
                                                    if newip != 'c':
                                                        mySQL.update_equipment(ID='Fronius_TWENTY', IP=newip)
                                                        print("IP Address updated to: ", newip, "\n")
                                                    else:
                                                        print("Update canceled.\n")
                                                case 'Fronius_SEVEN_SIX' | 'Fronius76' | 'Fronius_76' | 'FroniusSevenSix':
                                                    print("The current IP address for the Fronius_SEVEN_SIX is: ")
                                                    print(mySQL.get_from_table('equipment', 'Fronius_SEVEN_SIX', 'IP'))
                                                    newip = input("Enter the new IP address.  Type 'c' to cancel: ")
                                                    if newip != 'c':
                                                        mySQL.update_equipment(ID='Fronius_SEVEN_SIX', IP=newip)
                                                        print("IP Address updated to: ", newip, "\n")
                                                    else:
                                                        print("Update canceled.\n")
                                                case 'Leviton' | 'leviton':
                                                    print("The current IP address for the Leviton is: ")
                                                    print(mySQL.get_from_table('equipment', 'Leviton', 'IP'))
                                                    newip = input("Enter the new IP address.  Type 'c' to cancel: ")
                                                    if newip != 'c':
                                                        mySQL.update_equipment(ID='Leviton', IP=newip)
                                                        print("IP Address updated to: ", newip, "\n")
                                                    else:
                                                        print("Update canceled.\n")
                                                case default:
                                                    print("\n'", command[2], "' is not a valid equipment ID.  Please try again.\nType 'read equipment' to view all available IDs, or type 'help update' for all options.")
                                        except Exception as e: # if there is no 3rd command entered
                                            print("\nPlease specify the ID after 'equipment'.\nType 'read equipment' to view all available IDs, or type 'help update' for all options.")
                                    case 'reference':
                                        try:
                                            match command[2]:
                                                case 'NHR_ONE' | 'nhr' | 'nhr1' | 'nhr_one':
                                                    try:
                                                        mySQL.Close()
                                                        call_update_reference('NHR_ONE', command[3])
                                                    except Exception as e:
                                                        print("Incorrect number of parameters!\nFormat: update reference NHR_ONE 'column'")
                                                case 'NHR_TWO' | 'nhr2' | 'nhr_two':
                                                    try:
                                                        mySQL.Close()
                                                        call_update_reference('NHR_TWO', command[3])
                                                    except Exception as e:
                                                        print("Incorrect number of parameters!\nFormat: update reference NHR_TWO 'column'")
                                                case 'NHR_THREE' | 'nhr3' | 'nhr_three':
                                                    try:
                                                        mySQL.Close()
                                                        call_update_reference('NHR_THREE', command[3])
                                                    except Exception as e:
                                                        print("Incorrect number of parameters!\nFormat: update reference NHR_THREE 'column'")
                                                case 'Regatron' | 'regatron':
                                                    try:
                                                        mySQL.Close()
                                                        call_update_reference('Regatron', command[3])
                                                    except Exception as e:
                                                        print("Incorrect number of parameters!\nFormat: update reference Regatron 'column'")
                                                case 'MX_THIRTY' | 'mx30' | 'mxthirty' | 'mx_thirty':
                                                    try:
                                                        mySQL.Close()
                                                        call_update_reference('MX_THIRTY', command[3])
                                                    except Exception as e:
                                                        print("Incorrect number of parameters!\nFormat: update reference MX_THIRTY 'column'")
                                                case 'Grizl' | 'grizl':
                                                    try:
                                                        mySQL.Close()
                                                        call_update_reference('Grizl', command[3])
                                                    except Exception as e:
                                                        print("Incorrect number of parameters!\nFormat: update reference Grizl 'column'")
                                                case 'GK' | 'gk':
                                                    try:
                                                        mySQL.Close()
                                                        call_update_reference('GK', command[3])
                                                    except Exception as e:
                                                        print("Incorrect number of parameters!\nFormat: update reference GK 'column'")
                                                case 'ABB_East' | 'abbeast':
                                                    try:
                                                        mySQL.Close()
                                                        call_update_reference('ABB_East', command[3])
                                                    except Exception as e:
                                                        print("Incorrect number of parameters!\nFormat: update reference ABB_East 'column'")
                                                case 'ABB_West' | 'abbwest':
                                                    try:
                                                        mySQL.Close()
                                                        call_update_reference('ABB_West', command[3])
                                                    except Exception as e:
                                                        print("Incorrect number of parameters!\nFormat: update reference ABB_West 'column'")
                                                case default:
                                                    print("\n'", command[2], "' is not a valid equipment ID.  Please try again.\nType 'read equipment' to view all available IDs, or type 'help update' for more information\nFormat: update reference 'ID' 'column' 'value'")
                                        except Exception as e:
                                            print("\nPlease specify the ID after 'equipment'.\nType 'read equipment' to view all available IDs, or type 'help update' for all options.\nFormat: update reference 'id'' 'column' 'value'")
                                    case default:
                                        print("\n'", command[1], "' is not a valid table.  Valid tables are 'equipment' and 'reference'.  Type 'help update' for all options.\nFormat: update 'table' 'id' 'column' 'value'")
                            except Exception as e: #if there is no second command entered, the user wants to see all the tables
                                print("\nPlease specify the name of a table after 'update'.\nOnly some tables are avaliable to be changed, or type 'help update' for all options.\nFormat: update 'table' 'id' 'column' 'value'")
                        case 'help':
                            try:
                                match command[1]:
                                    case 'read':
                                        print("\n------------ Help Read -----------\nType 'read all' to view all tables.\nType 'read' followed by one of the following options to view data from a specific table:")
                                        print("'battery', 'chargerscheduling', 'equipment', 'events', 'externalreference', 'pwdReset', 'reference', 'scheduling', 'users'")
                                        print("You can also specify the information from a certain row of the table by adding a third parameter.\n")
                                        print("Format: read <table> <id> \n")
                                    case 'delete':
                                        print("\n----------- Help Delete -----------\nType 'delete' followed by the specified table, and the ID number of the row to delete.")
                                        print("To find the ID number of the row you want to delete, use the 'read' command.\n")
                                        print("Format: delete <table> <id>\n")
                                    case 'update':
                                        print("\n----------- Help Update -----------\n'update' allows you to change the SQL values for a piece of equipment.\nType 'update' followed by the specified table, and the machine ID to update.")
                                        print("To find the ID of the row and column you want to change, use the 'read' command.")
                                        print("Only certain tables are available to be updated, currently they are: 'equipment', 'reference'\n")
                                        print("Format: update <table> <id> <column>\n")
                                        print("To be safe, type in the names of tables, equipment, and column parameters exactly as they appear in SQL.")
                                        print("Some shorthand is available, for example, 'NHR_ONE' can be entered as 'nhr1',\nand 'NHR_slewPower' can be entered as 'slewpower'")
                                    case 'add':
                                        print("adding to the sql database is not currently supported")
                            except Exception as e:
                                print("\n------------ Welcome to the Help Menu -----------\nType help, followed by one of the options below for more information on certain commands.")
                                print("'update', 'read', 'delete', 'add'\n")
                                print("General command format is as follows: <command> <table> <id> (column)\n")
                                print("command --> main commands, they are: 'update', 'read', 'delete', 'add'")
                                print("table --> specifies the table to pull from sql.  Type 'read' to see all tables")
                                print("id --> specifies the row in the selected table.  In phpmyadmin, it will be the 'ID' or 'id' column.\n\tType 'read <table>' to see id values for a specific table.")
                                print("column --> only used in the update function.  specifies the column to update its value")
                        case default:
                            print("\nInvalid command.  Available commands are 'read', 'delete', 'add', or 'update'\nType 'help' for more information.")
                mySQL.Close()
        except Exception as e:
            print("\nCommand error: ", e)

def call_update_reference(ID, parameter): # this function calls an update for a single value in the reference table
    try:                                        # written to avoid adding 500+ lines of code to the server
        mySQL.sql_connect()
        match parameter:
            case 'Mode_State' | 'modestate' | 'mode_state' | 'state':
                print("The current Mode_State for the ", ID, " is: ")
                print(mySQL.get_from_table('reference', ID, 'Mode_State'))
                newval = input("Enter the new value.  Type 'c' to cancel: ")
                if newval != 'c':
                    mySQL.update_reference(ID=ID, State=newval)
                    print("Mode_State updated to: ", newval, "\n")
                else:
                    print("Update canceled.\n")
            case 'Range_Type' | 'rangetype' | 'range_type' | 'range':
                print("The current Range_Type for the ", ID, " is: ")
                print(mySQL.get_from_table('reference', ID, 'Range_Type'))
                newval = input("Enter the new value.  Type 'c' to cancel: ")
                if newval != 'c':
                    mySQL.update_reference(ID=ID, Range=newval)
                    print("Range_Type updated to: ", newval, "\n")
                else:
                    print("Update canceled.\n")
            case 'BDV_Minimum' | 'bdv' | 'BDV' | 'bdv_minimum':
                print("The current BDV for the ", ID, " is: ")
                print(mySQL.get_from_table('reference', ID, 'BDV_Minimum'))
                newval = input("Enter the new value.  Type 'c' to cancel: ")
                if newval != 'c':
                    mySQL.update_reference(ID=ID, BDV=newval)
                    print("BDV updated to: ", newval, "\n")
                else:
                    print("Update canceled.\n")
            case 'Voltage_AC' | 'voltageac' | 'voltage_ac' | 'VoltageAC' | 'voltage':
                print("The current Voltage_AC for the ", ID, " is: ")
                print(mySQL.get_from_table('reference', ID, 'Voltage_AC'))
                newval = input("Enter the new value.  Type 'c' to cancel: ")
                if newval != 'c':
                    mySQL.update_reference(ID=ID, Voltage_AC=newval)
                    print("Voltage_AC updated to: ", newval, "\n")
                else:
                    print("Update canceled.\n")
            case 'Voltage_DC' | 'voltagedc' | 'voltage_dc' | 'VoltageDC':
                print("The current Voltage_DC for the ", ID, " is: ")
                print(mySQL.get_from_table('reference', ID, 'Voltage_DC'))
                newval = input("Enter the new value.  Type 'c' to cancel: ")
                if newval != 'c':
                    mySQL.update_reference(ID=ID, Voltage=newval)
                    print("Voltage_DC updated to: ", newval, "\n")
                else:
                    print("Update canceled.\n")
            case 'Current' | 'current':
                print("The Current for the ", ID, " is: ")
                print(mySQL.get_from_table('reference', ID, 'Current'))
                newval = input("Enter the new value.  Type 'c' to cancel: ")
                if newval != 'c':
                    mySQL.update_reference(ID=ID, Current=newval)
                    print("Current updated to: ", newval, "\n")
                else:
                    print("Update canceled.\n")
            case 'Power' | 'power':
                print("The current Power for the ", ID, " is: ")
                print(mySQL.get_from_table('reference', ID, 'Power'))
                newval = input("Enter the new value.  Type 'c' to cancel: ")
                if newval != 'c':
                    mySQL.update_reference(ID=ID, Power=newval)
                    print("Power updated to: ", newval, "\n")
                else:
                    print("Update canceled.\n")
            case 'Over_Current' | 'oc' | 'overcurrent' | 'over_current':
                print("The Over_Current for the ", ID, " is: ")
                print(mySQL.get_from_table('reference', ID, 'Over_Current'))
                newval = input("Enter the new value.  Type 'c' to cancel: ")
                if newval != 'c':
                    mySQL.update_reference(ID=ID, OCurr=newval)
                    print("Over_Current updated to: ", newval, "\n")
                else:
                    print("Update canceled.\n")
            case 'Internal_Resistance' | 'ir' | 'ires':
                print("The Internal_Resistance for the ", ID, " is: ")
                print(mySQL.get_from_table('reference', ID, 'Internal_Resistance'))
                newval = input("Enter the new value.  Type 'c' to cancel: ")
                if newval != 'c':
                    mySQL.update_reference(ID=ID, IRes=newval)
                    print("Internal_Resistance updated to: ", newval, "\n")
                else:
                    print("Update canceled.\n")
            case 'NHR_mode' | 'nhrmode' | 'nhr_mode' | 'mode':
                print("The NHR_mode for the ", ID, " is: ")
                print(mySQL.get_from_table('reference', ID, 'NHR_mode'))
                newval = input("Enter the new value.  Type 'c' to cancel: ")
                if newval != 'c':
                    mySQL.update_reference(ID=ID, NHR_mode=newval)
                    print("NHR_mode updated to: ", newval, "\n")
                else:
                    print("Update canceled.\n")
            case 'NHR_enable' | 'nhrenable' | 'nhr_enable' | 'enable':
                print("The NHR_enable for the ", ID, " is: ")
                print(mySQL.get_from_table('reference', ID, 'NHR_enable'))
                newval = input("Enter the new value.  Type 'c' to cancel: ")
                if newval != 'c':
                    mySQL.update_reference(ID=ID, NHR_enable=newval)
                    print("NHR_enable updated to: ", newval, "\n")
                else:
                    print("Update canceled.\n")
            case 'NHR_safety' | 'nhrsafety' | 'nhr_safety' | 'safety':
                print("The NHR_safety for the ", ID, " is: ")
                print(mySQL.get_from_table('reference', ID, 'NHR_safety'))
                newval = input("Enter the new value.  Type 'c' to cancel: ")
                if newval != 'c':
                    mySQL.update_reference(ID=ID, NHR_safety=newval)
                    print("NHR_safety updated to: ", newval, "\n")
                else:
                    print("Update canceled.\n")
            case 'NHR_slewVolt' | 'slewvolt' | 'nhrslewvolt' | 'nhr_slewvolt':
                print("The NHR_slewVolt for the ", ID, " is: ")
                print(mySQL.get_from_table('reference', ID, 'NHR_slewVolt'))
                newval = input("Enter the new value.  Type 'c' to cancel: ")
                if newval != 'c':
                    mySQL.update_reference(ID=ID, NHR_slewVolt=newval)
                    print("NHR_slewVolt updated to: ", newval, "\n")
                else:
                    print("Update canceled.\n")
            case 'NHR_slewCurr' | 'slewcurr' | 'nhrslewcurr' | 'nhr_slewcurr':
                print("The NHR_slewCurr for the ", ID, " is: ")
                print(mySQL.get_from_table('reference', ID, 'NHR_slewCurr'))
                newval = input("Enter the new value.  Type 'c' to cancel: ")
                if newval != 'c':
                    mySQL.update_reference(ID=ID, NHR_slewCurr=newval)
                    print("NHR_slewCurr updated to: ", newval, "\n")
                else:
                    print("Update canceled.\n")
            case 'NHR_slewPower' | 'slewpower' | 'nhrslewpower' | 'nhr_slewpower':
                print("The NHR_slewPower for the ", ID, " is: ")
                print(mySQL.get_from_table('reference', ID, 'NHR_slewPower'))
                newval = input("Enter the new value.  Type 'c' to cancel: ")
                if newval != 'c':
                    mySQL.update_reference(ID=ID, NHR_slewPower=newval)
                    print("NHR_slewPower updated to: ", newval, "\n")
                else:
                    print("Update canceled.\n")
            case 'NHR_slewRes' | 'slewres' | 'nhrslewres' | 'nhr_slewres':
                print("The NHR_slewRes for the ", ID, " is: ")
                print(mySQL.get_from_table('reference', ID, 'NHR_slewRes'))
                newval = input("Enter the new value.  Type 'c' to cancel: ")
                if newval != 'c':
                    mySQL.update_reference(ID=ID, NHR_slewRes=newval)
                    print("NHR_slewRes updated to: ", newval, "\n")
                else:
                    print("Update canceled.\n")
            case 'NHR_Rgain' | 'rgain' | 'nhrrgain' | 'nhr_rgain':
                print("The NHR_Rgain for the ", ID, " is: ")
                print(mySQL.get_from_table('reference', ID, 'NHR_Rgain'))
                newval = input("Enter the new value.  Type 'c' to cancel: ")
                if newval != 'c':
                    mySQL.update_reference(ID=ID, NHR_Rgain=newval)
                    print("NHR_Rgain updated to: ", newval, "\n")
                else:
                    print("Update canceled.\n")
            case 'MX_shape' | 'mxshape' | 'mx_shape' | 'shape':
                print("The MX_shape for the ", ID, " is: ")
                print(mySQL.get_from_table('reference', ID, 'MX_shape'))
                newval = input("Enter the new value.  Type 'c' to cancel: ")
                if newval != 'c':
                    mySQL.update_reference(ID=ID, MX_shape=newval)
                    print("MX_shape updated to: ", newval, "\n")
                else:
                    print("Update canceled.\n")
            case 'MX_cliplevel' | 'mxclip' | 'mxcliplevel' | 'mx_cliplevel' | 'clip' | 'cliplevel':
                print("The MX_cliplevel for the ", ID, " is: ")
                print(mySQL.get_from_table('reference', ID, 'MX_cliplevel'))
                newval = input("Enter the new value.  Type 'c' to cancel: ")
                if newval != 'c':
                    mySQL.update_reference(ID=ID, MX_cliplevel=newval)
                    print("MX_cliplevel updated to: ", newval, "\n")
                else:
                    print("Update canceled.\n")
            case 'Reset' | 'reset':
                print("The Reset for the ", ID, " is: ")
                print(mySQL.get_from_table('reference', ID, 'Reset'))
                newval = input("Enter the new value.  Type 'c' to cancel: ")
                if newval != 'c':
                    mySQL.update_reference(ID=ID, Reset=newval)
                    print("Reset updated to: ", newval, "\n")
                else:
                    print("Update canceled.\n")
            case 'NHR_parallel' | 'parallel' | 'nhrparallel' | 'nhr_parallel':
                print("The NHR_parallel for the ", ID, " is: ")
                print(mySQL.get_from_table('reference', ID, 'NHR_parallel'))
                newval = input("Enter the new value.  Type 'c' to cancel: ")
                if newval != 'c':
                    mySQL.update_reference(ID=ID, NHR_parallel=newval)
                    print("NHR_parallel updated to: ", newval, "\n")
                else:
                    print("Update canceled.\n")
            case 'NHR_slaveunits' | 'slaveunits' | 'nhrslaveunits' | 'nhr_slaveunints' | 'slave':
                print("The NHR_slaveunits for the ", ID, " is: ")
                print(mySQL.get_from_table('reference', ID, 'NHR_slaveunits'))
                newval = input("Enter the new value.  Type 'c' to cancel: ")
                if newval != 'c':
                    mySQL.update_reference(ID=ID, NHR_slaveunits=newval)
                    print("NHR_slaveunits updated to: ", newval, "\n")
                else:
                    print("Update canceled.\n")
            case default:
                print("The parameter '", parameter , "' is not a valid column, please try again.")
        mySQL.Close()
    except Exception as e:
        print("error passing parameters, incorrect parameter?")

#mySQL.update_equipment(ID=ID, IP='', State='', Fault='', Voltage=None, Current=None, Power=None, SOC=None)
        #         if primary == 4 and Table == 'equipment' and ID != '':
        #             mySQL.update_equipment(ID=ID, IP=IP, State=State, Fault='')
        #             if IP != '':
        #                 update_IP(ID)
        #         elif primary == 4 and Table == 'reference' and ID != '':
        #             mySQL.update_reference(ID, State, Range, BDV, Voltage_AC, Voltage, Current, Power, OCurr, IRes)
        #             reference_check(ID)
        #         elif primary == 4 and Table == 'externalreference' and ID != '':
        #             mySQL.update_externalreference(ID, Power)
        #         # add update to users table
        #         elif primary == 4 and Table == 'battery' and ID != '':
        #             mySQL.update_battery(ID=ID,Status=State, SOC=SOC, charge=charge_Rate, Power=Power)

#-------------------------------------------------------------------------------------------
# Checks the scheduled events 
# if event is not scheduled it will send lockout to PowerSupply
#-------------------------------------------------------------------------------------------
def machine_Check(t): # Runs on seperate thread
    TIME.sleep(.2)
    cycle = 0
    state = ''
    scheduled = 0

    while True:
        try:
            TIME.sleep(.16)

            if cycle == 0:
                ID = 'NHR_ONE'
                SID = 'NHR1'
            elif cycle == 1:
                ID = 'NHR_TWO'
                SID = 'NHR2'
            elif cycle == 2:
                ID = 'NHR_THREE'
                SID = 'NHR3'
            elif cycle == 3:
                ID = 'Regatron'
                SID = 'Regatron'
            elif cycle == 4:
                ID = 'MX_THIRTY'
                SID = 'MX_THIRTY'
            elif cycle == 5:
                ID = 'GK'
                SID = 'GK'

            with Lock:
                mySQL.sql_connect()

                scheduled = mySQL.get_active_event("scheduling", ID=SID, Column='id') # get the id for the active event if there is one
                End = mySQL.get_active_event("scheduling", ID=SID, Column='end') # get the end time for the active event if there is one
                End = str(End).split(':')
                t = str(TIME.strftime("%H:%M:%S", TIME.localtime())).split(':')
                #print(ID,state, scheduled)
                
                if scheduled == None: # The machine is not currently scheduled
                    #Lock_out(ID)    # <--- Uncomment this when we are ready to test the Lockout for the machines
                    #print(SID, " Not Scheduled\n")
                    scheduled = scheduled # <--- can remove this once Lock_out is uncommented, python does not like empty if statements
                else:
                    #print(TIME.strftime("%H:%M:%S", TIME.localtime()),' , ',End, '\n')
                    if(int(t[0]) == int(End[0]) and int(t[1]) == int(End[1]) and int(t[2]) == int(End[2]) ): # Event has expired
                        print("time = ", End, "  power supply = ", ID, "Sending OFF command")
                        #Lock_out(ID)
                
                mySQL.Close()
            
            if cycle < 5:
                cycle += 1
            else:
                cycle = 0
 

        except Exception as E:
            print("\nread error\n", E)

#-----------------------------------------------------
# sends an Emergency_OFF command to power supplies
#-----------------------------------------------------
def Lock_out(ID):
    print ('recieved eoff for ', ID)
    if ID == "NHR_ONE":
        Emergency_OFF( "nhr1_EO", 0) # 0 = OFF
    if ID == "NHR_TWO":
        Emergency_OFF( "nhr2_EO", 0) # 0 = OFF
    if ID == "NHR_THREE":
        Emergency_OFF( "nhr3_EO", 0) # 0 = OFF
    if ID == "MX_THIRTY":
        Emergency_OFF( "mx_EO", 0) # 0 = OFF
    if ID == "Regatron":
        Emergency_OFF("reg_EO", 0) # 0 = OFF
    #if ID == "GK":
        #Emergency_OFF_gk("gk_EO", 0) # 0 = OFF
    
#-----------------------------------------------------
# function to control the Logix battery
#-----------------------------------------------------
def auto_Control(name): # Runs on seperate thread
    TIME.sleep(.5)
    
    with Lock:
        mySQL.sql_connect()
        oldPower = mySQL.get_from_table('battery', 'Control', 'Power_Delivery')
        mySQL.Close()

    with Lock:
        mySQL.sql_connect()
        events = mySQL.select_events(signal_name = "ELECTRICITY_PRICE", signal_type ="price", dtstart=datetime.combine(date.today(), time.min).strftime("%Y-%m-%d %H:%M:%S"), \
                dtend = datetime.combine(date.today(), time.max).strftime("%Y-%m-%d %H:%M:%S"))
        signal_data = []
        min_price = [sys.maxsize, 0]
        energy_price_index = 0
        avg_rate = float()
        for (ven_id, signal_name, signal_type, signal_id, dtstart, duration, signal_payload) in events :
            # print(ven_id + " " + signal_name + " " + signal_type + " " + signal_id + " " + dtstart.strftime("%Y-%m-%d %H:%M:%S") + " " + str(duration) + " " + str(signal_payload))
            if signal_name == 'ELECTRICITY_PRICE' :
                signal_data.append([ven_id, signal_name, signal_type, signal_id, dtstart, duration, signal_payload])
                if signal_payload < min_price[0] :
                    min_price = [int(signal_payload), len(signal_data)-1] # Record the minimum price and index
                avg_rate = signal_payload + avg_rate
                energy_price_index = energy_price_index + 1
        #print(signal_data)
        if energy_price_index != 0 :
            avg_rate = avg_rate / energy_price_index
        for (ven_id, signal_name, signal_type, signal_id, dtstart, duration, signal_payload) in signal_data :
            dtcmp1_1 = TIME.mktime(dtstart.timetuple())
            dtcmp1_2 = duration
            if signal_payload <= avg_rate and dtcmp1_1 >= int(TIME.time()) and dtcmp1_2 + dtcmp1_1 < int(TIME.time()) and mySQL.read_table('battery', 'Logix_Blue', 'alter_schedule') == False:
                mySQL.update_battery_schedule('Logix_Blue', True)
                update_battery_schedule(True)
            elif mySQL.read_table('battery', 'Logix_Blue', 'alter_schedule') == True :
                mySQL.update_battery_schedule('Logix_Blue', False)
                update_battery_schedule(False)
        mySQL.Close()

        # if the solar is active and greater than consumption then fully charge the battery

        #signal_data.sort()
    while True:
        TIME.sleep(.2) # need to give the system some time for the other threads or it runs really slow
        with Lock:
            mySQL.sql_connect()
            Power = mySQL.get_from_table('battery', 'Control', 'Power_Delivery') # check if battery power changed
            if(oldPower != Power ):
                # print('Power: ',oldPower, " is now ", Power)
                update_battery_power(power=Power) # update the battery with new power level
                oldPower = Power
            events = mySQL.select_events(dtstart=datetime.combine(date.today(), time.min).strftime("%Y-%m-%d %H:%M:%S"), \
                    dtend = datetime.combine(date.today(), time.max).strftime("%Y-%m-%d %H:%M:%S"))
            signal_data = []
            min_price = [sys.maxsize, 0]
            energy_price_index = 0
            avg_rate = float()
            for (ven_id, signal_name, signal_type, signal_id, dtstart, duration, signal_payload) in events :
                # print(ven_id + " " + signal_name + " " + signal_type + " " + signal_id + " " + dtstart.strftime("%Y-%m-%d %H:%M:%S") + " " + str(duration) + " " + str(signal_payload))
                if signal_name == 'ELECTRICITY_PRICE' and signal_type == 'price':
                    signal_data.append([ven_id, signal_name, signal_type, signal_id, dtstart, duration, signal_payload])
                    if signal_payload < min_price[0] :
                        min_price = [int(signal_payload), len(signal_data)-1] # Record the minimum price and index
                    avg_rate = signal_payload + avg_rate
                    energy_price_index = energy_price_index + 1

            #print(signal_data)
            if energy_price_index != 0 :
                avg_rate = avg_rate / energy_price_index
            trigger_value = False
            if mySQL.get_from_table('battery', 'Logix_Blue', 'alter_schedule') ==  None:
                mySQL.update_battery_schedule('Logix_Blue', 0)
            for (ven_id, signal_name, signal_type, signal_id, dtstart, duration, signal_payload) in signal_data :
                dtcmp1_1 = TIME.mktime(dtstart.timetuple())
                dtcmp1_2 = duration
                #print("Check battery schedule: " + str(avg_rate) + " " + str(dtcmp1_1) + " " + str(dtcmp1_2) + " " + str(int(TIME.time())) + " " + str(signal_payload))
                #print(mySQL.get_from_table('battery', 'Logix_Blue', 'alter_schedule'))
#                if signal_payload <= avg_rate and dtcmp1_1 <= int(TIME.time()) and dtcmp1_2 + dtcmp1_1 > int(TIME.time()) and mySQL.get_from_table('battery', 'Logix_Blue', 'alter_schedule') == 0:
                if ( signal_payload <= avg_rate and dtcmp1_1 <= int(TIME.time()) and dtcmp1_2 + dtcmp1_1 > int(TIME.time()) ) or signal_payload <= 0 :
                    #print("Update battery to true")
                    trigger_value = True
                    break
#                if (signal_payload < 0) # Curtail solar to 0.


#                elif mySQL.get_from_table('battery', 'Logix_Blue', 'alter_schedule') == 1 and  dtcmp1_1 > int(TIME.time()) and dtcmp1_2 + dtcmp1_1 <= int(TIME.time()):
#                elif dtcmp1_1 <= int(TIME.time()) and dtcmp1_2 + dtcmp1_1 > int(TIME.time()):
#                    print("Update battery to False")
#                    mySQL.update_battery_schedule('logix_blue', 0)
#                    update_battery_schedule(False)
#                elif dtcmp1_2 + dtcmp1_1 < int(TIME.time()):
#                    print("Update battery to False False")
#                    mySQL.update_battery_schedule('logix_blue', 0)
#                    update_battery_schedule(False)
            if trigger_value == True :
                mySQL.update_battery_schedule('Logix_Blue', 1)
                update_battery_schedule(True)
            else :
                mySQL.update_battery_schedule('Logix_Blue', 0)
                update_battery_schedule(False)


            mySQL.Close()

def Decode_RMP(value):
    val = 0

    mySQL.sql_connect()
    if value == 1011:
        print("1011 is here")
        val = mySQL.get_from_table("externalreference", "SMA_FIFTY", "Power_Limit")
        print(val)
        RMP_update(val)
    else:
        value = 0
    mySQL.Close()

#-------------------------------------------------------------------------------------------------------------

# Create the server object
try:
    server = OpenADRServer(vtn_id='myvtn', http_port=8030, requested_poll_freq=timedelta(seconds=1))
except Exception as e:
    print("\nCould not initialize OpenADR Server on selected port\n", e)

# Add the handler for client (VEN) registrations
server.add_handler('on_create_party_registration', on_create_party_registration)

# Add the handler for report registrations from the VEN
server.add_handler('on_register_report', on_register_report)

# Add a prepared event for a VEN that will be picked up when it polls for new messages.
now = datetime.now()

prompt = prompt_thread()
prompt.start()

_thread.start_new_thread(manage_sql,("u1",))     # used for user to control database
#_thread.start_new_thread(call_update_reference,("u1",))     # used for user to control database
_thread.start_new_thread(machine_Check, ("t2",))   # runs in background to check the machine is scheduled 
_thread.start_new_thread(auto_Control, ("t3",))    # runs in background to check SQL database control for battery
_thread.start_new_thread(reference_check, ("t4",)) # runs in background to check SQL database control for machines

# Run the server on the asyncio event loop
loop = asyncio.get_event_loop()
loop.create_task(server.run())
loop.run_forever()
