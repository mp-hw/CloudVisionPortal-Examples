#
# Copyright (c) 2016, Arista Networks, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
#   Neither the name of Arista Networks nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ARISTA NETWORKS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

#!/usr/bin/env python

import cvp, optparse, json
from string import Template

#
# Parse command line options
#

usage = 'usage: %prog [options]'
op = optparse.OptionParser(usage=usage)
op.add_option( '-c', '--cvphostname', dest='cvphostname', action='store', help='CVP host name FQDN or IP', type='string')
op.add_option( '-u', '--cvpusername', dest='cvpusername', action='store', help='CVP username', type='string')
op.add_option( '-p', '--cvppassword', dest='cvppassword', action='store', help='CVP password', type='string')
op.add_option( '-n', '--name', dest='dcname', action='store', help='Name of DC to build', type='string')
op.add_option( '-s', '--spines', dest='spines', action='store', help='Number of spine switches in DC fabric', type='int')
op.add_option( '-l', '--leafs', dest='leafs', action='store', help='Number of leaf switch MLAG pairs in DC fabric', type='int')
op.add_option( '-d', '--defaultgw', dest='defaultgw', action='store', help='Default gateway for management network', type='string')
op.add_option( '-m', '--mgmtnetwork', dest='mgmtnet', action='store', help='Management network prefix without last octet. Example: 192.168.0.', type='string')
op.add_option( '-o', '--mgmtnetmask', dest='mgmtnetmask', action='store', help='Management network netmask in bit length. Example: 24', type='int')
op.add_option( '-v', '--vxlanloopback', dest='vxlanloopback', action='store', help='Prefix to use for VXLAN loobacks without last octet. Example: 192.168.0.', type='string')
op.add_option( '-z', '--loopback', dest='loopback', action='store', help='Prefix to use for loobacks without last octet. Example: 192.168.0.', type='string')
op.add_option( '-x', '--linknetworks', dest='linknetwork', action='store', help='Prefix to use for linknetworks without last octet. Example: 192.168.0.', type='string')
op.add_option( '-t', '--type', dest='deploymenttype', action='store', help='Type of deployment, her for ip fabric HER, cvx for ip fabric cvx, evpn for ip fabric EVPN', type='string')
op.add_option( '-a', '--debug', dest='debug', action='store', help='If debug is yes, nothing will actually be sent to CVP and proposed configs are written to terminal', type='string', default='no')

opts, _ = op.parse_args()

#
# Assign command line options to variables and assign static variables
#

host = opts.cvphostname
user = opts.cvpusername
password = opts.cvppassword
name = opts.dcname
no_spine = opts.spines
no_leaf = opts.leafs
defaultgw = opts.defaultgw
mgmtnetwork = opts.mgmtnet
mgmtnetmask = opts.mgmtnetmask
vxlanloopback = opts.vxlanloopback
loopback = opts.loopback
linknetwork = opts.linknetwork
deploymenttype = opts.deploymenttype
debug = opts.debug

parentName = 'Tenant'
my_spine_container_name = name + " Spine"
my_leaf_container_name = name + " Leaf"
dc_configlet_name = name + " Base config"
configlet_list = []

#
# Build the DC list of switches in dictionary form
#

linksubnetcounter = 0
loopbackcounter = 0
vxlanloopbackcounter = 0
mgmtnetworkcounter = 1

DC = []
Leafs = []

for counter in range(1,no_spine+1):
	spine_name = name + "spine" + str(counter)
	interface_list = []
	element_dict = {}
	element_dict['name'] = spine_name
	element_dict['loopback'] = loopback + str(loopbackcounter)
	loopbackcounter = loopbackcounter + 1
	element_dict['mgmt'] = mgmtnetwork + str(mgmtnetworkcounter)
	mgmtnetworkcounter = mgmtnetworkcounter + 1

	for counter2 in range(1,no_leaf+1):
		spine_interface_name = "Ethernet"+str(counter2)
		leaf_name = name + "leaf" + str(counter2)
		neighbor_dict = {}
		neighbor_dict['neighbor'] = leaf_name
		link = linknetwork + str(linksubnetcounter)
		neighborlink = linknetwork + str(linksubnetcounter+1)
		linksubnetcounter = linksubnetcounter + 2
		neighbor_dict['linknet'] = link
		neighbor_dict['neighbor_ip'] = neighborlink
		neighbor_dict['neighbor_interface'] = "Ethernet" + str(counter)
		neighbor_dict['local_interface'] = spine_interface_name
		if deploymenttype == "evpn":
			neighbor_dict['asn'] = 65000 + counter2
		interface_list.append(neighbor_dict)
		
	element_dict['interfaces'] = interface_list
	DC.append(element_dict)

