import json
import time
from datetime import datetime, timedelta, timezone
from time import sleep

from nectar import Hive
from nectar.account import Account
from nectar.nodelist import NodeList
from nectar.utils import formatTimeString

from hive_sbi.hsbi.core import load_config, setup_database_connections, setup_storage_objects
from hive_sbi.hsbi.member import Member
from hive_sbi.hsbi.transfer_ops_storage import TransferTrx
from hive_sbi.hsbi.utils import measure_execution_time


def memo_sp_delegation(
    transferMemos,
    memo_transfer_acc,
    sponsor,
    shares,
    sp_share_ratio,
    HIVE_symbol="HIVE",
):
    if "sp_delegation" not in transferMemos:
        return
    if transferMemos["sp_delegation"]["enabled"] == 0:
        return
    if memo_transfer_acc is None:
        return
    try:
        if (
            "%d" in transferMemos["sp_delegation"]["memo"]
            and "%.1f" in transferMemos["sp_delegation"]["memo"]
        ):
            if transferMemos["sp_delegation"]["memo"].find("%d") < transferMemos["sp_delegation"][
                "memo"
            ].find("%.1f"):
                memo_text = transferMemos["sp_delegation"]["memo"] % (
                    shares,
                    sp_share_ratio,
                )
            else:
                memo_text = transferMemos["sp_delegation"]["memo"] % (
                    sp_share_ratio,
                    shares,
                )
        elif "%d" in transferMemos["sp_delegation"]["memo"]:
            memo_text = transferMemos["sp_delegation"]["memo"] % shares
        else:
            memo_text = transferMemos["sp_delegation"]["memo"]
        memo_transfer_acc.transfer(sponsor, 0.001, HIVE_symbol, memo=memo_text)
        sleep(4)
    except Exception as e:
        print(f"Could not send 0.001 {HIVE_symbol} to {sponsor}: {str(e)}")


def memo_welcome(transferMemos, memo_transfer_acc, sponsor, HIVE_symbol="HIVE"):
    if "welcome" not in transferMemos:
        return

    if transferMemos["welcome"]["enabled"] == 0:
        return
    if memo_transfer_acc is None:
        return
    try:
        memo_text = transferMemos["welcome"]["memo"]
        memo_transfer_acc.transfer(sponsor, 0.001, HIVE_symbol, memo=memo_text)
        sleep(4)
    except Exception as e:
        print(f"Could not send 0.001 {HIVE_symbol} to {sponsor}: {str(e)}")


def memo_sponsoring(transferMemos, memo_transfer_acc, s, sponsor, HIVE_symbol="HIVE"):
    if "sponsoring" not in transferMemos:
        return
    if transferMemos["sponsoring"]["enabled"] == 0:
        return
    if memo_transfer_acc is None:
        return
    try:
        if "%s" in transferMemos["sponsoring"]["memo"]:
            memo_text = transferMemos["sponsoring"]["memo"] % sponsor
        else:
            memo_text = transferMemos["sponsoring"]["memo"]
        memo_transfer_acc.transfer(s, 0.001, HIVE_symbol, memo=memo_text)
        sleep(4)
    except Exception as e:
        print(f"Could not send 0.001 {HIVE_symbol} to {s}: {str(e)}")


def memo_update_shares(transferMemos, memo_transfer_acc, sponsor, shares, HIVE_symbol="HIVE"):
    if "update_shares" not in transferMemos:
        return
    if transferMemos["update_shares"]["enabled"] == 0:
        return
    if memo_transfer_acc is None:
        return
    try:
        if "%d" in transferMemos["update_shares"]["memo"]:
            memo_text = transferMemos["update_shares"]["memo"] % shares
        else:
            memo_text = transferMemos["update_shares"]["memo"]
        memo_transfer_acc.transfer(sponsor, 0.001, HIVE_symbol, memo=memo_text)
        sleep(4)
    except Exception as e:
        print(f"Could not send 0.001 {HIVE_symbol} to {sponsor}: {str(e)}")


