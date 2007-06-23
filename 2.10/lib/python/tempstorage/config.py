from ZODB.config import BaseConfig

class TemporaryStorage(BaseConfig):
    def open(self):
        from tempstorage.TemporaryStorage import TemporaryStorage
        return TemporaryStorage(self.config.name)
