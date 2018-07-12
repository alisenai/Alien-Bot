# Returns the title of the user by their ID
from Common import DataManager


# TODO: Add single user to owner

permissions = {}

def load_permissions():
    global permissions
    permissions_config = DataManager.get_data("bot_config",  key="Permissions")
    level = len(permissions_config)
    for permission in permissions_config:
        title = permission["Title"]
        permissions[title] = Permission(title, permission["Has Permissions"], permission["Enabled"])
        level -= 1

def get_user_title(user_id):
    return DataManager.get_data("bot_config", key="Permissions")[str(user_id)]


# Returns a level, given a title
def get_title_level(title):
    return DataManager.get_data("bot_config", key="Permissions")


class Permission:
    def __init__(self, title, has_permissions, enabled):
        self.title = title
        self.has_permissions = has_permissions
        self.enabled = enabled
