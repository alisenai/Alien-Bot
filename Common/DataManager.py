import json

dataManagers = {}

# TODO: Compress
class File:
    # Initializes the dataManager with a local DB
    def __init__(self, save_file):
        print("[Loading", save_file, "...]")
        self.store_file = save_file
        self.database = self.get_data()
        print("[Done loading]")

    # Writes data to the DB
    def write_data(self, data, key=None):
        if key is None:
            self.database = data
        else:
            self.database[key] = data
        with open(self.store_file, 'w', encoding="utf-8") as outfile:
            json.dump(self.database, outfile, indent=2, sort_keys=True)

    # Gets data from the local DB
    def get_data(self, key=None):
        if key is None:
            with open(self.store_file, 'r', encoding="utf-8") as json_file:
                return json.load(json_file)
        else:
            return self.database[key]


def add_manager(manager_name, save_file):
    global dataManagers
    new_manager = File(save_file)
    dataManagers[manager_name] = new_manager
    return new_manager


# Returns a manager given a name
def get_manager(manager_name):
    return dataManagers[manager_name]


# Returns data from a manager
def get_data(manager_name, key=None):
    return get_manager(manager_name).get_data(key=key)


# Writes data to a specific manager
def write_data(manager_name, data, key=None):
    get_manager(manager_name).write_data(data, key=key)
