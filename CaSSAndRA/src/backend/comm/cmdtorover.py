import logging
logger = logging.getLogger(__name__)

import numpy as np
import pandas as pd

from .. data import mapdata
from .. data.roverdata import robot
from . import cmdlist

def takemap(perimeter: pd.DataFrame(), way: pd.DataFrame(), dock: bool) -> pd.DataFrame():
    logger.info('Backend: Prepare map and way data for transmition')

    #Remove dockpoints, if neccessary (e.g. for goto command)
    if not dock:
        perimeter = perimeter[perimeter['type'] != 'dockpoints']

    data = pd.concat([perimeter, way], ignore_index=True)
    
    #Create AT+W messages
    data = data.round(2)
    amount_of_packages = data.index//30
    data['package_nr'] = amount_of_packages
    data['coords'] = ','+data['X'].astype(str)+','+data['Y'].astype(str) 
    data = data.groupby('package_nr').agg({'coords': lambda x: list(x)})
    buffer = pd.DataFrame()
    for i, row in data.iterrows():
        buffer_str = ''.join(row['coords'])
        msg = {'msg': 'AT+W,'+str(i*30)+buffer_str}
        msg_df = pd.DataFrame([msg])
        buffer = pd.concat([buffer, msg_df], ignore_index=True)
        logger.debug('Add to takemap buffer: '+str(msg))

    #Create AT+N message
    perimeter_cnt = len(perimeter[perimeter['type'] == 'perimeter'])
    exclusion_names = perimeter['type'].unique()
    exclusion_names = np.delete(exclusion_names, np.where(exclusion_names == 'perimeter'))
    exclusion_names = np.delete(exclusion_names, np.where(exclusion_names == 'dockpoints'))
    exclusions_cnt = len(perimeter[perimeter['type'].isin(exclusion_names)])
    docking_cnt = len(perimeter[perimeter['type'] == 'dockpoints'])
    if way.empty:
        way_cnt = 0
    else:
        way_cnt = len(way[way['type'] == 'way'])
    msg = {'msg': 'AT+N,'+str(perimeter_cnt)+','+str(exclusions_cnt)+','+str(docking_cnt)+','+str(way_cnt)+',0'}
    msg_df = pd.DataFrame([msg])
    buffer = pd.concat([buffer, msg_df], ignore_index=True)

    #Create AT+X message
    exclusion_pts = []
    for exclusion in exclusion_names:
        exclusion_pts.append(len(perimeter[perimeter['type'] == exclusion]))
    exclusion_pts = str(exclusion_pts)
    exclusion_pts = exclusion_pts.replace('[', '')
    exclusion_pts = exclusion_pts.replace(']', '')
    exclusion_pts = exclusion_pts.replace(' ', '')
    msg = {'msg': 'AT+X,0,'+exclusion_pts}
    msg_df = pd.DataFrame([msg])
    buffer = pd.concat([buffer, msg_df], ignore_index=True)

    cmdlist.cmd_take_map = False
    return buffer

def move(movement: list()) -> pd.DataFrame():
    if movement[0] !=0 or movement[1] != 0:
        msg = {'msg': 'AT+M,'+str(movement[0])+','+str(movement[1])}
        buffer = pd.DataFrame([msg])
        logger.debug(f'Backend: Command "MOVE" is send to rover. X:{movement[0]} Y:{movement[1]}')
        return buffer
    elif movement[0] == 0 and movement[1] == 0:
        msg = {'msg': 'AT+M,0.0,0.0'}
        buffer = pd.DataFrame([msg])
        logger.debug(f'Backend: Command "MOVE" is send to rover. X:{movement[0]} Y:{movement[1]}')
        cmdlist.cmd_move = False
        return buffer

def goto() -> pd.DataFrame():
    msg = {'msg': 'AT+C,0,1,0.3,100,0,-1,-1,-1'}
    buffer = pd.DataFrame([msg])
    logger.debug('Backend: Command goto is send to rover')
    cmdlist.cmd_goto = False
    return buffer

def stop():
    msg = {'msg': 'AT+C,0,0,-1,-1,-1,-1,-1,-1'}
    buffer = pd.DataFrame([msg])
    logger.debug('Backend: Command stop is send to rover')
    cmdlist.cmd_stop = False
    return buffer

def dock() -> pd.DataFrame():
    msg = {'msg': 'AT+C,0,4,-1,-1,-1,-1,-1,-1'}
    buffer = pd.DataFrame([msg])
    logger.debug('Backend: Command dock is send to rover')
    cmdlist.cmd_dock = False
    return buffer

def mow() -> pd.DataFrame():
    msg = {'msg': 'AT+C,1,1,0.3,100,0,-1,-1,-1'}
    buffer = pd.DataFrame([msg])
    logger.debug('Backend: Command start is send to rover')
    cmdlist.cmd_mow = False
    return buffer

def shutdown() -> pd.DataFrame():
    msg = {'msg': 'AT+Y3'}
    buffer = pd.DataFrame([msg])
    logger.debug('Backend: Command shutdown is send to rover')
    cmdlist.cmd_shutdown = False
    return buffer

def reboot() -> pd.DataFrame():
    msg = {'msg': 'AT+Y'}
    buffer = pd.DataFrame([msg])
    logger.debug('Backend: Command reboot is send to rover')
    cmdlist.cmd_reboot = False
    return buffer

def gpsreboot() -> pd.DataFrame():
    msg = {'msg': 'AT+Y2'}
    buffer = pd.DataFrame([msg])
    logger.debug('Backend: Command GPS reboot is send to rover')
    cmdlist.cmd_gps_reboot = False
    return buffer

def togglemowmotor() -> pd.DataFrame():
    #mow motor switch on
    if not robot.last_mow_status:
        msg = {'msg': 'AT+C,1,-1,-1,-1,-1,-1,-1,-1'}
        cmdlist.cmd_toggle_mow_motor = False
    #mow motor switch off
    else:
        msg = {'msg': 'AT+C,0,-1,-1,-1,-1,-1,-1,-1'}
        cmdlist.cmd_toggle_mow_motor = False
    buffer = pd.DataFrame([msg])
    return buffer

def takepositionmode() -> pd.DataFrame():
    positionmode = mapdata.positionmode
    if positionmode == 'absolute':
        positionmode = '1,'
    else:
        positionmode = '0,'
    msg = {'msg': 'AT+P,'+positionmode+str(mapdata.lon)+','+str(mapdata.lat)}
    buffer = pd.DataFrame([msg])
    cmdlist.cmd_set_positionmode = False
    return buffer