#!/usr/bin/env python

import os
import sys
import argparse
import socket
import subprocess
import json


user = 'jd'
pw = 'toor'

hostObjs = {}
ipaddresses = []
configs = {}
ansible_hosts = {}
config_children = {}
hostVars = {}
ansible_vars = {
                'ansible_connection': 'ssh',
                'ansible_user': user,
                'ansible_ssh_pass': pw,
                'ansible_sudo_pass': pw,
               }

ansible_host_vars = [ ]

class CreateInventoryFile(object):


    def __init__(self):
     
        with open('ip_addresses.txt') as my_file:
            ipaddresses = [x.strip() for x in my_file.readlines()]

        #create ip hostnames dictonary and starts the creation of hostvars
        setHostNames(ipaddresses)
        #print(hostVars)

        #isolate configs and set config_primary and config_children
        setHosts(hostObjs,'config','config_primary','config_children')
        setHosts(hostObjs,'router','router_primary','router_children')
        setShards(hostObjs)
    
        #print(hostVars)
        #print(config_primary)
        #for host in hostObjs:
            #print (hostObjs[host]['ip'])
            #print (hostObjs[host]['host'])

        ansible_hosts['_meta'] = {'hostvars':hostVars}
        ansible_host_vars.append('_meta')
 
        hosts = {}
        for i in ansible_host_vars:
            hosts[i] = ansible_hosts[i]
            #print("'{0}' : {1}{2}".format(i ,ansible_hosts[i],addComma) )
        

        #print (hostCollection)
        print(json.dumps(ansible_hosts))


def setHostNames(ips):
    count = 0;  
    for ip in ips:
        hostname = subprocess.Popen("ssh {user}@{host} {cmd}".format(user=user, host=ip , cmd='hostname'), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True).communicate()
        hostObjs[count] = {'ip':ip,'host':hostname[0]}
        mongo_type = ''
        if 'config' in hostname[0]:
            mongo_type = 'config'
        elif 'shard' in hostname[0]:
            mongo_type = 'shard'
        elif 'router' in hostname[0]:
            mongo_type = 'router'

        hostVars[ip] = {'hostname':hostname[0].strip(),'mongo_type':mongo_type}
        #hostObjs[count,1] = hostname[0]
        count+=1;

def setHosts(hostObjs,mongo_host,primary,children):
    hostDic = {}
    count = 0;
    primary_hostname = ''
    primary_ip = []
    children_ips = []

    #seperate config servers and find primary config
    for host in hostObjs:
        #config primary
        if mongo_host in hostObjs[host]['host']:
            if primary_hostname == '' or primary_hostname > hostObjs[host]['host']:
                primary_hostname = hostObjs[host]['host']
                #print (primary_hostname)

            hostDic[count] = {'ip':hostObjs[host]['ip'],'host':hostObjs[host]['host']}
            #print(configHosts[count])
            count+=1

    count = 0
    #create ansible host objects
    for i in hostDic:
        if primary_hostname == hostDic[i]['host']:
            primary_ip.append(hostDic[i]['ip'])
            #print (configHosts[config]['host'])
        else:
            children_ips.append(hostDic[i]['ip'])

    ansible_hosts[primary] = { 'hosts':primary_ip, 'children': [children], 'vars': ansible_vars }
    ansible_host_vars.append(primary)
    for ip in primary_ip:
        setHostVars(True,ip,mongo_host)

    if(len(children_ips)>0):
        ansible_host_vars.append(children)
        ansible_hosts[children] = { 'hosts':children_ips,'vars': ansible_vars }
        for ip in children_ips:
            setHostVars(False,ip,mongo_host)



def setShards(hostObjs):
    count = 0;
    shardIps = []
    shardP = 'shard_primary'
    shardC = 'shard_children'
    #seperate shard servers and find primary config
    for host in hostObjs:
        if 'shard' in hostObjs[host]['host']:
            ansible_host_vars.append(shardP+str(count))
            ansible_hosts[shardP+str(count)] = { 'hosts': [ hostObjs[host]['ip'] ], 'children': [shardC+str(count)], 'vars': ansible_vars }
            setShardChildren(hostObjs[host]['ip'],shardC+str(count))
            ansible_host_vars.append(shardC+str(count))

            count+=1   

    #print(ansible_hosts)

def setShardChildren(parentIp,ansible_group):
    count = 0;
    shardChilIps = []
    #seperate shard servers and find primary config
    for host in hostObjs:
        if 'shard' in hostObjs[host]['host']:
            if hostObjs[host]['ip'] != parentIp:
                shardChilIps.append(hostObjs[host]['ip'])
         
    
    ansible_hosts[ansible_group] = { 'hosts':shardChilIps,'vars': ansible_vars }

    #print(ansible_hosts[ansible_group])

def setHostVars(primary,ip,mongo_host):
    #print(ip)
    #print(primary)
    hostVars[ip]['isPrimary'] = primary
    hostVars[ip]['container_name'] = 'phoenix_'+mongo_host
    hostVars[ip]['mongo_port'] = '27017'
    hostVars[ip]['mongo_dir'] = '/mongo_cluster/'+mongo_host



# Get the inventory.
CreateInventoryFile()


