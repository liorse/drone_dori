
# Logger is the active object that has the following specifications:
# 1. enable or disable logging
# 2. on data ready signal from various instrument services, the logger will update its local state variable
# 3. on a specific interval chosen by an epic variable, it will save the mean number of samples for each measurment. 
#    it will record the count number of samples for each type of instrument

import time

from miros import Event
from miros import spy_on
from miros import signals
from miros import ActiveObject
from miros import return_status
import logging
import numpy as np
#from logger_dummy_class import LOGGER
#from logger_class import LOGGER
import json
import epics
import pandas as pd
import os
from datetime import datetime
import yaml

OK = 0
logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)

class LOGGER(ActiveObject):
    '''
    LOGGER class will include methods for updating its local 
    state measurements from all instruments
    '''
    def __init__(self, config_data, opc_dev_epics, aeth_dev_epics, sniffer_dev_epics, logger_dev_epics):

        logging.info("Instantiated Logger class!")
        self.logger_dev_epics = logger_dev_epics
        self.config_data = config_data
        self.logger_dev_epics.folder_name = self.config_data['logger']['save_folder']
        self.thread_save_to_file_id = None
        self.temp_save_interval = self.config_data['logger']['interval_between_save_s']
        self.logger_dev_epics.save_interval = self.temp_save_interval
        self.logger_dev_epics.project_name = self.config_data['logger']['project_name']
              
        # Sniffer initializatoin
        self.sniffer_dev_epics = sniffer_dev_epics
        self.list_sniffer_PVs = self.config_data['logger']['sniffer_PVs']
        self.save_sniffer_bool = self.config_data['logger']['save_sniffer_bool']
        self.logger_dev_epics.save_sniffer = self.save_sniffer_bool
        
        # AETH initialization
        self.aeth_dev_epics = aeth_dev_epics
        self.list_aeth_PVs = self.config_data['logger']['aeth_PVs']
        self.save_aeth_bool = self.config_data['logger']['save_aeth_bool']
        self.logger_dev_epics.save_aeth = self.save_aeth_bool
        
        # initialize sniffer meta file
        self.sniffer_meta=[]
        self.sniffer_meta.append('None') # the counts units for aeth records
        for pv_name in self.list_sniffer_PVs:
            self.pv_type = self.sniffer_dev_epics.PV(pv_name).type
            if self.pv_type == 'time_double':
                self.sniffer_meta.append(self.sniffer_dev_epics.get(pv_name + '.EGU'))
                # opc_device.PV('pm1').get_ctrlvars()  to get units in another method
            elif self.pv_type == 'time_enum':
                self.sniffer_meta.append("BOOL")
            else:
                self.sniffer_meta.append("None")

        sniffer_header = ['sniffer_' + sniffer_pv_name for sniffer_pv_name in self.list_sniffer_PVs]
        self.sniffer_df_array = pd.DataFrame(columns=sniffer_header)
        
        # intialize aeth meta file                
        self.aeth_meta=[]
        self.aeth_meta.append('None') # the counts units for aeth records
        for pv_name in self.list_aeth_PVs:
            self.pv_type = self.aeth_dev_epics.PV(pv_name).type
            if self.pv_type == 'time_double':
                self.aeth_meta.append(self.aeth_dev_epics.get(pv_name + '.EGU'))
                # opc_device.PV('pm1').get_ctrlvars()  to get units in another method
            elif self.pv_type == 'time_enum':
                self.aeth_meta.append("BOOL")
            else:
                self.aeth_meta.append("None")

        
        aeth_header = ['aeth_' + aeth_pv_name for aeth_pv_name in self.list_aeth_PVs]
        self.aeth_df_array = pd.DataFrame(columns=aeth_header)
        
        # OPC initialization
        self.opc_dev_epics = opc_dev_epics
        self.list_opc_PVs = self.config_data['logger']['opc_PVs']
        
        self.logger_dev_epics.save_opc = self.config_data['logger']['save_opc_bool']
        
        self.bins_opc_PV_name = self.config_data['logger']['opc_array_PV']
        self.bins_names = ['0.35-0.46_um', '0.46-0.66_um', '0.66-1.0_um', '1.0-1.3_um', '1.3-1.7_um', 
                           '1.7-2.3_um', '2.3-3.0_um', '3.0-4.0_um', '4.0-5.2_um', '5.2-6.5_um', '6.5-8.0_um',
                           '8.0-10.0_um', '10.0-12.0_um', '12.0-14.0_um', '14.0-16.0_um', '16.0-18.0_um', '18.0-20.0_um',
                           '20.0-22.0_um', '22.0-25.0_um', '25.0-28.0_um', '28.0-31.0_um', '31.0-34.0_um', '34.0-37.0_um',
                           '37.0_-40.0um']
        self.bins_names = ['opc_' + bin_name for bin_name in self.bins_names]
        
        # intialize opc meta file                
        self.opc_meta=[]
        self.opc_meta.append('None') # the counts units
        for pv_name in self.list_opc_PVs:
            self.pv_type = self.opc_dev_epics.PV(pv_name).type
            if self.pv_type == 'time_double':
                self.opc_meta.append(self.opc_dev_epics.get(pv_name + '.EGU'))
                # opc_device.PV('pm1').get_ctrlvars()  to get units in another method
            elif self.pv_type == 'time_enum':
                self.opc_meta.append("BOOL")
            else:
                self.opc_meta.append("None")

        for bins_name in self.bins_names:
            self.opc_meta.append(self.opc_dev_epics.get('bins.EGU'))

        opc_header = ['opc_' + opc_pv_name for opc_pv_name in self.list_opc_PVs]
        self.opc_df_array = pd.DataFrame(columns=opc_header + self.bins_names)

        # update default values
            
        super().__init__()


    def update_sniffer_dataframe(self):
        '''
        update sniffer local dataframe from EPIC variables upon data_ready signal
        '''
        self.sniffer_dict_single = dict()
        for pv_name in self.list_sniffer_PVs:
            self.sniffer_dict_single['sniffer_' + pv_name] = [self.sniffer_dev_epics.get(pv_name)]
        
        self.sniffer_df_single = pd.DataFrame.from_dict(self.sniffer_dict_single) 
        # append to array dataframe of sniffer data
        self.sniffer_df_array = self.sniffer_df_array.append(self.sniffer_df_single)#, ignore_index=True)
    
                
    def update_aeth_dataframe(self):
        '''
        update aeth local dataframe from EPIC variables upon data_ready signal
        '''
        self.aeth_dict_single = dict()
        for pv_name in self.list_aeth_PVs:
            self.aeth_dict_single['aeth_' + pv_name] = [self.aeth_dev_epics.get(pv_name)]

        
        self.aeth_df_single = pd.DataFrame.from_dict(self.aeth_dict_single) 
        # append to array dataframe of aeth data
        self.aeth_df_array = self.aeth_df_array.append(self.aeth_df_single)#, ignore_index=True)
        
    
    def update_opc_dataframe(self):
        '''
        update opc local dataframe from EPIC variables upon data_ready signal
        '''
        self.opc_dict_single = dict()
        for pv_name in self.list_opc_PVs:
            self.opc_dict_single['opc_' + pv_name] = [self.opc_dev_epics.get(pv_name)]

        self.opc_bins = self.opc_dev_epics.get(self.bins_opc_PV_name)

        for i, bin_value in enumerate(self.opc_bins):
            self.opc_dict_single[self.bins_names[i]] = bin_value
            
        
        self.opc_df_single = pd.DataFrame.from_dict(self.opc_dict_single) 
        # append to array dataframe of OPC data
        self.opc_df_array = self.opc_df_array.append(self.opc_df_single)#, ignore_index=True)
        
    def write_to_file(self):
        '''
        calculate mean of all different instruments
        construct a new dataframe
        append this dataframe to file if it exists
        report how long this process took in seconds
        '''

        ##########################################
        # sniffer start of analysis
        ##########################################
        if 'sniffer_utcTime' in self.sniffer_df_array:
            # get the original column of utc time, add 1 to compensate for adding the sniffer count at the beginning
            self.col_location = self.sniffer_df_array.columns.get_loc('sniffer_utcTime') + 1
            # exclude the utc column from the mean operation
            self.sniffer_mean_df = self.sniffer_df_array.loc[:,self.sniffer_df_array.columns != 'sniffer_utcTime'].mean().to_frame().T
            # insert the count number of the mean
            self.sniffer_mean_df.insert(0,'sniffer_mean_count', [len(self.sniffer_df_array)])
            # reinsert the date and time in to the correct column position to maintain its position relative to the meta data
            try:
                date_time_string = self.sniffer_df_array.iloc[-1, self.sniffer_df_array.columns.get_loc('sniffer_utcTime')]
            except IndexError:
                date_time_string = ""                
            self.sniffer_mean_df.insert(self.col_location,'sniffer_utcTime', [date_time_string])# [self.sniffer_dev_epics.get('utcTime')])
        else:
            self.sniffer_mean_df = self.sniffer_df_array.mean().to_frame().T
            self.sniffer_mean_df.insert(0,'sniffer_mean_count', [len(self.sniffer_df_array)])

        self.logger_dev_epics.no_records_saved_sniffer = len(self.sniffer_df_array)
        
        # add meta data of aeth
        self.sniffer_mean_df.columns = pd.MultiIndex.from_tuples(zip(self.sniffer_mean_df.columns, self.sniffer_meta))
        
        ##########################################
        # OPC start of analysis
        ##########################################
        self.opc_mean_df = self.opc_df_array.mean().to_frame().T

        # initialize date and tiem dataframe
        self.concat_df = pd.DataFrame({'date_time':[datetime.now().strftime('%Y/%m/%d %H:%M:%S')]})
        self.concat_df.columns = pd.MultiIndex.from_tuples(zip(self.concat_df.columns, ['None']))
               
        # add the count column
        self.opc_mean_df.insert(0,'opc_mean_count', [len(self.opc_df_array)])
        self.logger_dev_epics.no_records_saved_opc = len(self.opc_df_array)
        #self.opc_mean_df.insert(0,'date_time',[datetime.now().strftime('%Y/%m/%d %H:%M:%S')])

        # add meta data of measurement
        self.opc_mean_df.columns = pd.MultiIndex.from_tuples(zip(self.opc_mean_df.columns, self.opc_meta))

        ##########################################
        # AETH start of analysis
        ##########################################
        if 'aeth_date_time_GMT' in self.aeth_df_array:
            # get the original column of utc time, add 1 to compensate for adding the aeth count at the beginning
            self.col_location = self.aeth_df_array.columns.get_loc('aeth_date_time_GMT') + 1
            # exclude the utc column from the mean operation
            self.aeth_mean_df = self.aeth_df_array.loc[:,self.aeth_df_array.columns != 'aeth_date_time_GMT'].mean().to_frame().T
            # insert the count number of the mean
            self.aeth_mean_df.insert(0,'aeth_mean_count', [len(self.aeth_df_array)])
            # reinsert the date and time in to the correct column position to maintain its position relative to the meta data
            # get the last data in the aeth_df_array, if it doesn't exist put an empty string
            try:
                date_time_string = self.aeth_df_array.iloc[-1, self.aeth_df_array.columns.get_loc('aeth_date_time_GMT')]
            except IndexError:
                date_time_string = ""                
            self.aeth_mean_df.insert(self.col_location,'aeth_date_time_GMT', [date_time_string]) # [self.aeth_dev_epics.get('date_time_GMT')])
        else:
            self.aeth_mean_df = self.aeth_df_array.mean().to_frame().T
            self.aeth_mean_df.insert(0,'aeth_mean_count', [len(self.aeth_df_array)])

        self.logger_dev_epics.no_records_saved_aeth = len(self.aeth_df_array)
        
        # add meta data of aeth
        self.aeth_mean_df.columns = pd.MultiIndex.from_tuples(zip(self.aeth_mean_df.columns, self.aeth_meta))
        
        # join this frame with other dataframes
        # to be done

        # write to file
        self.save_opc_bool = True if self.logger_dev_epics.save_opc == 1 else False
        self.save_aeth_bool = True if self.logger_dev_epics.save_aeth == 1 else False
        self.save_sniffer_bool = True if self.logger_dev_epics.save_sniffer == 1 else False
        self.file_name_and_path = os.path.join(self.logger_dev_epics.get('folder_name', as_string=True), 
                                               self.logger_dev_epics.get('file_name', as_string=True))

        if self.save_opc_bool or self.save_aeth_bool or self.save_sniffer_bool:
 
            if self.save_opc_bool:
                self.concat_df = pd.concat([self.concat_df, self.opc_mean_df], axis=1, sort=False)
                logging.info(self.opc_df_array)
            if self.save_aeth_bool:
                self.concat_df = pd.concat([self.concat_df, self.aeth_mean_df], axis=1, sort=False)
                logging.info(self.aeth_df_array)
            if self.save_sniffer_bool:
                self.concat_df = pd.concat([self.concat_df, self.sniffer_mean_df], axis=1, sort=False)          
                #logging.info(self.sniffer_df_array)
                logging.info(self.sniffer_mean_df)
                
            # concat df
            #self.concat_df = pd.concat([self.opc_mean_df, self.aeth_mean_df], axis=1, sort=False)
            self.concat_df.to_csv(self.file_name_and_path, 
                                    mode='a', 
                                    header=not os.path.exists(self.file_name_and_path),
                                    index=False)

        # restart the opc array
        opc_header = ['opc_' + opc_pv_name for opc_pv_name in self.list_opc_PVs]
        self.opc_df_array = pd.DataFrame(columns=opc_header + self.bins_names)

        # restart the aeth array
        aeth_header = ['aeth_' + aeth_pv_name for aeth_pv_name in self.list_aeth_PVs]
        self.aeth_df_array = pd.DataFrame(columns=aeth_header)

        # restart the sniffer array
        sniffer_header = ['sniffer_' + sniffer_pv_name for sniffer_pv_name in self.list_sniffer_PVs]
        self.sniffer_df_array = pd.DataFrame(columns=sniffer_header)
                
                
                
