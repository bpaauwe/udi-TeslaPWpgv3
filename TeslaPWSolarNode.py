#!/usr/bin/env python3
PG_CLOUD_ONLY = False


import udi_interface


#from os import truncate
import sys
import TeslaInfo
import ISYprofile

LOGGER = udi_interface.LOGGER
               
class teslaPWSolarNode(udi_interface.Node):

    def __init__(self, polyglot, primary, address, name, TPW):
        super(teslaPWSolarNode, self).__init__(polyglot, primary, address, name)
        LOGGER.info('_init_ Tesla Power Wall Status Node')
        self.ISYforced = False
        self.TPW = TPW
        self.address = address 
        self.name = name
        self.hb = 0

        polyglot.subscribe(polyglot.START, self.start, address)
        
    def start(self):                
        LOGGER.debug('Start Tesla Power Wall Solar Node')  
        self.updateISYdrivers('all')

    def stop(self):
        LOGGER.debug('stop - Cleaning up')
    
    def updateISYdrivers(self, level):
        LOGGER.debug('SolarNode updateISYdrivers')
        self.setDriver('GV1', self.TPW.getTPW_solarSupply())

        if level == 'all':
            self.setDriver('GV2', self.TPW.getTPW_daysSolar())
            self.setDriver('GV3', self.TPW.getTPW_yesterdaySolar())


    def ISYupdate (self, command):
        LOGGER.debug('ISY-update called')
        if self.TPW.pollSystemData('all'):
            self.updateISYdrivers('all')
            #self.reportDrivers()
 

    commands = { 'UPDATE': ISYupdate, 
                }


    drivers = [
            {'driver': 'GV1', 'value': 0, 'uom': 33},  #Current solar supply
            {'driver': 'GV2', 'value': 0, 'uom': 33},  #solar power today
            {'driver': 'GV3', 'value': 0, 'uom': 33},  #solar power yesterday
            ]


