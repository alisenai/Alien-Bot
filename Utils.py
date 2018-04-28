import re


# Used to check if a string is a hex value
def is_hex(string):
    if re.match(r'^0x(?:[0-9a-fA-F]{3}){1,2}$', string):
        return True
    return False

