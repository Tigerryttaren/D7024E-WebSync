from os import listdir, remove
from os.path import isfile, isdir, join, abspath, getmtime, getsize
from datetime import datetime
from flask import Flask, render_template, Blueprint, request, redirect, make_response
from werkzeug import secure_filename

import subprocess
import time

from os import system
import uuid

management_console = Blueprint('add_new_node', __name__, template_folder='../templates')
node_list = []
docker_image_name=""

class Node(object):
	#TODO: Which fields are a node going to have? 
	id = ""
	port = 0
	synced = False
	
	def __init__(self, id, port, synced):
		self.id = id
		self.port = port
		self.synced = synced
	
# ===
# Redirects

@management_console.route('/')
def index():
	return redirect('/nodes')

# ===
# === Actual Paths

@management_console.route('/nodes')
def list_nodes():
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
	#TODO: Implement
	
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

