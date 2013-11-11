import sys
import threading
import atexit

sys.path.append('blueprints')
from flask import Flask, Blueprint, json
from os import system
import add_new_node, sync_master_manager, remote_management

app = Flask(__name__)
app.register_blueprint(add_new_node.management_console)
app.register_blueprint(remote_management.remote_management)
app.register_blueprint(sync_master_manager.sync_master_manager)
app.config['UPLOAD_FOLDER'] = 'master_sync_folder/'

# @app.before_first_request
# def make_metadata_file_and_sync_folder():
	# system('mkdir %s' % 'master_sync_folder')
	# metadata = open('files_metadata', 'w')
	# metadata.write(json.dumps({'files':sync_master_manager.JSON_files_info('master_sync_folder')}, indent=2))
	# metadata.close()

def remove_app_files():
	sync_master_manager.remove_meta_data_file()
	system('rm -r master_sync_folder/')

atexit.register(remove_app_files)

if __name__ == "__main__":
	try:
		system('mkdir %s' % 'master_sync_folder')
		metadata = open('files_metadata', 'w')
		metadata.write(json.dumps({'files':sync_master_manager.JSON_files_info('master_sync_folder')}, indent=2))
		metadata.close()
		
		sync_manager_thread=threading.Thread(target=sync_master_manager.update_watcher)
		sync_manager_thread.setDaemon(True) # This will make sure that the thread stops without cleanup
		sync_manager_thread.start()

		add_new_node.docker_image_name=sys.argv[1]
		app.run(debug=True, host='0.0.0.0', use_reloader=False) 		
	except IndexError:
		print 'Error: no docker image name'