import pika
import json
from os import system
from commands import getoutput
from flask import Blueprint, jsonify, request
from werkzeug import secure_filename
from datetime import datetime
from time import sleep

from os import listdir
from os.path import isfile, getmtime, join

meta_data_file_name = 'files_metadata'
files_to_sync = {'download':[], 'delete':[], 'local ip':'', 'port':'', 'sync_timestamp':''}

sync_master_manager = Blueprint('sync_master_manager', __name__, template_folder='../templates')

####################### URL Functions #######################

@sync_master_manager.route('/upload', methods=['POST'])
def upload_files():
	global files_to_sync
	file_list = request.files.getlist('file')
	if len(file_list) > 1:
		for file in file_list:
			filename = secure_filename(file.filename)
			for file_to_download in files_to_sync['download']:
				if filename == file_to_download['name']:
					print 'Saved file %s' % filename
					file.save(join('master_sync_folder/', filename))
					system('touch -m -t ' + str(convert_from_UNIX_time(file_to_download['last edited'])) + ' ' + 'master_sync_folder/%s' % filename) 
	# The python request package cannot generate a list of items so a iterator is used instead
	else:
		iterator = request.files.itervalues()
		for file in iterator:
			filename = secure_filename(file.filename)
			for file_to_download in files_to_sync['download']:
				if filename == file_to_download['name']:
					print 'Saved file %s' % filename
					file.save(join('master_sync_folder/', filename))
					system('touch -m -t ' + str(convert_from_UNIX_time(file_to_download['last edited'])) + ' ' + 'master_sync_folder/%s' % filename) 
	# TODO: check if files are missing
	write_meta_data_file(json.dumps({'files':JSON_files_info('master_sync_folder')}, indent=2))
	for file_to_delete in files_to_sync['delete']:
		system('rm %s/%s' % ('master_sync_folder', file_to_delete['name']))
	send_update_message(json.dumps(files_to_sync, indent=2))
	print 'Sent update message \n %s' % json.dumps(files_to_sync, indent=2)
	files_to_sync['download'] = []
	files_to_sync['delete'] = []
	return jsonify({'message':'files uploaded'})

@sync_master_manager.route('/json/files', methods=['GET'])
def json_get_all_file():
	return jsonify({'files':JSON_files_info('master_sync_folder')})

####################### RabbitMQ Functions #######################

def update_watcher():
	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()

	channel.exchange_declare(exchange='update_request', type='fanout')
	result = channel.queue_declare(exclusive=True)
	queue_name = result.method.queue
	channel.queue_bind(exchange='update_request', queue=queue_name)
	print ' [*] Waiting for update requests'

	def callback(ch, method, properties, body):
		handle_sync_request(body)

	channel.basic_consume(callback, queue=queue_name, no_ack=True)
	channel.start_consuming()

	
def handle_sync_request(sync_message):
	print 'Recived: ' + sync_message
	sync_message = json.loads(sync_message)
	files_metadata = open(meta_data_file_name, 'r')
	files = files_metadata.read()
	files = json.loads(files)
	files_metadata.close()
	ack_message = {'message':'Ok to sync', 'edit conflicts':[], 'delete conflicts':[]}
	for local_file in files['files']:
		for new_file in sync_message['new']:
			if new_file['name'] == local_file['name'] and new_file['last edited'] < local_file['last edited']:
				ack_message['edit conflicts'].append(new_file)
		for deleted_file in sync_message['deleted']:
			# If a old version of the file is deleted then it is a delete conflict
			if deleted_file['name'] == local_file['name'] and deleted_file['last edited'] < local_file['last edited']:
				ack_message['delete conflicts'].append(deleted_file)
	global files_to_sync
	files_to_sync['download'] = [file for file in sync_message['new'] if file not in ack_message['edit conflicts']]
	files_to_sync['delete'] = [file for file in sync_message['deleted'] if file not in ack_message['delete conflicts']]
	files_to_sync['local ip'] = sync_message['local ip']
	files_to_sync['port'] = sync_message['port']
	send_ack(json.dumps(ack_message, indent=2))

def send_ack(message):
	sleep(1) # Gives the client enought time to open a new connection
	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()
	channel.exchange_declare(exchange='update_ack', type='fanout')
	channel.basic_publish(exchange='update_ack', routing_key='', body=message)
	print " [x] Sent update message \n %s" % message
	connection.close()

def send_update_message(json_string):
	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()
	channel.exchange_declare(exchange='update', type='fanout')
	channel.basic_publish(exchange='update', routing_key='', body=json_string)
	print " [x] Sent update message \n %s" % json_string
	connection.close()


####################### Other Functions #######################

def remove_meta_data_file():
	system('rm %s' % (getoutput('pwd') + '/files_metadata'))

def write_meta_data_file(files):
	system('rm %s' % (getoutput('pwd') + '/files_metadata'))
	files_metadata = open(meta_data_file_name, 'w')
	files_metadata.write(files)
	files_metadata.close()


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
				"size":getoutput('wc -c < %s' % join(folder_path, file_name))
			})
	return files

def convert_from_UNIX_time(UNIX_time):
	return datetime.fromtimestamp(float(UNIX_time)).strftime('%Y%m%d%H%M.%S')