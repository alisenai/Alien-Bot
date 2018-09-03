from Common import DataManager

permissions = {}
default_perm = None
owner_perm = None


def load_permissions():
    global default_perm
    global owner_perm
    print("[Loading permissions]", end='')
    permissions_config = DataManager.get_manager("bot_config").get_data(key="Permissions")
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
            assert owner_perm is None, "Bot config contains more than one owner permission."
            owner_perm = permission
    assert owner_perm is not None, "There must be one owner permission"
    assert default_perm is not None, "There must be one default permission"
    print("[Done]")


# Returns a user's permission, given that user
def get_user_permission(user):
    for permission_name in permissions:
        permission = permissions[permission_name]
        if len([role for role in user.roles if int(role.id) in permission.associated_roles]):
            return permission
    return default_perm


# Returns True if the given user has the given permission, else false
def has_permission(user, minimum_permission):
    user_permissions = get_user_permission(user)
    while True:
        # If the user is a bot owner, they can use any command (that is enabled) -> Return True
        if user_permissions.is_owner:
            return True
        # If user title has no permissions -> Return false
        if user_permissions.has_permissions is False:
            return False
        # If the user has a role that counts as having that permission
        if minimum_permission in permissions:
            needed_roles = permissions[minimum_permission].associated_roles
            if len([role for role in user.roles if int(role.id) in needed_roles]) > 0:
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
