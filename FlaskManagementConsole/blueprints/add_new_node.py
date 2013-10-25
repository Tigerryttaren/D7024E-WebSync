from os import listdir, remove
from os.path import isfile, isdir, join, abspath, getmtime, getsize
from datetime import datetime
from flask import Flask, render_template, Blueprint, request, redirect, make_response
from werkzeug import secure_filename

import subprocess
import time
import boto
import boto.ec2

from os import system
#import uuid

management_console = Blueprint('add_new_node', __name__, template_folder='../templates')
node_list = []
instance_list = []
docker_image_name=""
#current_ip = ""

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

class Instance(object):
	#TODO Which field should an instance have?

	id = ""
	ip = ""
	number = 0

	def __init__(self, id, ip, number):
		self.id = id
		self.ip = ip
		self.number = number
	



# BOTO stuff and things related to those stuffs
image_name = "ubuntu-12.04-lts-x86_64" # add name of standard everytime run image from OpenStack

boto_region = boto.ec2.regioninfo.RegionInfo(name="nova", endpoint="130.240.233.106")
boto_conn = boto.connect_ec2(
aws_access_key_id = "7a2da111b5934c14be7fa1f2b45ea45d",
aws_secret_access_key = "507d4bb12b614b2f8c36648564ef8fbe",
is_secure = False, 
region = boto_region,
port = 8773,
path = "/services/Cloud")

# ===
# Redirects

@management_console.route('/')
def index():
	return redirect('/nodes')

# ===
# === Actual Paths

@management_console.route('/instances')
def list_instances():
	#TODO: Fix functionality for displaying the instances	
	return render_template('instanceList.html')
	
@management_console.route('/instances/add')
def add_instance():

	# Starts the instance on OpenStack
	response = boto_conn.run_instances(
	image_name,
	key_name = "websync",
	instance_type = "m1.tiny",
	security_groups = ["websync"],
	)
	
	for instance in response.instances:
		while instance.private_ip_address == "":
			instance.update()
	inst = response.instances[0]
	
	# Adding it to the display list
	instance_list.append(inst) 

	address_alloc = boto_conn.allocate_address()
	address = (str(address_alloc).split(":"))[1]	

	boto_conn.associate_address(inst, address)
	
	#TODO: ADD FUCTIONALITY FOR DISPLAYING THE INSTANCES
	
	return redirect('/instances')

@management_console.route('/in')
	

@management_console.route('/nodes')
def list_nodes():
	# change path to /instances/<instande_id>/nodes
	# add ssh in to instance from URL and then run all this shit?

	output = subprocess.check_output(["sudo", "docker", "ps"])
	output = output.split('\n')
	output.pop(0)				# removes first item due to was only headers
	output.pop()				# removes last item due to it was empty

	#node_list = []
	if len(output) is 0:			# handles empty list
		pass
	else: 
		for item in output:
			temp = item.split(" ")	
			temp = filter(None, temp)
			tempid = temp[0]		# get the first
			tempport = temp[len(temp)-1]	# get the last
			
			exists = False
			
			for node in node_list:
				if tempid == node.id:
					exists = True
					break
				else:
					pass
			
			if exists == False:
				node_list.append(Node(tempid, tempport, False))
			else:
				pass	
	
	return render_template('nodeList.html', node_list=node_list)

@management_console.route('/nodes/add', methods=['GET', 'POST'])
def add_node():
	if request.method == 'POST':
		port = request.form.get('port_number')		
		broker = request.form.get('message_broker')		
		system("sudo docker run -d -p :" + port + " " + docker_image_name + " python /D7024E-WebSync-develop/FlaskWebServer/run.py " + port + " " + broker)
		
		return redirect('/nodes')
	return render_template('addNode.html')

@management_console.route('/nodes/<string:node_id>', methods=['GET'])
def node_info(node_id):		
	for node in node_list:
		if node.id == node_id:
			return render_template('nodeInfo.html', node=node)
		else:
			pass
		
	return render_template('nodeInfo.html')

@management_console.route('/nodes/<string:node_id>/delete', methods=['GET', 'DELETE'])
def delete_node(node_id):
	
	system("sudo docker stop " + node_id)
	system("sudo docker rm " + node_id)
	
	for node in node_list:
		if node.id == node_id:
			node_list.remove(node)
		else: 	
			pass
	
	return redirect('/nodes')


# ===

# ===
# Support Functions


