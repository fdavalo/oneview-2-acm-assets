#!/usr/bin/env python3
"""
Very simple HTTP server in python for logging requests
Usage::
    ./server.py [<port>]
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
    used = False
    
    def _set_response(self, ct):
        self.send_response(200)
        self.send_header('Content-type', ct)
        self.end_headers()

    def do_GET(self):
        if self.path == "/assets.js":
            self._set_response('text/javascript')
            js = "var assets = "+json.dumps(assets())
            self.wfile.write(js.encode('utf-8'))
        elif self.path == "/index.html" or self.path == "/":
            file = open("resources/index.html")
            self._set_response('text/html')
            self.wfile.write(file.read().encode('utf-8'))
        elif self.path == "/index.css":
            file = open("resources/index.css")
            self._set_response('text/css')
            self.wfile.write(file.read().encode('utf-8'))
        else:
            self._set_response('text/html')
            self.wfile.write("GET request for {}".format(self.path).encode('utf-8'))

    def do_POST(self):
        if self.path == "/index.html" or self.path == "/":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            if post_data.startswith("asset="):
              serverName = ""
              if post_data != "asset=":
                serverName = post_data.split("=")[1]
              createAsset(serverName)
            file = open("resources/index.html")
            self._set_response('text/html')
            self.wfile.write(file.read().encode('utf-8'))
        else:
            content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
            post_data = self.rfile.read(content_length) # <--- Gets the data itself
            self._set_response('text/html')
            self.wfile.write("POST request for {}".format(self.path).encode('utf-8'))

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

def assets():
  assets = {}
  if S.used: return assets
  S.used = True
  file=open('resources/asset.yaml')
  yaml = file.read()
  file.close()
  oneview_client = oneviewClient()
  try:
    server_profiles = oneview_client.server_profiles
    server_hardwares = oneview_client.server_hardware
    server_hardware_all = server_hardwares.get_all()
    all_profiles = server_profiles.get_all()
    for profile in all_profiles:
      role = ''
      if 'master' in profile['name']: role = 'master'
      if 'worker' in profile['name']: role = 'worker'
      asset = {'role':role, 'username':os.environ.get('ONEVIEWSDK_USERNAME', ''),'password':os.environ.get('ONEVIEWSDK_PASSWORD', '')}
      for conn in profile['connectionSettings']['connections']:
        if conn['name'] == "RedHat_MGMT":
          asset['mac']=conn['mac']
      for hard in server_hardware_all:
        if hard['uri'] == profile['serverHardwareUri'] and hard['powerState'] == 'Off' and hard['maintenanceMode'] == False:
          asset['url']='ipmi://'+hard['mpHostInfo']['mpIpAddresses'][0]['address']
      cluster = None
      try:
          file=open("assets/"+profile['name']+".cluster")
          asset['cluster']=file.read()
          file.close()
      except Exception ee:
          pass
      if 'url' in asset and 'mac' in asset and 'role' in asset and 'cluster' not in asset:
        file=open('assets/'+profile['name']+'.yaml', 'w+')
        str=yaml.replace('@name@', profile['name'])
        for key in ['url', 'mac', 'role']:
          str = str.replace('@'+key+'@', asset[key])
        str=str.replace('@username64@', b64(asset['username']))
        str=str.replace('@password64@', b64(asset['password']))
        file.write(str)
        file.close()
        assets[profile['name']]=asset
  except Exception e:
    pprint(e)
  #pprint(assets)
  S.used = False
  return assets

def b64(message):
  message_bytes = message.encode('ascii')
  base64_bytes = base64.b64encode(message_bytes)
  return base64_bytes.decode('ascii')        

def createAsset(serverName):
  oneview_client = OneViewClient.from_environment_variables()
  server_profiles = oneview_client.server_profiles
  all_profiles = server_profiles.get_all()
  server_hardwares = oneview_client.server_hardware
  server_hardware_all = server_hardwares.get_all()
  profile_templates = oneview_client.server_profile_templates
  all_templates = profile_templates.get_all()

  if serverName != '':
    for prof in all_profiles:
      if prof['name'] == serverName:
        return False
    
  servers = []
  for serv in server_hardware_all:
    if serv['serverProfileUri'] is None and \
       serv['powerState'] == 'Off' and \
       serv['maintenanceMode'] == False and \
       serv['model'] == 'ProLiant BL460c Gen9' and \
       serv['state'] == 'NoProfileApplied' and \
       serv['status'] != 'Critical':
      servers.append(serv)

  serv_template = None
  for template in all_templates:
    if template['name'] == "Openshift-BM":
      serv_template = template;

  server = servers[-1];
  if serverName == '': serverName = 'node-'+server['serialNumber'].lower();
  options = dict(
      name=serverName,
      serverHardwareUri=server['uri'],
      serverProfileTemplateUri=serv_template['uri']
  )
  profile = oneview_client.server_profiles.create(options, force=True)

  options = dict(serverProfileTemplateUri=serv_template['uri'])
  profile.patch(operation="replace", path="/templateCompliance", value="Compliant")
  return True

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
