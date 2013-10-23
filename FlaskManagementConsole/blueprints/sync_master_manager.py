import pika
import json
from os import system
from commands import getoutput

meta_data_files_name = 'files_metadata'

def update_watcher():
	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()

	channel.exchange_declare(exchange='update_request', type='fanout')
	result = channel.queue_declare(exclusive=True)
	queue_name = result.method.queue
	channel.queue_bind(exchange='update_request', queue=queue_name)
	print ' [*] Waiting for messages. To exit press CTRL+C'

	def callback(ch, method, properties, body):
		handle_sync_request(body)

	channel.basic_consume(callback, queue=queue_name, no_ack=True)
	channel.start_consuming()

def handle_sync_request(sync_message):
	print 'Recived: ' + sync_message
	sync_message = json.loads(sync_message)
	files_to_sync = {'download':[], 'delete':[], 'conflict':[], 'local ip':sync_message['local ip'], 'port':sync_message['port']}
	try:
		files_metadata = open('files_metadata', 'r')
		files = files_metadata.read()
		files = json.loads(files)
		files_metadata.close()
		conflict_files = []
		name_list = [] # Used for detecting deletions
		if len(files['files']) <= 0:
				files_to_sync['download'] = sync_message['files']
		else:
			for node_file_index, node_file in enumerate(sync_message['files']):
				name_list.append(node_file['name'])
				for local_file_index, local_file in enumerate(files['files']):
					print 'Comparing %s with %s' % (node_file['name'], local_file['name'])

					if local_file['name'] == node_file['name']:
						# TODO: add size check
						if local_file['last edited'] == node_file['last edited']:
							print 'Ignoring: ' + sync_message['files'][node_file_index]['name']
						elif local_file['last edited'] > node_file['last edited']:
							files_to_sync['conflict'].append(sync_message['files'][node_file_index])
							conflict_files.append(sync_message['files'][node_file_index])
							print 'Added to conflict list: ' + sync_message['files'][node_file_index]['name']
						else:
							files_to_sync['download'].append(sync_message['files'][node_file_index])
							files['files'][local_file_index] = sync_message['files'][node_file_index]
							print 'Updating file: ' + sync_message['files'][node_file_index]['name']
						break
					
					# Meta data for node_file does not exist, must be uploaded
					elif local_file_index == len(files['files'])-1:
						files_to_sync['download'].append(sync_message['files'][node_file_index])
						print 'Downloading file: ' + sync_message['files'][node_file_index]['name']
			
			remove_files_on_index = []
			for local_file_index, local_file in enumerate(files['files']):
				if local_file['name'] not in name_list and local_file['name'] not in conflict_files:
					print '%s marked for removal' % files['files'][local_file_index] 
					files_to_sync['delete'].append(files['files'][local_file_index])
					remove_files_on_index.append(local_file_index)

			remove_files_on_index.reverse()
			for remove_file_index in remove_files_on_index:
				print 'Removing %s' % files['files'][remove_file_index]
				del files['files'][remove_file_index]

		for new_file_index, new_file in enumerate(files_to_sync['download']):
			files['files'].append(files_to_sync['download'][new_file_index])
			print 'Added file localy: ' + files_to_sync['download'][new_file_index]['name']
			
		files_json = json.dumps(files, indent=2)
		write_meta_data_file(files_json)
		files_to_sync = json.dumps(files_to_sync, indent=2)
		send_message(files_to_sync)
			
		# for local_file_index, local_file in enumerate(files['files']):
		# 	if local_file not in sync_message['files'] and local_file not in conflict_files:
		# 		files_to_sync['delete'].append(files['files'][local_file_index])
		# 		del files['files'][local_file_index]
		
		# # Removes files that are identical from the sync_message
		# for node_file_index, node_files in enumerate(sync_message['files']):
		# 	for local_file_index, local_file in enumerate(files['files']):
		# 		if local_file['name'] == node_files['name']:
		# 			# TODO: add size check
		# 			if local_file['last edited'] == node_files['last edited']:
		# 				del sync_message['files'][node_file_index]
		# 				break
		# 			elif local_file['last edited'] > node_files['last edited']:
		# 				files_to_sync['conflict'].append(sync_message['files'][node_file_index])
		# 				del sync_message['files'][node_file_index]
		# 				break
		# 			else:
		# 				files_to_sync['download'].append(sync_message['files'][node_file_index])
		# 				files['files'][local_file_index] = sync_message['files'][node_file_index]
		# 				del sync_message['files'][node_file_index]
		# 				break
		# 	# Meta data for node_file does not exist, must be uploaded
		# 	try:
		# 		files_to_sync['download'].append(sync_message['files'][node_file_index])
		# 		files['files'].append(sync_message['files'][node_file_index])
		# 		del sync_message['files'][node_file_index]
		# 	except IndexError:
		# 		pass
		# for local_file_index, local_file in enumerate(files['files']):
		# 	if local_file not in sync_message['files']:
		# 		files_to_sync['delete'].append(files['files'][local_file_index])
		# 		del files['files'][local_file_index]
	# If ther is no meta data file or if it's empty
	except IOError:
		write_meta_data_file(json.dumps(sync_message, indent=2))
		for file in sync_message['files']:
			files_to_sync['download'].append(file)	
		files_to_sync = json.dumps(files_to_sync, indent=2)
		send_message(files_to_sync)

def remove_meta_data_file():
	system('rm %s' % (getoutput('pwd') + '/files_metadata'))

def write_meta_data_file(files):
	system('rm %s' % (getoutput('pwd') + '/files_metadata'))
	files_metadata = open('files_metadata', 'w')
	files_metadata.write(str(files))
	files_metadata.close()

def send_message(json_string):
	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()
	channel.exchange_declare(exchange='update', type='fanout')
	channel.basic_publish(exchange='update', routing_key='', body=json_string)
	print " [x] Sent update message \n %s" % json_string
	connection.close()
