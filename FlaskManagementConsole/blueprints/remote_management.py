from commands import getoutput
from requests import post
from flask import Flask, Blueprint, jsonify, json

remote_management = Blueprint('remote_management', __name__, template_folder='../templates')

class Node(object):
	#TODO: Which fields are a node going to have? 
	id = ""
	port = 0
	ip = ""
	synced = False
	
	def __init__(self, id, port, synced):
		self.id = id
		self.port = port
		self.synced = synced

####################### URL Functions #######################

# @remote_management.route('/<string:ip>/nodes', methods=['GET'])
# def test_render(ip):
# 	node_list = get_server_nodes(ip)

@remote_management.route('/json/nodes', methods=['GET'])
def send_json_node_list():
	output = getoutput('sudo docker ps')
	output = output.split('\n')
	output.pop(0)				# removes first item due to was only headers

	node_list = {'running containers':[]}
	if len(output) is 0:			# handles empty list
		pass
	else: 
		for item in output:
			temp = item.split(" ")	
			temp = filter(None, temp)
			tempid = temp[0]		# get the first
			tempport = temp[len(temp)-1]	# get the last
			
			exists = False
			
			for node in node_list['running containers']:
				print 'Comparing %s with %s' % (tempid, node['id'])
				if tempid == node['id']:
					exists = True
					break
				else:
					pass
			
			if exists == False:
				node_list['running containers'].append(
					{
						'id':tempid,
						'port':tempport,
						'synced':False
					})
			else:
				pass
	return jsonify(node_list)	

####################### Other Functions #######################

def get_server_nodes(ip_addr):
	nodes_json = json.loads(requests.get('http://%s/json/nodes' % ip_addr).text)
	node_list = []
	for node in nodes_json['running containers']:
		node_list.append(Node(node['id'], node['port'], node=['synced']))
	return node_list

def make_remote_node(ip_addr, port, message_broker):
	requests.post('http://%s/nodes/add' % ip_addr, data={'port_number':str(port), 'message_broker':message_broker})

def delete_node(ip_addr, node_id):
	requests.delete('http://%s/nodes/%s/delete' % (ip_addr, node_id))