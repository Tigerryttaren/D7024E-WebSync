import sys
import threading
import atexit

sys.path.append('blueprints')
from flask import Flask, Blueprint
from os import system
import add_new_node, sync_master_manager, remote_management

app = Flask(__name__)
app.register_blueprint(add_new_node.management_console)
app.register_blueprint(remote_management.remote_management)

atexit.register(sync_master_manager.remove_meta_data_file)

def run_web():
	system('python /D7024E-WebSync-develop/FlaskWebServer/run.py 4000 localhost')

if __name__ == "__main__":
	try:
		sync_manager_thread=threading.Thread(target=sync_master_manager.update_watcher)
		sync_manager_thread.setDaemon(True) # This will make sure that the thread stops without cleanup
		sync_manager_thread.start()

		sync_manager_thread=threading.Thread(target=run_web)
		sync_manager_thread.setDaemon(True) # This will make sure that the thread stops without cleanup
		sync_manager_thread.start()

		add_new_node.docker_image_name=sys.argv[1]
		app.run(debug=True, host='0.0.0.0', use_reloader=False) 		
	except IndexError:
		print 'Error: no docker image name'