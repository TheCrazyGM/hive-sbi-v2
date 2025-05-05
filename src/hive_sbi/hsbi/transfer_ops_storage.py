class TransferTrx(object):
    """Transfer transaction storage"""

    def __init__(self, db, account):
        self.db = db
        self.account = account
        self.table_name = f"transfer_trx_{account}"
        self.create_table()

    def create_table(self):
        """Create the table"""
        if self.table_name not in self.db.tables:
            self.db.create_table(self.table_name)

    def add(self, trx_data):
        """Add a transaction to the database"""
        table = self.db[self.table_name]
        if table.find_one(trx_id=trx_data["trx_id"]) is None:
            table.insert(trx_data)
        else:
            table.update(trx_data, ["trx_id"])

    def get(self, trx_id):
        """Get a transaction from the database"""
        table = self.db[self.table_name]
        return table.find_one(trx_id=trx_id)

    def get_all(self):
        """Returns all transactions stored in the database"""
        table = self.db[self.table_name]
        return table.all()

    def get_latest(self, limit=100):
        """Returns the latest transactions stored in the database"""
        table = self.db[self.table_name]
        return table.find(order_by="-timestamp", _limit=limit)

    def get_latest_block_num(self):
        """Returns the latest block number stored in the database"""
        table = self.db[self.table_name]
        latest = table.find_one(order_by="-block_num")
        if latest is None:
            return 0
        return latest["block_num"]

    def get_latest_trx_index(self, block_num):
        """Returns the latest transaction index stored in the database for a given block"""
        table = self.db[self.table_name]
        latest = table.find_one(block_num=block_num, order_by="-trx_in_block")
        if latest is None:
            return -1
        return latest["trx_in_block"]


class AccountTrx(object):
    """Account transaction storage"""

    def __init__(self, db, account):
        self.db = db
        self.account = account
        self.table_name = f"account_trx_{account}"
        self.create_table()

    def create_table(self):
        """Create the table"""
        if self.table_name not in self.db.tables:
            self.db.create_table(self.table_name)

    def add(self, trx_data):
        """Add a transaction to the database"""
        table = self.db[self.table_name]
        if table.find_one(trx_id=trx_data["trx_id"]) is None:
            table.insert(trx_data)
        else:
            table.update(trx_data, ["trx_id"])

    def get(self, trx_id):
        """Get a transaction from the database"""
        table = self.db[self.table_name]
        return table.find_one(trx_id=trx_id)

    def get_all(self):
        """Returns all transactions stored in the database"""
        table = self.db[self.table_name]
        return table.all()

    def get_latest(self, limit=100):
        """Returns the latest transactions stored in the database"""
        table = self.db[self.table_name]
        return table.find(order_by="-timestamp", _limit=limit)

    def get_latest_block_num(self):
        """Returns the latest block number stored in the database"""
        table = self.db[self.table_name]
        latest = table.find_one(order_by="-block_num")
        if latest is None:
            return 0
        return latest["block_num"]

    def get_latest_trx_index(self, block_num):
        """Returns the latest transaction index stored in the database for a given block"""
        table = self.db[self.table_name]
        latest = table.find_one(block_num=block_num, order_by="-trx_in_block")
        if latest is None:
            return -1
        return latest["trx_in_block"]