for counter in range (1,no_leaf+1):
	leaf_dict = {}
	leaf_dict['name'] = name + "leaf" + str(counter)
	leaf_dict['loopback'] = loopback + str(loopbackcounter)
	loopbackcounter = loopbackcounter +1
	leaf_dict['vxlan'] = vxlanloopback + str(vxlanloopbackcounter)
	vxlanloopbackcounter = vxlanloopbackcounter +1
	leaf_dict['mgmt'] = mgmtnetwork + str(mgmtnetworkcounter)
	mgmtnetworkcounter = mgmtnetworkcounter + 1
	if deploymenttype == "evpn":
		asn = 65000 + counter
		leaf_dict['asn'] = asn

	Leafs.append(leaf_dict)

if debug != "no":
	print '%s' % ( json.dumps(DC, sort_keys=True, indent=4) )
	print '!'
	print '!'
	print '!'
	print '%s' % ( json.dumps(Leafs, sort_keys=True, indent=4) )

#
# Connect and authenticate with CVP server
#

if debug == "no":
	server = cvp.Cvp( host )
	server.authenticate( user , password )

#
# Build base config configlets for spines and add them to CVP.
# Start with config that is the same in all deployment types.
#

for spine_switch in DC:
	Replacements = {
					"hostname": spine_switch['name'],
					"loopaddress": spine_switch['loopback'],
					"mgmtaddress": spine_switch['mgmt'],
					"mgmtnetmask": mgmtnetmask
					}

	spine_base_config = Template("""
!
hostname $hostname
!
interface Loopback0
   ip address $loopaddress/32
!
interface Management1
   ip address $mgmtaddress/$mgmtnetmask
""").safe_substitute(Replacements)
	
	for interface in spine_switch['interfaces']:
		Replacements = {
						"local_interface": interface['local_interface'] ,
						"description": interface['neighbor'],
						"linknet": interface['linknet']
						}
		add_to_spine_config = Template("""
!
interface $local_interface
   description $description
   ip address $linknet/31
!""").safe_substitute(Replacements)

		spine_base_config = spine_base_config + add_to_spine_config

	if debug == "no":
		spine_configlet_name = spine_switch['name'] + " configuration"
		spine_configlet = cvp.Configlet( spine_configlet_name , spine_base_config )
		server.addConfiglet( spine_configlet )
	else:
		spine_configlet_name = spine_switch['name'] + " configuration"
		print "Contents of configlet %s:" % ( spine_configlet_name )
		print "%s" % ( spine_base_config )
		print "!"
		print "!"
		print "!"
#
# Create config unique for spine in cvx and her deployment types
#

	if deploymenttype == "her" or deploymenttype == "cvx":
		Replacements = {
						"routerid": spine_switch['loopback'],
						"linknet": linknetwork + "0/24"
						}

		spine_bgp_config = Template("""
router bgp 65000
   router-id $routerid
   maximum-paths 4
   bgp listen range $linknet peer-group leafs remote-as 65001
   neighbor leafs peer-group
   neighbor leafs allowas-in 3
   neighbor leafs fall-over bfd
   neighbor leafs maximum-routes 12000 
   redistribute connected""").safe_substitute(Replacements)

#
# Create config unique for spine in evpn deployment type
#

	if deploymenttype == "evpn":
		Replacements = {
						"routerid": spine_switch['loopback'],
						"linknet": linknetwork
						}

		spine_bgp_config = Template("""
router bgp 65000
   router-id $routerid
   maximum-paths 4
   neighbor leafs peer-group
   neighbor leafs fall-over bfd
   neighbor leafs maximum-routes 12000 
   redistribute connected""").safe_substitute(Replacements)

		for interface in spine_switch['interfaces']:
			Replacements = {
							"neighbor": interface['neighbor_ip'],
							"asn": interface['asn']
							}
			add_to_sping_bgp_config = Template("""
   neighbor $neighbor peer-group leafs
   neighbor $neighbor remote-as $asn""").safe_substitute(Replacements)
			spine_bgp_config = spine_bgp_config + add_to_sping_bgp_config

	if debug == "no":
		spine_bgp_configlet_name = spine_switch['name'] + " BGP configuration"
		spine_bgp_configlet = cvp.Configlet( spine_bgp_configlet_name , spine_bgp_config )
		server.addConfiglet( spine_bgp_configlet )
	else:
		spine_bgp_configlet_name = spine_switch['name'] + " BGP configuration"
		print "Contents of configlet %s:" % ( spine_bgp_configlet_name )
		print "%s" % ( spine_bgp_config )
		print "!"
		print "!"
		print "!"


