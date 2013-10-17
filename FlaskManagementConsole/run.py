import sys

sys.path.append('blueprints')
from flask import Flask, Blueprint
import add_new_node

app = Flask(__name__)
app.register_blueprint(add_new_node.management_console)

if __name__ == "__main__":
	#app.run()
	#app.run(host='0.0.0.0') 	# Makes the server publicly available
	try:
		add_new_node.docker_image_name=sys.argv[1]
		app.run(debug=True, host='0.0.0.0') 		
	except IndexError:
		print 'Error: no docker image name'
