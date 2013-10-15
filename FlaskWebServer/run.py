import sys
import threading

sys.path.append('blueprints')
import file_sync_manager
from flask import Flask, Blueprint
from file_transfer import file_transfer
from os import system
from variables import file_folder_path

app = Flask(__name__)
app.register_blueprint(file_transfer)
app.register_blueprint(file_sync_manager.file_sync_manager)    
app.config['UPLOAD_FOLDER'] = file_folder_path

def stop_thread(thread):
	print "\n Stopping thread"
	thread.shutdown = True
	thread.join()

# Makes shure that the script is run direcly from the interpiter and not used as a imported module.
if __name__ == "__main__":
	try:
		port = int(sys.argv[1]) # The first argument is the file name
		try:
			file_sync_manager.rabbitMQ_message_broaker = sys.argv[2]
			file_sync_thread=threading.Thread(target=file_sync_manager.wait_for_update)
				file_sync_thread.setDaemon(True) # This will make sure that the thread stops without cleanup
				file_sync_thread.start()
			app.run(host='0.0.0.0', port=port, use_reloader=False) # Turning off reload so that it doesn't launch two threads
		except IndexError:
			print "Error: no message broaker given"
	except IndexError:
		print "Error: no port given"
	
