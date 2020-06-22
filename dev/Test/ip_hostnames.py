#!/usr/bin/env python

import os
import sys
import argparse
import socket

import subprocess
import json


ipaddresses = []



class CreateInventoryFile(object):


    def __init__(self):
     
        with open('ip_addresses.txt') as my_file:
            ipaddresses = [x.strip() for x in my_file.readlines()]

        hosts = {
            'configs': {
                'hosts': getHosts(ipaddresses,'config'),
                'vars': {
                    'ansible_connection': 'ssh',
                    'ansible_user': 'jd',
                    'ansible_ssh_pass': 'toor',
                     }
                   },
            'routers': {
                'hosts': getHosts(ipaddresses,'router'),
                'vars': {
                    'ansible_connection': 'ssh',
                    'ansible_user': 'jd',
                    'ansible_ssh_pass': 'toor',
                     }
                   },
            'shards': {
                'hosts': getHosts(ipaddresses,'shard'),
                'vars': {
                    'ansible_connection': 'ssh',
                    'ansible_user': 'jd',
                    'ansible_ssh_pass': 'toor',
                     }
                   },
                      "_meta": {
                         "hostvars": {}
                        }
               }

        print(hosts)

        #print(json.dumps(hosts))


    
def getHosts(ipaddresses,group):
        myIps = []
        for ip in ipaddresses:
            hostname = subprocess.Popen("ssh {user}@{host} {cmd}".format(user='jd', host=ip , cmd='hostname'), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True).communicate()
            
            if(group in hostname[0]):
                myIps.append(ip)

        return myIps



# Get the inventory.
CreateInventoryFile()


