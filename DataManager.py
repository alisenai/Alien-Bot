import json

database = {}
store_file = ''


# Inits the dataManager with a local DB
def init(save_file):
    global store_file
    global database
    print("[Loading DB]")
    store_file = save_file
    database = load_data()
    print("[Done loading DB]")


# Writes data to the DB
def write_data(key, data):
    global database
    database[key] = data
    with open(store_file, 'w') as outfile:
        json.dump(database, outfile)


# Gets data from the local DB
def get_data(key):
    return database[key]


# Gets all data from the DB file
def load_data():
    with open(store_file) as json_file:
        return json.load(json_file)
