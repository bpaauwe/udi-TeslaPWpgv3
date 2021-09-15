# udi-powerwall
## Power wall Node server
The main node displays node status - 
Setup node allows configuration of different parameters 
Status node gives a firewall status 


For the setup node to show one need to connect to the cloud (Tesla only allows changes via cloud)
Note - there is a discrepancy between local and cloud back-off limt.  Local power wall reports about 3% higher than the value specified perventage in the cloud (one can only change back-f value via the cloud or Tesla App)

## Code
Code uses API (local power wall) from https://github.com/jrester/tesla_powerwall API - not official Tesla API 
Also based code taken from: https://github.com/bismuthfoundation/TornadoWallet and https://github.com/fkhera/powerwallCloud for OAUTH on Tesla cloud data.  Added code for more efficient Token refresh
Code is under MIT license.
Some info on the clould API can be found at https://tesla-api.timdorr.com/



## Installation
To run node server user must first select data source - from Local Power Wall and/or Tesla Cloud.   Local is not working on polyglot cloud.  Select  LOCAL/CLOUD/BOTH
### Polisy/Polyglot (local) 
Configuration requires 4 steps first time:
1) First user needs to sepcifiy source of data (LOCAL/BOTH) 
2) Next user will speficy the needed user IDs and passwords for the selected option and local Tesla power wall IP address if chosen.
3) Restart

### Polyglot Cloud
1) First user needs to sepcifiy source of data (CLOUD/BOTH) 
Configuration requires user to enter CLOUD_USER_EMAIL and CLOUD_USER_PASSWORD keywords under confuguration.  Furthermore, a API key for 2captcha is required to pass the recaptcha Tesla is presenting.  Key can be acquired from https://2captcha.com?from=12244449 (referral to me).  Cost is reasonable ~ 3$ for 1000 recapta solves (1000 time starting the node)
Restart 

## Notes 
Using cloud access user can set all parameters mobile app currently supports (except car charging limit).

Generator support is not tested (I do not have one) and I have not tested without solar connected.

An option to generate a daily log file is included - file must be down loaded separately from polisy/polyglot - CSV formatted data".  Disabled by default.