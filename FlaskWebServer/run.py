import sys
import threading
import atexit

sys.path.append('blueprints')
import file_sync_manager
from flask import Flask, Blueprint, json
from file_transfer import file_transfer
from os import system
from os.path import isfile
from variables import file_folder_path, sync_metadata_file

app = Flask(__name__)
app.register_blueprint(file_transfer)
app.register_blueprint(file_sync_manager.file_sync_manager)    
app.config['UPLOAD_FOLDER'] = file_folder_path

@app.before_first_request
def run_this_first():
	# TODO: Sync with master server
	f = open(sync_metadata_file, 'w')
	f.write(json.dumps({"files":[]}, indent=2))
	f.close()

# Makes shure that the script is run direcly from the interpiter and not used as a imported module.
if __name__ == "__main__":
	try:
		port = int(sys.argv[1]) # The first argument is the file name
	except IndexError:
		print "Error: no port given"
	try:
		file_sync_manager.rabbitMQ_message_broaker = sys.argv[2]
	except IndexError:
		print "Error: no message broaker given"
	system('mkdir %s' % file_folder_path)
	if isfile(sync_metadata_file):
		system('rm %s' % sync_metadata_file)
	system('touch %s' % sync_metadata_file)
	file_sync_manager.flask_port = port
	file_sync_manager.sync_metadata_file = sync_metadata_file
	file_sync_thread=threading.Thread(target=file_sync_manager.wait_for_update)
	file_sync_thread.setDaemon(True) # This will make sure that the thread stops without cleanup
	file_sync_thread.start()
	app.run(host='0.0.0.0', debug=True, port=port, use_reloader=False) # Turning off reload so that it doesn't launch two threads
	
	
	
