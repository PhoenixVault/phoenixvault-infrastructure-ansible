#!/usr/bin/env python

import os
import sys
import argparse
import socket
import subprocess
import json


user = 'phoenix'
pw = 'Phoenix1!'

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
        setRouterConfigSet()
        setShardConfigSet()
       
   
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

    ansible_hosts[primary] = { 'hosts':primary_ip, 'vars': ansible_vars }
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
            ansible_hosts[shardP+str(count)] = { 'hosts': [ hostObjs[host]['ip'] ],'vars': ansible_vars }
            setHostVars(True, hostObjs[host]['ip'],'shard')
            setShardChildren(hostObjs[host]['ip'],shardC+str(count))
            ansible_host_vars.append(shardC+str(count))

            count+=1   

    #print(ansible_hosts)
def getRouterIP():
    ip = ''
    for host in hostObjs:
        if 'router' in hostObjs[host]['host']:
            ip = hostObjs[host]['ip']

    return ip

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

    if mongo_host == 'config' or mongo_host == 'router':
        hostVars[ip]['configRepSetName'] = 'phoenixrs1'
        hostVars[ip]['isPrimary'] = primary
        hostVars[ip]['container_name'] = 'phoenix_'+mongo_host
        hostVars[ip]['mongo_port'] = '27017'
        hostVars[ip]['mongo_dir'] = '/'+mongo_host+'/'

    if mongo_host == 'shard':
        hostVars[ip]['shardRepSetName0'] = 'phoenixsh0'
        hostVars[ip]['shardRepSetName1'] = 'phoenixsh1'
        hostVars[ip]['shardRepSetName2'] = 'phoenixsh2'

        hostVars[ip]['mongo_dir0'] = '/' + 'shard0' + '/'
        hostVars[ip]['mongo_dir1'] = '/' + 'shard1' + '/'
        hostVars[ip]['mongo_dir2'] = '/' + 'shard2' + '/'
        hostVars[ip]['container_name0'] = 'phoenix_shard0'
        hostVars[ip]['container_name1'] = 'phoenix_shard1'
        hostVars[ip]['container_name2'] = 'phoenix_shard2'
        hostVars[ip]['container_port0'] = '27020'
        hostVars[ip]['container_port1'] = '27021'
        hostVars[ip]['container_port2'] = '27022'




def setRouterConfigSet():
    configSet = ''
    for host in hostObjs:
        if 'config' in hostObjs[host]['host']:
            configSet += "{0}:{1},".format(hostObjs[host]['ip'],hostVars[hostObjs[host]['ip']]['mongo_port'])
    configSet = configSet[:-1]

    hostVars[getRouterIP()]['configSet'] = configSet

def setShardConfigSet():
    shardip1 = ''
    shardip2 = ''
    shardip3 = ''

    for host in hostObjs:
        if 'shard' in hostObjs[host]['host']:
           
            if shardip1 == '':
                shardip1 = hostObjs[host]['ip']
                
            elif shardip2 == '':
                shardip2 = hostObjs[host]['ip']

            elif shardip3 == '':
                shardip3 = hostObjs[host]['ip']



    shardSet1 = "phoenixsh0/{0}:27020,{1}:27020,{2}:27020".format(shardip1,shardip2,shardip3)
    shardSet2 = "phoenixsh1/{0}:27021,{1}:27021,{2}:27021".format(shardip2,shardip1,shardip3)
    shardSet3 = "phoenixsh2/{0}:27022,{1}:27022,{2}:27022".format(shardip3,shardip1,shardip2)
    hostVars[getRouterIP()]['shardSet0'] = shardSet1
    hostVars[getRouterIP()]['shardSet1'] = shardSet2
    hostVars[getRouterIP()]['shardSet2'] = shardSet3
   





# Get the inventory.
CreateInventoryFile()