def memo_sponsoring_update_shares(
    transferMemos, memo_transfer_acc, s, sponsor, shares, HIVE_symbol="HIVE"
):
    if "sponsoring_update_shares" not in transferMemos:
        return
    if transferMemos["sponsoring_update_shares"]["enabled"] == 0:
        return
    if memo_transfer_acc is None:
        return
    try:
        if (
            "%s" in transferMemos["sponsoring_update_shares"]["memo"]
            and "%d" in transferMemos["sponsoring_update_shares"]["memo"]
        ):
            if transferMemos["sponsoring_update_shares"]["memo"].find("%s") < transferMemos[
                "sponsoring_update_shares"
            ]["memo"].find("%d"):
                memo_text = transferMemos["sponsoring_update_shares"]["memo"] % (
                    sponsor,
                    shares,
                )
            else:
                memo_text = transferMemos["sponsoring_update_shares"]["memo"] % (
                    shares,
                    sponsor,
                )
        elif "%s" in transferMemos["sponsoring_update_shares"]["memo"]:
            memo_text = transferMemos["sponsoring_update_shares"]["memo"] % sponsor
        elif "%d" in transferMemos["sponsoring_update_shares"]["memo"]:
            memo_text = transferMemos["sponsoring_update_shares"]["memo"] % shares
        else:
            memo_text = transferMemos["sponsoring_update_shares"]["memo"]
        memo_transfer_acc.transfer(s, 0.001, HIVE_symbol, memo=memo_text)
        sleep(4)
    except Exception as e:
        print(f"Could not send 0.001 {HIVE_symbol} to {s}: {str(e)}")


