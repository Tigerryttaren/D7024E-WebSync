import sys

sys.path.append('blueprints')
from flask import Flask, Blueprint
from file_transfer import file_transfer

UPLOAD_FOLDER = 'sync_files/'

app = Flask(__name__)
app.register_blueprint(file_transfer)    
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Makes shure that the script is run direcly from the interpiter and not used as a imported module.
if __name__ == "__main__":
	#app.run()
	#app.run(host='0.0.0.0') # Makes the server publicly available
	app.run(debug=True) # Turns debug on