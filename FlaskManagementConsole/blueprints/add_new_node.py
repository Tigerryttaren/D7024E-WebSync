from os import listdir, remove
from os.path import isfile, isdir, join, abspath, getmtime, getsize
from datetime import datetime
from flask import Flask, render_template, Blueprint, request, redirect, make_response
from werkzeug import secure_filename

from os import system
import uuid

management_console = Blueprint('add_new_node', __name__, template_folder='../templates')
node_list = []


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
	#TODO: Implement
	return render_template('nodeList.html', node_list=node_list)

@management_console.route('/nodes/add', methods=['GET', 'POST'])
def add_node():
	#TODO: Implement
	if request.method == 'POST':
		port = request.form.get('port_number')
		id = uuid.uuid4()
		status = False
		node_list.append(Node(id, port, status))
		# Running bash command from python?
		# begin EXPERIMENTAL
		
		#system("")
		system("sudo docker run -d -p :" + port  +  " WebSync python /D7024E-WebSync-develop/FlaskWebServer/run.py " + port)

		# end EXPERIMENTAL
		return redirect('/nodes')
	return render_template('addNode.html')

@management_console.route('/nodes/<int:node_id>', methods=['GET'])
def remove_node():
	#TODO: Implement
	return "Specific node with ID from URL"

# ===

# ===
# Support Functions

