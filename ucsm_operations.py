"""
ucsm_operations.py
Purpose:
    UCS Manager functions for the DevNet Alexa Data Center Skill
Author:
    John McDonough (jomcdono@cisco.com)
    Cisco Systems, Inc.
"""

import os
import urllib2
from ucsmsdk.ucshandle import UcsHandle
from ucsmsdk.ucssession import UcsException

ucsmhost = os.environ['UCSMHOST']
handle = None
status = {}

# Add a VLAN to UCS Manager
def add_ucs_vlan(vlan_id):

    vlan_id_num = int(vlan_id)

    from ucsmsdk.mometa.fabric.FabricVlan import FabricVlan
    
    if vlan_id == "1":
        message = ("For the requested UCS Manager V Lan add operation, " +
            "V Lan 1 can be given additional names, however, this skill does not allow for that procedure.")
        return message
    elif ((vlan_id_num <= 1) or
        (vlan_id_num >= 4030 and vlan_id_num <= 4048) or
        (vlan_id_num > 4093)):
        message = ("For the requested UCS Manager V Lan add operation, " + 
            "the provided V Lan I D " + vlan_id + ", is not allowed.")
        return message

    ucsm_login()

    if status['login'] == "success":
        response = handle.query_dn("fabric/lan/net-vlan" + vlan_id)
    else:
        message = ("there was an error connecting to the UCS Manager, " +
            "please check the access credentials or IP address")
        return message

    if not response:
        fabric_lan_cloud = handle.query_dn("fabric/lan")
        vlan = FabricVlan(parent_mo_or_dn=fabric_lan_cloud,
                        name="vlan" + vlan_id,
                        id=vlan_id)

        handle.add_mo(vlan)
        handle.commit()

        response = handle.query_dn("fabric/lan/net-vlan" + vlan_id)

        if response and response.name == "vlan" + vlan_id:
            message = "V Lan " + vlan_id + " has been added to UCS Manager."
        else:
            message = "V Lan " + vlan_id + " was not added to UCS Manager."
    else:
        message = "V Lan " + vlan_id + " already exists on UCS Manager."
    
    ucsm_logout()

    return "For the requested UCS Manager V Lan add operation, " + message

# Remove a VLAN from UCS Manager
def remove_ucs_vlan(vlan_id):
    
    if vlan_id == "1":
        message = ("For the requested UCS Manager V Lan remove operation, " + 
            "this skill does not support the removal of V Lan 1.")
        return message

    ucsm_login()

    if status['login'] == "success":
        response = handle.query_dn("fabric/lan/net-vlan" + vlan_id)
    else:
        message = ("there was an error connecting to the UCS Manager, " +
            "please check the access credentials or IP address")
        return message

    if response and response.name == "vlan" + vlan_id:
        
        handle.remove_mo(response)
        handle.commit()

        response = handle.query_dn("fabric/lan/net-vlan" + vlan_id)

        if not response:
            message = "V Lan " + vlan_id + " has been removed from UCS Manager."
        else:
            message = "V Lan " + vlan_id + " was not removed from UCS Manager."
    else:
        message = "V Lan " + vlan_id + " does not exist on UCS Manager."
    
    ucsm_logout()

    return "For the requested UCS Manager V Lan remove operation, " + message

# Retrieve fault counts for, critical, major, minor and warning faults from UCS Manager
def get_ucs_faults():

    ucsm_login()

    if status['login'] == "success":
        response = handle.query_classid("FaultInst")
    else:
        message = ("there was an error connecting to the UCS Manager, " +
            "please check the access credentials or IP address")
        return message
    
    ucsm_logout()

    sev_critical = 0
    sev_major    = 0
    sev_minor    = 0
    sev_warning  = 0

    for fault in response:
        if fault.severity == 'critical':
            sev_critical += 1
        elif fault.severity == 'major':
            sev_major += 1
        elif fault.severity == 'minor':
            sev_minor += 1
        elif fault.severity == 'warning':
            sev_warning += 1
 
    message = ("For the requested UCS Manager fault retrieval operation, there are " +
        str(sev_critical) + " critical faults, " +
        str(sev_major) + " major faults, " +
        str(sev_minor) + " minor faults, and " +
        str(sev_warning) + " warnings")

    return message

