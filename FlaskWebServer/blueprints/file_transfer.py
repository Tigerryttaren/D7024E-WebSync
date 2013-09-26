from os import listdir, remove
from os.path import isfile, isdir, join, abspath, getmtime, getsize
from datetime import datetime
from flask import Flask, render_template, Blueprint, request, redirect, make_response
from werkzeug import secure_filename

file_transfer = Blueprint('file_transfer', __name__, template_folder='../templates')

#WARNING this duplicated in the run.py file. TODO: change this!
file_folder_path = 'sync_files/' # File path from the run.py file

class SyncFile(object):
	name = ""
	path = ""
	sync_folder_path = "" # The files search path in the sync folder
	last_edited = 0


####################### URL Functions #######################

@file_transfer.route('/files')
def list_files():
	file_name_list = listdir(file_folder_path)
	file_list = get_file_list(file_folder_path)
	return render_template('fileList.html', file_list=file_list)

@file_transfer.route('/upload', methods=['GET', 'POST'])
def upload_file():
	if request.method == 'POST':
		file = request.files['file']
		filename = secure_filename(file.filename)
		file.save(join(file_folder_path, filename))
		return redirect('/files')
	return render_template('fileUpload.html')

@file_transfer.route('/file/<string:file_name>', methods=['GET'])
def file_info(file_name):
	file_path = join(file_folder_path, file_name)
	if isfile(file_path):
		file = get_file_info(file_path)
		return render_template('fileInfo.html', file=file)
	elif isdir(file_path):
		# TODO: Give a error message that it is a directory
		pass
	else:
		# TODO: Throw file does not exists error
		pass

@file_transfer.route('/file/<string:file_name>', methods=['DELETE'])
def remove_file(file_name):
	file_path = join(file_folder_path, file_name)
	if isfile(file_path):
		remove(file_path)
		return redirect('/files')
	elif isdir(file_path):
		# TODO: Give a error message that it is a directory
		pass
	else:
		# TODO: Throw file does not exists error
		pass

# Workaround so that it's possible to delete files from the web browser
@file_transfer.route('/delete/<string:file_name>', methods=['GET'])
def remove_file_http(file_name):
	file_path = join(file_folder_path, file_name)
	if isfile(file_path):
		remove(file_path)
		return redirect('/files')
	elif isdir(file_path):
		# TODO: Give a error message that it is a directory
		pass
	else:
		# TODO: Throw file does not exists error
		pass

@file_transfer.route('/download/<string:file_name>', methods=['GET', 'POST'])
def download_file(file_name):
	file_path = join(file_folder_path, file_name)
	if isfile(file_path):
		file_size = getsize(file_path)
		response = make_response()
		response.headers['Pragma'] = 'public'
		response.headers['Content-Type'] = get_file_type(file_path)
		response.headers['Content-Transfer-Encoding'] = 'binary'
        response.headers['Content-Description'] = 'File Transfer'
        response.headers['Content-Disposition'] = 'attachment; filename=%s' % file_name
        response.headers['Content-Length'] = file_size
        with open (file_path, "r") as file_data:
        	response.data = file_data.read()
        return response

####################### Helper Functions #######################

#Returns the type of the file
def get_file_type(file_path):
	file_type_name = ''
	for char in reversed(file_path):
		if char == '.':
			break
		else:
			file_type_name = file_type_name + char
	return file_type_name

# Returns a array with file objects that are located in the folder and it's sub folders (in that case the the list object is a array of files)
def get_file_list(folder_path):
	file_list = []
	file_name_list = listdir(folder_path)
	for file_name in file_name_list:
		if isfile(join(folder_path, file_name)):
			sync_file = SyncFile()
			sync_file.name = file_name
			sync_file.path = format_file_path(join(folder_path, file_name))
			sync_file.sync_folder_path = file_name
			last_edited_unix_time = getmtime(sync_file.path)
			sync_file.last_edited = datetime.fromtimestamp(int(last_edited_unix_time)).strftime('%Y-%m-%d %H:%M:%S')
			file_list.append(sync_file)
		# If it's a folder
		else:
			sub_file_list = get_file_list(join(folder_path, file_name))
			for file in sub_file_list:
				file.sync_folder_path = file_name + '/' + file.sync_folder_path
				file_list.append(file)
	return file_list

# Returns a SyncFile object with the information about the file
def get_file_info(path):
	if isfile(path):
		sync_file = SyncFile()
		file_name = ''
		for char in reversed(path):
			if char == '/':
				break
			else:
				file_name = file_name + char
		sync_file.name = file_name[::-1] # Reverses the string (with magic?)
		sync_file.path = format_file_path(path)
		last_edited_unix_time = getmtime(sync_file.path)
		sync_file.last_edited = datetime.fromtimestamp(int(last_edited_unix_time)).strftime('%Y-%m-%d %H:%M:%S')
		return sync_file
	elif isdir(path):
		raise Exception("error from get_file_info, path is to a directory.")
	else:
		raise Exception("error from get_file_info, path doesn't lead to anything.")

# Returns the full search path to the file
def format_file_path(path):
	threeChars = ''
	char_counter = 0
	steps_back = 2 # Start value of so that it starts from the main.py file location and removes the file name from path_to_script
	# Removes the '../' from file path and counts the number of steps the next loop has to go back
	for char in path:
		threeChars = threeChars + char
		char_counter = char_counter + 1
		if char_counter == 3:
			if threeChars == '../':
				path = path[3:] # Removes the first three characters 
				char_counter = 0
				threeChars = ''
				steps_back = steps_back + 1
			else:
				break
	# Gives the complete path to the file folder
	path_to_script = abspath(__file__)
	while steps_back > 0:
		if path_to_script[len(path_to_script)-1] == '/':
			steps_back = steps_back - 1
			if steps_back > 0:
				path_to_script = path_to_script[:-1]
		else:
			path_to_script = path_to_script[:-1]
	path = join(path_to_script, path)
	return path
