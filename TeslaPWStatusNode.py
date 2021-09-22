#!/usr/bin/env python3
PG_CLOUD_ONLY = False


import udi_interface


#from os import truncate
import sys
import TeslaInfo
import ISYprofile

LOGGER = udi_interface.LOGGER
               
class teslaPWStatusNode(udi_interface.Node):

    def __init__(self, polyglot, primary, address, name, TPW):
        super(teslaPWStatusNode, self).__init__(polyglot, primary, address, name)

        LOGGER.info('_init_ Tesla Power Wall Status Node')
        self.ISYforced = False
        self.TPW = TPW
        self.address = address 
        self.id = address
        self.name = name
        self.hb = 0


        self.drivers = []
        self.poly.subscribe(self.poly.LOGLEVEL, self.handleLevelChange)
        self.poly.subscribe(self.poly.START, self.start, address)

        
        self.nodeDefineDone = False
        LOGGER.debug('Start Tesla Power Wall Status Node')  

        self.ISYparams = self.TPW.supportedParamters(self.id)
        #LOGGER.debug ('Node = ISYparams :' + str(self.ISYparams))

        self.ISYcriticalParams = self.TPW.criticalParamters(self.id)
        #LOGGER.debug ('Node = ISYcriticalParams :' + str(self.ISYcriticalParams))
    

        for key in self.ISYparams:
            info = self.ISYparams[key]
            #LOGGER.debug(key )
            if info != {}:
                value = self.TPW.getISYvalue(key, self.id)
                LOGGER.debug('StatusNode: driver' + str(key)+ ' value:' + str(value) + ' uom:' + str(info['uom']) )
                self.drivers.append({'driver':key, 'value':value, 'uom':info['uom'] })
        LOGGER.debug( 'Status node init - DONE')


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
        LOGGER.debug('Tesla Power Wall Status Node shortPoll')
        if self.nodeDefineDone:
            self.updateISYdrivers('critical')
        else:
           LOGGER.info('Status Node: waiting for system/nodes to get created')

            
    def longPoll(self):
        #No need to poll data - done by Controller
        LOGGER.debug('Tesla Power Wall  status Node longPoll')
        if self.nodeDefineDone:
           self.updateISYdrivers('all')
           #self.reportDrivers() 
        else:
           LOGGER.info('Status Node: waiting for system/nodes to get created')

    def updateISYdrivers(self, level):
        LOGGER.debug('StatusNode updateISYdrivers')
        params = []
        if level == 'all':
            params = self.ISYparams
            if params:
                for key in params:
                    info = params[key]
                    if info != {}:
                        value = self.TPW.getISYvalue(key, self.id)
                        #LOGGER.debug('Update all ISY drivers :' + str(key)+ ' ' + info['systemVar']+ ' value:' + str(value) )
                        self.setDriver(key, value, report = True, force = True)      
        elif level == 'critical':
            params = self.ISYcriticalParams
            if params:
                for key in params:
                    value = self.TPW.getISYvalue(key, self.id)
                    #LOGGER.debug('Update critical ISY drivers :' + str(key)+ ' value: ' + str(value) )
                    self.setDriver(key, value, report = True, force = True)        

        else:
           LOGGER.error('Wrong parameter passed: ' + str(level))
  
        #LOGGER.debug('updateISYdrivers - Status node DONE')


    def ISYupdate (self, command):
        LOGGER.debug('ISY-update called')
        if self.TPW.pollSystemData('all'):
            self.updateISYdrivers('all')
            #self.reportDrivers()
 

    commands = { 'UPDATE': ISYupdate, 
                }




