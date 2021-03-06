#!/usr/bin/env python3
# -*- coding: utf-8 -*

import json
import logging
from ftntlib import FortiManagerJSON

log = logging.getLogger()

class Device:
    def __init__(self):
        self.type = ""
        self.sn = ""
        self.model_device = ""
        self.name = ""
        self.adom = ""
        self.vdom = ""
        # cluster id would be -1 for single machine, -2 for a cluster and positive value for a device which needs to be a cluster
        self.cluster_id = ""
        self.master = False
        self.second_member = None # address to second member device object
        self.enforce_firmware = ""
        self.target_firmware = ""
        self.policy_package = ""
        self.system_template = ""
        self.cli_template = ""
        self.device_group = ""
        self.city = ""
        self.contact = ""
        self.company = ""
        self.country = ""
        self.latitude = ""
        self.longitude = ""
        self.id_site = ""
        self.downstream_wan1 = ""
        self.downstream_wan2 = ""
        self.upstream_wan1 = ""
        self.upstream_wan2 = ""
        self.sd_wan_template = ""
        self.vpn_community = ""
        self.fortiswitch_template = ""
        self.fap_template = ""
        self.fgt_name = ""
        self.cli_script = ""
        self.sdbranch = ""
        self.platform = ""

    def print(self):
        print("type: " + self.type + "\nsn : " + self.sn + "\nname : " + self.name + "\nenforce_firmware : " + self.enforce_firmware + "\ntarget_firmware : " + self.target_firmware + "\npolicy_package : "
              + self.policy_package + "\nsystem_template : " + self.system_template + "\ncli_template : " +
              self.cli_template + "\ndevice_group : " + self.device_group +
              "\ncity : " + self.city + "\ncontact : "
              + self.contact + "\ncompany : " + self.company + "\ncountry : " + self.country + "\nlatitude : " + self.latitude + "\nlongitude : " + self.longitude + "\nid_site : " +
              str(self.id_site) + "\ndownstream_wan1 : " +
              str(self.downstream_wan1) + "\ndownstream_wan2 : "
              + str(self.downstream_wan2) + "\nupstream_wan1 : " + str(self.upstream_wan1) + "\nupstream_wan2 : " +
              str(self.upstream_wan2) + "\nsd_wan_template : " +
              self.sd_wan_template + "\nvpn_community : "
              + self.vpn_community + "\nfortiswitch_template : " + self.fortiswitch_template + "\nfap_template : " + self.fap_template + "\nadom : " + self.adom + "\nvdom : " + self.vdom)

    # recupère les infos du device sur le FMG comme l'oid
    def get_device(self, api):
        url = "/dvmdb/adom/{}/device/{}".format(self.adom, self.name)
        status, response = api.get(url)
        # print_response(status, response)
        return response

    # construit le scope d'un device et de son vdom. 1 device = 1 vdom
    def scope(self):
        scope = {
            'name': self.name,
            'vdom': self.vdom
        }
        return scope

    ###############################################
    ######### Add model device to FMG #############
    ###############################################
    def add_model_device(self, api):
        url = "/dvmdb/adom/{}/device/{}".format(self.adom, self.name)
        status, response = api.get(url)
        # print_response(status, response)
        # si la réponse de la requete échoue, le FortiGate n'existe PROBABLEMENT pas (cf autre erreur ?)
        if status['code'] == 0:
            print(">> {} already exist".format(self.name))
            return

        print(">> Add Device Model for : " + self.name)
        url = 'dvm/cmd/add/device'

        json_device={}
        json_device['mgmt_mode'] = "fmg"
        json_device['device action'] = "add_model"
        json_device['mr'] = "2"
        json_device['os_type'] = "fos"
        json_device['os_ver'] = "6.0"
        json_device['branch_pt'] = "1005"
        json_device['name'] = self.name
        json_device['sn'] = self.sn
        json_device['desc'] = "FortiGate du site de " + self.name
        json_device['adm_usr'] = "admin"
        json_device['adm_pass'] = "fortinet"
        json_device['latitude'] = str(self.latitude)
        json_device['longitude'] = str(self.longitude)

        meta_fields = {}
        meta_fields['Company/Organization'] = self.company
        meta_fields['Contact Phone Number'] = "0680441134"
        meta_fields['Address'] = self.city
        meta_fields['Contact Email'] = self.contact
        meta_fields['Country'] = self.country
        meta_fields['City'] = self.city
        meta_fields['Site_Name'] = self.name
        meta_fields['id_site'] = str(self.id_site)

        json_device['meta fields'] = meta_fields

        data = {
            'adom' : self.adom,
            'device' : json_device,
            'flags' : [ 'create_task' , 'nonblocking' ]
        }

        status, response = api._do('exec', url, data)
        if response['taskid']:
          status, response = api.taskwait(response['taskid'])
        else:
          return status, response

        if response['line'][0]['err'] != 0:
            print("Error: add device fail")
            return False

        self.link_device(api)

        #ucode, ures = api.update_device(device.adom, device.name)
        #if ucode !=0:
        #  return ucode, ures
        #rcode, rres = api.reload_devlist(device.adom, {'name' : device.name}, 'dvm')
        #if rcode !=0:
        #  return rcode, rres
        return True

    def assign_cli_template(self, api):
        print("\n>>> Ajout du template group {} au device {}".format(self.cli_template, self.name))
        # On récupère la liste des templates groups
        url = "/pm/config/adom/{}/obj/cli/template-group/{}".format(self.adom, self.cli_template)
        status, response = api.get(url)
        # print_response(status, response)
        # si la réponse de la requete échoue, le template group n'existe PROBABLEMENT pas (cf autre erreur ?)
        if status['code'] != 0:
            self.print_error(
                "Template group {} doesn't exist".format(self.cli_template))

        # on ajoute le device dans le scope du group
        scope_member = [self.scope()]
        url += "/scope member"
        status, response = api.add(url, scope_member)
        if status['code'] != 0:
            self.print_error("unable to add template group {} to device {}".format(
                self.cli_template, self.name))
        return

    def assign_policy_package (self,api):
        print("\n>>> Ajout du policy package {} au device {}".format(self.policy_package, self.name))
        # On récupère la liste des templates groups
        url = "/pm/pkg/adom/{}/{}".format(self.adom, self.policy_package)
        status, response = api.get(url)
        # print_response(status, response)
        # si la réponse de la requete échoue, le template group n'existe PROBABLEMENT pas (cf autre erreur ?)
        if status['code'] != 0:
            self.print_error(
                "Policy Package {} doesn't exist".format(self.policy_package))

        # on ajoute le device dans le scope du group
        scope_member = [self.scope()]
        url += "/scope member"
        status, response = api.add(url, scope_member)
        if status['code'] != 0:
            self.print_error("unable to add policy package {} to device {}".format(
                self.policy_package, self.name))
        return
    
    def assign_device_group (self,api):
        print("\n>>> Ajout du device {} au device group {}".format(self.name, self.device_group))
        # On récupère la liste des templates groups
        url = "/dvmdb/adom/{}/group/{}".format(self.adom, self.device_group)
        status, response = api.get(url)
        # print_response(status, response)
        # si la réponse de la requete échoue, le template group n'existe PROBABLEMENT pas (cf autre erreur ?)
        if status['code'] != 0:
            self.print_error(
                "Device Group {} doesn't exist".format(self.device_group))

        # on ajoute le device dans le scope du group
        scope_member = [self.scope()]
        url += "/object member"
        status, response = api.add(url, scope_member)
        if status['code'] != 0:
            self.print_error("unable to add device {} to device group {}".format(
                self.name, self.device_group))
        return
    
    def assign_system_template (self,api):
        print("\n>>> Ajout du System Template {} au device {}".format(self.system_template, self.name))
        # On récupère la liste des system template
        url = "/pm/devprof/adom/{}/{}".format(self.adom, self.system_template)
        status, response = api.get(url)
        # print_response(status, response)
        # si la réponse de la requete échoue, le template group n'existe PROBABLEMENT pas (cf autre erreur ?)
        if status['code'] != 0:
            self.print_error(
                "System Template {} doesn't exist".format(self.system_template))

        # on ajoute le device dans le scope du group
        scope_member = [self.scope()]
        url += "/scope member"
        status, response = api.add(url, scope_member)
        if status['code'] != 0:
            self.print_error("unable to assgin System Tempalte {} to device {}".format(
                self.system_template, self.name))
        return

    def assign_sdwan_template (self,api):
        print("\n>>> Ajout du SD-WAN Template {} au device {}".format(self.sd_wan_template, self.name))
        # On récupère la liste des sd-wan template
        url = "/pm/wanprof/adom/{}/{}".format(self.adom, self.sd_wan_template)
        status, response = api.get(url)
        # print_response(status, response)
        # si la réponse de la requete échoue, le template group n'existe PROBABLEMENT pas (cf autre erreur ?)
        if status['code'] != 0:
            self.print_error(
                "SD-WAN Template {} doesn't exist".format(self.sd_wan_template))

        # on ajoute le device dans le scope du group
        scope_member = [self.scope()]
        url += "/scope member"
        status, response = api.add(url, scope_member)
        if status['code'] != 0:
            self.print_error("unable to assgin SD-WAN Template {} to device {}".format(
                self.sd_wan_template, self.name))
        return

    def assign_vpn_community(self, api):
        # TODO
        return

    def add_fap_to_fmg(self, api):
        # On récupère la liste des WTP Profile
        url = "/pm/config/adom/{}/obj/wireless-controller/wtp-profile/{}".format(self.adom, self.fap_template)
        status, response = api.get(url)
        # print_response(status, response)
        # si la réponse de la requete échoue, le profile d'AP n'existe PROBABLEMENT pas (cf autre erreur ?)
        if status['code'] != 0:
            self.print_error(
                "WTP Profile {} doesn't exist".format(self.fap_template))
        
        url = "/dvmdb/adom/{}/device/{}".format(self.adom, self.fgt_name)
        status, response = api.get(url)
        # print_response(status, response)
        # si la réponse de la requete échoue, le FortiGate n'existe PROBABLEMENT pas (cf autre erreur ?)
        if status['code'] != 0:
            self.print_error(
                "FGT {} doesn't exist".format(self.fgt_name))
        
        # On assigne la FAP au FGT
        print("\n>> Ajout de la FAP {} au device {}".format(self.name, self.fgt_name))
        url = "/pm/config/device/{}/vdom/{}/wireless-controller/wtp".format(self.fgt_name, self.vdom)
        data= {
          'name': self.name,
          'wtp-id': self.sn,
          'wtp-profile': "FAP221E-default"
        }
        
        params= [
            {
                'data': data,
                'push':1,
                'url' : url
            }
        ]

        status, response = api.do('add', params)
        #print(str(status) + "\n" + json.dumps(response, indent=2))
        if status['code'] != 0:
            self.print_error("unable Add FAP {} to device {}".format(
                self.name, self.fgt_name))

        # On assigne le profil WTP a la FAP
        print("\n>>> Ajout du profil {} à la FAP {}".format(self.fap_template, self.name))
        url = "/pm/config/adom/{}/obj/wireless-controller/wtp/{}".format(self.adom, self.sn)
        data= {
          'name': self.name,
          'wtp-profile':  self.fap_template
        }
        scope = [
            {
                'name': self.fgt_name,
                'vdom': self.vdom
            }
        ]
        params= [
            {
                'data': data,
                'scope member': scope,
                'url' : url
            }
        ]
        status, response = api.do('update', params)
        #print(str(status) + "\n" + json.dumps(response, indent=2))
        if status['code'] != 0:
            self.print_error("unable to assgin WTP Profile {} to device {}".format(
                self.fap_template, self.name))
        return

    def add_fsw_to_fmg(self, api):
        # On récupère la liste des FGT    
        url = "/dvmdb/adom/{}/device/{}".format(self.adom, self.fgt_name)
        status, response = api.get(url)
        # print_response(status, response)
        # si la réponse de la requete échoue, le FortiGate n'existe PROBABLEMENT pas (cf autre erreur ?)
        if status['code'] != 0:
            self.print_error(
                "FGT {} doesn't exist".format(self.fgt_name))
        
        # On assigne le FSW au FGT
        print("\n>> Ajout du FSW {} au device {}".format(self.name, self.fgt_name))
        url = "/pm/config/device/{}/vdom/{}/switch-controller/managed-switch".format(self.fgt_name, self.vdom)
        data= {
          'name': self.name,
          'switch-id': self.sn,
        }
        
        params= [
            {
                'data': data,
                'push':1,
                'url' : url
            }
        ]

        status, response = api.do('add', params)
        #print(str(status) + "\n" + json.dumps(response, indent=2))
        if status['code'] != 0:
            self.print_error("unable Add FSW {} to device {}".format(
                self.name, self.fgt_name))
        
        # On assigne le Template FSW
        print("\n>>> Ajout du Template {} au FSW {}".format(self.fortiswitch_template, self.name))
        scope = [
            {
                'name': self.fgt_name,
                'vdom': self.vdom
            }
        ]
        data= {
          'template':  self.fortiswitch_template,
        }
        url = "/pm/config/adom/{}/obj/fsp/managed-switch/{}".format(self.adom, self.sn)
        params= [
            {
                'data': data,
                'scope member': scope,
                'url' : url
            }
        ]
        #print(json.dumps(params, indent=4))
        status, response = api.do('update', params)
        #print(str(status) + "\n" + json.dumps(response, indent=2))
        if status['code'] != 0:
            self.print_error("unable to assgin FSW Profile {} to device {}".format(
                self.fap_template, self.name))
        return

    def interface_mapping(self, api):
        print("\n>>> Config interface mapping pour {}".format(self.name))
        url = "/pm/config/adom/{}/obj/dynamic/interface/Z_LAN".format(self.adom)
        #On récupère l'objet Z_LAN
        status, response = api.get(url)
        #self.print_response(status, response)
        # si la réponse de la requete échoue, l'objet n'existe PROBABLEMENT pas (cf autre erreur ?)
        if status['code'] != 0:
            self.print_error("Object Z_LAN doesn't exist")
                
        new_dynamic_mapping={}
        new_dynamic_mapping['_scope'] = self.scope()
        if self.sdbranch == "yes":
            new_dynamic_mapping['local-intf'] = ["LAN","CORP"]
        elif self.platform == "fgt-60e":
            new_dynamic_mapping['local-intf'] = "internal"
        else:
            new_dynamic_mapping['local-intf'] = "lan"  
        response['dynamic_mapping'].append(new_dynamic_mapping)
        data = {
            'dynamic_mapping' : response['dynamic_mapping'],           
        }
        #print(json.dumps(data, indent=4))
        status, response = api._do('set',url, data)
        #print(str(status) + "\n" + json.dumps(response, indent=2))
        if status['code'] != 0:
            self.print_error("Unable to do per device mapping to device {}".format(self.name))
        return
    
    def address_mapping(self, api, address):
        print("\n>>> Config {} address mapping pour {}".format(address, self.name))
        url = "/pm/config/adom/{}/obj/firewall/address/{}".format(self.adom, address)
        #On récupère l'objet NET-LAN
        status, response = api.get(url)
        #self.print_response(status, response)
        # si la réponse de la requete échoue, l'objet n'existe PROBABLEMENT pas (cf autre erreur ?)
        if status['code'] != 0:
            self.print_error("Object {} doesn't exist".format(address))
        if address == "NET-LAN":
            subnet = "172.16." + str(self.id_site) + ".0/24"
        else:
            subnet = "172.16.1" + str(self.id_site) + ".0/24"
        new_dynamic_mapping={}
        new_dynamic_mapping['_scope'] = self.scope()
        new_dynamic_mapping['subnet'] = subnet
        if response['dynamic_mapping'] != None:
            response['dynamic_mapping'].append(new_dynamic_mapping)
        else:
            response['dynamic_mapping'] = new_dynamic_mapping
        data = {
            'dynamic_mapping' : response['dynamic_mapping'],        
        }
        #print(json.dumps(data, indent=4))
        status, response = api._do('set',url, data)
        #print(str(status) + "\n" + json.dumps(response, indent=2))
        if status['code'] != 0:
            self.print_error("Unable to do per device mapping to {} for device {}".format(address, self.name))
        return
    
    def link_device(self, api):
        print("\n>>> Link {} to real device".format(self.name))
        url = 'dvmdb/device/{}'.format(self.name)
        data = {
            'flags' : [ 'is_model' , 'linked_to_model' ]
        }
        status, response = api._do('update', url, data) 
        #print(str(status) + "\n" + json.dumps(response, indent=2))
        if status['code'] != 0:
            self.print_error("Unable to link to real device")
        return


    def install_config(self, api):
        print("\n>>> Installation des configurations du device {}".format(self.name))
        status, response = api.install_package(self.adom, self.policy_package, [self.scope()])
        #if response['taskid']:
        #    status, response = api.taskwait(response['taskid'])
        #else:
        #    return status, response
        #print(str(status) + "\n" + json.dumps(response, indent=2))
        #if response['line'][0]['err'] != 0:
        #    self.print_error("Unable install config for device {}".format(self.name))
        return

    def print_error(self, msg):
        print("Error {} : {}".format(self.name, msg))
        return

    def print_response(self, status, response):
        if status['code'] != 0:
            print(status['message'])
        # Debug
        print(json.dumps(response, indent=2))
        return