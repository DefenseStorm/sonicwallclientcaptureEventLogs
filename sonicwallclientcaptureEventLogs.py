#!/usr/bin/env python3

import sys,os,getopt
import traceback
import os
import requests
import re
import datetime

sys.path.insert(0, 'ds-integration')
from DefenseStorm import DefenseStorm

class integration(object):

    def get_token(self):
        params = {'email':self.ds.config_get('sonicwall', 'email'), 'password':self.ds.config_get('sonicwall', 'password')}
        response = requests.post(self.url + "/login", data=params)
        if response.status_code == 200:
            results = response.json()
            return results['token']
        else:
            self.ds.log("ERROR", "Failed to Login" + response.status_code)
            return None

    def get_clientLogsEvents(self, since=None):
        if since == None:
            self.ds.log("ERROR", "No 'since' time specificed for clientLogsEvents")
            return None
        params = {'since':since, 'sizePerPage':'1'}
        response = requests.get(self.url + "/clientLogsEvents/logs", headers=self.headers, params=params)
        if response.status_code != 200:
            self.ds.log("ERROR", "Failed to get managementConsoleLogs" + response.status_code)
            return None
        results = response.json()
        self.ds.log("INFO", "clientLogsEvents retrieving " + str(results['count']) + " events")
        params = {'since':since, 'sizePerPage':results['count']}
        response = requests.get(self.url + "/clientLogsEvents/logs", headers=self.headers, params=params)
        if response.status_code != 200:
            self.ds.log("ERROR", "Failed to get managementConsoleLogs" + response.status_code)
            return None
        results = response.json()
        return results['data']

    def get_managementConsoleLogs(self, since=None):
        if since == None:
            self.ds.log("ERROR", "No 'since' time specificed for managementConsoleLogs")
            return None
        params = {'since':since, 'sizePerPage':'1'}
        response = requests.get(self.url + "/logs", headers=self.headers,params=params)
        if response.status_code != 200:
            self.ds.log("ERROR", "Failed to get managementConsoleLogs" + response.status_code)
            return None
        results = response.json()
        self.ds.log("INFO", "managementConsoleLogs retrieving " + str(results['count']) + " events")
        params = {'since':since, 'sizePerPage':results['count']}
        response = requests.get(self.url + "/logs", headers=self.headers,params=params)
        if response.status_code != 200:
            self.ds.log("ERROR", "Failed to get managementConsoleLogs" + response.status_code)
            return None
        results = response.json()
        return results['data']

    def run(self):

        self.url = self.ds.config_get('sonicwall', 'url')
        token = self.get_token()
        self.headers = {'Authorization':token}
        if self.headers == None:
            self.ds.log("ERROR", "Failed to get Token")
            return None
            
        self.state_dir = self.ds.config_get('sonicwall', 'state_dir')
        last_run = self.ds.get_state(self.state_dir)
        if last_run == None:
            self.ds.log("INFO", "No datetime found, defaulting to last 12 hours for results")
            last_run = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
        current_run = datetime.datetime.utcnow()

        last_run_str = last_run.strftime("%Y-%m-%dT%H:%M:%SZ")
        current_run_str = current_run.strftime("%Y-%m-%dT%H:%M:%SZ")

        results = self.get_clientLogsEvents(since=last_run_str)
        for item in results:
            item['timestamp'] = item['messageTime']
            self.ds.writeJSONEvent(item)
        self.get_managementConsoleLogs(since=last_run_str)
        for item in results:
            item['timestamp'] = item['messageTime']
            self.ds.writeJSONEvent(item)


        self.ds.set_state(self.state_dir, current_run)
    
    def usage(self):
        print
        print(os.path.basename(__file__))
        print
        print('  No Options: Run a normal cycle')
        print
        print('  -t    Testing mode.  Do all the work but do not send events to GRID via ')
        print('        syslog Local7.  Instead write the events to file \'output.TIMESTAMP\'')
        print('        in the current directory')
        print
        print('  -l    Log to stdout instead of syslog Local6')
        print
    
    def __init__(self, argv):

        self.testing = False
        self.send_syslog = True
        self.ds = None
    
        try:
            opts, args = getopt.getopt(argv,"htnld:",["datedir="])
        except getopt.GetoptError:
            self.usage()
            sys.exit(2)
        for opt, arg in opts:
            if opt == '-h':
                self.usage()
                sys.exit()
            elif opt in ("-t"):
                self.testing = True
            elif opt in ("-l"):
                self.send_syslog = False
    
        try:
            self.ds = DefenseStorm('sonicwallclientcaptureEventLogs', testing=self.testing, send_syslog = self.send_syslog)
        except Exception as e:
            traceback.print_exc()
            try:
                self.ds.log('ERROR', 'ERROR: ' + str(e))
            except:
                pass

        except Exception as e:
            traceback.print_exc()
            try:
                self.ds.log('ERROR', 'ERROR: ' + str(e))
            except:
                pass



if __name__ == "__main__":
    i = integration(sys.argv[1:]) 
    i.run()
