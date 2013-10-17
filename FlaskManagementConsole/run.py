import sys

sys.path.append('blueprints')
from flask import Flask, Blueprint
<<<<<<< HEAD
from add_new_node import management_console

app = Flask(__name__)
app.register_blueprint(management_console)
=======
import add_new_node

app = Flask(__name__)
app.register_blueprint(add_new_node.management_console)
>>>>>>> e5ae4d48a532de1a3f626ccedf184ac6ea77bf45

if __name__ == "__main__":
	#app.run()
	#app.run(host='0.0.0.0') 	# Makes the server publicly available
<<<<<<< HEAD
	app.run(debug=True, host='0.0.0.0') 		
=======
	try:
		add_new_node.docker_image_name=sys.argv[1]
		app.run(debug=True, host='0.0.0.0') 		
	except IndexError:
		print 'Error: no docker image name'
>>>>>>> e5ae4d48a532de1a3f626ccedf184ac6ea77bf45
