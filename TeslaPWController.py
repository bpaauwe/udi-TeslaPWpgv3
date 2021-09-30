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
        super(TeslaPWController, self).__init__(polyglot, primary, address, name)
        self.poly = polyglot

        LOGGER.info('_init_ Tesla Power Wall Controller - 1')
        self.ISYforced = False
        self.name = 'Tesla PowerWall Info'
        self.primary = primary
        self.address = address

        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.LOGLEVEL, self.handleLevelChange)
        self.poly.subscribe(self.poly.CUSTOMPARAMS, self.handleParams)
        self.poly.subscribe(self.poly.POLL, self.systemPoll)

        self.Parameters = Custom(polyglot, 'customparams')
        self.Notices = Custom(polyglot, 'notices')
       
        #self.poly.ready()
        #self.poly.addNode(self)
 
        LOGGER.debug('self.address : ' + str(self.address))
        LOGGER.debug('self.name :' + str(self.name))
        self.hb = 0
        #if not(PG_CLOUD_ONLY):
        
        #self.drivers = []
        #LOGGER.debug('MAIN ADDING DRIVER' + str(self.drivers))
        self.nodeDefineDone = False

        LOGGER.debug('Controller init DONE')
        self.longPollCountMissed = 0
        
        self.defaultParams = {  'CLOUD':  { } ,
                                'LOCAL':  { },
                            }   

        self.poly.ready()
        self.poly.addNode(self)


    def start(self):
       
        LOGGER.debug('start')
        #self.poly.setCustomParamsDoc()
        self.Notices['start'] = 'Check Configuration to make sure all relevant parameters are set'
        #self.poly.Notices.clear()
        #self.poly.Notices['start'] = 'Check CONFIG to make sure all relevant paraeters are set'
        self.cloudAccess = False
        self.localAccess = False
   
        # Wait for self.Parameters['ACCESS'] to be updated
        if 'ACCESS' in self.Parameters:
            if self.Parameters['ACCESS']  == 'LOCAL/CLOUD/BOTH':
                self.Notices['ACCESS'] = 'access must be set to LOCAL CLOUD or BOTH'
                LOGGER.debug('ACCESS must be set ')
                self.stop()
        else:
            self.checkParameters()
           
        
        if self.Parameters['ACCESS'] == 'BOTH' or self.Parameters['ACCESS'] == 'CLOUD':
            # wait for user to set parameters
            allKeysSet = True
            for keys in self.defaultParams['CLOUD']:
                if self.Parameters[keys] ==  self.defaultParams['CLOUD'][keys]:
                    allKeysSet = False
                    self.Notices[keys] =  str(keys) + 'not set'
            if not allKeysSet:
                 LOGGER.debug('Not all CLOUD parameters are specified' )
                 self.checkParameters()
                 self.stop()
            else:
                self.cloudAccess = True
            # All cloud keys defined

        if  self.Parameters['ACCESS'] == 'BOTH' or self.Parameters['ACCESS'] == 'LOCAL':
            allKeysSet = True
            for keys in self.defaultParams['LOCAL']:
                if self.Parameters[keys]==  self.defaultParams['LOCAL'][keys]:
                    allKeysSet = False
                    self.Notices[keys] =  str(keys) + 'not set'
            if not allKeysSet:
                 LOGGER.debug('Not all LOCAL parameters are specified' )
                 self.checkParameters()
                 self.stop()
            else:
                self.localAccess = True
            #all local keys defined


        LOGGER.debug('starting Login process')
        try:
            self.TPW = tesla_info(self.name, self.address, self.Parameters['ACCESS'])
            #self.poly.Notices.clear()
            if self.localAccess:
                self.TPW.loginLocal(self.Parameters['LOCAL_USER_EMAIL'], self.Parameters['LOCAL_USER_PASSWORD'], self.Parameters['IP_ADDRESS'])
            if self.cloudAccess:
                self.TPW.loginCloud(self.Parameters['CLOUD_USER_EMAIL'], self.Parameters['CLOUD_USER_PASSWORD'], self.Parameters['CAPTCHA_APIKEY'])
                self.TPW.teslaCloudConnect()

            self.TPW.teslaInitializeData()
            self.TPW.pollSystemData('all')          
            self.ISYparams = self.TPW.supportedParamters(self.address)
            #LOGGER.debug( self.ISYparams)
            self.ISYcriticalParams = self.TPW.criticalParamters(self.address)

            if self.Parameters['LOGFILE'] == 'ENABLED':
                self.TPW.createLogFile(self.logFile)
            
                     
            LOGGER.info('Creating Nodes')

            self.ISYparams = self.TPW.supportedParamters(self.address)
            self.ISYcriticalParams = self.TPW.criticalParamters(self.address)
            '''
            LOGGER.debug(self.ISYparams)
            for key in self.ISYparams:
                info = self.ISYparams[key]
                if info != {}:
                    value = self.TPW.getISYvalue(key, self.address)
                    LOGGER.debug('Controller driver' + str(key)+ ' value:' + str(value) + ' uom:' + str(info['uom']) )
                    self.drivers.append({'driver':key, 'value':value, 'uom':info['uom'] })
            LOGGER.debug('Drivers:')        
            LOGGER.debug(self.drivers)
            '''
            self.poly.updateProfile()
            self.poly.Notices.clear()

            '''
            nodeList = self.TPW.getNodeIdList()
            for node in nodeList:
                name = self.TPW.getNodeName(node)
                LOGGER.debug('Adding Node(node, name, address) ' + str(node) + ' , '+ str(name) + ' , '+str(self.address))
                if node == self.TPW.getSetupNodeID():  
                    setupNode = teslaPWSetupNode((self.poly, self.address, node, name, self.TPW))
                    self.poly.addNode(setupNode)
                    #self.poly.addNode(teslaPWSetupNode(self.poly, self.address, node, name, self.TPW))
                    #self.addNode(teslaPWSetupNode(self,self.address, node, name))
                if node == self.TPW.getStatusNodeID():    
                    ##self.addNode(teslaPWStatusNode(self,self.address, node, name))
                    ctrlNode = teslaPWStatusNode(self.poly, self.address, node, name, self.TPW)
                    self.poly.addNode(ctrlNode)
                    #self.poly.addNode(teslaPWStatusNode(self.poly, self.address, node, name, self.TPW))
            '''
            LOGGER.debug('Node installation complete')
            self.nodeDefineDone = True
            LOGGER.debug('updateISYdrivers')
            self.updateISYdrivers('all')
            

            #self.longPoll() # Update all drivers

        except Exception as e:
            LOGGER.error('Exception Controller start: '+ str(e))
            LOGGER.info('Did not connect to power wall')
            self.stop()
        LOGGER.debug ('Controler - start done')

    def handleLevelChange(self, level):
        LOGGER.info('New log level: {}'.format(level))

    def handleParams (self, userParam ):
        LOGGER.debug('handleParams')
        self.Parameters.load(userParam)
        
        
    def checkParameters(self):
        if self.Parameters['ACCESS'] is None:
            self.Parameters['ACCESS'] = 'LOCAL/CLOUD/BOTH'
             
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
       
    #def handleNotifications(self):
        

    def stop(self):
        #self.removeNoticesAll()
        if self.TPW:
            self.TPW.disconnectTPW()
        self.setDriver('ST', 0 )
        LOGGER.debug('stop - Cleaning up')


    def heartbeat(self):
        LOGGER.debug('heartbeat: ' + str(self.hb))
        
        if self.hb == 0:
            self.reportCmd('DON',2)
            self.hb = 1
        else:
            self.reportCmd('DOF',2)
            self.hb = 0
        
    def systemPoll(self, pollList):
        LOGGER.debug('systemPoll')
        if 'longPoll' in pollList:
            self.longPoll()
        elif 'shortPoll' in pollList:
            self.shortPoll()


    def shortPoll(self):
        LOGGER.info('Tesla Power Wall Controller shortPoll')
        if self.nodeDefineDone:
            self.heartbeat()    
            if self.TPW.pollSystemData('critical'):
                self.updateISYdrivers('critical')
                #self.reportDrivers()
                self.nodes = self.poly.getNodes()
                for node in self.nodes:
                    LOGGER.debug('Node : ' + node)
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
                
                self.nodes = self.poly.getNodes()
                for node in self.nodes:
                    LOGGER.debug('Node : ' + node)
                    if node != self.address:
                        self.nodes[node].longPoll()
            else:
                LOGGER.error ('Problem polling data from Tesla system')
        else:
            LOGGER.info('Waiting for system/nodes to get created')
        
    #Need to update to use variables 
    def updateISYdrivers(self, level):
        LOGGER.debug('System updateISYdrivers - ' + str(level))       
        if level == 'all':
            value = self.TPW.getISYvalue('GV2', self.address)
            if value == 0:
               self.longPollCountMissed = self.longPollCountMissed + 1
            else:
               self.longPollCountMissed = 0
            self.setDriver('GV2', value )
            self.setDriver('GV3', self.longPollCountMissed)     
            LOGGER.debug('CTRL Update ISY drivers : GV2  value:' + str(value) )
            LOGGER.debug('CTRL Update ISY drivers : GV3  value:' + str(self.longPollCountMissed) )
        elif level == 'critical':
            value = self.TPW.getISYvalue('GV2', self.address)
            self.setDriver('GV2', value)   
            LOGGER.debug('CTRL Update ISY drivers : GV2  value:' + str(value) )
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
    drivers = [{'driver': 'ST', 'value':0, 'uom':2}, {'driver': 'GV2', 'value':0, 'uom':25}, {'driver': 'GV3', 'value':0, 'uom':71}]
    '''
    drivers= [{'driver': 'ST', 'value':0, 'uom':2},
              {'driver': 'GV3', 'value':0, 'uom':25},

              
              {'driver': 'GV2', 'value':0, 'uom':25}]
    '''

if __name__ == "__main__":
    try:
        #LOGGER.info('Starting Tesla Power Wall Controller')
        polyglot = udi_interface.Interface([])
        polyglot.start()
        TeslaPWController(polyglot, 'controller', 'controller', 'TeslaPowerWall')
        polyglot.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
