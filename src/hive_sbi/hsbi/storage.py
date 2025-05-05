class BaseDB(object):
    """Base database class for all storage objects"""

    def __init__(self, db):
        self.db = db

    def exists_table(self):
        """Check if the table exists"""
        return self.__tablename__ in self.db.tables

    def create_table(self):
        """Create the table"""
        table = self.db.create_table(self.__tablename__)
        return table


class ConfigurationDB(BaseDB):
    """Configuration storage"""

    __tablename__ = "configuration"

    def __init__(self, db):
        super(ConfigurationDB, self).__init__(db)

    def get(self):
        """Get configuration"""
        table = self.db[self.__tablename__]
        config = table.find_one(id=1)
        if config is None:
            return {}
        return config

    def set(self, config):
        """Set configuration"""
        table = self.db[self.__tablename__]
        config["id"] = 1
        if table.find_one(id=1) is None:
            table.insert(config)
        else:
            table.update(config, ["id"])

    def update(self, config):
        """Update configuration"""
        table = self.db[self.__tablename__]
        current_config = table.find_one(id=1)
        if current_config is None:
            config["id"] = 1
            table.insert(config)
        else:
            for key, value in config.items():
                current_config[key] = value
            table.update(current_config, ["id"])


class AccountsDB(BaseDB):
    """Accounts storage"""

    __tablename__ = "accounts"

    def __init__(self, db):
        super(AccountsDB, self).__init__(db)

    def get(self):
        """Returns the accounts stored in the database"""
        table = self.db[self.__tablename__]
        accounts = []
        for a in table.all():
            if a["voting"]:
                accounts.append(a["name"])
        return accounts

    def get_transfer(self):
        """Returns the accounts stored in the database"""
        table = self.db[self.__tablename__]
        accounts = []
        for a in table.all():
            if a["transfer"] == 1:
                accounts.append(a["name"])
        return accounts

    def add(self, account_data):
        """Add an account to the database"""
        table = self.db[self.__tablename__]
        if table.find_one(name=account_data["name"]) is None:
            table.insert(account_data)
        else:
            table.update(account_data, ["name"])

    def update(self, account_data):
        """Update an account in the database"""
        table = self.db[self.__tablename__]
        table.update(account_data, ["name"])

    def get_all(self):
        """Returns all accounts stored in the database"""
        table = self.db[self.__tablename__]
        return table.all()


class KeysDB(BaseDB):
    """Keys storage"""

    __tablename__ = "keys"

    def __init__(self, db):
        super(KeysDB, self).__init__(db)

    def get(self, account, key_type):
        """Get a key from the database"""
        table = self.db[self.__tablename__]
        return table.find_one(account=account, key_type=key_type)

    def add(self, account, key_type, wif, pub_key=None):
        """Add a key to the database"""
        table = self.db[self.__tablename__]
        key_data = {
            "account": account,
            "key_type": key_type,
            "wif": wif,
            "pub_key": pub_key,
        }
        if table.find_one(account=account, key_type=key_type) is None:
            table.insert(key_data)
        else:
            table.update(key_data, ["account", "key_type"])


class MemberDB(BaseDB):
    """Member storage"""

    __tablename__ = "member"

    def __init__(self, db):
        super(MemberDB, self).__init__(db)

    def get(self, account):
        """Get a member from the database"""
        table = self.db[self.__tablename__]
        return table.find_one(account=account)

    def add(self, member_data):
        """Add a member to the database"""
        table = self.db[self.__tablename__]
        if table.find_one(account=member_data["account"]) is None:
            table.insert(member_data)
        else:
            table.update(member_data, ["account"])

    def update(self, member_data):
        """Update a member in the database"""
        table = self.db[self.__tablename__]
        table.update(member_data, ["account"])

    def get_all(self):
        """Returns all members stored in the database"""
        table = self.db[self.__tablename__]
        return table.all()


class TrxDB(BaseDB):
    """Transaction storage"""

    __tablename__ = "trx"

    def __init__(self, db):
        super(TrxDB, self).__init__(db)

    def add(self, trx_data):
        """Add a transaction to the database"""
        table = self.db[self.__tablename__]
        if table.find_one(trx_id=trx_data["trx_id"]) is None:
            table.insert(trx_data)
        else:
            table.update(trx_data, ["trx_id"])

    def get(self, trx_id):
        """Get a transaction from the database"""
        table = self.db[self.__tablename__]
        return table.find_one(trx_id=trx_id)

    def get_all(self):
        """Returns all transactions stored in the database"""
        table = self.db[self.__tablename__]
        return table.all()


class TransactionMemoDB(BaseDB):
    """Transaction memo storage"""

    __tablename__ = "trx_memo"

    def __init__(self, db):
        super(TransactionMemoDB, self).__init__(db)

    def add(self, memo_data):
        """Add a transaction memo to the database"""
        table = self.db[self.__tablename__]
        if table.find_one(trx_id=memo_data["trx_id"]) is None:
            table.insert(memo_data)
        else:
            table.update(memo_data, ["trx_id"])

    def get(self, trx_id):
        """Get a transaction memo from the database"""
        table = self.db[self.__tablename__]
        return table.find_one(trx_id=trx_id)

    def get_all(self):
        """Returns all transaction memos stored in the database"""
        table = self.db[self.__tablename__]
        return table.all()


class TransferMemoDB(BaseDB):
    """Transfer memo storage"""

    __tablename__ = "transfer_memo"

    def __init__(self, db):
        super(TransferMemoDB, self).__init__(db)

    def add(self, memo_data):
        """Add a transfer memo to the database"""
        table = self.db[self.__tablename__]
        if table.find_one(trx_id=memo_data["trx_id"]) is None:
            table.insert(memo_data)
        else:
            table.update(memo_data, ["trx_id"])

    def get(self, trx_id):
        """Get a transfer memo from the database"""
        table = self.db[self.__tablename__]
        return table.find_one(trx_id=trx_id)

    def get_all(self):
        """Returns all transfer memos stored in the database"""
        table = self.db[self.__tablename__]
        return table.all()
