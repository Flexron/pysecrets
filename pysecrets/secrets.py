from cryptography.fernet import Fernet, InvalidToken
from datetime import datetime

import pickle
import base64
import pathlib
import shutil
import os

from pysecrets import constants


class KeyGenerator:

    def __new__(cls, password: str):
        return cls.generate_password_size_32(password)

    @classmethod
    def generate_password_size_32(cls, password):
        size = len(password)

        if size >= 32:
            return password[:32]

        nb = 32 // size
        rest = 32 % size
        res = password * nb + password[:rest]

        return base64.urlsafe_b64encode(str.encode(res))


class Secrets:

    def __init__(self, database: str, password: str):
        self._key: Fernet = Fernet(KeyGenerator(password))
        self._database: str = database
        self._secrets: dict = {}

    def set_key(self, password: str):
        self._key = Fernet(KeyGenerator(password))

    def __getitem__(self, key):
        encrypted_secret = self._secrets[key]
        try:
            secret = self._key.decrypt(encrypted_secret).decode()
        except InvalidToken:
            return "Your password is wrong !!"
        else:
            return secret

    def __setitem__(self, key, secret):
        value = self._key.encrypt(secret.encode())
        self._secrets[key] = value

    def list_keys(self):
        return list(self._secrets.keys())

    def __getstate__(self):
        content = self.__dict__.copy()
        content["_key"] = None
        return content


class StorageManager:

    @classmethod
    def _get_app_path(cls, app_path):
        if app_path:
            return app_path
        return os.path.join(os.getenv("HOME"), f".{constants.Data.APP_NAME}")

    def __init__(self, database: str, app_path: str = None):
        self._app_path = self._get_app_path(app_path)

        if not os.path.exists(self._app_path):
            os.mkdir(self._app_path)

        self._archive_path = self._app_path + "/_archives"
        if not os.path.exists(self._archive_path):
            os.mkdir(self._archive_path)

        self._archive_database_path = self._archive_path + f"/{database}"
        if not os.path.exists(self._archive_database_path):
            os.mkdir(self._archive_database_path)

        self._database_path = self._app_path + f"/{database}"
        if not os.path.exists(self._database_path):
            os.mkdir(self._database_path)

        self._secret_file_name = f"{constants.Data.SECRET_FILE_NAME}.{constants.Data.SECRET_FILE_EXT}"

    def save(self, secret):
        path = self._database_path + f"/{self._secret_file_name}"

        with open(path, "wb") as f:
            pickle.dump(secret, f)

        self._archive(path)

        self._vacuum()

    def load(self):
        path = self._database_path + f"/{self._secret_file_name}"
        if not os.path.exists(path):
            paths = self._get_secret_file_paths_from_archive()
            if not paths:
                return None
            path = paths[-1].__str__()

        with open(path, "rb") as f:
            secret = pickle.load(f)

        return secret

    def _archive(self, secret_file_path: str, name=constants.Data.SECRET_FILE_NAME):
        date = datetime.now().strftime('%y%m%d_%H%M%S_%f')
        secret_archive_path = self._archive_database_path + f"/{name}_{date}.{constants.Data.SECRET_FILE_EXT}"
        #os.rename(src=secret_file_path, dst=secret_archive_path)
        shutil.copy(src=secret_file_path, dst=secret_archive_path)

    def _get_secret_file_paths_from_archive(self):
        path = pathlib.Path(self._archive_database_path)
        return sorted(
            path.glob(f"{constants.Data.SECRET_FILE_NAME}*.{constants.Data.SECRET_FILE_EXT}")
        )

    def _vacuum(self, files_to_keep=7):
        secret_file_paths = self._get_secret_file_paths_from_archive()
        if len(secret_file_paths) > files_to_keep:
            to_remove = secret_file_paths[0]
            os.remove(to_remove.__str__())

