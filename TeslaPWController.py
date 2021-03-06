#!/usr/bin/env python3
PG_CLOUD_ONLY = False

import udi_interface


#from os import truncate
import sys
import time 
from  TeslaInfo import tesla_info
from TeslaPWSetupNode import teslaPWSetupNode
from TeslaPWStatusNode import teslaPWStatusNode
from TeslaPWSolarNode import teslaPWSolarNode
from TeslaPWGenNode import teslaPWGenNode


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
        self.cloudAccess = False
        self.localAccess = False
        self.initialized = False

        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.LOGLEVEL, self.handleLevelChange)
        self.poly.subscribe(self.poly.CUSTOMPARAMS, self.handleParams)
        self.poly.subscribe(self.poly.POLL, self.systemPoll)

        self.Parameters = Custom(polyglot, 'customparams')
        self.Notices = Custom(polyglot, 'notices')
       
        LOGGER.debug('self.address : ' + str(self.address))
        LOGGER.debug('self.name :' + str(self.name))
        self.hb = 0
        #if not(PG_CLOUD_ONLY):
        
        self.nodeDefineDone = False
        self.longPollCountMissed = 0

        LOGGER.debug('Controller init DONE')
        
        self.poly.ready()
        self.poly.addNode(self)


    def start(self):
       
        LOGGER.debug('start')

        # Wait for things to initialize....
        while not self.initialized:
            time.sleep(1)

        # Poll for current values (and update drivers)
        self.TPW.pollSystemData('all')          
        self.updateISYdrivers('all')
   

    '''
    This may be called multiple times with different settings as the user
    could be enabling or disabling the various types of access.  So if the
    user changes something, we want to re-initialize.
    '''
    def tesla_initialize(self, local_email, local_password, local_ip, cloud_email, cloud_password, cloud_key):
        LOGGER.debug('starting Login process')
        try:

            self.TPW = tesla_info(self.name, self.address, self.localAccess, self.cloudAccess)
            if self.localAccess:
                LOGGER.debug('Attempting to log in via local auth')
                try:
                    self.TPW.loginLocal(local_email, local_password, local_ip)
                except:
                    LOGGER.error('local authenticated failed.')
                    self.localAccess = False

            if self.cloudAccess:
                self.TPW.loginCloud(cloud_email, cloud_password, cloud_key)
                self.TPW.teslaCloudConnect()

            if not self.localAccess and not self.cloudAccess:
                LOGGER.error('Configuration invalid, initialization aborted.')
                self.poly.Notices['err'] = 'Configuration is not valid, please update configuration.'
                return

            self.TPW.teslaInitializeData()

            if self.Parameters['LOGFILE'] == 'ENABLED':
                self.TPW.createLogFile(self.logFile)
                     
            '''
            node addresses:
               setup node:            pwsetup 'Control Parameters'
               main status node:      pwstatus 'Power Wall Status'
               generator status node: genstatus 'Generator Status'
               solar status node:     solarstatus 'Solar Status'
            '''
            LOGGER.info('Creating Nodes')
            if not self.poly.getNode('pwstatus'):
                node = teslaPWStatusNode(self.poly, self.address, 'pwstatus', 'Power Wall Status', self.TPW)
                self.poly.addNode(node)

            if self.TPW.solarInstalled:
                if not self.poly.getNode('solarstatus'):
                    node = teslaPWSolarNode(self.poly, self.address, 'solarstatus', 'Solar Status', self.TPW)
                    self.poly.addNode(node)
            else:
                self.poly.delNode('solarstatus')

            if self.TPW.generatorInstalled:
                if not self.poly.getNode('genstatus'):
                    node = teslaPWGenNode(self.poly, self.address, 'genstatus', 'Generator Status', self.TPW)
                    self.poly.addNode(node)
            else:
                self.poly.delNode('genstatus')

            if self.cloudAccess:
                if not self.poly.getNode('pwsetup'):
                    node = teslaPWSetupNode(self.poly, self.address, 'pwsetup', 'Control Parameters', self.TPW)
                    self.poly.addNode(node)
            else:
                self.poly.delNode('pwsetup')

            LOGGER.debug('Node installation complete')
            self.nodeDefineDone = True
            self.initialized = True

        except Exception as e:
            LOGGER.error('Exception Controller start: '+ str(e))
            LOGGER.info('Did not connect to power wall')

        LOGGER.debug ('Controller - initialization done')

    def handleLevelChange(self, level):
        LOGGER.info('New log level: {}'.format(level))

    def handleParams (self, userParam ):
        LOGGER.debug('handleParams')
        self.Parameters.load(userParam)
        self.poly.Notices.clear()
        cloud_valid = False
        local_valid = False
        self.localAccess = False
        self.cloudAccess = False

        if 'LOGFILE' in userParam:
            self.logfile = userParam['LOGFILE'].lower()

        if 'LOCAL_USER_EMAIL' in userParam:
            local_email = userParam['LOCAL_USER_EMAIL']
        else:
            self.poly.Notices['lu'] = 'Missing Local User Email parameter'
            local_email = ''

        if 'LOCAL_USER_PASSWORD' in userParam:
            local_password = userParam['LOCAL_USER_PASSWORD']
        else:
            self.poly.Notices['lp'] = 'Missing Local User Password parameter'
            local_password = ''

        if 'LOCAL_IP_ADDRESS' in userParam:
            local_ip = userParam['LOCAL_IP_ADDRESS']
        else:
            self.poly.Notices['ip'] = 'Missing Local IP Address parameter'
            local_ip = ''

        if 'CLOUD_USER_EMAIL' in userParam:
            cloud_email = userParam['CLOUD_USER_EMAIL']
        else:
            self.poly.Notices['cu'] = 'Missing Cloud User Email parameter'
            cloud_email = ''

        if 'CLOUD_USER_PASSWORD' in userParam:
            cloud_password = userParam['CLOUD_USER_PASSWORD']
        else:
            self.poly.Notices['cp'] = 'Missing Cloud User Password parameter'
            cloud_password = ''

        if 'CLOUD_CAPTCHA_APIKEY' in userParam:
            cloud_key = userParam['CLOUD_CAPTCHA_APIKEY']
        else:
            self.poly.Notices['ck'] = 'Missing Cloud Captch API Key parameter'
            cloud_key = ''

        if local_email != '' or local_password != '' or local_ip != '':
            LOGGER.debug('local access true, cfg = {} {} {}'.format(local_email, local_password, local_ip))
            local_valid = True
            if local_email == '':
                self.poly.Notices['lu'] = 'Please enter the local user name'
                local_valid = False
            if local_password == '':
                self.poly.Notices['lp'] = 'Please enter the local user password'
                local_valid = False
            if local_ip == '':
                self.poly.Notices['ip'] = 'Please enter the local IP address'
                local_valid = False


        if cloud_email != '' or cloud_password != '' or cloud_key != '':
            LOGGER.debug('cloud access true, cfg = {} {} {}'.format(cloud_email, cloud_password, cloud_key))
            cloud_valid = True
            if cloud_email == '':
                self.poly.Notices['cu'] = 'Please enter the cloud user name'
                cloud_valid = False
            if cloud_password == '':
                self.poly.Notices['cp'] = 'Please enter the cloud user password'
                cloud_valid = False
            if cloud_key == '':
                self.poly.Notices['ck'] = 'Please enter the cloud captch API key'
                cloud_valid = False

        if local_valid:
            LOGGER.debug('Local access is valid, configure....')
            self.localAccess = True

        if cloud_valid:
            LOGGER.debug('Cloud access is valid, configure....')
            self.cloudAccess = True

        if cloud_valid or local_valid:
            self.tesla_initialize(local_email, local_password, local_ip, cloud_email, cloud_password, cloud_key)

        if not cloud_valid and not local_valid:
            self.poly.Notices['cfg'] = 'Tesla PowerWall NS needs configuration.'

        LOGGER.debug('done with parameter processing')
        
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
                for node in self.poly.nodes():
                    node.updateISYdrivers('critical')
            else:
                LOGGER.info('Problem polling data from Tesla system') 
        else:
            LOGGER.info('Waiting for system/nodes to get created')
        

    def longPoll(self):

        LOGGER.info('Tesla Power Wall  Controller longPoll')
        if self.nodeDefineDone:
            #self.heartbeat()

            if self.TPW.pollSystemData('all'):
                for node in self.poly.nodes():
                    node.updateISYdrivers('all')
            else:
                LOGGER.error ('Problem polling data from Tesla system')
        else:
            LOGGER.info('Waiting for system/nodes to get created')
        
    def updateISYdrivers(self, level):
        LOGGER.debug('System updateISYdrivers - ' + str(level))       
        if level == 'all':
            value = self.TPW.isNodeServerUp()
            if value == 0:
               self.longPollCountMissed = self.longPollCountMissed + 1
            else:
               self.longPollCountMissed = 0
            self.setDriver('GV2', value)
            self.setDriver('GV3', self.longPollCountMissed)     
            LOGGER.debug('CTRL Update ISY drivers : GV2  value:' + str(value) )
            LOGGER.debug('CTRL Update ISY drivers : GV3  value:' + str(self.longPollCountMissed) )
        elif level == 'critical':
            value = self.TPW.isNodeServerUp()
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
 
    id = 'controller'
    commands = { 'UPDATE': ISYupdate }
    drivers = [
            {'driver': 'ST', 'value':0, 'uom':2},
            {'driver': 'GV2', 'value':0, 'uom':25},
            {'driver': 'GV3', 'value':0, 'uom':71}
            ]

if __name__ == "__main__":
    try:
        #LOGGER.info('Starting Tesla Power Wall Controller')
        polyglot = udi_interface.Interface([])
        polyglot.start()
        polyglot.updateProfile()
        polyglot.setCustomParamsDoc()
        TeslaPWController(polyglot, 'controller', 'controller', 'TeslaPowerWall')
        polyglot.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
