from Common import DataManager

database = None
currency = None


# This will be called by the Economy Mod to init the DB ONCE
def init_database():
    global database
    database = DataManager.add_manager("bank_database", "Mods/Economy/Bank.db", file_type=DataManager.FileType.SQL)
    return database


# Execute a custom SQLite3 Command
def database_execute(command):
    return database.execute(command)


# Sets a given user's cash balance from a given server
def set_cash(server_id, user_id, amount):
    # database.execute("UPDATE '" + server_id + "' SET cash=" + str(amount) + " WHERE user='" + user_id + "'")
    database.execute("UPDATE '%s' SET cash='%s' WHERE user='%s'" % (str(server_id), str(amount), str(user_id)))


# Sets a given user's bank balance from a given server
def set_bank(server_id, user_id, amount):
    # database.execute("UPDATE '" + server_id + "' SET bank=" + str(amount) + " WHERE user='" + user_id + "'")
    database.execute("UPDATE '%s' SET bank='%s' WHERE user='%s'" % (str(server_id), str(amount), str(user_id)))


# Gets a given user's cash balance from a given server
def get_cash(server_id, user_id):
    # return int(database.execute("SELECT cash FROM '" + server_id + "' WHERE user='" + user_id + "' LIMIT 1")[0])
    return int(database.execute("SELECT cash FROM '%s' WHERE user='%s' LIMIT 1" % (str(server_id), str(user_id)))[0])


# Gets a given user's bank balance from a given server
def get_bank(server_id, user_id):
    # return int(database.execute("SELECT bank FROM '" + server_id + "' WHERE user='" + user_id + "' LIMIT 1")[0])
    return int(database.execute("SELECT bank FROM '%s' WHERE user='%s' LIMIT 1" % (str(server_id), str(user_id)))[0])


# Gets a given user's rank from a given server
def get_rank(server_id, user_id):
    # return int(database.execute("SELECT COUNT(user) FROM '" + server_id +
    #                             "' WHERE bank + cash >= (SELECT bank + cash from '" + server_id + "' WHERE user='" +
    #                             user_id + "')")[0])
    return int(database.execute(
        "SELECT COUNT(user) FROM '%s' WHERE bank + cash >= (SELECT bank + cash from '%s' WHERE user='%s')" %
        (str(server_id), str(server_id), str(user_id))
    )[0])


# Returns true if a given user exists within the DB for the given server
def user_exists(server_id, user_id):
    return database.execute("SELECT EXISTS(SELECT * FROM '%s' WHERE user='%s' LIMIT 1)" % (server_id, user_id))[0] == 1
