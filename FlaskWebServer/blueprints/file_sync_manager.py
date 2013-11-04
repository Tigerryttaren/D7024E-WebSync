import pika
import commands
import threading
from unicodedata import normalize
from urllib import urlretrieve
from datetime import datetime
from os import listdir, system
from os.path import isfile, getmtime, join
from flask import Flask, render_template, Blueprint, json, jsonify, current_app
from variables import file_folder_path, sync_metadata_file
from requests import post, get

from time import sleep # Remove later

file_sync_manager = Blueprint('file_sync_manager', __name__, template_folder='../templates')

rabbitMQ_message_broaker = '' # Edited by run.py
rabbitMQ_message_broaker_file_port = 5000
flask_port = 0 # Edited by run.py
is_synced = False

####################### URL Functions #######################

@file_sync_manager.route('/sync', methods=['GET'])
def index_page():
	current_files = JSON_files_info(file_folder_path)
	file = open(sync_metadata_file, 'r')
	last_synced = json.loads(file.read())
	file.close()
	files_to_upload = [file for file in current_files if file not in last_synced['files']]
	files_to_delete = []
	if len(current_files) > 0:
		for old_file in last_synced['files']:
			for new_file_index, new_file in enumerate(current_files):
				if old_file['name'] == new_file['name']:
					break
				elif new_file_index == len(current_files)-1:
					files_to_delete.append(old_file)
	else:
		files_to_delete = last_synced['files']
	message = json.dumps({'new':files_to_upload, 'deleted':files_to_delete, 'local ip':local_ip(), 'port':flask_port}, indent=2)
	send_update(message)
	wait_for_ack(message)
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

def wait_for_ack(update_request):
	connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQ_message_broaker))
	channel = connection.channel()

	channel.exchange_declare(exchange='update_ack', type='fanout')
	result = channel.queue_declare(exclusive=True)
	queue_name = result.method.queue
	channel.queue_bind(exchange='update_ack', queue=queue_name)
	print ' [*] Waiting for server'

	def callback(ch, method, properties, body):
		handle_ack_from_server(body, update_request)
		channel.basic_cancel(consumer_tag='temp')

	channel.basic_consume(callback, queue=queue_name, no_ack=True, consumer_tag='temp')
	channel.start_consuming()	

def send_update(update_message):
	connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQ_message_broaker))
	channel = connection.channel()
	channel.exchange_declare(exchange='update_request', type='fanout')
	channel.basic_publish(exchange='update_request', routing_key='', body=update_message)
	print " [x] Sent update message"
	connection.close()

def handle_ack_from_server(message, update_request):
	print 'Ack from server received: %s' % message
	message = json.loads(message)
	for file in message['edit conflicts']:
		path = complete_sync_file_path(file['name'])
		system('mv %s %s[conflict]' % (path, path))
		download_file(rabbitMQ_message_broaker, rabbitMQ_message_broaker_file_port, file['name'])
	for file in message['delete conflicts']:
		download_file(rabbitMQ_message_broaker, rabbitMQ_message_broaker_file_port, file['name'])
		path = complete_sync_file_path(file['name'])
		system('mv %s %s[newer]' % (path, path))
	update_request = json.loads(update_request)
	update_request['new'][:] = (file for file in update_request['new'] if file not in message['delete conflicts'])
	upload_to_master(update_request['new'])
	update_metadata_file()

# TODO: use helper functions instead
def handle_update_message(update_message):
	update_dict = json.loads(update_message)
	if str(update_dict['local ip']) != local_ip() or update_dict['port'] != flask_port:
		for file in update_dict['download']:
			complete_folder_path = '%s/%s' % (commands.getoutput('pwd'), file_folder_path)
			file_url = 'http://%s:%r/download/%s' % (update_dict['local ip'], update_dict['port'], file['name'])
			print 'Downloading: %s' % file['name']
			complete_file_path = str(complete_folder_path + file['name'])
			try:
				urlretrieve(file_url, complete_file_path)
			except IOError:
				sleep(2) # Just for testing, remove later
				file_url = 'http://%s:%r/download/%s' % (rabbitMQ_message_broaker, rabbitMQ_message_broaker_file_port, file['name'])
				urlretrieve(file_url, complete_file_path)
			system('touch -m -t ' + str(convert_from_UNIX_time(file['last edited'])) + ' ' + complete_file_path) 
		for file in update_dict['delete']:
			complete_folder_path = '%s/%s' % (commands.getoutput('pwd'), file_folder_path)
			print "Removing " + str(complete_folder_path + file['name'])
			system('rm %s' % str(complete_folder_path + file['name']))
		update_metadata_file()


####################### Other Functions #######################

def start_initial_sync():
	files = get('http://%s:%s/json/files' % (rabbitMQ_message_broaker, rabbitMQ_message_broaker_file_port))
	files = files.json()
	for file in files['files']:
		download_file(rabbitMQ_message_broaker, rabbitMQ_message_broaker_file_port, file['name'])
	print 'Now synced with server'


def JSON_files_info(folder_path):
	file_name_list = listdir(folder_path)
	files = []
	for file_name in file_name_list:
		if isfile(join(folder_path, file_name)):
			files.append(
			{
				"name":file_name,
				"path":join(folder_path, file_name),
				"last edited":str(int(getmtime(join(folder_path, file_name)))), # Contains a dot and is therefore typecast to string
				"size":commands.getoutput('wc -c < %s' % join(folder_path, file_name))
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

def upload_to_master(file_list):
	files_to_send = {}
	for file_index, file in enumerate(file_list):
		files_to_send['file%s' % file_index] = open('%s/%s' % (file_folder_path, file['name']), 'rb')
	print 'Uploading: %s' % files_to_send
	post('http://%s:%s/upload' % (rabbitMQ_message_broaker, rabbitMQ_message_broaker_file_port), files=files_to_send)

def download_file(address, port, file_name):
	file_url = 'http://%s:%r/download/%s' % (address, port, file_name)
	urlretrieve(file_url, complete_sync_file_path(file_name))

def update_metadata_file():
	f = open(sync_metadata_file, 'w')
	f.write(json.dumps({"files":JSON_files_info(file_folder_path)}, indent=2))
	f.close()

def complete_sync_file_path(file_name):
	return '%s/%s%s' % (commands.getoutput('pwd'), file_folder_path, file_name)