@spy_on
def LOGGER_COMMON_BEHAVIOUR(logger, e):
    status = return_status.UNHANDLED
    if e.signal == signals.ENTRY_SIGNAL:
        status = return_status.HANDLED
    elif e.signal == signals.disable_logger:
        status = logger.trans(LOGGER_DISABLED)
    elif e.signal == signals.enable_logger:
        status = logger.trans(LOGGER_ENABLED)
    else:
        logger.temp.fun = logger.top
        status = return_status.SUPER
    return status


@spy_on
def LOGGER_DISABLED(logger, e):
    status = return_status.UNHANDLED
    if e.signal == signals.ENTRY_SIGNAL:
        status = return_status.HANDLED
    else:
        logger.temp.fun = LOGGER_COMMON_BEHAVIOUR
        status = return_status.SUPER
    return status


@spy_on
def LOGGER_ENABLED(logger, e):
    status = return_status.UNHANDLED
    if e.signal == signals.ENTRY_SIGNAL:
        #logger.post_fifo(Event(signal=signals.start_comm))
        status = return_status.HANDLED
    elif e.signal == signals.INIT_SIGNAL:
        # setup a recurring signal to keep saving data to file every logger.save_interval_s
        if logger_dev_epics.save_interval<1 or logger_dev_epics.save_interval>100: # return to default value
            logger.temp_save_interval = 5
            logger.logger_dev_epics.save_interval = logger.temp_save_interval
        else:
            logger.temp_save_interval = logger.logger_dev_epics.save_interval # return to default value
            
        
        logger.thread_save_to_file_id = logger.post_fifo(
                                                            Event(signal=signals.SAVE_TO_FILE),
                                                            period=logger.temp_save_interval,
                                                            deferred=True
                                                        )
        # update the the file name with a new project name
        logger.logger_dev_epics.file_name = logger.logger_dev_epics.get('project_name' , as_string=True) \
                                            + datetime.now().strftime('_%Y-%m-%d_%H-%M-%S.csv')
        
        logging.info('created periodic thread id' + str(logger.thread_save_to_file_id))
        status = logger.trans(LOGGER_IDLE)
    elif e.signal == signals.SAVE_INTERVAL_VALUE_UPDATE or e.signal == signals.PROJECT_NAME_UPDATE:
        status = logger.trans(LOGGER_ENABLED)
    elif e.signal == signals.SAVE_OPC_UPDATE:
        status = logger.trans(LOGGER_ENABLED)
    elif e.signal == signals.SAVE_SNIFFER_UPDATE:
        status = logger.trans(LOGGER_ENABLED)
    elif e.signal == signals.SAVE_AETH_UPDATE:
        status = logger.trans(LOGGER_ENABLED)
    elif e.signal == signals.EXIT_SIGNAL:
        logging.info('cancelling thread id' + str(logger.thread_save_to_file_id))
        logger.cancel_event(logger.thread_save_to_file_id)
        status = return_status.HANDLED
    else:
        logger.temp.fun = LOGGER_COMMON_BEHAVIOUR
        status = return_status.SUPER
    return status


