from datetime import datetime


class Member(object):
    """Member class for Hive SBI"""

    def __init__(self, account, shares=0, bonus_shares=0, total_share_days=0, last_update=None):
        self.account = account
        self.shares = shares
        self.bonus_shares = bonus_shares
        self.total_share_days = total_share_days
        self.last_update = last_update or datetime.now()

    def get_total_shares(self):
        """Get total shares (regular + bonus)"""
        return self.shares + self.bonus_shares

    def add_shares(self, shares):
        """Add shares to the member"""
        self.shares += shares
        self.last_update = datetime.now()

    def add_bonus_shares(self, bonus_shares):
        """Add bonus shares to the member"""
        self.bonus_shares += bonus_shares
        self.last_update = datetime.now()

    def remove_shares(self, shares):
        """Remove shares from the member"""
        if shares > self.shares:
            shares = self.shares
        self.shares -= shares
        self.last_update = datetime.now()

    def remove_bonus_shares(self, bonus_shares):
        """Remove bonus shares from the member"""
        if bonus_shares > self.bonus_shares:
            bonus_shares = self.bonus_shares
        self.bonus_shares -= bonus_shares
        self.last_update = datetime.now()

    def update_share_days(self):
        """Update share days based on time since last update"""
        now = datetime.now()
        days_since_update = (now - self.last_update).total_seconds() / 86400
        self.total_share_days += self.get_total_shares() * days_since_update
        self.last_update = now

    def reset_share_days(self):
        """Reset share days to zero"""
        self.total_share_days = 0
        self.last_update = datetime.now()

    def to_dict(self):
        """Convert member to dictionary"""
        return {
            "account": self.account,
            "shares": self.shares,
            "bonus_shares": self.bonus_shares,
            "total_share_days": self.total_share_days,
            "last_update": self.last_update.isoformat(),
        }

    @classmethod
    def from_dict(cls, data):
        """Create member from dictionary"""
        last_update = data.get("last_update")
        if isinstance(last_update, str):
            from dateutil.parser import parse

            last_update = parse(last_update)

        return cls(
            account=data["account"],
            shares=data.get("shares", 0),
            bonus_shares=data.get("bonus_shares", 0),
            total_share_days=data.get("total_share_days", 0),
            last_update=last_update,
        )
