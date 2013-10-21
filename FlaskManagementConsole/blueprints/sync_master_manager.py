import pika

def update_watcher():
	connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
	channel = connection.channel()

	channel.exchange_declare(exchange='update_request', type='fanout')
	result = channel.queue_declare(exclusive=True)
	queue_name = result.method.queue
	channel.queue_bind(exchange='update_request', queue=queue_name)
	print ' [*] Waiting for messages. To exit press CTRL+C'

	def callback(ch, method, properties, body):
		handle_update_message(body)

	channel.basic_consume(callback, queue=queue_name, no_ack=True)
	channel.start_consuming()

def handle_sync_request(sync_message):
	print sync_message


