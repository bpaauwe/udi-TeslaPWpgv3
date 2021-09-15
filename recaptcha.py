import requests
from time import sleep
import base64


try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface
    PG_CLOUD_ONLY = True  
LOGGER = polyinterface.LOGGER


# It goes to say this work takes effort so please use my referral to support my work
# https://2captcha.com?from=11874928 
# The link above allows you to create a acount with 2captcha which is what we use
# If you know me we can share API key, just reach out to me  thanks
# Appreciate donations to keep 2captcha going, anything helps
#API_KEY = ''  # Your 2captcha API KEY
CAPTCHA_ENABLE = True

def solveRecaptcha(sitekey, pageurl, captchaApiKey):

    if(CAPTCHA_ENABLE): 
        # Captcha is session based so use the same headers
        LOGGER.debug('Getting recaptcha')
        #catpcha = session.get('https://auth.tesla.com/captcha', headers=headers)


        # Now use the image file saved locally to post to captcha service and wait for response
        # here we post site key to 2captcha to get captcha ID (and we parse it here too)
        current_url = "http://2captcha.com/in.php"

        data = { 
            'key': captchaApiKey,
            'method': 'userrecaptcha',
            'googlekey': sitekey,
            'pageurl': pageurl      
        }
           
        resp = requests.post(current_url, data=data)
        if 'OK' in resp.text:
            captcha_id = resp.text.split('|',1)[1]
        else:
            LOGGER.error('error posting captcha')
            return(None)
        # captcha_id = resp.text.split('|')[1]

        # Change data to be getting the answer from 2captcha
        data = {
            "key": captchaApiKey,
            "action": "get",
            "id": captcha_id
        }
        answer_url = "http://2captcha.com/res.php"
        resp = requests.get(answer_url, params=data)

        captcha_answer = resp.text
        while 'CAPCHA_NOT_READY' in captcha_answer:
            sleep(15)
            resp = requests.get(answer_url, params=data)
            captcha_answer = resp.text
            resp.close()
            
        if 'OK' in captcha_answer:
            captcha_answer = captcha_answer.split('|',1)[1]
        else:
            LOGGER.error('error getting captcha answer')
            return(None)

        #captcha_answer = captcha_answer.split('|')[1]
        #LOGGER.info('captcha = '+ captcha_answer)
        return captcha_answer
    # if captcha not enabled just return empty string
    else:
        print ('Skipping captcha')
        return ""


