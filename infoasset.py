#!/usr/bin/env python3

import logging
import json
from pprint import pprint
from hpeOneView.oneview_client import OneViewClient
import sys, os
import base64


def infoAsset(servername):
  file=open('resources/asset.yaml')
  yaml = file.read()
  file.close()
  oneview_client = oneviewClient.from_environment_variables()
  try:
    server_profiles = oneview_client.server_profiles
    server_hardwares = oneview_client.server_hardware
    server_hardware_all = server_hardwares.get_all()
    all_profiles = server_profiles.get_all()
    profile_templates = oneview_client.server_profile_templates
    all_templates = profile_templates.get_all()    
    
    templatesUri = {}
    for template in all_templates:
      templatesUri[template['uri']] = template['name']
    
    for profile in all_profiles:
      role = ''
      if 'master' in profile['name']: role = 'master'
      if 'worker' in profile['name']: role = 'worker'
      asset = {'role':role, 'username':os.environ.get('ONEVIEWSDK_USERNAME', ''),'password':os.environ.get('ONEVIEWSDK_PASSWORD', '')}
      if profile['serverProfileTemplateUri'] is not None and templatesUri[profile['serverProfileTemplateUri']]:
        asset['template']=templatesUri[profile['serverProfileTemplateUri']];
      for conn in profile['connectionSettings']['connections']:
        if conn['name'] == "RedHat_MGMT":
          asset['mac']=conn['mac']
        if conn['name'] == "RedHat_WRKLD":
          asset['mac-baremetal']=conn['mac']        
      for hard in server_hardware_all:
        if hard['uri'] == profile['serverHardwareUri'] and hard['maintenanceMode'] == False:
          asset['url']='ipmi://'+hard['mpHostInfo']['mpIpAddresses'][0]['address']
          asset['power'] = hard['powerState']
      if 'power' in asset and 'url' in asset and 'mac' in asset and 'role' in asset:
        if asset['power'] == 'Off':
          if profile['name'] == servername:
            file=open('/workspace/result/'+profile['name']+'.yaml', 'w+')
            str=yaml.replace('@name@', profile['name'])
            for key in ['url', 'mac', 'role']:
              str = str.replace('@'+key+'@', asset[key])
            str=str.replace('@username64@', b64(asset['username']))
            str=str.replace('@password64@', b64(asset['password']))
            file.write(str)
            file.close()
            file=open('/workspace/result/'+profile['name']+'.mac', 'w+')
            file.write(asset['mac-baremetal'])
            file.close()
  except Exception as e:
    pprint(e)

def b64(message):
  message_bytes = message.encode('ascii')
  base64_bytes = base64.b64encode(message_bytes)
  return base64_bytes.decode('ascii')        

def getServerProfileTemplates(all_templates, templateName):
  templates = {}
  for template in all_templates:
    if template['name'] == templateName or template['name'].startswith(templateName+'-'):
        templates[template['serverHardwareTypeUri']]=template['uri']
  return templates


if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
      sys.exit(infoAsset(argv[1]))
    else:
      print("1 argument needed : serverName")
      sys.exit(1)
