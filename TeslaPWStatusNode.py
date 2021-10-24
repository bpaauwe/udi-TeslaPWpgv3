#!/usr/bin/env python3
PG_CLOUD_ONLY = False


import udi_interface


#from os import truncate
import sys
import TeslaInfo

LOGGER = udi_interface.LOGGER
               
class teslaPWStatusNode(udi_interface.Node):

    def __init__(self, polyglot, primary, address, name, TPW):
        super(teslaPWStatusNode, self).__init__(polyglot, primary, address, name)
        LOGGER.info('_init_ Tesla Power Wall Status Node')
        self.ISYforced = False
        self.TPW = TPW
        self.address = address 
        self.name = name
        self.hb = 0

        polyglot.subscribe(polyglot.START, self.start, address)
        
    def start(self):                
        LOGGER.debug('Start Tesla Power Wall Status Node')  
        self.updateISYdrivers('all')

    def stop(self):
        LOGGER.debug('stop - Cleaning up')
    
    def updateISYdrivers(self, level):
        LOGGER.debug('StatusNode updateISYdrivers')
        self.setDriver('GV1', self.TPW.getTPW_chargeLevel())
        self.setDriver('GV2', self.TPW.getTPW_operationMode())
        self.setDriver('GV3', self.TPW.getTPW_gridStatus())
        self.setDriver('GV4', self.TPW.getTPW_onLine())
        self.setDriver('GV5', self.TPW.getTPW_gridServiceActive())
        self.setDriver('GV6', self.TPW.getTPW_batterySupply())
        self.setDriver('GV9', self.TPW.getTPW_gridSupply())
        self.setDriver('GV12', self.TPW.getTPW_load())

        if level == 'all':
            self.setDriver('GV7', self.TPW.getTPW_daysBattery())
            self.setDriver('GV8', self.TPW.getTPW_yesterdayBattery())
            self.setDriver('GV10', self.TPW.getTPW_daysGrid())
            self.setDriver('GV11', self.TPW.getTPW_yesterdayGrid())
            self.setDriver('GV13', self.TPW.getTPW_daysConsumption())
            self.setDriver('GV14', self.TPW.getTPW_yesterdayConsumption())
            self.setDriver('GV15', self.TPW.getTPW_daysGeneration())
            self.setDriver('GV16', self.TPW.getTPW_yesterdayGeneration())
            self.setDriver('GV17', self.TPW.getTPW_daysGridServicesUse())
            self.setDriver('GV18', self.TPW.getTPW_yesterdayGridServicesUse())


    def ISYupdate (self, command):
        LOGGER.debug('ISY-update called')
        if self.TPW.pollSystemData('all'):
            self.updateISYdrivers('all')
            #self.reportDrivers()
 

    id = 'pwstatus'
    commands = { 'UPDATE': ISYupdate, 
                }


    drivers = [
            {'driver': 'GV1', 'value': 0, 'uom': 51},  #battery level
            {'driver': 'GV2', 'value': 0, 'uom': 25},  #mode
            {'driver': 'GV3', 'value': 0, 'uom': 25},  #grid status
            {'driver': 'GV4', 'value': 0, 'uom': 25},  #on/off line
            {'driver': 'GV5', 'value': 0, 'uom': 25},  #grid services
            {'driver': 'GV6', 'value': 0, 'uom': 33},  #battery supply
            {'driver': 'GV7', 'value': 0, 'uom': 33},  #battery today
            {'driver': 'GV8', 'value': 0, 'uom': 33},  #battery yesterday
            {'driver': 'GV9', 'value': 0, 'uom': 33},  #grid supply
            {'driver': 'GV10', 'value': 0, 'uom': 33}, #grid today
            {'driver': 'GV11', 'value': 0, 'uom': 33}, #grid yesterday
            {'driver': 'GV12', 'value': 0, 'uom': 33}, #load
            {'driver': 'GV13', 'value': 0, 'uom': 33}, #consumption today
            {'driver': 'GV14', 'value': 0, 'uom': 33}, #consumption yesterday
            {'driver': 'GV15', 'value': 0, 'uom': 33}, #generation today
            {'driver': 'GV16', 'value': 0, 'uom': 33}, #generation yesterday
            {'driver': 'GV17', 'value': 0, 'uom': 33}, #grid service today
            {'driver': 'GV18', 'value': 0, 'uom': 33}, #grid service yesterday
            ]


