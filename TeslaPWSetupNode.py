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

        self.drivers = []
        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.LOGLEVEL, self.handleLevelChange)
        
        self.nodeDefineDone = False
        LOGGER.debug('Start Tesla Power Wall Setup Node')  

        self.ISYparams = self.TPW.supportedParamters(self.id)
        #LOGGER.debug ('Node = ISYparams :' + str(self.ISYparams))

        self.ISYcriticalParams = self.TPW.criticalParamters(self.id)
        #LOGGER.debug ('Node = ISYcriticalParams :' + str(self.ISYcriticalParams))
    

        for key in self.ISYparams:
            info = self.ISYparams[key]

            if info != {}:
                value = self.TPW.getISYvalue(key, self.id)
                LOGGER.debug('SetupNode: driver' + str(key)+ ' value:' + str(value) + ' uom:' + str(info['uom']) )
                self.drivers.append({'driver':key, 'value':value, 'uom':info['uom'] })
        LOGGER.debug( 'Setup node init - DONE')
        LOGGER.debug (self.drivers)
        self.poly.updateProfile()
        self.poly.ready()
        #self.heartbeat()


    def start(self):                
        self.updateISYdrivers('all')
        #self.reportDrivers()
        self.nodeDefineDone = True


    def stop(self):
        LOGGER.debug('stop - Cleaning up')

    
    def handleLevelChange(self, level):
        LOGGER.info('New log level: {}'.format(level))

    def shortPoll(self):
        #No need to poll data - done by Controller
        LOGGER.debug('Tesla Power Wall setupNode shortPoll')
        if self.nodeDefineDone:
            self.updateISYdrivers('critical')
        else:
           LOGGER.info('Setup Node: waiting for system/nodes to get created')

                

    def longPoll(self):
        #No need to poll data - done by Controller
        LOGGER.debug('Tesla Power Wall  sentupNode longPoll')
        if self.nodeDefineDone:
           self.updateISYdrivers('all')
        else:
           LOGGER.info('Setup Node: waiting for system/nodes to get created')

    def updateISYdrivers(self, level):
        LOGGER.debug('Node updateISYdrivers')
        params = []
        if level == 'all':
            params = self.ISYparams
            if params:
                for key in params:
                    info = params[key]
                    if info != {}:
                        value = self.TPW.getISYvalue(key, self.id)
                        LOGGER.debug('SETUP Update ISY drivers :' + str(key)+ ' ' + info['systemVar']+ ' value:' + str(value) )
                        self.setDriver(key, value)      
        elif level == 'critical':
            params = self.ISYcriticalParams
            if params:
                for key in params:
                    value = self.TPW.getISYvalue(key, self.id)
                    LOGGER.debug('SETUP Update ISY drivers :' + str(key)+ ' value: ' + str(value) )
                    self.setDriver(key, value)        

        else:
           LOGGER.debug('Wrong parameter passed: ' + str(level))
        LOGGER.debug('updateISYdrivers - setupnode DONE')



    def setStormMode(self, command):
        LOGGER.debug('setStormMode')
        value = int(command.get('value'))
        self.TPW.setTPW_stormMode(value)
        ISYvar = self.TPW.getStormModeISYVar(self.id)
        self.setDriver(ISYvar, value)
        #self.reportDrivers() 
        
    def setOperatingMode(self, command):
        LOGGER.debug('setOperatingMode')
        value = int(command.get('value'))
        self.TPW.setTPW_operationMode(value)
        ISYvar = self.TPW.getOperatingModeISYVar(self.id)
        self.setDriver(ISYvar, value)
        #self.reportDrivers() 
    
    def setBackupPercent(self, command):
        LOGGER.debug('setBackupPercent')
        value = float(command.get('value'))
        self.TPW.setTPW_backoffLevel(value)
        ISYvar = self.TPW.getBackupPercentISYVar(self.id)
        self.setDriver(ISYvar, value)
        #self.reportDrivers() 

    def setTOUmode(self, command):
        LOGGER.debug('setTOUmode')
        value = int(command.get('value'))
        self.TPW.setTPW_touMode(value)
        ISYvar = self.TPW.getTOUmodeISYVar(self.id)
        self.setDriver(ISYvar, value)
        #self.reportDrivers() 

    def setWeekendOffpeakStart(self, command):
        LOGGER.debug('setWeekendOffpeakStart')
        value = int(command.get('value'))
        self.TPW.setTPW_updateTouSchedule('off_peak', 'weekend', 'start', value)
        ISYvar = self.TPW.getTouWeekendOffpeakStartISYVar(self.id)
        self.setDriver(ISYvar, value)
        #self.reportDrivers() 

    def setWeekendOffpeakEnd(self, command):
        LOGGER.debug('setWeekendOffpeakEnd')
        value = int(command.get('value'))
        self.TPW.setTPW_updateTouSchedule('off_peak', 'weekend', 'end', value)
        ISYvar = self.TPW.getTouWeekendOffpeakEndISYVar(self.id)
        self.setDriver(ISYvar, value)
        #self.reportDrivers() 

    def setWeekendPeakStart(self, command):
        LOGGER.debug('setWeekendPeakStart')
        value = int(command.get('value'))
        self.TPW.setTPW_updateTouSchedule('peak', 'weekend', 'start', value)
        ISYvar = self.TPW.getTouWeekendPeakStartISYVar(self.id)
        self.setDriver(ISYvar, value)
        #self.reportDrivers()       

    def setWeekendPeakEnd(self, command):
        LOGGER.debug('setWeekendPeakEnd')
        value = int(command.get('value'))
        self.TPW.setTPW_updateTouSchedule('peak', 'weekend', 'end', value)
        ISYvar = self.TPW.getTouWeekendPeakEndISYVar(self.id)
        self.setDriver(ISYvar, value)
        #self.reportDrivers()    

    def setWeekOffpeakStart(self, command):
        LOGGER.debug('setWeekOffpeakStart')
        value = int(command.get('value'))
        self.TPW.setTPW_updateTouSchedule('off_peak', 'week', 'start', value)
        ISYvar = self.TPW.getTouWeekOffpeakStartISYVar(self.id)
        self.setDriver(ISYvar, value)
        #self.reportDrivers() 

    def setWeekOffpeakEnd(self, command):
        LOGGER.debug('setWeekOffpeakEnd')
        value = int(command.get('value'))
        self.TPW.setTPW_updateTouSchedule('off_peak', 'week', 'end', value)
        ISYvar = self.TPW.getTouWeekOffpeakEndISYVar(self.id)
        self.setDriver(ISYvar, value)
        #self.reportDrivers() 

    def setWeekPeakStart(self, command):
        LOGGER.debug('setWeekPeakStart')
        value = int(command.get('value'))
        self.TPW.setTPW_updateTouSchedule('peak', 'week', 'start', value)
        ISYvar = self.TPW.getTouWeekPeakStartISYVar(self.id)
        self.setDriver(ISYvar, value)
        #self.reportDrivers()   

    def setWeekPeakEnd(self, command):
        LOGGER.debug('setWeekPeakEnd')
        value = int(command.get('value'))
        self.TPW.setTPW_updateTouSchedule('peak', 'week', 'end', value)
        ISYvar = self.TPW.getTouWeekPeakEndISYVar(self.id)
        self.setDriver(ISYvar, value)
        #self.reportDrivers() 


    def ISYupdate (self, command):
        LOGGER.debug('ISY-update called  Setup Node')
        if self.TPW.pollSystemData('all'):
            self.updateISYdrivers('all')
            #self.reportDrivers()
 

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



        