@spy_on
def LOGGER_IDLE(logger, e):
    status = return_status.UNHANDLED
    if e.signal == signals.ENTRY_SIGNAL:
        status = return_status.HANDLED
    elif e.signal == signals.SAVE_TO_FILE:
        logging.info('writing to file')
        logger.write_to_file()
        status = return_status.HANDLED
    elif e.signal == signals.OPC_DATA_READY:
        logging.info('new OPC data recieved - updating internal dataframe')
        logger.update_opc_dataframe()
        status = return_status.HANDLED
    elif e.signal == signals.AETH_DATA_READY:
        logging.info('new AETH data recieved - updating internal dataframe')
        logger.update_aeth_dataframe()
        status = return_status.HANDLED
    elif e.signal == signals.SNIFFER_DATA_READY:
        logging.info('new SNIFFER data recieved - updating internal dataframe')
        logger.update_sniffer_dataframe()
        status = return_status.HANDLED
    else:
        logger.temp.fun = LOGGER_ENABLED
        status = return_status.SUPER
    return status



def on_logger_enable(value, **kw):
    if value == True:
        logger.post_fifo(Event(signal=signals.enable_logger))
    else:
        logger.post_fifo(Event(signal=signals.disable_logger))

def on_save_interval_value_change(value, **kw):
    logger.post_fifo(Event(signal=signals.SAVE_INTERVAL_VALUE_UPDATE, payload=value))
        
  
