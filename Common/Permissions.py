# Returns the title of the user by their ID
from Common import DataManager

permissions = {}
default = None


# TODO: Remove single owner
def load_permissions():
    global default
    print("[Loading permissions]", end='')
    permissions_config = DataManager.get_manager("bot_config").get_data(key="Permissions")
    DataManager.get_manager("database").execute("CREATE TABLE IF NOT EXISTS permissions(user TEXT, title TEXT)")
    for permission_name in permissions_config:
        permission_config = permissions_config[permission_name]
        permission = Permission(permission_name, permission_config["Has Permissions"],
                                permission_config["Is Owner"], permission_config["Inherits"])
        permissions[permission_name] = permission
        if permission_config["Default"]:
            default = permission
    print("[Done]")


# Returns a user's permission title by their ID
def get_user_title(user_id):
    database_manager = DataManager.get_manager("database")
    user_title = database_manager.execute("SELECT title FROM permissions WHERE user='" + str(user_id) + "' LIMIT 1")
    if len(user_title) == 0:
        database_manager.execute("INSERT INTO permissions VALUES('" + str(user_id) + "', '" + default.title + "')")
        return default.title
    return user_title[0]


def has_permission(user_id, minimum_permission):
    user_title = get_user_title(user_id)
    user_permissions = permissions[user_title]
    # If the user is a bot owner, they can use any command (that is enabled) -> Return True
    if user_permissions.is_owner:
        return True
    # If user title has no permissions -> Return false
    if user_permissions.has_permissions is False:
        return False
    # If user permissions meets the minimum requirement -> Return True
    if user_title == minimum_permission:
        return True
    # Must be the lowest rank and thus previous checks have already determined that this user doesn't have the perms
    if user_permissions.sub_permissions is None:
        return False
    # If the method hasn't returned, then call the method again with the sub-perm
    has_permission(user_id, user_permissions.sub_permissions.title)


class Permission:
    def __init__(self, title, has_permissions, is_owner, sub_permissions):
        self.title = title
        self.has_permissions = has_permissions
        self.is_owner = is_owner
        self.sub_permissions = sub_permissions
