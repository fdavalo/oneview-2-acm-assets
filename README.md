# Use of HPE OneView SDK to provision Hosts for Openshift clusters

## functions 

   * poweroff.py
  
   * deleprofile.py
  
   * createasset.py 
  
  are used to recreate a server profile with oneview python SDK

## function 

   * infoasset.py
    
  is used to fetch information on a server profile with oneview python SDK

## not used anymore

   * server.py
   
  was used to run this deployment in open-cluster-management namespace and synchronize server available and Bare Metal Hosts
  
## manifests

   * buildconfig.yaml : to build and push the image
  
   * pipelines.yaml and tasks.yaml : tekton task to provision hosts for an Openshift cluster (Agent based)
   
     cf https://github.com/fdavalo/mce-agent-provisioning-pxe
  
   * deployment.yaml, service.yaml, route.yaml : not used anymore, linked to server.py
