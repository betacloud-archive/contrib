#!/usr/bin/env python

import openstack

conn = openstack.connect(cloud='service')

for network in conn.network.networks():
    if network.is_admin_state_up == False or network.is_router_external:
         continue

    is_dhcp_enabled = False
    for subnet in network.subnet_ids:
        subnet = conn.network.find_subnet(subnet)
        if subnet.is_dhcp_enabled:
            is_dhcp_enabled = True

    if is_dhcp_enabled:
        agents = conn.network.network_hosting_dhcp_agents(network)
        length = sum(1 for x in agents)
        if length < 2:
            print(network.name)

            for agent in conn.network.agents(binary="neutron-dhcp-agent"):
                conn.network.add_dhcp_agent_to_network(agent, network)
