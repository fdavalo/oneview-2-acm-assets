#!/usr/bin/env python3
"""
Very simple HTTP server in python for logging requests
Usage::
    ./api.py [<port>]
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import json
from pprint import pprint
from hpeOneView.oneview_client import OneViewClient
import sys, os
import base64

class S(BaseHTTPRequestHandler):
    oneviewClient = None
    
    def _set_response(self, ct):
        self.send_response(200)
        self.send_header('Content-type', ct)
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/asset/yaml/"):
            self._set_response('text/plain')
            arr = self.path.split("/")
            if len(arr) > 2: 
               asset = arr[3]
              yaml = assetInfo(asset, "yaml")
              self.wfile.write(yaml.encode('utf-8'))
            else:
              self.wfile.write("")
        if self.path.startswith("/asset/mac/"):
            self._set_response('text/plain')
            arr = self.path.split("/")
            if len(arr) > 2: 
               asset = arr[3]
              mac = assetInfo(asset, "mac")
              self.wfile.write(mac.encode('utf-8'))
            else:
              self.wfile.write("")
        else:
            self._set_response('text/html')
            self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

def run(server_class=HTTPServer, handler_class=S, port=80):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')

def assetInfo(servername, filetype):
  file=open('resources/asset.yaml')
  yaml = file.read()
  file.close()
  oneview_client = oneviewClient()
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
            if filetype == "yaml":
              str=yaml.replace('@name@', profile['name'])
              for key in ['url', 'mac', 'role']:
                str = str.replace('@'+key+'@', asset[key])
              str=str.replace('@username64@', b64(asset['username']))
              str=str.replace('@password64@', b64(asset['password']))
              return str
            if filetype == "yaml": 
              return asset['mac-baremetal']
        assets[profile['name']]=asset
  except Exception as e:
    pprint(e)
  return ""

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

def oneviewClient():
  if S.oneviewClient is None:
    try:
      S.oneviewClient = OneViewClient.from_environment_variables()
    except Exception:
      sys.exit(1)
  return S.oneviewClient

if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