#
# Build base config configlets for leafs and add them to CVP.
# Start with config that is the same in all deployment types.
#

for leaf in Leafs:
	if deploymenttype == "cvx" or deploymenttype == "her":
		Replacements = {
						"hostname": leaf['name'],
						"loopback": leaf['loopback'],
						"vxlan": leaf['vxlan']
						}
		leaf_config = Template("""
!
hostname $hostname
!
interface Loopback0
   ip address $loopback/32
!
interface Loopback1
   ip address $vxlan/32
!
""").safe_substitute(Replacements)

	if deploymenttype == "evpn":
		Replacements = {
						"hostname": leaf['name'],
						"loopback": leaf['loopback'],
						}
		leaf_config = Template("""
!
hostname $hostname
!
interface Loopback0
   ip address $loopback/32
!
""").safe_substitute(Replacements)		
#
# Create Vxlan1 config based on CVX
#

	if deploymenttype == "cvx":
		Replacements = { "dummy": "dummy"
						}
		vxlan_add_to_leaf_config = Template("""
interface Vxlan1
   vxlan source-interface Loopback1
   vxlan udp-port 4789
   vxlan controller-client
!
""").safe_substitute(Replacements)
		leaf_config = leaf_config + vxlan_add_to_leaf_config

#
# Create Vxlan1 config based on HER
#

	if deploymenttype == "her":
		Replacements = { "dummy": "dummy"
						}
		vxlan_add_to_leaf_config = Template("""
interface Vxlan1
   vxlan source-interface Loopback1
   vxlan udp-port 4789
!
""").safe_substitute(Replacements)

	if deploymenttype == "evpn":
		Replacements = { "dummy": "dummy"
						}
		vxlan_add_to_leaf_config = Template("""
interface Vxlan1
   vxlan source-interface Loopback0
   vxlan udp-port 4789
!
""").safe_substitute(Replacements)

		leaf_config = leaf_config + vxlan_add_to_leaf_config

	if deploymenttype == "her" or deploymenttype == "cvx":
		Replacements = {
						"routerid": leaf['loopback']
						}
		leaf_bgp_config = Template("""
router bgp 65001
   router-id $routerid
   maximum-paths 4
   neighbor spines peer-group
   neighbor spines remote-as 65000
   neighbor spines allowas-in 3
   neighbor spines ebgp-multihop 4
   neighbor spines maximum-routes 12000""").safe_substitute(Replacements)

	if deploymenttype ==  "evpn":
		Replacements = {
						"asn": leaf['asn'] ,
						"routerid": leaf['loopback']
						}
		leaf_bgp_config = Template("""
router bgp $asn
   router-id $routerid
   neighbor EVPN peer-group
   neighbor EVPN update-source Loopback0
   neighbor EVPN ebgp-multihop
   neighbor EVPN send-community extended
   neighbor EVPN maximum-routes 12000 
   neighbor spines peer-group
   neighbor spines remote-as 65000
   neighbor spines fall-over bfd
   neighbor spines ebgp-multihop 4
   neighbor spines maximum-routes 12000""").safe_substitute(Replacements)

