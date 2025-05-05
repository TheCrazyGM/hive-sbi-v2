import json
from datetime import datetime, timedelta, timezone

from nectar import Hive
from nectar.block import Block
from nectar.blockchain import Blockchain
from nectar.comment import Comment
from nectar.nodelist import NodeList
from nectar.utils import addTzInfo, formatTimeString
from nectar.wallet import Wallet
from nectarbase.signedtransactions import Signed_Transaction
from nectargraphenebase.base58 import Base58

from hive_sbi.hsbi.member import Member
from hive_sbi.hsbi.transfer_ops_storage import AccountTrx
from hive_sbi.hsbi.utils import (
    load_config,
    measure_execution_time,
    setup_database_connections,
    setup_storage_objects,
)


def run():
    """Run the check promotion post module"""
    start_time = measure_execution_time()

    # Load configuration
    config_data = load_config()

    # Setup database connections
    db, db2 = setup_database_connections(config_data)

    # Setup storage objects
    storage = setup_storage_objects(db, db2)

    # Get storage objects
    transferStorage = storage["transfers"]
    trxStorage = storage["trx"]
    memberStorage = storage["members"]
    accountStorage = storage["accounts"]
    confStorage = storage["conf"]

    # Get configuration values
    accounts = accountStorage.get()
    hive_blockchain = config_data.get("hive_blockchain", True)

    # Initialize account transaction storage
    accountTrx = {}
    for account in accounts:
        accountTrx[account] = AccountTrx(db, account)

    # Get configuration settings
    conf_setup = confStorage.get()

    last_cycle = conf_setup["last_cycle"]
    share_cycle_min = conf_setup["share_cycle_min"]
    sp_share_ratio = conf_setup["sp_share_ratio"]
    rshares_per_cycle = conf_setup["rshares_per_cycle"]
    upvote_multiplier = conf_setup["upvote_multiplier"]
    last_paid_post = conf_setup["last_paid_post"]
    last_paid_comment = conf_setup["last_paid_comment"]

    minimum_vote_threshold = conf_setup["minimum_vote_threshold"]
    comment_vote_divider = conf_setup["comment_vote_divider"]
    comment_vote_timeout_h = conf_setup["comment_vote_timeout_h"]

    time_diff = (datetime.now(timezone.utc) - last_cycle).total_seconds() / 60
    print(f"Last cycle: {formatTimeString(last_cycle)} - {time_diff:.2f} min")

    # Update last cycle time
    last_cycle = datetime.now(timezone.utc) - timedelta(seconds=60 * 145)
    confStorage.update({"last_cycle": last_cycle})
    print("Updating member database...")

    # Get member accounts
    member_accounts = memberStorage.get_all_accounts()
    data = trxStorage.get_all_data()

    # Update current node list from @fullnodeupdate
    nodes = NodeList()
    try:
        nodes.update_nodes()
    except Exception as e:
        print(f"Could not update nodes: {str(e)}")
    hv = Hive(node=nodes.get_nodes(hive=hive_blockchain))

    # Load member data
    member_data = {}
    for m in member_accounts:
        member_data[m] = Member(memberStorage.get(m))

    # Process blockchain data
    b = Blockchain(blockchain_instance=hv)
    wallet = Wallet(blockchain_instance=hv)

    for acc_name in accounts:
        print(f"Processing account: {acc_name}")
        comments_transfer = []
        ops = accountTrx[acc_name].get_all(op_types=["transfer"])
        cnt = 0
        for o in ops:
            cnt += 1
            if cnt % 10 == 0:
                print(f"{cnt}/{len(ops)}")
            op = json.loads(o["op_dict"])
            if op["memo"] == "":
                continue
            try:
                c = Comment(op["memo"], blockchain_instance=hv)
            except Exception:
                continue
            if c["author"] not in accounts:
                continue
            if c["authorperm"] not in comments_transfer:
                comments_transfer.append(c["authorperm"])
        print(f"{len(comments_transfer)} comments with transfer found")

        for authorperm in comments_transfer:
            c = Comment(authorperm, blockchain_instance=hv)
            print(c["authorperm"])
            for vote in c["active_votes"]:
                if vote["rshares"] == 0:
                    continue
                if (
                    addTzInfo(datetime.now(timezone.utc)) - (vote["time"])
                ).total_seconds() / 60 / 60 / 24 <= 7:
                    continue
                if vote["voter"] not in member_data:
                    continue
                if vote["rshares"] > 50000000:
                    try:
                        block_num = b.get_estimated_block_num(vote["time"])
                        current_block_num = b.get_current_block_num()
                        transaction = None
                        block_search_list = [
                            0,
                            1,
                            -1,
                            2,
                            -2,
                            3,
                            -3,
                            4,
                            -4,
                            5,
                            -5,
                        ]
                        block_cnt = 0
                        while transaction is None and block_cnt < len(block_search_list):
                            if block_num + block_search_list[block_cnt] > current_block_num:
                                block_cnt += 1
                                continue
                            block = Block(
                                block_num + block_search_list[block_cnt],
                                blockchain_instance=hv,
                            )
                            for tt in block.transactions:
                                for op in tt["operations"]:
                                    if isinstance(op, dict) and op["type"][:4] == "vote":
                                        if op["value"]["voter"] == vote["voter"]:
                                            transaction = tt
                                    elif (
                                        isinstance(op, list) and len(op) > 1 and op[0][:4] == "vote"
                                    ):
                                        if op[1]["voter"] == vote["voter"]:
                                            transaction = tt
                            block_cnt += 1
                        vote_did_sign = True
                        key_accounts = []
                        if transaction is not None:
                            signed_tx = Signed_Transaction(transaction)
                            public_keys = []
                            for key in signed_tx.verify(
                                chain=hv.chain_params, recover_parameter=True
                            ):
                                public_keys.append(
                                    format(
                                        Base58(key, prefix=hv.prefix),
                                        hv.prefix,
                                    )
                                )

                            empty_public_keys = []
                            for key in public_keys:
                                pubkey_account = wallet.getAccountFromPublicKey(key)
                                if pubkey_account is None:
                                    empty_public_keys.append(key)
                                else:
                                    key_accounts.append(pubkey_account)

                        for a in key_accounts:
                            if vote["voter"] == a:
                                continue
                            if a not in ["quarry", "steemdunk"]:
                                print(a)
                            if a in [
                                "smartsteem",
                                "smartmarket",
                                "upme",
                                "boomerang",
                                "minnowbooster",
                                "tipu",
                                "bdvoter",
                                "rocky1",
                                "buildawhale",
                                "booster",
                                "sneaky-ninja",
                                "upmewhale",
                                "promobot",
                            ]:
                                print(f"Found vote bot: {a}")
                                member_data[vote["voter"]]["blacklist"] = True
                                member_data[vote["voter"]]["comment"] = f"Vote bought from {a}"
                                member_data[vote["voter"]]["skip_rounds"] = 10
                                member_data[vote["voter"]]["last_update"] = datetime.now(
                                    timezone.utc
                                )
                                memberStorage.update(member_data[vote["voter"]])
                    except Exception as e:
                        print(f"Error: {str(e)}")

    print(f"Promotion post check completed in {measure_execution_time(start_time):.2f} seconds")


if __name__ == "__main__":
    run()
