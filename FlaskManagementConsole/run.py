import sys
import threading
import atexit

sys.path.append('blueprints')
from flask import Flask, Blueprint
import add_new_node, sync_master_manager

app = Flask(__name__)
app.register_blueprint(add_new_node.management_console)

atexit.register(sync_master_manager.remove_meta_data_file)

if __name__ == "__main__":
	try:
		sync_manager_thread=threading.Thread(target=sync_master_manager.update_watcher)
		sync_manager_thread.setDaemon(True) # This will make sure that the thread stops without cleanup
		sync_manager_thread.start()

		add_new_node.docker_image_name=sys.argv[1]
		app.run(debug=True, host='0.0.0.0', use_reloader=False) 		
	except IndexError:
		print 'Error: no docker image name'
