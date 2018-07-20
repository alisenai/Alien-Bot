import json
import sqlite3

dataManagers = {}


class FileType:
    SQL = 1
    JSON = 2


class JSON:
    file_type = FileType.JSON

    # Initializes the dataManager with a local DB
    def __init__(self, save_file):
        print("[Loading", save_file, "...]", end='')
        self.store_file = save_file
        self.database = self.get_data()
        print("[Done]")

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


class SQL:
    file_type = FileType.SQL

    def __init__(self, save_file):
        print("[Loading", save_file, "...]", end='')
        self.store_file = save_file
        print("[Done]")

    def execute(self, command):
        with sqlite3.connect(self.store_file) as connection:
            cursor = connection.cursor()
            data = cursor.execute(command)
            connection.commit()
            return [item for tuple_data in data for item in tuple_data]


def add_manager(manager_name, save_file, file_type=FileType.JSON):
    global dataManagers
    if file_type is FileType.JSON:
        new_manager = JSON(save_file)
    else:
        new_manager = SQL(save_file)
    dataManagers[manager_name] = new_manager
    return new_manager


# Returns a manager given a name
def get_manager(manager_name):
    return dataManagers[manager_name]


# # Returns data from a manager
# def get_data(manager_name, key=None):
#     return get_manager(manager_name).get_data(key=key)


# Writes data to a specific manager
# def write_data(manager_name, data, key=None):
#     get_manager(manager_name).write_data(data, key=key)
