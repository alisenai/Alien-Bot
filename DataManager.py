import json


class DataManager:
    # Initializes the dataManager with a local DB
    def __init__(self, save_file):
        print("[Loading", save_file, "DB]")
        self.store_file = save_file
        self.database = self.get_data()
        print("[Done loading DB]")

    # Writes data to the DB
    def write_data(self, key, data):
        self.database[key] = data
        with open(self.store_file, 'w', encoding="utf-8") as outfile:
            json.dump(self.database, outfile, indent=2)

    # Gets data from the local DB
    def get_data(self, key=None):
        if key is None:
            with open(self.store_file, 'r', encoding="utf-8") as json_file:
                return json.load(json_file)
        else:
            return self.database[key]
