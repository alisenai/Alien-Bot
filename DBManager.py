import pickle


save_file = "Config/dataSave.db"


def save_data(key, data):
    database = load_data()
    database[key] = data
    with open(save_file, 'wb') as handle:
        pickle.dump(database, handle, protocol=pickle.HIGHEST_PROTOCOL)


def get_data(key):
    database = load_data()
    return database[key]


def load_data():
    with open(save_file, 'rb') as handle:
        database = pickle.load(handle)
    return database