#
# Build interface config for each leaf
#

	for spine_switch in DC:
		for interface in spine_switch['interfaces']:
			if interface['neighbor'] == leaf['name']:
				Replacements = {
								"interface": interface['neighbor_interface'],
								"description": spine_switch['name'],
								"neighbor_ip": interface['neighbor_ip']
								}
				add_to_leaf_config = Template("""
!
interface $interface
   description $description
   ip address $neighbor_ip/31
!
""").safe_substitute(Replacements)
				leaf_config = leaf_config + add_to_leaf_config

				if deploymenttype == "her" or deploymenttype == "cvx":
					Replacements = {
									"neighborip": interface['neighbor_ip']
									}
					add_to_leaf_bgp_config = Template("""
   neighbor $neighborip peer-group spines""").safe_substitute(Replacements)
					leaf_bgp_config = leaf_bgp_config + add_to_leaf_bgp_config

				if deploymenttype == "evpn":
					Replacements = {
									"neighborip": interface['neighbor_ip']
					}
					add_to_leaf_bgp_config = Template("""
   neighbor $neighborip peer-group spines""").safe_substitute(Replacements)
					leaf_bgp_config = leaf_bgp_config + add_to_leaf_bgp_config
					
	if deploymenttype == "evpn":
		for evpnleaf in Leafs:
			if evpnleaf['loopback'] != leaf['loopback']:
				Replacements = {
								"loopback": evpnleaf['loopback'],
								"asn": evpnleaf['asn']
								}
				add_to_leaf_bgp_config = Template("""
   neighbor $loopback peer-group EVPN
   neighbor $loopback remote-as $asn""").safe_substitute(Replacements)
				leaf_bgp_config = leaf_bgp_config + add_to_leaf_bgp_config

	if deploymenttype == "evpn":
	
		add_to_leaf_bgp_config = """
   address-family evpn"""
		leaf_bgp_config = leaf_bgp_config + add_to_leaf_bgp_config

	if deploymenttype == "evpn":
		for evpnleaf in Leafs:
			if evpnleaf['loopback'] != leaf['loopback']:
				Replacements = {
								"loopback": evpnleaf['loopback'],
								"asn": evpnleaf['asn']
								}
				add_to_leaf_bgp_config = Template("""
      neighbor $loopback activate""").safe_substitute(Replacements)
				leaf_bgp_config = leaf_bgp_config + add_to_leaf_bgp_config

	if deploymenttype == "evpn":
		add_to_leaf_bgp_config = """
   address-family ipv4
      redistribute connected"""
		leaf_bgp_config = leaf_bgp_config + add_to_leaf_bgp_config

	if deploymenttype == "evpn":
		for evpnleaf in Leafs:
			if evpnleaf['loopback'] != leaf['loopback']:
				Replacements = {
								"loopback": evpnleaf['loopback'],
								"asn": evpnleaf['asn']
								}
				add_to_leaf_bgp_config = Template("""
      no neighbor $loopback activate""").safe_substitute(Replacements)
				leaf_bgp_config = leaf_bgp_config + add_to_leaf_bgp_config

#
# Based on all config, create configlets
#

	if debug == "no":
		leaf_configlet_name = leaf['name'] + " configuration"
		leaf_configlet = cvp.Configlet( leaf_configlet_name , leaf_config )
		server.addConfiglet( leaf_configlet )
		leaf_bgp_configlet_name = leaf['name'] + " bgp configuration"
		leaf_bgp_configlet = cvp.Configlet( leaf_bgp_configlet_name , leaf_bgp_config )
		server.addConfiglet( leaf_bgp_configlet )
	else:
		leaf_configlet_name = leaf['name'] + " configuration"
		print "Contents of configlet %s:" % ( leaf_configlet_name )
		print "%s" % ( leaf_config )
		print "!"
		print "!"
		print "!"
		leaf_bgp_configlet_name = leaf['name'] + " bgp configuration"
		print "Contents of configlet %s:" % ( leaf_bgp_configlet_name )
		print "%s" % ( leaf_bgp_config )
		print "!"
		print "!"
		print "!"

#
# Create needed configlets for the new DC
#

Replacements = {
                "defaultgw": defaultgw
                }

dc_base_config = Template("""
transceiver qsfp default-mode 4x10G
snmp-server community private rw
snmp-server community public ro
!
spanning-tree mode mstp
!
no aaa root
!
username becs privilege 15 secret 5 $1$edXmdxfz$lwH8NTWgA/q3DC8a456JN0
username cvpadmin privilege 15 secret 5 $1$E6VAxeV9$rMrf9bnHXs0AkCM8RJ/kt0
username df privilege 15 secret 5 $1$yorRLk72$Js0Z3mXVE0hydvFYGAQ0r.
ip virtual-router mac-address 00:11:22:33:44:55
!
ip route 0.0.0.0/0 $defaultgw
ip routing
!
management api http-commands
   protocol http
   cors allowed-origin all
   no shutdown
""").safe_substitute(Replacements)

if debug == "no":
	dc_configlet = cvp.Configlet( dc_configlet_name , dc_base_config  )
	server.addConfiglet( dc_configlet )
	configlet_list.append( dc_configlet )
else:
		print "Contents of configlet %s:" % ( dc_configlet_name )
		print "%s" % ( dc_base_config )
		print "!"
		print "!"
		print "!"


#
# Create Container structure for new DC
#

if debug == "no":
	my_dc_container = cvp.Container( name, parentName )
	server.addContainer( my_dc_container )
	server.mapConfigletToContainer( my_dc_container , configlet_list )

	my_leaf_container = cvp.Container( my_leaf_container_name , name )
	server.addContainer( my_leaf_container )

	my_spine_container = cvp.Container( my_spine_container_name , name )
	server.addContainer( my_spine_container )
