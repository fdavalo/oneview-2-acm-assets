#!/usr/bin/env python3

import logging
import json
from pprint import pprint
from hpeOneView.oneview_client import OneViewClient
import sys, os

def createBM4Asset():
  templateName = "Openshift-BM2"
  serverNames = {"cz24440420":"ocp-bm4-master01","cz2444041w":"ocp-bm4-master02","cz2444041z":"ocp-bm4-master03"}
  
  oneview_client = OneViewClient.from_environment_variables()
  server_profiles = oneview_client.server_profiles
  all_profiles = server_profiles.get_all()
  server_hardwares = oneview_client.server_hardware
  server_hardware_all = server_hardwares.get_all()
  profile_templates = oneview_client.server_profile_templates
  all_templates = profile_templates.get_all()

  serv_template = None
  for template in all_templates:
    if template['name'] == templateName:
      serv_template = template
      break
      
  if serv_template is None:
    print("server template "+templateName+" is not found")
    return False
  
  for serialNumber in serverNames:
    serverName = serverNames[serialNumber]
    server = None
    for serv in server_hardware_all:
      if serialNumber == serv['serialNumber'].lower():
        server = serv
        break
    if server is None:
      print("hardware with serial number "+serialNumber+" not found")
       return False     
    if server['serverProfileUri'] is not None:
      print("a server profile corresponding already exists")
      return False
    if server['powerState'] != 'Off':
      print("server should be Off")
      return False
    if server['maintenanceMode'] != False:
      print("server is in maintenance mode")
      return False
    if server['model'] != 'ProLiant BL460c Gen9':
      print("server model does not match 'ProLiant BL460c Gen9'")
    if server['state'] != 'NoProfileApplied':
      print("a profile is already applied to this hardware")
      return False
    if server['status'] == 'Critical':
      print("server is in Critical state")
      return False

    ls =  {'controllers': [{'deviceSlot': 'Embedded',
                                   'driveWriteCache': 'Unmanaged',
                                   'importConfiguration': False,
                                   'initialize': False,
                                   'logicalDrives': [],
                                   'mode': 'HBA',
                                   'predictiveSpareRebuild': 'Unmanaged'}],
                  'reapplyState': 'NotApplying',
                  'sasLogicalJBODs': []}
    options = dict(
      name=serverName,
      serverHardwareUri=server['uri'],
      serverProfileTemplateUri=serv_template['uri'],
      localStorage=ls
    )
    profile = oneview_client.server_profiles.create(options, force=True)

    options = dict(serverProfileTemplateUri=serv_template['uri'])
    profile.patch(operation="replace", path="/templateCompliance", value="Compliant")
    return True
    
if __name__ == '__main__':
    from sys import argv

    createBM4Asset()