def run():
    """Run the update member database module"""

    start_time = time.time()

    # Load configuration
    config_data = load_config()

    # Setup database connections
    db, db2 = setup_database_connections(config_data)

    # Setup storage objects
    storage = setup_storage_objects(db, db2)

    # Get storage objects
    transferStorage = TransferTrx(db)
    trxStorage = storage["trxStorage"]
    keyStorage = storage["keyStorage"]
    memberStorage = storage["memberStorage"]
    confStorage = storage["confStorage"]
    transactionStorage = storage["transactionStorage"]
    transferMemosStorage = storage["transferMemosStorage"]
    accountStorage = storage["accountStorage"]

    # Get configuration values
    accounts = accountStorage.get()
    other_accounts = accountStorage.get_transfer()
    mgnt_shares = config_data.get("mgnt_shares", {})
    hive_blockchain = config_data.get("hive_blockchain", True)

    # Get configuration settings
    conf_setup = confStorage.get()

    last_cycle = conf_setup["last_cycle"]
    
    # Ensure last_cycle has timezone info
    if last_cycle is not None:
        if isinstance(last_cycle, str):
            from nectar.utils import addTzInfo
            
            # Try to parse the datetime string directly instead of using formatTimeString
            try:
                # Try ISO format first (2025-01-01T00:00:00)
                last_cycle = datetime.fromisoformat(last_cycle)
            except ValueError:
                try:
                    # Try with space instead of T (2025-01-01 00:00:00)
                    last_cycle = datetime.strptime(last_cycle, '%Y-%m-%d %H:%M:%S%z')
                except ValueError:
                    try:
                        # Try without timezone (2025-01-01 00:00:00)
                        last_cycle = datetime.strptime(last_cycle, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        # Fall back to original method as last resort
                        # Using the globally imported formatTimeString
                        last_cycle = formatTimeString(last_cycle)
            
            # Ensure timezone info is added if needed
            if last_cycle.tzinfo is None:
                last_cycle = addTzInfo(last_cycle)
        elif last_cycle.tzinfo is None:
            from nectar.utils import addTzInfo
            last_cycle = addTzInfo(last_cycle)
    share_cycle_min = conf_setup["share_cycle_min"]
    sp_share_ratio = conf_setup["sp_share_ratio"]
    rshares_per_cycle = conf_setup["rshares_per_cycle"]
    upvote_multiplier = conf_setup["upvote_multiplier"]
    last_paid_post = conf_setup["last_paid_post"]
    last_paid_comment = conf_setup["last_paid_comment"]
    last_delegation_check = conf_setup["last_delegation_check"]
    minimum_vote_threshold = conf_setup["minimum_vote_threshold"]
    upvote_multiplier_adjusted = conf_setup["upvote_multiplier_adjusted"]

    time_diff = (datetime.now(timezone.utc) - last_cycle).total_seconds() / 60
    print(f"Last cycle: {formatTimeString(last_cycle)} - {time_diff:.2f} min")

    # Update last cycle if needed
    if last_cycle is None:
        last_cycle = datetime.now(timezone.utc) - timedelta(seconds=60 * 145)
        confStorage.update({"last_cycle": last_cycle})
    elif (datetime.now(timezone.utc) - last_cycle).total_seconds() > 60 * share_cycle_min:
        new_cycle = (datetime.now(timezone.utc) - last_cycle).total_seconds() > 60 * share_cycle_min
        current_cycle = last_cycle + timedelta(seconds=60 * share_cycle_min)

        print(f"Update member database, new cycle: {str(new_cycle)}")
        member_accounts = memberStorage.get_all_accounts()
        data = trxStorage.get_all_data()

        # Update current node list from @fullnodeupdate
        nodes = NodeList()
        try:
            nodes.update_nodes()
        except Exception as e:
            print(f"Could not update nodes: {str(e)}")
        hv = Hive(node=nodes.get_nodes(hive=hive_blockchain))

        # Get memo transfer account key
        # Using get_all_data() instead of get() since get() requires a memo_type parameter
        transferMemos = transferMemosStorage.get_all_data()
        db_entry = keyStorage.get("steembasicincome", "memo")
        if db_entry is not None:
            keyStorage.update(
                "steembasicincome",
                "memo",
                {
                    "pub": db_entry["pub"],
                    "wif": db_entry["wif"],
                    "memo": db_entry["memo"],
                },
            )
        # Get memo transfer account
        memo_transfer_acc = accountStorage.get_transfer_memo_sender()
        if len(memo_transfer_acc) > 0:
            memo_transfer_acc = memo_transfer_acc[0]
            if memo_transfer_acc is not None:
                try:
                    memo_transfer_acc = Account(memo_transfer_acc, blockchain_instance=hv)
                except Exception as e:
                    print(
                        f"{memo_transfer_acc} is not a valid Hive account! Will NOT be able to send transfer memos: {str(e)}"
                    )
        else:
            print("No transfer memo sender account found in the database")
            memo_transfer_acc = None

        member_data = {}
        share_age_member = {}
        for m in member_accounts:
            member_data[m] = Member(memberStorage.get(m))

        mngt_shares_assigned = False
        mngt_shares = 0
        delegation = {}
        delegation_timestamp = {}
        # clear shares
        for m in member_data:
            member_data[m]["shares"] = 0
            member_data[m]["bonus_shares"] = 0
            delegation[m] = 0
            delegation_timestamp[m] = None
            member_data[m].reset_share_age_list()

        shares_sum = 0
        latest_share = trxStorage.get_lastest_share_type("Mgmt")
        if latest_share is None:
            print("No management shares found in the database")
            mngt_shares_sum = 0
        else:
            mngt_shares_sum = (latest_share["index"] + 1) / len(mgnt_shares) * 100
            print(f"Management shares sum: {int(mngt_shares_sum)}")
        latest_data_timestamp = None

        for op in data:
            if op["status"] == "Valid":
                share_type = op["share_type"]
                if latest_data_timestamp is None:
                    latest_data_timestamp = formatTimeString(op["timestamp"])
                elif latest_data_timestamp < formatTimeString(op["timestamp"]):
                    latest_data_timestamp = formatTimeString(op["timestamp"])
                if share_type in ["DelegationLeased"]:
                    continue
                if isinstance(op["timestamp"], str):
                    timestamp = formatTimeString(op["timestamp"])
                else:
                    timestamp = op["timestamp"]
                if share_type in ["RemovedDelegation", "Delegation"]:
                    if share_type == "Delegation":
                        delegation[op["account"]] = op["vests"]
                        delegation_timestamp[op["account"]] = timestamp
                    else:
                        delegation[op["account"]] = 0
                        delegation_timestamp[op["account"]] = timestamp
                    continue
                if share_type in ["Mgmt", "MgmtTransfer"]:
                    if not mngt_shares_assigned:
                        for account in mgnt_shares:
                            mngt_shares = mgnt_shares[account]
                            if account not in member_data:
                                member = Member(account, mngt_shares, timestamp)
                                member.append_share_age(timestamp, mngt_shares)
                                member_data[account] = member
                            else:
                                member_data[account]["latest_enrollment"] = timestamp
                                member_data[account]["shares"] = mngt_shares
                                member_data[account].append_share_age(timestamp, mngt_shares)
                        mngt_shares_assigned = True
                    continue
                if share_type in ["ShareTransfer"]:
                    continue
                sponsor = op["sponsor"]
                sponsee = json.loads(op["sponsee"])
                shares = op["shares"]
                if shares == 0:
                    continue
                if sponsor not in member_data:
                    member = Member(sponsor, shares, timestamp)
                    member.append_share_age(timestamp, shares)
                    member_data[sponsor] = member
                else:
                    member_data[sponsor]["latest_enrollment"] = timestamp
                    member_data[sponsor]["shares"] += shares
                    member_data[sponsor].append_share_age(timestamp, shares)
                if len(sponsee) == 0:
                    continue
                for s in sponsee:
                    shares = sponsee[s]
                    if s not in member_data:
                        member = Member(s, shares, timestamp)
                        member.append_share_age(timestamp, shares)
                        member_data[s] = member
                        memo_sponsoring(transferMemos, memo_transfer_acc, s, sponsor)
                    else:
                        member_data[s]["latest_enrollment"] = timestamp
                        member_data[s]["shares"] += shares
                        member_data[s].append_share_age(timestamp, shares)
                        memo_sponsoring_update_shares(
                            transferMemos, memo_transfer_acc, s, sponsor, member_data[s]["shares"]
                        )

        # Add bonus shares from delegation
        for m in member_data:
            if m in delegation and delegation[m] > 0:
                hp = hv.vests_to_hp(float(delegation[m]))
                bonus_shares = int(hp / sp_share_ratio)
                member_data[m]["bonus_shares"] = bonus_shares
                member_data[m]["sp_delegation_shares"] = bonus_shares
                if delegation_timestamp[m] is not None:
                    member_data[m]["sp_delegation_timestamp"] = delegation_timestamp[m]
                memo_sp_delegation(
                    transferMemos, memo_transfer_acc, m, bonus_shares, sp_share_ratio
                )

        # Calculate share age
        for m in member_data:
            member_data[m].calc_share_age()

        # Calculate total shares
        shares = 0
        bonus_shares = 0
        for m in member_data:
            shares += member_data[m]["shares"]
            bonus_shares += member_data[m]["bonus_shares"]

        print(f"Shares: {shares}")
        print(f"Bonus shares: {bonus_shares}")
        print(f"Total shares: {shares + bonus_shares}")

        # Save member data to database
        member_list = []
        for m in member_data:
            member_list.append(member_data[m])
        memberStorage.add_batch(member_list)

        # Update last_cycle
        confStorage.update({"last_cycle": current_cycle})

    print(f"Member database update completed in {measure_execution_time(start_time):.2f} seconds")


if __name__ == "__main__":
    run()
