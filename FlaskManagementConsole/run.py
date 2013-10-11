import sys

sys.path.append('blueprints')
from flask import Flask, Blueprint
from add_new_node import management_console

app = Flask(__name__)
app.register_blueprint(management_console)

if __name__ == "__main__":
	#app.run()
	#app.run(host='0.0.0.0') 	# Makes the server publicly available
	app.run(debug=True, host='0.0.0.0') 		
