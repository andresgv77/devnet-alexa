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

# Agregar una VLAN al administrador de UCS
def add_ucs_vlan(vlan_id):

    vlan_id_num = int(vlan_id)

    from ucsmsdk.mometa.fabric.FabricVlan import FabricVlan
    
    if vlan_id == "1":
        message = ("Para la operacion solicitada de agregar una Vi Lan al Administrador de UCS, " +
            "Vi Lan 1 puede recibir nombres adicionales, sin embargo, esta habilidad no permite ese procedimiento.")
        return message
    elif ((vlan_id_num <= 1) or
        (vlan_id_num >= 4030 and vlan_id_num <= 4048) or
        (vlan_id_num > 4093)):
        message = ("Para la operacion solicitada de agregar una Vi Lan al Administrador de UCS, " + 
            "el ID de la Vlan proporcionado " + vlan_id + ", no esta permitido.")
        return message

    ucsm_login()

    if status['login'] == "listo":
        response = handle.query_dn("fabric/lan/net-vlan" + vlan_id)
    else:
        message = ("hubo un error al conectarse al Administrador UCS, " +
            "compruebe las credenciales de acceso o la direccion IP")
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
            message = "V Lan " + vlan_id + " se ha agregado al Administrador de UCS."
        else:
            message = "V Lan " + vlan_id + " no se agrego al Administrador de UCS."
    else:
        message = "V Lan " + vlan_id + " ya existe en Administrador de UCS."
    
    ucsm_logout()

    return "Para la operacion solicitada de agregar una Vi Lan al Administrador de UCS, " + message

# Eliminar una VLAN del Administrador de UCS
def remove_ucs_vlan(vlan_id):
    
    if vlan_id == "1":
        message = ("Para la operacion solicitada de eliminar una Vi Lan del Administrador de UCS, " + 
            "Esta habilidad no admite la eliminacion de la Vi Lan 1.")
        return message

    ucsm_login()

    if status['login'] == "success":
        response = handle.query_dn("fabric/lan/net-vlan" + vlan_id)
    else:
        message = ("hubo un error al conectarse al Administrador UCS, " +
            "compruebe las credenciales de acceso o la direccion IP")
        return message

    if response and response.name == "vlan" + vlan_id:
        
        handle.remove_mo(response)
        handle.commit()

        response = handle.query_dn("fabric/lan/net-vlan" + vlan_id)

        if not response:
            message = "V Lan " + vlan_id + " se ha eliminado del Administrador de UCS."
        else:
            message = "V Lan " + vlan_id + " no se elimino del Administrador de UCS."
    else:
        message = "V Lan " + vlan_id + " no existe en el Administrador de UCS."
    
    ucsm_logout()

    return "Para la operacion solicitada de eliminar una Vi Lan del Administrador de UCS, " + message

# Retrieve fault counts for, critical, major, minor and warning faults from UCS Manager
def get_ucs_faults():

    ucsm_login()

    if status['login'] == "listo":
        response = handle.query_classid("FaultInst")
    else:
        message = ("hubo un error al conectarse al Administrador UCS, " +
            "compruebe las credenciales de acceso o la direccion IP")
        return message
    
    ucsm_logout()

    sev_critical = 0
    sev_major    = 0
    sev_minor    = 0
    sev_warning  = 0

    for fault in response:
        if fault.severity == 'critico':
            sev_critical += 1
        elif fault.severity == 'mayor':
            sev_major += 1
        elif fault.severity == 'menor':
            sev_minor += 1
        elif fault.severity == 'advertencia':
            sev_warning += 1
 
    message = ("Para la operacion solicitada de recuperacion de fallas del Administrador, hay " +
        str(sev_critical) + " fallas criticas, " +
        str(sev_major) + " fallas mayores, " +
        str(sev_minor) + " fallas menores, y " +
        str(sev_warning) + " advertencias")

    return message

# Crear y asociar un perfil de servicio a un servidor disponible
def set_ucs_server():

    from ucsmsdk.mometa.ls.LsServer import LsServer
    from ucsmsdk.mometa.ls.LsBinding import LsBinding
    from ucsmsdk.mometa.macpool.MacpoolPool import MacpoolPool
    from ucsmsdk.mometa.macpool.MacpoolBlock import MacpoolBlock
    from ucsmsdk.mometa.org.OrgOrg import OrgOrg

    ucsm_login()

    if status['login'] != "success":
        message = ("hubo un error al conectarse al Administrador UCS, " +
            "compruebe las credenciales de acceso o la direccion IP")
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

    message = ("Para la operacion solicitada de aprovisionamiento del servidor del Administrador de UCS," +
        " servidor, " + blade.slot_id + ", " + 
        " en el chasis, " + blade.chassis_id + ", " + 
        " se ha aprovisionado con el perfil de servicio, " + service_profile_name.replace('_',' ') + "," +
        " en la organizacion Dev Net.")
    
    return message

# Retrieve fault counts for, critical, major, minor and warning faults from UCS Manager
def reset_ucs_skill():

    ucsm_login()

    if status['login'] == "listo":
        pass
    else:
        message = ("hubo un error al conectarse al Administrador UCS, " +
            "compruebe las credenciales de acceso o la direccion IP")
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

    message = "Para la operacion solicitadade limpieza del Administrador de UCS, el Administrador de UCS se ha limpiado."

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