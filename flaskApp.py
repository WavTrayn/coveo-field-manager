from flask import Flask, jsonify, request
import requests
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import time
import threading
from typing import List


#ORGANIZATION_ID = 'npagecoveocompurplestingray22mcumbr'
ORGANIZATION_ID = 'dmattetestingdeletefieldsd1rmvqke'
COVEO_API_URL = 'https://platform.cloud.coveo.com/rest/organizations/'+ORGANIZATION_ID+'/indexes/fields'
#API_KEY ='xxc8a08e11-b69f-41d4-908e-23fd37d79b9e'
API_KEY = 'xx74db816b-e08f-402f-b208-010ca7ac6837'
#API_KEY = 'xxa1c6ffba-a769-4773-94ff-c875f495334e'

headers = {
    'Authorization': 'Bearer '+API_KEY,
    'Content-Type': 'application/json'
}

class LogEntry:
    def __init__(self, field: str,status: str,details: str):
        self.set_field(field)
        self.set_status(status)
        self.set_details(details)

    def set_field(self, field: str):
        if not isinstance(field,str): raise Exception("logEntry's field is not a string!")
        else:
            self.field = field
            
    
    def set_status(self, status: str):
        if not isinstance(status,str): raise Exception("logEntry's status is not a string!")
        else:
            self.status = status
    
    def set_details(self, details: str):
        if not isinstance(details,str): raise Exception("logEntry's details is not a string!")
        else:
            self.details = details

    def __str__(self):
        return f"Log entry: (field={self.field}, status={self.status}, details={self.details})"

class Task:

    IN_PROGRESS = "in progress"
    CANCELED = "canceled"
    COMPLETE = "complete"
    FAILED = "failed"

    def __init__(self, id, status):
        self.id = id
        self.status = status
        self.logs: List[LogEntry] = []

    def get_id(self) -> str:
        return self.id
    
    def get_status(self) -> str:
        return self.status
    
    def setId(self, id:str) -> None:
        self.id = id

    def set_status(self, status:str) -> None:
        """ Sets the status and creates a web socket"""
        is_valid = status == Task.CANCELED
        is_valid = is_valid or status == Task.COMPLETE
        is_valid = is_valid or status == Task.IN_PROGRESS
        is_valid = is_valid or status == Task.FAILED

        if is_valid:
            self.status = status
            socketio.emit('task_update', {'task_id': self.get_id(), 'task_status': self.status, 'task_logs': self.get_logs()})
        else: 
            raise Exception('The task status set is not a valid option.')
        
    def log(self, log_entry: LogEntry) -> None:
        if not isinstance(log_entry,LogEntry): raise Exception('Expected a LogEntry got something else')
        else:
            self.logs.append(log_entry)
        
    def run(self, fields: list) -> None:       
        self.set_status(Task.IN_PROGRESS)   # set the status to in progress.

        # Check if 'fields' array is provided and is non-empty
        if not fields: 
            self.set_status(Task.FAILED)
            return jsonify({"message": "Field names are required"}), 400

        # check if the fields are strings
        if not isinstance(fields[0],str):
            self.set_status(Task.FAILED)
            raise Exception("field is not a string")
            return jsonify({"message": "Field names are required"}), 400
        
        for field in fields:
            time.sleep(2) # simulate the delete process. 
            """
            DELETE PROCESS HERE
            """
            delete_url = f"{COVEO_API_URL}/{field}"
            response = requests.delete(delete_url, headers=headers)

            # Check for successful deletion (204 No Content)
            if response.status_code != 204:
                           
                new_log_entry = LogEntry(field,str(response.status_code),response.text)
                self.log(new_log_entry)
                #print("New Log Entry: ",+str(new_log_entry))


            # check if the task is canceled.
            if  self.get_status() == Task.CANCELED: 
                self.set_status(Task.CANCELED)
                return
        
        self.set_status(Task.COMPLETE)
        print(self.get_logs())

    def get_logs(self):
        s = "" + "Logs\n"
        for log_entry in self.logs:
            s = s + str(log_entry)+ "\n"
        
        return s

    @staticmethod
    def get_task_by_id(tasks: list) -> object:
        raise Exception("NOT READY YET")    

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Enable CORS for WebSocket
CORS(app)  # This will enable CORS for all routes

tasks = []

@app.route('/fields', methods=['GET'])
def get_fields():
    response = requests.get(COVEO_API_URL, headers=headers)
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({'error': 'Failed to retrieve fields'}), response.status_code
    
# DELETE endpoint to delete multiple fields by names
@app.route('/fields', methods=['DELETE'])
def delete_fields():
    data = request.get_json()  # Get JSON data from the request
    print("Received data:", data)
    fields = data.get("fields", [])

    # Generate a unique task ID
    task_id = "-".join(fields)
    new_task = Task(task_id,Task.IN_PROGRESS)   # create a new task
    tasks.append(new_task) # add to the list

    threading.Thread(target=new_task.run, args=(fields,)).start()   # start the task

    return jsonify({"task_id": task_id, "message": "Delete task started"}), 202


# New endpoint to cancel delete operation
@app.route('/cancel-delete', methods=['POST'])
def cancel_delete():
    global operationCanceled
    operationCanceled = True
    return jsonify({"message": "Delete operation canceled"}), 200

if __name__ == '__main__':
    socketio.run(app, debug=True)
