#!/usr/bin/env python3
PG_CLOUD_ONLY = False

import udi_interface


#from os import truncate
import sys
import TeslaInfo
import ISYprofile

LOGGER = udi_interface.LOGGER
               
class teslaPWSetupNode(udi_interface.Node):

    def __init__(self, polyglot, primary, address, name, TPW):
        super(teslaPWSetupNode, self).__init__(polyglot, primary, address, name)

        LOGGER.info('_init_ Tesla Power Wall setup Node')
        self.ISYforced = False
        self.TPW = TPW
        self.address = address 
        self.id = address
        self.name = name
        self.hb = 0

        self.poly.subscribe(self.poly.START, self.start, address)
        

    def start(self):                
        LOGGER.debug('Start Tesla Power Wall Setup Node')  
        self.updateISYdrivers('all')

    def stop(self):
        LOGGER.debug('stop - Cleaning up')

    def updateISYdrivers(self, level):
        LOGGER.debug('Node updateISYdrivers')
        self.setDriver('GV1', self.TPW.getTPW_backoffLevel())
        self.setDriver('GV2', self.TPW.getTPW_operationMode())
        self.setDriver('GV3', self.TPW.getTPW_stormMode())
        self.setDriver('GV4', self.TPW.getTPW_touMode())
        if level == 'all':
            self.setDriver('GV5', self.TPW.getTPW_getTouData('weekend', 'off_peak', 'start'))
            self.setDriver('GV6', self.TPW.getTPW_getTouData('weekend', 'off_peak', 'stop'))
            self.setDriver('GV7', self.TPW.getTPW_getTouData('weekend', 'peak', 'start'))
            self.setDriver('GV8', self.TPW.getTPW_getTouData('weekend', 'peak', 'stop'))
            self.setDriver('GV9', self.TPW.getTPW_getTouData('weekday', 'off_peak', 'start'))
            self.setDriver('GV10', self.TPW.getTPW_getTouData('weekday', 'off_peak', 'stop'))
            self.setDriver('GV11', self.TPW.getTPW_getTouData('weekday', 'peak', 'start'))
            self.setDriver('GV12', self.TPW.getTPW_getTouData('weekday', 'peak', 'stop'))
        LOGGER.debug('updateISYdrivers - setupnode DONE')



    def setStormMode(self, command):
        LOGGER.debug('setStormMode')
        value = int(command.get('value'))
        self.TPW.setTPW_stormMode(value)
        self.setDriver('GV3', value)
        
    def setOperatingMode(self, command):
        LOGGER.debug('setOperatingMode')
        value = int(command.get('value'))
        self.TPW.setTPW_operationMode(value)
        self.setDriver('GV2', value)
    
    def setBackupPercent(self, command):
        LOGGER.debug('setBackupPercent')
        value = float(command.get('value'))
        self.TPW.setTPW_backoffLevel(value)
        self.setDriver('GV1', value)

    def setTOUmode(self, command):
        LOGGER.debug('setTOUmode')
        value = int(command.get('value'))
        self.TPW.setTPW_touMode(value)
        self.setDriver('GV4', value)

    def setWeekendOffpeakStart(self, command):
        LOGGER.debug('setWeekendOffpeakStart')
        value = int(command.get('value'))
        self.TPW.setTPW_updateTouSchedule('off_peak', 'weekend', 'start', value)
        self.setDriver('GV5', value)

    def setWeekendOffpeakEnd(self, command):
        LOGGER.debug('setWeekendOffpeakEnd')
        value = int(command.get('value'))
        self.TPW.setTPW_updateTouSchedule('off_peak', 'weekend', 'end', value)
        self.setDriver('GV6', value)

    def setWeekendPeakStart(self, command):
        LOGGER.debug('setWeekendPeakStart')
        value = int(command.get('value'))
        self.TPW.setTPW_updateTouSchedule('peak', 'weekend', 'start', value)
        self.setDriver('GV7', value)

    def setWeekendPeakEnd(self, command):
        LOGGER.debug('setWeekendPeakEnd')
        value = int(command.get('value'))
        self.TPW.setTPW_updateTouSchedule('peak', 'weekend', 'end', value)
        self.setDriver('GV8', value)

    def setWeekOffpeakStart(self, command):
        LOGGER.debug('setWeekOffpeakStart')
        value = int(command.get('value'))
        self.TPW.setTPW_updateTouSchedule('off_peak', 'week', 'start', value)
        self.setDriver('GV9', value)

    def setWeekOffpeakEnd(self, command):
        LOGGER.debug('setWeekOffpeakEnd')
        value = int(command.get('value'))
        self.TPW.setTPW_updateTouSchedule('off_peak', 'week', 'end', value)
        self.setDriver('GV10', value)

    def setWeekPeakStart(self, command):
        LOGGER.debug('setWeekPeakStart')
        value = int(command.get('value'))
        self.TPW.setTPW_updateTouSchedule('peak', 'week', 'start', value)
        self.setDriver('GV11', value)

    def setWeekPeakEnd(self, command):
        LOGGER.debug('setWeekPeakEnd')
        value = int(command.get('value'))
        self.TPW.setTPW_updateTouSchedule('peak', 'week', 'end', value)
        self.setDriver('GV12', value)


    def ISYupdate (self, command):
        LOGGER.debug('ISY-update called  Setup Node')
        if self.TPW.pollSystemData('all'):
            self.updateISYdrivers('all')
            #self.reportDrivers()
 

    id = 'pwsetup'
    commands = { 'UPDATE': ISYupdate
                ,'BACKUP_PCT' : setBackupPercent
                ,'STORM_MODE' :setStormMode
                ,'OP_MODE': setOperatingMode
                ,'TOU_MODE':setTOUmode
                ,'WE_O_PEAK_START': setWeekendOffpeakStart
                ,'WE_O_PEAK_END':setWeekendOffpeakEnd
                ,'WE_PEAK_START':setWeekendPeakStart
                ,'WE_PEAK_END':setWeekendPeakEnd
                ,'WK_O_PEAK_START':setWeekOffpeakStart
                ,'WK_O_PEAK_END':setWeekOffpeakEnd
                ,'WK_PEAK_START':setWeekPeakStart
                ,'WK_PEAK_END':setWeekPeakEnd

                }

    drivers = [
            {'driver': 'GV1', 'value': 0, 'uom': 51},  #backup reserve
            {'driver': 'GV2', 'value': 0, 'uom': 25},  #operating mode
            {'driver': 'GV3', 'value': 0, 'uom': 25},  #storm mode
            {'driver': 'GV4', 'value': 0, 'uom': 25},  #time of use mode
            {'driver': 'GV5', 'value': 0, 'uom': 58},  #weekend off start
            {'driver': 'GV6', 'value': 0, 'uom': 58},  #weekend off end
            {'driver': 'GV7', 'value': 0, 'uom': 58},  #weekend on start
            {'driver': 'GV8', 'value': 0, 'uom': 58},  #weekend on end
            {'driver': 'GV9', 'value': 0, 'uom': 58},  #weekday off start
            {'driver': 'GV10', 'value': 0, 'uom': 58}, #weekday off end
            {'driver': 'GV11', 'value': 0, 'uom': 58}, #weekday on start 
            {'driver': 'GV12', 'value': 0, 'uom': 58}, #weekday on end 
            ]

        

