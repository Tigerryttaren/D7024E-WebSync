import pika
import commands
import threading
from os import listdir
from os.path import isfile, getmtime, join
from flask import Flask, render_template, Blueprint, json, jsonify, current_app
from variables import file_folder_path

file_sync_manager = Blueprint('file_sync_manager', __name__, template_folder='../templates')

rabbitMQ_message_broaker = '' # Edited by run.py

####################### URL Functions #######################

@file_sync_manager.route('/sync')
def index_page():
	message = { 'local ip':local_ip(), 'files':JSON_files_info() }
	data = json.dumps(message)
	send_update(json.dumps(message)) # TODO: change so that localhost is not hard coded
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
		# print " [x] Received %r" % (body,)

	channel.basic_consume(callback, queue=queue_name, no_ack=True)
	channel.start_consuming()

def send_update(update_message):
	connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitMQ_message_broaker))
	channel = connection.channel()
	channel.exchange_declare(exchange='update', type='fanout')
	channel.basic_publish(exchange='update', routing_key='', body=update_message)

	# channel.basic_publish(exchange='', routing_key='update', body=update_message)
	print " [x] Sent update message"
	connection.close()

def handle_update_message(update_message):
	update_dict = json.loads(update_message)
	if update_dict['local ip'] == local_ip():
		for file in update_dict['files']:
			print file['name']

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
				"last edited":str(getmtime(join(file_folder_path, file_name))) # Contains a dot and is therefore typecast to string
			})
	return files

def local_ip():
	return commands.getoutput("/sbin/ifconfig").split("\n")[1].split()[1][5:]