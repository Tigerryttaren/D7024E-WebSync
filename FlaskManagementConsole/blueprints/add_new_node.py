from os import listdir, remove
from os.path import isfile, isdir, join, abspath, getmtime, getsize
from datetime import datetime
from flask import Flask, render_template, Blueprint, request, redirect, make_response
from werkzeug import secure_filename

management_console = Blueprint('add_new_node', __name__, template_folder='../templates')
node_list = []

class Node(object):
	id = ""
	synced = False
	#TODO: Fill with serious fields
	cats = 0
# ===
# Redirects

@management_console.route('/')
def index():
	return redirect('/nodes')

# ===
# === Real Paths

@management_console.route('/nodes')
def list_nodes():
	#TODO: Implement
	return render_template('nodeList.html', node_list=node_list)

@management_console.route('/nodes/add', methods=['GET', 'POST'])
def add_node():
	#TODO: Implement
	return render_template('addNode.html')

@management_console.route('/nodes/<int:node_id>', methods=['GET'])
def remove_node():
	#TODO: Implement
	return "Specific node with ID from URL"

# ===






 