def on_opc_data_ready(value, **kw):
    logger.post_lifo(Event(signal=signals.OPC_DATA_READY))

def on_aeth_data_ready(value, **kw):
    logger.post_lifo(Event(signal=signals.AETH_DATA_READY))

def on_sniffer_data_ready(value, **kw):
    logger.post_lifo(Event(signal=signals.SNIFFER_DATA_READY))

def on_change_project_name(value, **kw):
    logger.post_fifo(Event(signal=signals.PROJECT_NAME_UPDATE))

def on_change_save_opc(value, **kw):
    logger.post_fifo(Event(signal=signals.SAVE_OPC_UPDATE))

def on_change_save_sniffer(value, **kw):
    logger.post_fifo(Event(signal=signals.SAVE_SNIFFER_UPDATE))

def on_change_save_aeth(value, **kw):
    logger.post_fifo(Event(signal=signals.SAVE_AETH_UPDATE))

    
if __name__ == "__main__":

    # establish EPICS variable connection
    #logger_dev_epics = epics.Device('logger:',
    #                             attrs=[
    #                                 'comm_ON','enable', 'CO', 'NO2', 'Ox', 'PM1', 'PM10',
    #                                 'PM2dot5', 'SO2', 'altitude', 'hdop', 'humidity','latitude', 'longitude', 'pressure',
    #                                 'sateNum', 'serial', 'temperature', 'utcTime'
    #                             ])

    logger_dev_epics = epics.Device('logger:',attrs=['save_interval'])
    opc_dev_epics = epics.Device('opc:')
    aeth_dev_epics = epics.Device('aeth:')
    sniffer_dev_epics = epics.Device('sniffer:')
    
    # set an active object
    # read config file and send to logger object
    with open('../config/config.yaml') as file:
        config_data = yaml.load(file, Loader=yaml.FullLoader)
        
    logger = LOGGER(config_data, opc_dev_epics, aeth_dev_epics, sniffer_dev_epics, logger_dev_epics)
    logger.live_trace = True
    #logger.live_spy = True
    time.sleep(0.1)

    logger_dev_epics.add_callback('enable', on_logger_enable)
    logger_dev_epics.add_callback('save_interval', on_save_interval_value_change)
    logger_dev_epics.add_callback('project_name', on_change_project_name)
    logger_dev_epics.add_callback('save_opc', on_change_save_opc)
    logger_dev_epics.add_callback('save_sniffer', on_change_save_sniffer)
    logger_dev_epics.add_callback('save_aeth', on_change_save_aeth)
                                
    opc_dev_epics.add_callback('data_ready', on_opc_data_ready)
    aeth_dev_epics.add_callback('data_ready', on_aeth_data_ready)
    sniffer_dev_epics.add_callback('data_ready', on_sniffer_data_ready)

    save_interval_PV = epics.PV('logger:save_interval')
    
    logger.start_at(LOGGER_DISABLED)

            
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    '''
    logger.establish_comm()
    logger.read_data_from_logger()
    logger.set_fan(True)
    logger.set_fan(False)
    logger.set_laser(True)
    logger.set_laser(False)
    '''