# Create and Associate a Service Profile to an available server
def set_ucs_server():

    from ucsmsdk.mometa.ls.LsServer import LsServer
    from ucsmsdk.mometa.ls.LsBinding import LsBinding
    from ucsmsdk.mometa.macpool.MacpoolPool import MacpoolPool
    from ucsmsdk.mometa.macpool.MacpoolBlock import MacpoolBlock
    from ucsmsdk.mometa.org.OrgOrg import OrgOrg

    ucsm_login()

    if status['login'] != "success":
        message = ("there was an error connecting to the UCS Manager, " +
            "please check the access credentials or IP address")
        return message
    
    # Create Org DevNet
    mo_org = OrgOrg(parent_mo_or_dn="org-root", name="DevNet")
    handle.add_mo(mo_org, modify_present=True)
    handle.commit()

    # Create MacPool
    mac_pool_default = handle.query_dn("org-root/mac-pool-default")
    mo_mac_pool_block = MacpoolBlock(parent_mo_or_dn=mac_pool_default,r_from="00:25:B5:00:00:AA",to="00:25:B5:00:00:D9")
    handle.add_mo(mo_mac_pool_block, modify_present=True)
    handle.commit()

    # Add/Update Service Profile Template
    mo_sp_template = LsServer(parent_mo_or_dn="org-root/org-DevNet", type="initial-template", name="DevNet_Skill_Template")
    handle.add_mo(mo_sp_template, modify_present=True)
    handle.commit()

    # Retrive the MO for the created/updated Service Profile template
    filter_exp = '(name,"DevNet_Skill_Template")'
    mo_sp_templ = handle.query_classid("lsServer",filter_str=filter_exp)
    
    # Retrive MOs for any existing Service Profiles
    filter_exp = '(name,"DevNet_Skill_*", type="re") and (type,"instance")'
    mo_sp_instances = handle.query_classid("lsServer",filter_str=filter_exp)
    
    # Find the highest suffix for existing Service Profiles
    if len(mo_sp_instances) >= 1:
        sp_suffixes = [int(sp_instance.name[sp_instance.name.rindex('_')+1:]) for sp_instance in mo_sp_instances]
        num_sp_instances = max(sp_suffixes) + 1
    else:
        num_sp_instances =1

    # Create the next Service Profile name
    if num_sp_instances <= 9:
        service_profile_name = "DevNet_Skill_Server_0" + str(num_sp_instances)
    else:
        service_profile_name = "DevNet_Skill_Server_" + str(num_sp_instances)

    # Find an available compute blade
    response = handle.query_classid("computeBlade")
    for blade in response:
        if blade.admin_state == 'in-service' and blade.availability == 'available':
            break

    # Create the Service Profile
    mo_sp = LsServer(parent_mo_or_dn="org-root/org-DevNet", src_templ_name="DevNet_Skill_Template", name=service_profile_name)
    mo_sp_templ_ls_binding = LsBinding(parent_mo_or_dn=mo_sp, pn_dn=blade.dn)
    handle.add_mo(mo_sp, modify_present=True)
    handle.commit()

    ucsm_logout()

    message = ("For the requested UCS Manager Server Provisioning operation," +
        " server, " + blade.slot_id + ", " + 
        " in chassis, " + blade.chassis_id + ", " + 
        " has been provisioned with service profile, " + service_profile_name.replace('_',' ') + "," +
        " in the Dev Net Organization.")
    
    return message

# Retrieve fault counts for, critical, major, minor and warning faults from UCS Manager
def reset_ucs_skill():

    ucsm_login()

    if status['login'] == "success":
        pass
    else:
        message = ("there was an error connecting to the UCS Manager, " +
            "please check the access credentials or IP address")
        return message
    
    # Remove the DevNet Org
    mo_org = handle.query_dn("org-root/org-DevNet")
    if mo_org:
        handle.remove_mo(mo_org)
        handle.commit()
    
    # Remove all VLANs other than VLAN 1
    mo_vlans = handle.query_classid("fabricVlan")
    if mo_vlans:
        for vlan in mo_vlans:
            if vlan.id != "1":
                handle.remove_mo(vlan)
        
        handle.commit()

    # Remove all MAC Pool Blocks from the default MAC Pool
    mo_mac_pool_blocks = handle.query_classid("macpoolBlock")
    if mo_mac_pool_blocks:
        for block in mo_mac_pool_blocks:
            handle.remove_mo(block)
        
        handle.commit()

    message = "For the requested UCS Manager clean up operation, the UCS Manager has been cleaned."

    return message


def ucsm_login():

    global handle, status

    username = "admin"
    password = "password"

    try:
        handle = UcsHandle(ucsmhost,username,password)
        if handle.login() == True:
            status['login'] = "success"
            return
    
    except urllib2.URLError as err:
        status['login'] = "URLError"
        return

    except UcsException as err:
        status['login'] = "UcsException"
        return


def ucsm_logout():

    handle.logout()


if __name__ == "__main__":

    print "Accesed Directly!"
    # Uncomment for local testing

    #print get_ucs_faults(), status['login']

    #print add_ucs_vlan("1")
    #print add_ucs_vlan("4029")
    #print add_ucs_vlan("4030")
    #print add_ucs_vlan("0")
    #print add_ucs_vlan("4047")
    #print add_ucs_vlan("4048")
    #print add_ucs_vlan("4093")
    #print add_ucs_vlan("4094")
    #print add_ucs_vlan("100")
    #print add_ucs_vlan("110")
    #print add_ucs_vlan("100")

    #print remove_ucs_vlan("1")
    #print remove_ucs_vlan("4029")
    #print remove_ucs_vlan("4030")
    #print remove_ucs_vlan("0")
    #print remove_ucs_vlan("4047")
    #print remove_ucs_vlan("4048")
    #print remove_ucs_vlan("4093")
    #print remove_ucs_vlan("4094")  
    #print remove_ucs_vlan("100")
    #print remove_ucs_vlan("110")
    #print remove_ucs_vlan("100")

    #print set_ucs_server()
    #print set_ucs_server()
    #print set_ucs_server()
    #print set_ucs_server()

    print reset_ucs_skill()
