import json
from datetime import datetime, timezone

import requests
from nectar import Hive
from nectar.memo import Memo
from nectar.nodelist import NodeList

from hive_sbi.hsbi.core import load_config, setup_database_connections, setup_storage_objects
from hive_sbi.hsbi.member import Member
from hive_sbi.hsbi.memo_parser import MemoParser
from hive_sbi.hsbi.transfer_ops_storage import AccountTrx, TransferTrx
from hive_sbi.hsbi.utils import measure_execution_time


def memo_sp_delegation(new_shares, sp_per_share):
    memo = f"Thank you for your SP delegation! Your shares have increased by {new_shares} ({sp_per_share} SP = +1 bonus share)"
    return memo


def memo_sp_adjustment(shares, sp_per_share):
    memo = "@steembasicincome has adjusted your shares according to your recalled delegation."
    memo += f"If you decide to delegate again, {sp_per_share}SP = +1 bonus share. You still have {shares} shares and will continue to receive upvotes"
    return memo


def memo_welcome():
    memo = "Your enrollment to Steem Basic Income has been processed."
    return memo


def memo_sponsoring(sponsor):
    memo = f"Congratulations! thanks to @{sponsor} you have been enrolled in Steem Basic Income."
    memo += "Learn more at https://steemit.com/basicincome/@steembasicincome/steem-basic-income-a-complete-overview"
    return memo


def memo_update_shares(shares):
    memo = f"Your Steem Basic Income has been increased. You now have {shares} shares!"
    return memo


def memo_sponsoring_update_shares(sponsor, shares):
    memo = f"Congratulations! thanks to @{sponsor} your Steem Basic Income has been increased. You now have "
    memo += f"{shares} shares! Learn more at https://steemit.com/basicincome/@steembasicincome/steem-basic-income-a-complete-overview"
    return memo


def check_blacklisted_members(memberStorage, hv):
    """Check if members are blacklisted"""
    member_accounts = memberStorage.get_all_accounts()
    member_data = {}
    for m in member_accounts:
        member_data[m] = Member(memberStorage.get(m))

    for m in member_data:
        response = requests.get(f"http://blacklist.usesteem.com/user/{m}")
        if "blacklisted" in response.json():
            if "steemcleaners" in response.json()["blacklisted"]:
                member_data[m]["steemcleaners"] = True
            else:
                member_data[m]["steemcleaners"] = False
            if "buildawhale" in response.json()["blacklisted"]:
                member_data[m]["buildawhale"] = True
            else:
                member_data[m]["buildawhale"] = False

    print("Writing member database")
    member_data_list = []
    for m in member_data:
        member_data_list.append(member_data[m])
    memberStorage.add_batch(member_data_list)


def process_less_or_no_sponsee(data, trxStorage, memberStorage, hv):
    """Process transactions with LessOrNoSponsee status"""
    memo_parser = MemoParser(blockchain_instance=hv)
    member_data = {}
    for m in memberStorage.get_all_accounts():
        member_data[m] = Member(memberStorage.get(m))

    for op in data:
        if op["status"] != "LessOrNoSponsee":
            continue
        processed_memo = ascii(op["memo"]).replace("\n", "").replace("\\n", "").replace("\\", "")
        print(processed_memo)
        if processed_memo[1] == "@":
            processed_memo = processed_memo[1:-1]

        if processed_memo[2] == "@":
            processed_memo = processed_memo[2:-2]
        [sponsor, sponsee, not_parsed_words, account_error] = memo_parser.parse_memo(
            processed_memo, op["shares"], op["account"]
        )
        sponsee_amount = 0
        for a in sponsee:
            sponsee_amount += sponsee[a]
        if account_error:
            continue
        if sponsee_amount != op["shares"]:
            continue
        for m in member_data:
            member_data[m].calc_share_age_until(op["timestamp"])

        max_avg_share_age = 0
        sponsee_name = None
        for m in member_data:
            if max_avg_share_age < member_data[m]["avg_share_age"]:
                max_avg_share_age = member_data[m]["avg_share_age"]
                sponsee_name = m
        if sponsee_amount == 0 and sponsee_name is not None:
            sponsee = {sponsee_name: op["shares"]}
            sponsee_dict = json.dumps(sponsee)
            print(sponsee_dict)
            trxStorage.update_sponsee_index(op["index"], op["source"], sponsee_dict, "Valid")


