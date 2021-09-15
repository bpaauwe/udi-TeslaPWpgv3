#from ISYprofile import PG_CLOUD_ONLY
import time
import json
import hashlib
from datetime import datetime
import requests
import os
from requests_oauth2 import OAuth2BearerToken
import re
import urllib.parse
import string
import random
import base64

import recaptcha

PG_CLOUD_ONLY = False

try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface
    PG_CLOUD_ONLY = True  


LOGGER = polyinterface.LOGGER 
#import LOGGER
MAX_COUNT = 6
class TPWauth:
    def __init__(self, email, password, captchaAPI):
        self.CLIENT_ID = "81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384"
        self.CLIENT_SECRET = "c7257eb71a564034f9419ee651c7d0e5f7aa6bfbd18bafb5c5c033b093bb2fa3"
        self.TESLA_URL = "https://owner-api.teslamotors.com"

        self.code_verifier = ''.join(random.choices(string.ascii_letters+string.digits, k=86))   
        self.code_challenge = hashlib.sha256(self.code_verifier.encode('utf-8')).hexdigest()
        self.email = email
        self.password = password
        self.captchaAPIKEY = captchaAPI
        self.state_str = 'ThisIsATest' 
        self.cookies = None
        self.data = {}
        

        self.token = 'fail'
        self.running = False

        #self.gateway_host = gateway_host
        #self.password = password
        #self.battery_soc = 0
  
        #self.base_path = 'https://' + self.gateway_host
        self.auth_header = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + self.token}
      
        #self.haveCar = True
        
  
        self.verifier_bytes = os.urandom(32)
        self.challenge = base64.urlsafe_b64encode(self.verifier_bytes).rstrip(b'=')
        self.challenge_bytes = hashlib.sha256(self.challenge).digest()
        self.challengeSum = base64.urlsafe_b64encode(self.challenge_bytes).rstrip(b'=')


        #self.__tesla_initConnect(self.email, self.password)


    def authUrl(self):
        LOGGER.debug ("getting authUrl")
        getVars = {'client_id': 'ownerapi', 
                'code_challenge': self.challengeSum,
                'code_challenge_method' : "S256",
                'redirect_uri' : "https://auth.tesla.com/void/callback",
                'response_type' : "code",
                'scope' : "openid email offline_access",
                'state' : "tesla_exporter"
        }
        url = 'https://auth.tesla.com/oauth2/v3/authorize'

        result = url + "?" + urllib.parse.urlencode(getVars)
        #LOGGER.debug(result)
        return result

    def rand_str(self, chars=43):
        letters = string.ascii_lowercase + string.ascii_uppercase + string.digits + "-" + "_"
        return "".join(random.choice(letters) for i in range(chars))        

    def __tesla_refresh_token(self):
        S = {}
        if self.Rtoken:
            data = {}
            data['grant_type'] = 'refresh_token'
            data['client_id'] = 'ownerapi'
            data['refresh_token']=self.Rtoken
            data['scope']='openid email offline_access'      
            resp = requests.post('https://auth.tesla.com/oauth2/v3/token', data=data)
            S = json.loads(resp.text)
            if 'refresh_token' in S:
                    self.Rtoken = S['refresh_token']
            else:
                self.Rtoken = None
            data = {}
            data['grant_type'] = 'urn:ietf:params:oauth:grant-type:jwt-bearer'
            data['client_id']=self.CLIENT_ID
            data['client_secret']=self.CLIENT_SECRET
            with requests.Session() as s:
                try:
                    s.auth = OAuth2BearerToken(S['access_token'])
                    r = s.post(self.TESLA_URL + '/oauth/token',data)
                    S = json.loads(r.text)
                except  Exception as e:
                    LOGGER.error('Exception __tesla_refersh_token: ' + str(e))
                    pass
            
            time.sleep(1)
            #self.S = S
            #self.S['created_at'] = datetime.now()
        return S


    '''
    --------------------------------------------------------------------------------------------------------------------------------------------------
    Following code originates from:
    https://github.com/bismuthfoundation/TornadoWallet/blob/c4c902a2fe2d45ec399416baac4eefd39d596418/wallet/crystals/420_tesla/teslaapihandler.py#L219
    but has been modified to support token renew and support captcha extranction 
    '''



    def __tesla_initConnect(self, email, pwd):
        self.data = {}
        self.data['audience'] = ''
        self.data['client_id']='ownerapi'
        self.data['code_challenge']=self.code_challenge
        self.data['code_challenge_method']='S256'
        self.data['redirect_uri']='https://auth.tesla.com/void/callback'
        self.data['response_type']='code'
        self.data['scope']='openid email offline_access'
        self.data['state']=self.state_str
        self.data['login_hint']=self.email
        r = requests.get('https://auth.tesla.com/oauth2/v3/authorize',  self.data)
        self.cookies = r.cookies
        self.data = self.html_parse(self.data,r.text)
        self.data['identity'] = self.email
        self.data['credential'] = self.password 


        '''
        self.captchaFile = captcha.getCaptcha(self.headers, self.cookies)
        if self.captchaMethod == 'EMAIL':
            captcha.sendEmailCaptcha(self.captchaFile, self.email)
        '''

    def tesla_connect(self, captchaAPIKey ):
        '''
        headers = {
        'User-Agent': 'PowerwallDarwinManager',
        'x-tesla-user-agent': '' ,
        'X-Requested-With': 'com.teslamotors.tesla',
        }
        '''
        try:
            session = requests.Session()
            headers = {}
            data = {}
            #data['audience'] = ''
            #data['client_id']='ownerapi'
            #data['code_challenge']=self.code_challenge
            #data['code_challenge_method']='S256'
            #data['redirect_uri']='https://auth.tesla.com/void/callback'
            #data['response_type']='code'
            #data['scope']='openid email offline_access'
            #data['state']=self.state_str
            #data['login_hint']=self.email
            #r = session.get('https://auth.tesla.com/oauth2/v3/authorize',  data=data)
            #self.cookies = r.cookies
            #data = self.html_parse(data,r.text)


            auth_url = self.authUrl()
    
            resp = session.get(auth_url, headers=headers)
            recaptcha_site_key = re.search(r".*sitekey.* : '(.*)'", resp.text).group(1)
            #LOGGER.debug ('captcha sitekey: ' + recaptcha_site_key)
            #LOGGER.debug ('auth url: ' + auth_url)

            data = self.html_parse(data, resp.text)
            data['cancel']=''
            data['identity'] = self.email
            data['credential'] = self.password
            LOGGER.info('Solving recaptcha - may take 30 sec')
            recaptchaCode = recaptcha.solveRecaptcha(recaptcha_site_key, auth_url, captchaAPIKey)
            data['g-recaptcha-response:'] = recaptchaCode
            data['recaptcha'] = recaptchaCode
            LOGGER.debug('recaptcha code:' + str(recaptchaCode))
            captchaOK = False
            while not(captchaOK):
                #r = session.post(auth_url, data=data, cookies=self.cookies, headers=headers, allow_redirects=False)
                resp = session.post(auth_url, data=data, headers=headers, allow_redirects=False)
                if "Captcha does not match" in resp.text:
                    captchaOK = False
                else:
                    captchaOK = True
                    count = 0
                    while resp.status_code != 302 and count < 5:
                        time.sleep(1)
                        count = count + 1
                        resp = session.post(auth_url, data=data, headers=headers, allow_redirects=False)   
                        #r = session.post(auth_url, data=data, cookies=self.cookies, headers=headers, allow_redirects=False)   

                #LOGGER.debug('Tesla Post r=:' + str(resp.text))


            code = self.myparse2(resp.text,'code=')

            data = {}
            data['grant_type'] = 'authorization_code'
            data['client_id'] = 'ownerapi'
            data['code'] = code
            data['code_verifier'] = self.rand_str(108)
            data['redirect_uri'] = 'https://auth.tesla.com/void/callback'        
            resp = session.post('https://auth.tesla.com/oauth2/v3/token', headers=headers, json=data)
            S = json.loads(resp.text)
            #LOGGER.debug('Tesla Access Auth: S= ' + str(S))
            if 'refresh_token' in S:
                self.Rtoken = S['refresh_token']
            else:
                self.Rtoken = None
            headers["authorization"] = "bearer " + S['access_token']
            data = {}
            data['grant_type'] = 'urn:ietf:params:oauth:grant-type:jwt-bearer'
            data['client_id']=self.CLIENT_ID
            data['client_secret']=self.CLIENT_SECRET
        except Exception as e:
            LOGGER.error('Exception Auth: ' + e)

        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])
                r = s.post(self.TESLA_URL + '/oauth/token',headers=headers, json=data)
                S = json.loads(r.text)
            except Exception as e:
                LOGGER.error('exception ' + str(e))
                pass
        owner_access_token = S["access_token"]
        self.token = owner_access_token
        self.auth_header =  {'Authorization': 'Bearer ' + self.token} 
        time.sleep(1)

        return S


        '''
        self.data = {}
        self.data['audience'] = ''
        self.data['client_id']='ownerapi'
        self.data['code_challenge']=self.code_challenge
        self.data['code_challenge_method']='S256'
        self.data['redirect_uri']='https://auth.tesla.com/void/callback'
        self.data['response_type']='code'
        self.data['scope']='openid email offline_access'
        self.data['state']=self.state_str
        self.data['login_hint']=self.email
        r = requests.get('https://auth.tesla.com/oauth2/v3/authorize',  self.data)
        self.cookies = r.cookies
        self.data = self.html_parse(self.data,r.text)
        self.data['identity'] = self.email
        self.data['credential'] = self.password 




        
        LOGGER.debug('AUTH tesla connect - method : '+ str(captchaMethod))


        if captchaMethod == 'AUTO': 
            captchaCode = captcha.solveCaptcha(self.captchaFile, captchaAPIKey )
        self.data['captcha'] =  captchaCode    
        LOGGER.debug('captcha code:' + str(captchaCode))
        
        r = requests.post('https://auth.tesla.com/oauth2/v3/authorize', data=self.data, cookies=self.cookies, headers=self.headers, allow_redirects=False)
        count = 1
        while "Captcha does not match" in r.text and count < MAX_COUNT:
            count = count + 1            
            if self.captchaMethod == 'EMAIL':
                LOGGER.debug('Captcha not correct - try to restart node server - captcha = ' + captchaCode)
                return(None)          
            else:
                #captchaFile = captcha.getCaptcha(self.headers, self.cookies)
                #captchaCode = captcha.solveCaptcha(captchaFile, self.captchaAPIKEY)
                self.data['captcha'] =  captchaCode  
                r = requests.post('https://auth.tesla.com/oauth2/v3/authorize', data=self.data, cookies=self.cookies, headers=self.headers, allow_redirects=False)
        if count > MAX_COUNT:
            LOGGER.debug('Maximum number of CAPTCHA solves reached')
            return(None)
        count = 1
        while r.status_code != 302 and count < MAX_COUNT:
            time.sleep(1)
            count = count + 1
            r = requests.post('https://auth.tesla.com/oauth2/v3/authorize', data=self.data, cookies=self.cookies, headers=self.headers, allow_redirects=False)   
    
        code = self.myparse2(r.text,'code=')

        data = {}
        data['grant_type'] = 'authorization_code'
        data['client_id'] = 'ownerapi'
        data['code'] = code
        data['code_verifier'] = self.code_verifier
        data['redirect_uri'] = 'https://auth.tesla.com/void/callback'        
        r = requests.post('https://auth.tesla.com/oauth2/v3/token', data=data)
        S = json.loads(r.text)
        if 'refresh_token' in S:
            self.Rtoken = S['refresh_token']
        else:
            self.Rtoken = None

        data = {}
        data['grant_type'] = 'urn:ietf:params:oauth:grant-type:jwt-bearer'
        data['client_id']=self.CLIENT_ID
        data['client_secret']=self.CLIENT_SECRET

        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])
                r = s.post(self.TESLA_URL + '/oauth/token',data)
                S = json.loads(r.text)
            except Exception as e:
                LOGGER.error('exception ' + str(e))
                pass
        
        time.sleep(1)

        return S
        '''
    '''
    def __tesla_connect(self,email, pwd):

        #code_verifier = ''.join(random.choices(string.ascii_letters+string.digits, k=86))
        #code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).hexdigest()

        state_str = 'ThisIsATest' #Random string
        
        headers = {
        'User-Agent': 'PowerwallDarwinManager',
        'x-tesla-user-agent': '' ,
        'X-Requested-With': 'com.teslamotors.tesla',
        }
        

        data = {}
        data['audience'] = ''
        data['client_id']='ownerapi'
        data['code_challenge']=self.code_challenge
        data['code_challenge_method']='S256'
        data['redirect_uri']='https://auth.tesla.com/void/callback'
        data['response_type']='code'
        data['scope']='openid email offline_access'
        data['state']=self.state_str
        data['login_hint']=self.email
        data['identity'] = email
        data['credential'] = pwd


        try:
            session = requests.Session()
            r = session.get('https://auth.tesla.com/oauth2/v3/authorize',  data)
            self.cookies = r.cookies
            data = self.html_parse(data,r.text)




            auth_url = self.authUrl()
            headers = {}
            resp = session.get(auth_url, headers=headers)
            recaptcha_site_key = re.search(r".*sitekey.* : '(.*)'", resp.text).group(1)
            print ('captcha sitekey: ' + recaptcha_site_key)
            print ('auth url: ' + auth_url)
    
            recaptchaCode = recaptcha.solveRecaptcha(recaptcha_site_key, auth_url, self.captchaAPIKEY)
            data['g-recaptcha-response:'] = recaptchaCode
            data['recaptcha'] = recaptchaCode
  
        except Exception as e:
            print('Exception: ' + e)


        captchaOK = False
        while not(captchaOK):
            r = session.post('https://auth.tesla.com/oauth2/v3/authorize', data=data, cookies=self.cookies, headers=self.headers, allow_redirects=False)
            if "Captcha does not match" in r.text:
                captchaOK = False
            else:
                captchaOK = True
                count = 0
                while r.status_code != 302 and count < 5:
                    time.sleep(1)
                    count = count + 1
                    r = requests.post('https://auth.tesla.com/oauth2/v3/authorize', data=data, cookies=self.cookies, headers=self.headers, allow_redirects=False)   
        
        code = self.myparse2(r.text,'code=')

        data = {}
        data['grant_type'] = 'authorization_code'
        data['client_id'] = 'ownerapi'
        data['code'] = code
        data['code_verifier'] = self.code_verifier
        data['redirect_uri'] = 'https://auth.tesla.com/void/callback'        
        r = requests.post('https://auth.tesla.com/oauth2/v3/token', data=data)
        S = json.loads(r.text)
        if 'refresh_token' in S:
            self.Rtoken = S['refresh_token']
        else:
            self.Rtoken = None

        data = {}
        data['grant_type'] = 'urn:ietf:params:oauth:grant-type:jwt-bearer'
        data['client_id']=self.CLIENT_ID
        data['client_secret']=self.CLIENT_SECRET

        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])
                r = s.post(self.TESLA_URL + '/oauth/token',data)
                S = json.loads(r.text)
            except Exception as e:
                LOGGER.error('exception ' + str(e))
                pass
        
        time.sleep(1)

        return S
    '''

    def myparse(self,html,search_string):
        L = len(search_string)
        i = html.find(search_string)
        j = html.find('"',i+L+1)
        return html[i+L:j]

    def myparse2(self,html,search_string):
        L = len(search_string)
        i = html.find(search_string)
        j = html.find('&',i+L+1)
        return html[i+L:j]

    def html_parse(self,data,html):
        data['_csrf'] = self.myparse(html,'name="_csrf" value="')
        data['_phase'] = self.myparse(html,'name="_phase" value="')
        data['_process'] = self.myparse(html,'name="_process" value="')
        data['transaction_id'] = self.myparse(html,'name="transaction_id" value="')
        return data