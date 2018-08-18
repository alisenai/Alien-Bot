from Common import DataManager

permissions = {}
default_perm = None
owner_perm = None


def load_permissions():
    global default_perm
    global owner_perm
    print("[Loading permissions]", end='')
    permissions_config = DataManager.get_manager("bot_config").get_data(key="Permissions")
    DataManager.get_manager("database").execute("CREATE TABLE IF NOT EXISTS permissions(user TEXT, title TEXT)")
    for permission_name in permissions_config:
        permission_config = permissions_config[permission_name]
        permission = Permission(permission_name, permission_config["Has Permissions"],
                                permission_config["Is Owner"], permission_config["Inherits"],
                                permission_config["Associated Roles"])
        permissions[permission_name] = permission
        if permission_config["Is Default"]:
            assert default_perm is None, "Bot config contains more than one default role."
            default_perm = permission
        if permission_config["Is Owner"]:
            assert owner_perm is None, "Bot config contains more than one owner role."
            owner_perm = permission

    print("[Done]")


# Returns a user's permission title by their ID
def get_user_title(user_id):
    database_manager = DataManager.get_manager("database")
    user_title = database_manager.execute("SELECT title FROM permissions WHERE user='" + str(user_id) + "' LIMIT 1")
    if len(user_title) == 0:
        database_manager.execute("INSERT INTO permissions VALUES('" + str(user_id) + "', '" + default_perm.title + "')")
        return default_perm.title
    return user_title[0]


def has_permission(user, minimum_permission):
    user_title = get_user_title(user.id)
    user_permissions = permissions[user_title]
    while True:
        # If the user is a bot owner, they can use any command (that is enabled) -> Return True
        if user_permissions.is_owner:
            return True
        # If the user has a role that counts as having that permission
        if minimum_permission in permissions:
            if len([role for role in user.roles if int(role.id) in permissions[minimum_permission].associated_roles]) > 0:
                return True
        else:
            if len([role for role in user.roles if int(role.id) in owner_perm.associated_roles]) > 0:
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
        # If the method hasn't returned, get sub permissions and loop again
        user_permissions = permissions[user_permissions.sub_permissions]


class Permission:
    def __init__(self, title, has_permissions, is_owner, sub_permissions, associated_roles):
        self.title = title
        self.has_permissions = has_permissions
        self.is_owner = is_owner
        self.sub_permissions = sub_permissions
        self.associated_roles = associated_roles
