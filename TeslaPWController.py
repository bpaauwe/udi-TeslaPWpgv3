#!/usr/bin/env python3
PG_CLOUD_ONLY = False

import udi_interface


#from os import truncate
import sys
import time 
from  TeslaInfo import tesla_info
from TeslaPWSetupNode import teslaPWSetupNode
from TeslaPWStatusNode import teslaPWStatusNode


LOGGER = udi_interface.LOGGER
Custom = udi_interface.Custom

class TeslaPWController(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name):
        super().__init__(polyglot, primary, address, name)
        self.poly = polyglot

        LOGGER.info('_init_ Tesla Power Wall Controller - 1')
        self.ISYforced = False
        self.name = 'Tesla PowerWall Info'
        self.primary = primary
        self.address = address

        self.poly.subscribe(self.poly.START, self.start, address)

        self.Parameters = Custom(polyglot, 'customparams')
        self.poly.subscribe(self.poly.CUSTOMPARAMS, self.handleParams)

        self.Notices = Custom(polyglot, 'notices')
        #self.poly.subscribe(self.poly.Notices, self.notifications)


        #self.poly.subscribe(self.poly.notices, self.notifications)
        
        self.poly.subscribe(self.poly.POLL, self.systemPoll)

        self.poly.ready()
        self.poly.addNode(self)
 
        LOGGER.debug('self.address : ' + str(self.address))
        LOGGER.debug('self.name :' + str(self.name))
        self.hb = 0
        #if not(PG_CLOUD_ONLY):
        #self.drivers = []
        #LOGGER.debug('MAIN ADDING DRIVER' + str(self.drivers))
        self.nodeDefineDone = False
        #self.setDriver('ST', 0, report = True, force = True)
        #self.setDriver('GV2', 0, report = True, force = True)
        LOGGER.debug('Controller init DONE')
        self.longPollCountMissed = 0
        
        self.defaultParams = {   'CLOUD':  { } ,
                                'LOCAL':  { },
                            }   

    def start(self):
        LOGGER.debug('start')
        #self.poly.Notices.clear()
        #self.poly.Notices['start'] = 'Check CONFIG to make sure all relevant paraeters are set'
        self.cloudAccess = False
        self.localAccess = False

      

        # Wait for self.Parameters['access'] to be updated
        while self.Parameters['access']  == 'LOCAL/CLOUD/BOTH':
            time.sleep(2)
            LOGGER.debug('Waiting for Access to be set ')
       
        
        if self.Parameters['access'] == 'BOTH' or self.Parameters['access'] == 'CLOUD':
            # wait for user to set parameters
            allKeysSet = False
            while not(allKeysSet):
                allKeysSet = True
                for keys in self.defaultParams['CLOUD']:
                    if self.Parameters[keys] ==  self.defaultParams['CLOUD'][keys]:
                        allKeysSet = False
                time.sleep(2)
                LOGGER.debug('Waiting for CLOUD parameters to get set' )
            self.cloudAccess = True
            # All cloud keys defined

        if  self.Parameters['access'] == 'BOTH' or self.Parameters['access'] == 'LOCAL':
            allKeysSet = False
            while not(allKeysSet):
                allKeysSet = True
                for keys in self.defaultParams['LOCAL']:
                    if self.Parameters[keys]==  self.defaultParams['LOCAL'][keys]:
                        allKeysSet = False
                time.sleep(2)
                LOGGER.debug('Waiting for LOCAL parameters to get set' )
            self.localAccess = True
            #all local keys defined
        

        LOGGER.debug('starting Login process')
        try:
            self.TPW = tesla_info(self.name, self.address, self.Parameters['access'])
            #self.poly.Notices.clear()
            if self.localAccess:
                self.TPW.loginLocal(self.Parameters['LOCAL_USER_EMAIL'], self.Parameters['LOCAL_USER_PASSWORD'], self.Parameters['IP_ADDRESS'])
            if self.cloudAccess:
                self.TPW.loginCloud(self.Parameters['CLOUD_USER_EMAIL'], self.Parameters['CLOUD_USER_PASSWORD'], self.Parameters['CAPTCHA_APIKEY'])
                self.TPW.teslaCloudConnect()

            self.TPW.teslaInitializeData()
            self.TPW.pollSystemData('all')          
     
            if self.Parameters['LOGFILE'] == 'ENABLED':
                self.TPW.createLogFile(self.logFile)
            
            self.poly.updateProfile()
            self.poly.Notices.clear()
            
            LOGGER.info('Creating Nodes')
            nodeList = self.TPW.getNodeIdList()
            
            for node in nodeList:
                name = self.TPW.getNodeName(node)
                LOGGER.debug('Setup Node(node, name, address) ' + str(node) + ' , '+ str(name) + ' , '+str(self.address))
                if node == self.TPW.getSetupNodeID():  
                    self.poly.addNode(teslaPWSetupNode(self.poly, self.address, node, name))
                    #self.addNode(teslaPWSetupNode(self,self.address, node, name))
                if node == self.TPW.getStatusNodeID():    
                    ##self.addNode(teslaPWStatusNode(self,self.address, node, name))
                    self.poly.addNode(teslaPWStatusNode(self.poly, self.address, node, name))
            LOGGER.debug('Node installation complete')
            self.nodeDefineDone = True
            LOGGER.debug('updateISYdrivers')
            self.updateISYdrivers('all')
            self.longPoll() # Update all drivers

        except Exception as e:
            LOGGER.error('Exception Controller start: '+ str(e))
            LOGGER.info('Did not connect to power wall')
            self.stop()
        LOGGER.debug ('Controler - start done')

    def handleParams (self, userParam ):
        self.Parameters.load(userParam)

        self.poly.Notices['start'] = 'Check CONFIG to make sure all relevant paraeters are set'
         
        if self.Parameters['access'] is None:
            self.Parameters['access'] = 'LOCAL/CLOUD/BOTH'
             
        if self.Parameters['LOCAL_USER_EMAIL'] is None:
            self.Parameters['LOCAL_USER_EMAIL'] = 'me@localPowerwall.com'
            self.defaultParams['LOCAL']['LOCAL_USER_EMAIL'] =  'me@localPowerwall.com'

        if self.Parameters['LOCAL_USER_PASSWORD'] is None:
            self.Parameters['LOCAL_USER_PASSWORD'] = 'XXXXXXXX'
            self.defaultParams['LOCAL']['LOCAL_USER_EMAIL'] =  'XXXXXXXX'

        if self.Parameters['IP_ADDRESS'] is None:
            self.Parameters['IP_ADDRESS'] = '192.168.1.xxx'
            self.defaultParams['LOCAL']['IP_ADDRESS'] =  '192.168.1.xxx'

        if self.Parameters['CLOUD_USER_EMAIL'] is None:
            self.Parameters['CLOUD_USER_EMAIL'] = 'me@myTeslaCloudemail.com'
            self.defaultParams['CLOUD']['CLOUD_USER_EMAIL'] =  'me@myTeslaCloudemail.com'

        if self.Parameters['CLOUD_USER_PASSWORD'] is None:
            self.Parameters['CLOUD_USER_PASSWORD'] = 'XXXXXXXX'
            self.defaultParams['CLOUD']['CLOUD_USER_PASSWORD'] =  'XXXXXXXX'

        if self.Parameters['CAPTCHA_APIKEY'] is None:
            self.Parameters['CAPTCHA_APIKEY'] = 'api key to enable AUTO captcha solver'
            self.defaultParams['CLOUD']['CAPTCHA_APIKEY'] =  'api key to enable AUTO captcha solver'

        if self.Parameters['LOGFILE'] is None:
            self.Parameters['LOGFILE'] = 'DISABLED'
       


    
    def stop(self):
        #self.removeNoticesAll()
        if self.TPW:
            self.TPW.disconnectTPW()
        
        LOGGER.debug('stop - Cleaning up')

    def parameterHandler(self, params):
        self.Parameters.load(params)

    def heartbeat(self):
        LOGGER.debug('heartbeat: ' + str(self.hb))
        
        if self.hb == 0:
            self.reportCmd('DON',2)
            self.hb = 1
        else:
            self.reportCmd('DOF',2)
            self.hb = 0
        
    def systemPoll(self, pollList):
        if 'shortPoll' in pollList:
            self.shortPoll()
        if 'longPoll' in pollList:
            self.longPoll()


    def shortPoll(self):
        LOGGER.info('Tesla Power Wall Controller shortPoll')
        if self.nodeDefineDone:
            self.heartbeat()    
            if self.TPW.pollSystemData('critical'):
                self.updateISYdrivers('critical')
                #self.reportDrivers()
                for node in self.nodes:
                    #LOGGER.debug('Node : ' + node)
                    if node != self.address:
                        self.nodes[node].shortPoll()
            else:
                LOGGER.info('Problem polling data from Tesla system') 
        else:
            LOGGER.info('Waiting for system/nodes to get created')
        

    def longPoll(self):
        LOGGER.info('Tesla Power Wall  Controller longPoll')
        if self.nodeDefineDone:
            #self.heartbeat()

            if self.TPW.pollSystemData('all'):
                self.updateISYdrivers('all')
                #self.reportDrivers() 
                
                for node in self.nodes:
                    #LOGGER.debug('Node : ' + node)
                    if node != self.address :
                        self.nodes[node].longPoll()
            else:
                LOGGER.error ('Problem polling data from Tesla system')
        else:
            LOGGER.info('Waiting for system/nodes to get created')
        

    def updateISYdrivers(self, level):
        LOGGER.debug('System updateISYdrivers - ' + str(level))
        value = 1
        if level == 'all':
            value = self.TPW.getISYvalue('ST', self.address)
            self.setDriver('ST',value, report = True, force = True) 
            #LOGGER.debug('Update ISY drivers :' + str('ST')+ '  value:' + str(value) )
            if value == 0:
                self.longPollCountMissed = self.longPollCountMissed + 1
            else:
                self.longPollCountMissed = 0
            self.setDriver('GV2', int(self.longPollCountMissed), report = True, force = True)     
            LOGGER.debug('Update ISY drivers :' + str('GV2')+ '  value:' + str(self.longPollCountMissed) )
        elif level == 'critical':
            value = self.TPW.getISYvalue('ST', self.address)
            self.setDriver('ST', value, report = True, force = True)  
            LOGGER.debug('Update ISY drivers :' + str('ST')+ '  value:' + str(value) )   
            if value == 0:
                self.longPollCountMissed = self.longPollCountMissed + 1
            else:
                self.longPollCountMissed = 0
            self.setDriver('GV2', int(self.longPollCountMissed), report = True, force = True)   
            LOGGER.debug('Update ISY drivers :' + str('GV2')+ '  value:' + str(self.longPollCountMissed) )
        else:
            LOGGER.error('Wrong parameter passed: ' + str(level))
 


    def ISYupdate (self, command):
        LOGGER.debug('ISY-update called')
        if self.TPW.pollSystemData('all'):
            self.updateISYdrivers('all')
            #self.reportDrivers()
            for node in self.nodes:
                #LOGGER.debug('Node : ' + node)
                if node != self.address :
                    self.nodes[node].longPoll()
 
    commands = { 'UPDATE': ISYupdate }

    #if PG_CLOUD_ONLY:
    drivers= [{'driver': 'ST', 'value':0, 'uom':2},
                {'driver': 'GV2', 'value':0, 'uom':107}]


if __name__ == "__main__":
    try:
        #LOGGER.info('Starting Tesla Power Wall Controller')
        polyglot = udi_interface.Interface([])
        polyglot.start()
        TeslaPWController(polyglot, 'controller', 'controller', 'TeslaPowerWall')
        polyglot.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
