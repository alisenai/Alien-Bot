# Returns the title of the user by their ID
from Common import DataManager

permissions = {}
default = None


# TODO: Remove single owner
def load_permissions():
    global default
    print("[Loading permissions]", end='')
    permissions_config = DataManager.get_manager("bot_config").get_data(key="Permissions")
    for permission_name in permissions_config:
        permission_config = permissions_config[permission_name]
        permission = Permission(permission_name, permission_config["Has Permissions"],
                                permission_config["Is Owner"], permission_config["Inherits"])
        permissions[permission_name] = permission
        if permission_config["Default"]:
            default = permission
    print("[Done]")


def get_user_title(user_id):
    return DataManager.get_manager("database").get_data(key="Permissions")[str(user_id)]


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
    # If the method hasn't returned, then call the method again with the sub-perm
    has_permission(user_id, user_permissions.sub_permission.title)


class Permission:
    def __init__(self, title, has_permissions, is_owner, sub_permissions):
        self.title = title
        self.has_permissions = has_permissions
        self.is_owner = is_owner
        self.sub_permissions = sub_permissions