def process_encrypted_memos(data, trxStorage, hv):
    """Process encrypted memos"""
    for op in data:
        if op["status"] != "EncryptedMemo":
            continue
        try:
            memo = Memo(
                from_account=op["account"], to_account="steembasicincome", blockchain_instance=hv
            )
            decrypted_memo = memo.decrypt(op["memo"])
            print(f"decrypted memo: {decrypted_memo}")
            if decrypted_memo[0] == "@":
                trxStorage.update_memo(op["index"], op["source"], decrypted_memo, "Valid")
        except Exception as e:
            print(f"Could not decrypt memo: {str(e)}")


def run():
    """Run the maintenance module"""
    start_time = measure_execution_time()

    # Load configuration
    config_data = load_config()

    # Setup database connections
    db, db2 = setup_database_connections(config_data)

    # Setup storage objects
    storage = setup_storage_objects(db, db2)

    # Get storage objects
    transferStorage = TransferTrx(db)
    trxStorage = storage["trx"]
    keyStorage = storage["keys"]
    memberStorage = storage["members"]
    confStorage = storage["conf"]
    transactionStorage = storage["transactions"]
    accountStorage = storage["accounts"]

    # Get configuration values
    accounts = accountStorage.get()
    other_accounts = accountStorage.get_transfer()
    mgnt_shares = config_data.get("mgnt_shares", {})
    hive_blockchain = config_data.get("hive_blockchain", True)

    conf_setup = confStorage.get()

    last_cycle = conf_setup["last_cycle"]
    share_cycle_min = conf_setup["share_cycle_min"]
    sp_share_ratio = conf_setup["sp_share_ratio"]
    rshares_per_cycle = conf_setup["rshares_per_cycle"]
    upvote_multiplier = conf_setup["upvote_multiplier"]
    last_paid_post = conf_setup["last_paid_post"]
    last_paid_comment = conf_setup["last_paid_comment"]
    last_delegation_check = conf_setup["last_delegation_check"]
    minimum_vote_threshold = conf_setup["minimum_vote_threshold"]
    upvote_multiplier_adjusted = conf_setup["upvote_multiplier_adjusted"]

    # Setup account transactions
    accountTrx = {}
    for account in accounts:
        if account == "steembasicincome":
            accountTrx["sbi"] = AccountTrx(db, "sbi")
        else:
            accountTrx[account] = AccountTrx(db, account)

    # Get transaction data
    data = trxStorage.get_all_data()
    data = sorted(
        data,
        key=lambda x: (datetime.now(timezone.utc) - x["timestamp"]).total_seconds(),
        reverse=True,
    )

    # Setup Hive connection
    key_list = []
    key = keyStorage.get("steembasicincome", "memo")
    if key is not None:
        key_list.append(key["wif"])

    nodes = NodeList()
    try:
        nodes.update_nodes()
    except Exception as e:
        print(f"Could not update nodes: {str(e)}")
    hv = Hive(keys=key_list, node=nodes.get_nodes(hive=hive_blockchain))

    # Maintenance operations can be enabled/disabled here

    # Example: Check if members are blacklisted
    if False:  # Disabled by default
        check_blacklisted_members(memberStorage, hv)

    # Example: Process less or no sponsee transactions
    if False:  # Disabled by default
        process_less_or_no_sponsee(data, trxStorage, memberStorage, hv)

    # Example: Deal with encrypted memos
    if False:  # Disabled by default
        process_encrypted_memos(data, trxStorage, hv)

    print(f"Maintenance completed in {measure_execution_time(start_time):.2f} seconds")


if __name__ == "__main__":
    run()
