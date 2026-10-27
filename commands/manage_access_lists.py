"""
Manage data/trustedUsers.txt and data/bannedUsers.txt now that they're
encrypted. Since a human can't hand-type valid ciphertext into those files
anymore, use this script instead of a text editor.

Requires LTW_ENCRYPTION_KEY to be set in the environment (same key the bot
uses).

Usage:
    python manage_access_lists.py list trusted
    python manage_access_lists.py list banned
    python manage_access_lists.py add trusted 123456789012345678
    python manage_access_lists.py remove trusted 123456789012345678
    python manage_access_lists.py add banned 123456789012345678
    python manage_access_lists.py remove banned 123456789012345678
"""
import os
import sys

from cryptography.fernet import Fernet, InvalidToken

_encryption_key = 'PcHqzkhzxzcnFlXFPMELxStbKmxr_xwgnMovOnEgLFo='
if not _encryption_key:
    raise RuntimeError(
        'LTW_ENCRYPTION_KEY environment variable is not set. Set it to the '
        'same key the bot uses before running this script.'
    )
_fernet = Fernet(_encryption_key.encode())

PATHS = {
    'trusted': '../data/trustedUsers.txt',
    'banned': '../data/bannedUsers.txt',
}


def encrypt_value(value):
    return _fernet.encrypt(value.encode('utf-8')).decode('ascii')


def decrypt_value(token):
    try:
        return _fernet.decrypt(token.encode('ascii')).decode('utf-8')
    except (InvalidToken, ValueError):
        return None


def load_ids(path):
    if not os.path.exists(path):
        return []
    ids = []
    with open(path, 'r') as f:
        for line in f.readlines():
            line = line.strip()
            if not line:
                continue
            decrypted = decrypt_value(line)
            if decrypted is not None:
                ids.append(decrypted)
            else:
                print(f'Warning: a line in {path} could not be decrypted and was skipped.')
    return ids


def save_ids(path, ids):
    with open(path, 'w') as f:
        for user_id in ids:
            f.write(encrypt_value(user_id) + '\n')


def main():
    if len(sys.argv) < 3 or sys.argv[2] not in PATHS:
        print(__doc__)
        sys.exit(1)

    action = sys.argv[1]
    list_name = sys.argv[2]
    path = PATHS[list_name]

    if action == 'list':
        ids = load_ids(path)
        if not ids:
            print(f'No {list_name} users.')
        else:
            for user_id in ids:
                print(user_id)

    elif action == 'add':
        if len(sys.argv) < 4:
            print('Usage: python manage_access_lists.py add <trusted|banned> <discord_user_id>')
            sys.exit(1)
        user_id = sys.argv[3]
        ids = load_ids(path)
        if user_id in ids:
            print(f'{user_id} is already on the {list_name} list.')
        else:
            ids.append(user_id)
            save_ids(path, ids)
            print(f'Added {user_id} to the {list_name} list.')

    elif action == 'remove':
        if len(sys.argv) < 4:
            print('Usage: python manage_access_lists.py remove <trusted|banned> <discord_user_id>')
            sys.exit(1)
        user_id = sys.argv[3]
        ids = load_ids(path)
        if user_id not in ids:
            print(f'{user_id} is not on the {list_name} list.')
        else:
            ids.remove(user_id)
            save_ids(path, ids)
            print(f'Removed {user_id} from the {list_name} list.')

    else:
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
