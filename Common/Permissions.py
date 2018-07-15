# Returns the title of the user by their ID
from Common import DataManager

# TODO: Add single user to owner

permissions = {}

"""
{
    "Title": "Owner",
    "Has Permissions": true,
    "Default": false,
    "Inherits": "Admin"
},"""


def load_permissions():
    global permissions
    permissions_config = DataManager.get_data("bot_config", key="Permissions")
    owner_permission = Permission("Owner", True, True, None)
    prev_permission = None
    for permission in permissions_config:
        title = permission["Title"]
        has_permissions = permission["Has Permissions"]
        enabled = permission["Enabled"]
        prev_permission = permissions[title] = Permission(title, has_permissions, enabled, prev_permission)


def get_user_title(user_id):
    return DataManager.get_data("bot_config", key="Permissions")[str(user_id)]


def has_permissions_by_id(user_id, permission_title):
    user_title = get_user_title(user_id)
    while permissions[user_title] is not None:
        if permissions[user_title].title == permission_title:
            return True
        else:
            user_title = permissions[user_title].sub_permission.title
    return False


class Permission:
    def __init__(self, title, has_permissions, enabled, sub_permission):
        self.title = title
        self.has_permissions = has_permissions
        self.enabled = enabled
        self.sub_permissions = sub_permission
