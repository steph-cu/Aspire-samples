import sys
sys.path.insert(0, '../Lib')
from distutils.log import Log
from xmlrpc.client import NOT_WELLFORMED_ERROR
import openleadr
import asyncio
import logging
import struct
#from aioconsole import ainput
from datetime import *
from datetime import datetime, timezone, timedelta
from openleadr import OpenADRClient, enable_default_logging
from functools import partial
from terminal_colors import Terminal_Colors
from Converted_server import *
import Converted_server #The communication file
from ocpp.v16 import call_result
from ocpp.v16 import call
from ocpp.v16.enums import *
from ocpp.messages import *
from ocpp.routing import on 
from websockets import serve
try:
    import websockets
except ModuleNotFoundError:
    print("This example relies on the 'websockets' package.")
    print("Please install it by running: ")
    print()
    print(" $ pip install websockets")
    import sys

    sys.exit(1)
import _thread
import time
import math

logging.basicConfig(level=logging.INFO)

enable_default_logging()

async def calling(name, duration, limit, number):
    global cpi 
    global ws
    while cpi == 0 or ws == 0 :
        continue
    try:
        cp = ChargePoint(cpi, ws,)
        if name == 'reset':
            if amount == 1:
                type_r = ResetType.hard
            elif amount == 0:
                type_r = ResetType.soft
            else:
                raise Exception("No Recognized Input")
            await cp.reset(type_r)
        elif name == 'profile':
            profile = {
                'id': number,#enter a number here,
                'chargingProfileId':100, # may or may not be needed
                'stackLevel':0,
                'chargingProfilePurpose':ChargingProfileKindType.tx_default_profile,#ChargingProfileKindType.tx_default_profile
                'chargingProfileKind':ChargingProfileKindType.Absolute, #ChargingProfileKindType
                'chargingSchedule':{
                    'duration': duration,
                    'startSchedule':datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S') + "Z",
                    'chargingRateUnit': 'W',# This is needed
                    'chargingSchedulePeriod':[{
                        'startPeriod':0,# this is needed
                        'limit': limit, # this is needed
                    }]
                },
                'connectorId':0, #either 0, 1, or 2 (for most cases)
                # 'handled':,
                # 'cleared':,
                # 'accepted':,
                # 'manualControl':,
                # 'createdAt':,
                # 'updatedAt':,
                'ChargerId':'grs' # probably needs to change b/t clients
            }
            await cp.send_max_limitation_from_db(profile)
        elif name == 'start':
            cp.remote_start_transaction()
        elif name == 'stop':
            cp.remote_stop_transaction(number)
        
    except Exception as e:
        print(e)
        print("Did not get called")

connected_clients = []
attempted_connection_clients = []

async def on_connect(websocket, path):
    print("GOT INTO ON_CONNECT")
    global chargePoints  
    global connected_clients
    global attempted_connection_clients
    charge_point_id = path.strip("/")
    cp = ChargePoint(charge_point_id, websocket,)
    chargePoints.append(cp)
    if not charge_point_id in attempted_connection_clients:
        attempted_connection_clients.append(charge_point_id)
        print(f"{Terminal_Colors.OKGREEN}Charge Point ID (First Connect):{Terminal_Colors.ENDC}{cp.id}")

    global cpi
    global ws
    cpi = charge_point_id
    ws = websocket
    # print("\nThis is the chargePointID: ", str(cpi), "\n")
    # print("\nThis is the websocket: ", str(ws), "\n")
    # await asyncio.gather(cp.start())
    await asyncio.gather(chargePoints[-1].start(), chargePoints[-1].send_trigger_message())

async def setup():
    server = await websockets.serve(
        on_connect, '0.0.0.0', 80, subprotocols=["ocpp1.6"]
    )
    global cpi
    global ws
    logging.info("Server Started listening to new connections...")
    print("AWAIT SERVER")
    await server.wait_closed()

def setup_prior(name):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    print("SETUP IS JUST ABOUT TO RUN")
    loop.run_until_complete(setup())
    loop.close()

_thread.start_new_thread(setup_prior,("u1",))

async def get_MeterCurrent():
    return server.current

async def get_MeterPower():
    return server.power

async def get_MeterEnergy():
    return server.energy

async def handle_event(event):
    description = event['event_descriptor']
    event_id = description['event_id']
    all_words = event_id.split()
    id = all_words[0]
    number = all_words[1]
    if id == 'Grizl': #set MaxEnergyOnInvalidId
        try:
            signal = event['event_signals'][0]
            name = signal['signal_id']
            intervals = signal['intervals'][0]
            duration = intervals['signal_payload']
            signal = event['event_signals'][1]
            intervals = signal['intervals'][0]
            limit = intervals['signal_payload']
            await calling(name, duration, limit, number)
        except Exception as e:
            print(e)
            print("ERROR WITH GRIZL")
    return 'optIn'

now = datetime.now()
client = openleadr.OpenADRClient(ven_name='Grizl', vtn_url='http://localhost:8020/OpenADR2/Simple/2.0b', ven_id='ven_id_300')

client.add_report(callback=get_MeterCurrent,
                    report_specifier_id='MeterValue',
                    resource_id='Grizl',
                    measurement='Current', # there is also Current and Energy
                    sampling_rate=timedelta(seconds=10),
                    report_duration=timedelta(seconds=100),
                    unit='A')
client.add_report(callback=get_MeterPower,
                    report_specifier_id='MeterValue',
                    resource_id='Grizl',
                    measurement='Power', # there is also Current and Energy
                    sampling_rate=timedelta(seconds=10),
                    report_duration=timedelta(seconds=100),
                    unit='W')
client.add_report(callback=get_MeterEnergy,
                    report_specifier_id='MeterValue',
                    resource_id='Grizl',
                    measurement='Energy', # there is also Current and Energy
                    sampling_rate=timedelta(seconds=10),
                    report_duration=timedelta(seconds=100),
                    unit='Wh')

client.add_handler('on_event', handle_event) 

loop = asyncio.get_event_loop()
loop.create_task(client.run())
loop.run_forever()
