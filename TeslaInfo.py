#!/usr/bin/env python3

PG_CLOUD_ONLY = False


import udi_interface
LOGGER = udi_interface.LOGGER

import requests
import json
import os 
from datetime import date
import time
from tesla_powerwall import Powerwall, GridStatus, OperationMode
from TeslaCloudAPI import TeslaCloudAPI


class tesla_info:
    def __init__ (self,  ISYname, ISY_Id, local, cloud):
        self.TEST = False

        LOGGER.debug('class tesla_info - init')
        self.TPWcloud = None
        self.localPassword = ''
        self.localEmail = ''
        self.IPAddress = ''
        self.cloudEmail = ''
        self.cloudPassword = ''
        self.controllerID = ISY_Id
        self.controllerName = ISYname
        self.captchaMethod = ''
        self.captchaCode = ''
        self.captchaAPIKey = ''
        self.generatorInstalled  = True # I have not found a way to identify this on clould only connection so it will report even if not there
        self.solarInstalled = False
        self.ISYCritical = {}
        self.localAccessUp = False
        self.cloudAccessUp = False
        self.lastDay = date.today()  
        self.TPWlocalAccess = local
        self.TPWcloudAccess = cloud

        if not local and not cloud:
            LOGGER.debug('No connection specified')


    def loginLocal (self, email, password, IPaddress):
        self.localEmail = email
        self.localPassword = password
        self.IPAddress = IPaddress
        LOGGER.debug('Local Access Supported')

        self.TPWlocal = Powerwall(IPaddress)
        self.TPWlocal.login(self.localPassword, self.localEmail)
        if not(self.TPWlocal.is_authenticated()):            
            LOGGER.debug('Error Logging into Tesla Power Wall') 
            self.localAccessUp = False 
        else:
            self.localAccessUp = True
            self.metersDayStart = self.TPWlocal.get_meters()
            generator  = self.TPWlocal._api.get('generators')
            if not(generator['generators']):
                self.generatorInstalled = False
            else:
                self.generatorInstalled = True
            solar = self.TPWlocal.get_solars()
            if solar:
                self.solarInstalled = True
            else:
                self.solarInstalled = False


    def loginCloud(self, email, password, captchaAPIkey = '' ):
        self.cloudEmail = email
        self.cloudPassword = password
        self.captchaAPIKey = captchaAPIkey

        LOGGER.debug('Cloud Access Supported')
        self.TPWcloud = TeslaCloudAPI(self.cloudEmail, self.cloudPassword, self.captchaAPIKey)
        self.TPWcloudAccess = True
           
    



    def teslaCloudConnect(self ):
        LOGGER.debug('teslaCloudConnect')
        if not(self.TPWcloud.teslaCloudConnect()):    
            LOGGER.debug('Error connecting to Tesla Could - check email, password, and API key')
        else:
            LOGGER.debug('Logged in Cloud - retrieving data')
            self.TPWcloudAccess = True
            self.TPWcloud.teslaCloudInfo()
            self.TPWcloud.teslaRetrieveCloudData()
            self.solarInstalled = self.TPWcloud.teslaGetSolar()


    def teslaInitializeData(self):
        LOGGER.debug('teslaInitializeData')
        if not(self.TPWcloudAccess):
            LOGGER.debug ('no access to cloud data - starting accumulting from 0')
            self.yesterdayTotalSolar = 0
            self.yesterdayTotalConsumption = 0 
            self.yesterdayTotalGeneration  = 0 
            self.yesterdayTotalBattery =  0 
            self.yesterdayTotalGridServices = 0
            self.yesterdayTotalGenerator = 0
            self.daysTotalGridServices = 0 #Does not seem to exist
            self.daysTotalGenerator = 0 #needs to be updated - may not ex     
        else:
            self.TPWcloud.teslaUpdateCloudData('all')
            self.daysTotalSolar = self.TPWcloud.teslaExtractDaysSolar()
            self.daysTotalConsumption = self.TPWcloud.teslaExtractDaysConsumption()
            self.daysTotalGeneraton = self.TPWcloud.teslaExtractDaysGeneration()
            self.daysTotalBattery = self.TPWcloud.teslaExtractDaysBattery()
            self.daysTotalGenerator = self.TPWcloud.teslaExtractDaysGeneratorUse()
            self.daysTotalGridServices = self.TPWcloud.teslaExtractDaysGridServicesUse()
            self.yesterdayTotalSolar = self.TPWcloud.teslaExtractYesteraySolar()
            self.yesterdayTotalConsumption = self.TPWcloud.teslaExtractYesterdayConsumption()
            self.yesterdayTotalGeneration  = self.TPWcloud.teslaExtractYesterdayGeneraton()
            self.yesterdayTotalBattery =  self.TPWcloud.teslaExtractYesterdayBattery() 
            self.yesterdayTotalGridServices = self.TPWcloud.teslaExtractYesterdayGridServiceUse()
            self.yesterdayTotalGenerator = self.TPWcloud.teslaExtractYesterdayGeneratorUse()

           
        #self.OPERATING_MODES = ["backup", "self_consumption", "autonomous"]
        #self.TOU_MODES = ["economics", "balanced"]
        self.metersStart = True
        self.gridstatus = {'on_grid':0, 'islanded_ready':1, 'islanded':2, 'transition ot grid':3}
        
        self.ISYgridEnum = {}
        for key in self.gridstatus:
            self.ISYgridEnum[self.gridstatus [key]]= key

        self.gridStatusEnum = {GridStatus.CONNECTED.value: 'on_grid', GridStatus.ISLANEDED_READY.value:'islanded_ready', GridStatus.ISLANEDED.value:'islanded', GridStatus.TRANSITION_TO_GRID.value:'transition ot grid' }
        self.operationLocalEnum =  {OperationMode.BACKUP.value:'backup',OperationMode.SELF_CONSUMPTION.value:'self_consumption', OperationMode.AUTONOMOUS.value:'autonomous', OperationMode.SITE_CONTROL.value: 'site_ctrl' }
        self.operationModeEnum = {0:'backup', 1:'self_consumption', 2:'autonomous', 3:'site_ctrl'}
        self.ISYoperationModeEnum = {}
        for key in self.operationModeEnum:
            self.ISYoperationModeEnum[self.operationModeEnum[key]] = key

        self.operationCloudEnum = {}  

        if self.TPWcloudAccess:
            ModeList = self.TPWcloud.supportedOperatingModes()
            for i in range(0,len(ModeList)):
                self.operationCloudEnum[i]= ModeList[i] 
            ModeList = self.ISYoperationModeEnum

            for  key in ModeList:
                self.operationCloudEnum[ModeList[key]]= key
            
            ModeList = self.TPWcloud.supportedTouModes()
            self.touCloudEnum = {}
            self.ISYtouEnum = {}
            for i in range(0,len(ModeList)):
                self.touCloudEnum[i]= ModeList[i]
                self.ISYtouEnum[ModeList[i]] = i
        else:
            ModeList=None
        
    def createLogFile(self, enabled):
        self.logFileEnabled = enabled


    def storeDaysData(self, filename, solar, consumption, generation, battery, gridUse, generator, dayInfo ):
        try:
            if not(os.path.exists('./dailyData')):
                os.mkdir('./dailyData')
                dataFile = open('./dailyData/'+filename, 'w+')
                dataFile.write('Date, solarKW, ConsumptionKW, GenerationKW, BatteryKW, GridServicesUseKW, GeneratorKW \n')
                dataFile.close()
            dataFile = open('./dailyData/'+filename, 'a')
            dataFile.write(str(dayInfo)+ ','+str(solar)+','+str(consumption)+','+str(generation)+','+str(battery)+','+str(gridUse)+','+str(generator)+'\n')
            dataFile.close()
        except Exception as e:
            LOGGER.error('Exception storeDaysData: '+  str(e))         
            LOGGER.error ('Failed to add data to '+str(filename))
        

    '''
    Get the most current data. We get data from the cloud first, if cloud
    access is enable, because we'll want to overwrite it  with local data
    if local access is enabled.

    When this finishes, we should have current PW data data.
    '''
    def pollSystemData(self, level):
        #LOGGER.debug('PollSystemData - ' + str(level))

        try:
            self.nowDay = date.today() 
            if (self.lastDay.day != self.nowDay.day) or self.TEST: # we passed midnight
                if not(PG_CLOUD_ONLY) and self.logFileEnabled:
                    self.storeDaysData( 'dailydata.txt', self.daysTotalSolar, self.daysTotalConsumption, self.daysTotalGeneraton, self.daysTotalBattery, self.daysTotalGridServices, self.daysTotalGenerator , self.lastDay)
                self.yesterdayTotalSolar = self.daysTotalSolar
                self.yesterdayTotalConsumption = self.daysTotalConsumption
                self.yesterdayTotalGeneration  = self.daysTotalGeneraton
                self.yesterdayTotalBattery =  self.daysTotalBattery 
                self.yesterdayTotalGridServices = self.daysTotalGridServices
                self.yesterdayTotalGenerator = self.daysTotalGenerator
                if self.TPWlocalAccess:
                    self.metersDayStart = self.TPWlocal.get_meters()
                self.lastDay = self.nowDay

            
            # Get data from the cloud....
            if self.TPWcloudAccess:
                LOGGER.debug('pollSystemData - CLOUD')
                self.cloudAccessUp = self.TPWcloud.teslaUpdateCloudData(level)
                if level == 'all':
                    self.daysTotalSolar = self.TPWcloud.teslaExtractDaysSolar()
                    self.daysTotalConsumption = self.TPWcloud.teslaExtractDaysConsumption()
                    self.daysTotalGeneraton = self.TPWcloud.teslaExtractDaysGeneration()
                    self.daysTotalBattery = self.TPWcloud.teslaExtractDaysBattery()
                    self.daysTotalGenerator = self.TPWcloud.teslaExtractDaysGeneratorUse()
                    self.daysTotalGridServices = self.TPWcloud.teslaExtractDaysGridServicesUse()
                    self.yesterdayTotalSolar = self.TPWcloud.teslaExtractYesteraySolar()
                    self.yesterdayTotalConsumption = self.TPWcloud.teslaExtractYesterdayConsumption()
                    self.yesterdayTotalGeneration  = self.TPWcloud.teslaExtractYesterdayGeneraton()
                    self.yesterdayTotalBattery =  self.TPWcloud.teslaExtractYesterdayBattery() 
                    self.yesterdayTotalGridServices = self.TPWcloud.teslaExtractYesterdayGridServiceUse()
                    self.yesterdayTotalGenerator = self.TPWcloud.teslaExtractYesterdayGeneratorUse()          

            # Get data directly from HW....
            if self.TPWlocalAccess:
                LOGGER.debug('pollSystemData - local - local connection = {}'.format(self.localAccessUp))
                if not self.TPWlocal.is_authenticated():
                    self.TPWlocal.logout()
                    time.sleep(1)
                    self.loginLocal(self.localEmail, self.localPassword, self.IPAddress)
                    if not self.TPWlocal.is_authenticated():
                        self.localAccessUp = False
                        LOGGER.error('No connection to Local Tesla Power Wall')
                        return False

                self.status = self.TPWlocal.get_sitemaster() 
                self.meters = self.TPWlocal.get_meters()
                if level == 'all':
                    # any of this that we got from the cloud calculations is
                    # overwritten here because local data takes priority
                    self.daysTotalSolar =  (self.meters.solar.energy_exported - self.metersDayStart.solar.energy_exported)
                    self.daysTotalConsumption = (self.meters.load.energy_imported - self.metersDayStart.load.energy_imported)
                    self.daysTotalGeneraton = (self.meters.site.energy_exported - self.metersDayStart.site.energy_exported - 
                                                (self.meters.site.energy_imported - self.metersDayStart.site.energy_imported))
                    self.daysTotalBattery =  (float(self.meters.battery.energy_exported - self.metersDayStart.battery.energy_exported - 
                                                (self.meters.battery.energy_imported - self.metersDayStart.battery.energy_imported)))
                    if not self.TPWcloudAccess:
                        self.daysTotalGridServices = 0.0 #Does not seem to exist
                        self.daysTotalGenerator = 0.0 #needs to be updated - may not exist

            return True

        except Exception as e:
            LOGGER.error('Exception PollSystemData: '+  str(e))
            LOGGER.error('problems extracting data from tesla power wall')
            # NEED To logout and log back in locally
            # Need to retrieve/renew token from cloud

        
    ''' *****************************************************************

    methods to retrieve data.  pollSystemData() is used to query the
    PW data.  Then use the methods below to access it.  If we have
    local access, then we'll use that data, otherwise we'll use data
    from the cloud.
    '''
    # Need to be imlemented 
    def isNodeServerUp(self):
        LOGGER.debug('isNodeServerUp - called' )
        if self.localAccessUp == True or self.cloudAccessUp == True:
             return(1)
        else:
             return(0) 

    def TPW_updateMeter(self):
        self.pollSystemData('all')
        return(None)

    def getTPW_chargeLevel(self):
 
        if self.TPWlocalAccess:
            chargeLevel = self.TPWlocal.get_charge()
        else:
            chargeLevel = self.TPWcloud.teslaExtractChargeLevel()
        LOGGER.debug('getTPW_chargeLevel' + str(chargeLevel))
        return(round(chargeLevel,1))


    def getTPW_backoffLevel(self):
        if self.TPWlocalAccess:
            backoffLevel=self.TPWlocal.get_backup_reserve_percentage()
        else:
            backoffLevel=self.TPWcloud.teslaExtractBackoffLevel()
        LOGGER.debug('getTPW_backoffLevel' + str(backoffLevel))
        return(round(backoffLevel,1))

    def getBackupPercentISYVar(self, node):
        return(self.isyINFO.varToISY(node, self.backoffLevel))


    def setTPW_backoffLevel(self, backupPercent):
        return(self.TPWcloud.teslaSetBackoffLevel(backupPercent))

    def getTPW_gridStatus(self):
        if self.TPWlocalAccess:
            statusVal = self.TPWlocal.get_grid_status()
            if statusVal.value in self.gridStatusEnum:
                key = self.gridStatusEnum[statusVal.value ]
                #LOGGER.debug(key)
        else:
            key = self.TPWcloud.teslaExtractGridStatus()
        LOGGER.debug('grid status '+str(self.gridstatus[key]))
        return(self.gridstatus[key])


    def getTPW_solarSupply(self):
        
        if self.TPWlocalAccess:
            #LOGGER.debug(self.meters)
            solarPwr = self.meters.solar.instant_power
        else:
            solarPwr = self.TPWcloud.teslaExtractSolarSupply()
        LOGGER.debug('getTPW_solarSupply - ' + str(solarPwr))
        return(round(solarPwr/1000,2))
        #site_live

    def getTPW_batterySupply(self):
        if self.TPWlocalAccess:
            batteryPwr = self.meters.battery.instant_power
        else:
            batteryPwr = self.TPWcloud.teslaExtractBatterySupply()
        LOGGER.debug('getTPW_batterySupply' + str(batteryPwr))
        return(round(batteryPwr/1000,2))
 


        #site_live
    def getTPW_gridSupply(self):
        if self.TPWlocalAccess:
            gridPwr = self.meters.site.instant_power
        else:
            gridPwr = self.TPWcloud.teslaExtractGridSupply()
        LOGGER.debug('getTPW_gridSupply'+ str(gridPwr))            
        return(round(gridPwr/1000,2))


    def getTPW_load(self):
        if self.TPWlocalAccess:
            loadPwr = self.meters.load.instant_power
        else:
            loadPwr = self.TPWcloud.teslaExtractLoad()
        LOGGER.debug('getTPW_load ' + str(loadPwr))
        return(round(loadPwr/1000,2))


    def getTPW_daysSolar(self):
        if self.TPWlocalAccess:
            Pwr = self.daysTotalSolar
        else:
            Pwr = self.TPWcloud.teslaExtractDaysSolar()
        LOGGER.debug('getTPW_daysSolar ' + str(Pwr))
        return(round(Pwr/1000,2))


    def getTPW_daysConsumption(self):
        if self.TPWlocalAccess:
            Pwr = self.daysTotalConsumption
        else:
            Pwr = self.TPWcloud.teslaExtractDaysConsumption()
            LOGGER.debug('getTPW_daysConsumption ' + str(Pwr))
        return(round(Pwr/1000,2))

    def getTPW_daysGeneration(self):  
        if self.TPWlocalAccess:
            Pwr = self.daysTotalGeneraton
        else:
            Pwr = self.TPWcloud.teslaExtractDaysGeneration()
        LOGGER.debug('getTPW_daysGeneration ' + str(Pwr))        
        return(round(Pwr/1000,2))

    def getTPW_daysBattery(self):  
        if self.TPWlocalAccess:
            Pwr = self.daysTotalBattery
        else:
            Pwr = self.TPWcloud.teslaExtractDaysBattery()
        LOGGER.debug('getTPW_daysBattery ' + str(Pwr))
        return(round(Pwr/1000,2))

    def getTPW_daysGridServicesUse(self):  
        if self.TPWlocalAccess:
            Pwr = self.daysTotalGridServices
        else:
            Pwr = self.TPWcloud.teslaExtractDaysGridServicesUse()
        LOGGER.debug('getTPW_daysGridServicesUse ' + str(Pwr))
        return(round(Pwr/1000,2))

    def getTPW_daysGeneratorUse(self):  
        if self.TPWlocalAccess:
            Pwr = self.daysTotalGenerator
        else:
            Pwr = self.TPWcloud.teslaExtractDaysGeneratorUse()
        LOGGER.debug('getTPW_daysGeneratorUse ' + str(Pwr))
        return(round(Pwr/1000,2))

    def getTPW_yesterdaySolar(self):
        if self.TPWlocalAccess:
            Pwr = self.yesterdayTotalSolar
        else:
            Pwr = self.TPWcloud.teslaExtractYesteraySolar()
        LOGGER.debug('getTPW_daysSolar ' + str(Pwr))
        return(round(Pwr/1000,2))

    def getTPW_yesterdayConsumption(self):
        if self.TPWlocalAccess:
            Pwr = self.yesterdayTotalConsumption
        else:
            Pwr = self.TPWcloud.teslaExtractYesterdayConsumption()
        LOGGER.debug('getTPW_daysConsumption ' + str(Pwr))
        return(round(Pwr/1000,2))

    def getTPW_yesterdayGeneration(self):  
        if self.TPWlocalAccess:
            Pwr = self.yesterdayTotalGeneration
        else:
            Pwr = self.TPWcloud.teslaExtractYesterdayGeneraton()
        LOGGER.debug('getTPW_daysGeneration ' + str(Pwr))
        return(round(Pwr/1000,2))

    def getTPW_yesterdayBattery(self):  

        if self.TPWlocalAccess:
            Pwr = self.yesterdayTotalBattery
        else:
            Pwr = self.TPWcloud.teslaExtractYesterdayBattery()
        LOGGER.debug('getTPW_daysBattery ' + str(Pwr))
        return(round(Pwr/1000,2))


    def getTPW_yesterdayGridServicesUse(self):  

        if self.TPWlocalAccess:
            Pwr = self.yesterdayTotalGridServices
        else:
            Pwr = self.TPWcloud.teslaExtractYesterdayGridServiceUse()
        LOGGER.debug('getTPW_daysGridServicesUse ' + str(Pwr))            
        return(round(Pwr/1000,2))
        #bat_history

    def getTPW_yesterdayGeneratorUse(self):  

        if self.TPWlocalAccess:
            Pwr = self.yesterdayTotalGenerator
        else:
            Pwr = self.TPWcloud.teslaExtractYesterdayGeneratorUse()
        LOGGER.debug('getTPW_daysGeneratorUse ' + str(Pwr))
        return(round(Pwr/1000,2))
        #bat_history


    def getTPW_operationMode(self):
        if self.TPWlocalAccess:
            operationVal = self.TPWlocal.get_operation_mode()
            key = self.operationLocalEnum[operationVal.value]
        else:
            key = self.TPWcloud.teslaExtractOperationMode()

        return( self.ISYoperationModeEnum [key])
    
    def setTPW_operationMode(self, index):
        return(self.TPWcloud.teslaSetOperationMode(self.operationModeEnum[index]))

    ''' 
    def getTPW_running(self):
        if self.status.is_running:  
           return(1)   
        else:
           return(0)
    '''

    def getTPW_powerSupplyMode(self):
        if self.status.is_power_supply_mode:
           return(1)   
        else:
           return(0)            
    
    def getTPW_ConnectedTesla(self):  # can check other direction 
        if self.status.is_connected_to_tesla:
            return(1)   
        else:
            return(0)


    def getTPW_gridServiceActive(self):
        if self.TPWlocalAccess:
            res = self.TPWlocal.is_grid_services_active()   
        else:
            res = self.TPWcloud.teslaExtractGridServiceActive()
        if res:
            return(1)
        else:
            return (0)


    def getTPW_stormMode(self):
        if self.TPWcloudAccess:
            if self.TPWcloud.teslaExtractStormMode():
                return (1)
            else:
                return(0)

    def setTPW_stormMode(self, mode):
        return(self.TPWcloud.teslaSetStormMode(mode==1))

    def getTPW_touMode(self):
        if self.TPWcloudAccess:
            return(self.ISYtouEnum[self.TPWcloud.teslaExtractTouMode()])        


    def getTPW_touSchedule(self):
        if self.TPWcloudAccess:        
            return(self.TPWcloud.teslaExtractTouScheduleList())


    def setTPW_touMode(self, index):
        if self.TPWcloudAccess:        
            return(self.TPWcloud.teslaSetTimeOfUseMode(self.touCloudEnum[index]))


    def setTPW_touSchedule(self, peakOffpeak, weekWeekend, startEnd, time_s):
        if self.TPWcloudAccess:        
            return(self.TPWcloud.teslaSetTouSchedule( peakOffpeak, weekWeekend, startEnd, time_s))

    def setTPW_updateTouSchedule(self, peakOffpeak, weekWeekend, startEnd, time_s):
        if self.TPWcloudAccess:        
            return(self.TPWcloud.teslaSetTouSchedule( peakOffpeak, weekWeekend, startEnd, time_s))

    def getTPW_getTouData(self, days, peakMode, startEnd ):
        if self.TPWcloudAccess:        
            return(self.TPWcloud.teslaExtractTouTime(days, peakMode, startEnd ))

    def disconnectTPW(self):
        if self.TPWlocalAccess:
            self.TPWlocal.close()

