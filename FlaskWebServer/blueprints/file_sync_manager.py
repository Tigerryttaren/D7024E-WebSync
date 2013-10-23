import pika
import commands
import threading
from unicodedata import normalize
from urllib import urlretrieve
from datetime import datetime
from os import listdir, system
from os.path import isfile, getmtime, join
from flask import Flask, render_template, Blueprint, json, jsonify, current_app
from variables import file_folder_path

file_sync_manager = Blueprint('file_sync_manager', __name__, template_folder='../templates')

rabbitMQ_message_broaker = '' # Edited by run.py
flask_port = 0 # Edited by run.py

####################### URL Functions #######################

@file_sync_manager.route('/sync', methods=['GET'])
def index_page():
	message = { 'local ip':local_ip(), 'port':flask_port, 'files':JSON_files_info() }
	send_update(json.dumps(message, indent=2))
	return render_template('fileSyncMessage.html')


####################### RabbitMQ Functions #######################

def wait_for_update():
	connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQ_message_broaker))
	channel = connection.channel()

	channel.exchange_declare(exchange='update', type='fanout')
	result = channel.queue_declare(exclusive=True)
	queue_name = result.method.queue
	channel.queue_bind(exchange='update', queue=queue_name)
	print ' [*] Waiting for messages. To exit press CTRL+C'

	def callback(ch, method, properties, body):
		handle_update_message(body)

	channel.basic_consume(callback, queue=queue_name, no_ack=True)
	channel.start_consuming()

def send_update(update_message):
	connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQ_message_broaker))
	channel = connection.channel()
	channel.exchange_declare(exchange='update_request', type='fanout')
	channel.basic_publish(exchange='update_request', routing_key='', body=update_message)
	print " [x] Sent update message"
	connection.close()

def handle_update_message(update_message):
	update_dict = json.loads(update_message)
	if str(update_dict['local ip']) != local_ip() or update_dict['port'] != flask_port:
		# --- The check below is now done at server level ---
		# local_files = { 'files':JSON_files_info() }
		# index_counter = 0
		# # Removes files that are already in the local file system
		# for file in update_dict['files']:
		# 	for local_file in local_files['files']:
		# 		if local_file['name'] == file['name'] and local_file['last edited'] == file['last edited']:
		# 			del update_dict['files'][index_counter]
		# 	index_counter += 1

		for file in update_dict['download']:
			complete_folder_path = '%s/%s' % (commands.getoutput('pwd'), file_folder_path)
			file_url = 'http://%s:%r/download/%s' % (update_dict['local ip'], update_dict['port'], file['name'])
			print 'Downloading: %s' % file['name']
			complete_file_path = str(complete_folder_path + file['name'])
			urlretrieve(file_url, complete_file_path)
			system('touch -m -t ' + str(convert_from_UNIX_time(file['last edited'])) + ' ' + complete_file_path) 
		for file in update_dict['delete']:
			complete_folder_path = '%s/%s' % (commands.getoutput('pwd'), file_folder_path)
			print "Removing " + str(complete_folder_path + file['name'])
			system('rm %s' % str(complete_folder_path + file['name']))
	elif str(update_dict['local ip']) == local_ip() and update_dict['port'] == flask_port and update_dict['conflict']:
		for file in update_dict['conflict']:
			print "Conflict detected with file: %s" % file['name']
			complete_file_path = '%s/%s%s' % (commands.getoutput('pwd'), file_folder_path, file['name'])
			system('mv %s "%s"' % (complete_file_path, complete_file_path + '(conflict)'))
			# Download from server

####################### Other Functions #######################

def JSON_files_info():
	file_name_list = listdir(file_folder_path)
	files = []
	for file_name in file_name_list:
		if isfile(join(file_folder_path, file_name)):
			files.append(
			{
				"name":file_name,
				"path":join(file_folder_path, file_name),
				"last edited":str(int(getmtime(join(file_folder_path, file_name)))), # Contains a dot and is therefore typecast to string
				"size":commands.getoutput('wc -c < %s' % join(file_folder_path, file_name))
			})
	return files

def local_ip():
	network_adapter = commands.getoutput("/sbin/ifconfig").split("\n")[0].split()[0]
	if network_adapter != 'docker0':
		return (commands.getoutput("/sbin/ifconfig").split("\n")[1].split()[1][5:])
	else:
		return str(commands.getoutput("/sbin/ifconfig").split("\n")[35].split()[1][5:])

def convert_from_UNIX_time(UNIX_time):
	return datetime.fromtimestamp(float(UNIX_time)).strftime('%Y%m%d%H%M.%S')
