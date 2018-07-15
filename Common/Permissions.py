# Returns the title of the user by their ID
from Common import DataManager

# TODO: Add single user to owner

permissions = {}


def load_permissions():
    print("[Loading permissions]")
    permissions_config = DataManager.get_data("bot_config", key="Permissions")
    permissions["Owner"] = Permission("Owner", True, False, None)
    for permission_name in permissions_config:
        permission = permissions_config[permission_name]
        permissions[permission_name] = Permission(permission_name, permission["Has Permissions"],
                                                  permission["Default"], permission["Inherits"])
    print("[Done loading permissions]")


def get_user_title(user_id):
    return DataManager.get_data("database", key="Permissions")[str(user_id)]


def has_permission(user_id, minimum_permission):
    user_title = get_user_title(user_id)
    if permissions[user_title] is None:
        return False
    if permissions[user_title].has_permissions is False:
        return False
    if user_title == "Owner":
        return True
    if user_title == minimum_permission:
        return True
    # If the method hasn't returned, then call the method again with the sub-perm
    has_permission(user_id, permissions[user_title].sub_permission.title)


class Permission:
    def __init__(self, title, has_permissions, default, sub_permissions):
        self.title = title
        self.has_permissions = has_permissions
        self.default = default
        self.sub_permissions = sub_permissions
