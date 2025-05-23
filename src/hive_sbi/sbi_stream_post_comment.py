import json
import random
import time

from nectar import Hive
from nectar.blockchain import Blockchain
from nectar.comment import Comment
from nectar.nodelist import NodeList
from nectar.utils import construct_authorperm

from hive_sbi.hsbi.core import (
    get_logger,
    load_config,
    setup_database_connections,
    setup_storage_objects,
)

logger = get_logger()
from hive_sbi.hsbi.member import Member
from hive_sbi.hsbi.storage import MemberDB
from hive_sbi.hsbi.transfer_ops_storage import PostsTrx
from hive_sbi.hsbi.utils import measure_execution_time
from hive_sbi.hsbi.version import version as sbiversion


def run():
    start_prep_time = time.time()

    # Load configuration
    config_data = load_config()

    # Setup database connections
    db, db2 = setup_database_connections(config_data)

    # Setup storage objects
    storage = setup_storage_objects(db, db2)

    # Get storage objects
    trxStorage = storage["trxStorage"]
    memberStorage = storage["memberStorage"]
    confStorage = storage["confStorage"]
    keyStorage = storage["keyStorage"]

    # Get blockchain setting
    hive_blockchain = config_data.get("hive_blockchain", True)

    accounts = storage["accounts"]
    other_accounts = storage["other_accounts"]

    blacklist = storage["blacklist"]

    blacklist_tags = []
    for t in blacklist["tags"].split(","):
        blacklist_tags.append(t.strip())

    blacklist_apps = []
    for t in blacklist["apps"].split(","):
        blacklist_apps.append(t.strip())

    blacklist_body = []
    for t in blacklist["body"].split(","):
        blacklist_body.append(t.strip())

    conf_setup = confStorage.get()

    last_cycle = conf_setup["last_cycle"]
    share_cycle_min = conf_setup["share_cycle_min"]
    sp_share_ratio = conf_setup["sp_share_ratio"]
    rshares_per_cycle = conf_setup["rshares_per_cycle"]
    minimum_vote_threshold = conf_setup["minimum_vote_threshold"]
    comment_vote_divider = conf_setup["comment_vote_divider"]
    comment_footer = conf_setup["comment_footer"]

    member_accounts = memberStorage.get_all_accounts()
    logger.info("%d members in list" % len(member_accounts))

    nobroadcast = False
    # nobroadcast = True

    member_data = {}
    for m in member_accounts:
        member_data[m] = Member(memberStorage.get(m))

    postTrx = PostsTrx(db)

    logger.info("stream new posts")

    max_batch_size = 50
    threading = False
    wss = False
    https = True
    normal = False
    appbase = True

    nodes = NodeList()
    # nodes.update_nodes(weights={"block": 1})
    try:
        nodes.update_nodes()
    except Exception as e:
        logger.warning(f"could not update nodes: {str(e)}")

    keys = []
    account_list = []
    for acc in accounts:
        account_list.append(acc)
        keys.append(keyStorage.get(acc, "posting"))
    keys_list = []
    for k in keys:
        if k["key_type"] == "posting":
            keys_list.append(k["wif"].replace("\n", "").replace("\r", ""))
    node_list = nodes.get_nodes(hive=hive_blockchain)
    hv = Hive(
        node=node_list,
        keys=keys_list,
        num_retries=5,
        call_num_retries=3,
        timeout=15,
        nobroadcast=nobroadcast,
    )

    b = Blockchain(blockchain_instance=hv)
    print("deleting old posts")
    postTrx.delete_old_posts(1)
    # print("reading all authorperm")
    already_voted_posts = []
    flagged_posts = []
    start_block = b.get_current_block_num() - int(28800)
    stop_block = b.get_current_block_num()
    last_block_print = start_block

    latest_update = postTrx.get_latest_post()
    latest_block = postTrx.get_latest_block()
    if latest_block is not None and latest_block > start_block:
        latest_update_block = latest_block
    elif latest_block is not None and latest_block < start_block:
        latest_update_block = start_block
    elif latest_update is not None:
        latest_update_block = b.get_estimated_block_num(latest_update)
    else:
        latest_update_block = start_block
    print("latest update %s - %d to %d" % (str(latest_update), latest_update_block, stop_block))

    start_block = max([latest_update_block, start_block]) + 1
    if stop_block > start_block + 6000:
        stop_block = start_block + 6000
    cnt = 0
    updated_accounts = []
    posts_dict = {}
    changed_member_data = []
    for ops in b.stream(
        start=start_block,
        stop=stop_block,
        opNames=["comment"],
        max_batch_size=max_batch_size,
        threading=threading,
        thread_num=8,
    ):
        # print(ops)
        timestamp = ops["timestamp"]
        # timestamp = timestamp.replace(tzinfo=None)
        # continue
        if ops["author"] not in member_accounts:
            continue
        if ops["block_num"] <= latest_update_block:
            continue
        if ops["block_num"] - last_block_print > 50:
            last_block_print = ops["block_num"]
            print(
                "blocks left %d - post found: %d" % (ops["block_num"] - stop_block, len(posts_dict))
            )
        authorperm = construct_authorperm(ops)
        c = None
        cnt = 0
        use_tags_api = True
        while c is None and cnt < 5:
            cnt += 1
            try:
                c = Comment(authorperm, use_tags_api=use_tags_api, blockchain_instance=hv)
            except Exception:
                c = None
                use_tags_api = False
                continue
        if c is None:
            continue
        main_post = c.is_main_post()
        if ops["author"] not in changed_member_data:
            changed_member_data.append(ops["author"])
        if main_post:
            if "last_update" in c:
                last_update = c["last_update"]
            else:
                last_update = c["updated"]
            if c["created"] == last_update:
                member_data[ops["author"]]["last_post"] = c["created"]
                member_data[ops["author"]]["comment_upvote"] = 0
        else:
            member_data[ops["author"]]["last_comment"] = c["created"]
            status_command = c.body.find("!sbi status")
            if status_command > -1 and abs((ops["timestamp"] - c["created"]).total_seconds()) <= 10:
                rshares_denom = (
                    member_data[ops["author"]]["rewarded_rshares"]
                    + member_data[ops["author"]]["balance_rshares"]
                )

                reply_body = "Hi @%s!\n\n" % ops["author"]
                reply_body += "* you have %d units and %d bonus units\n" % (
                    member_data[ops["author"]]["shares"],
                    member_data[ops["author"]]["bonus_shares"],
                )
                reply_body += "* your rshares balance is %d or %.3f $\n" % (
                    member_data[ops["author"]]["balance_rshares"],
                    hv.rshares_to_sbd(member_data[ops["author"]]["balance_rshares"]),
                )
                if member_data[ops["author"]]["comment_upvote"] == 0:
                    rshares = member_data[ops["author"]]["balance_rshares"] / comment_vote_divider
                    if rshares > minimum_vote_threshold:
                        reply_body += "* your next SBI upvote is predicted to be %.3f $\n" % (
                            hv.rshares_to_sbd(rshares)
                        )
                    else:
                        reply_body += (
                            "* you need to wait until your upvote value (current value: %.3f $) is above %.3f $\n"
                            % (
                                hv.rshares_to_sbd(rshares),
                                hv.rshares_to_sbd(minimum_vote_threshold),
                            )
                        )
                else:
                    rshares = member_data[ops["author"]]["balance_rshares"] / comment_vote_divider
                    # reply_body += "* as you did not wrote a post within the last 7 days, your pending vote accumulates until you post."
                    if rshares > minimum_vote_threshold * 20:
                        reply_body += "* your next SBI upvote is predicted to be %.3f $\n" % (
                            hv.rshares_to_sbd(int(minimum_vote_threshold * 20))
                        )
                    elif rshares > minimum_vote_threshold * 2:
                        reply_body += "* your next SBI upvote is predicted to be %.3f $\n" % (
                            hv.rshares_to_sbd(rshares)
                        )
                    else:
                        reply_body += (
                            "* you need to wait until your upvote value (current value: %.3f $) is above %.3f $\n"
                            % (
                                hv.rshares_to_sbd(rshares),
                                hv.rshares_to_sbd(minimum_vote_threshold * 2),
                            )
                        )
                if rshares_denom > 0:
                    reply_body += "\n\nStructure of your total SBI vote value:\n"
                    reply_body += "* %.2f %% has come from your subscription level\n" % (
                        member_data[ops["author"]]["subscribed_rshares"] / rshares_denom * 100
                    )
                    reply_body += "* %.2f %% has come from your bonus units\n" % (
                        member_data[ops["author"]]["delegation_rshares"] / rshares_denom * 100
                    )
                    reply_body += "* %.2f %% has come from upvoting rewards\n" % (
                        member_data[ops["author"]]["curation_rshares"] / rshares_denom * 100
                    )
                    reply_body += (
                        "* %.2f %% has come from new account bonus or extra value from pre-automation rewards\n"
                        % (member_data[ops["author"]]["other_rshares"] / rshares_denom * 100)
                    )
                if len(comment_footer) > 0:
                    reply_body += "<br>\n"
                    reply_body += comment_footer

                account_name = account_list[random.randint(0, len(account_list) - 1)]
                try:
                    hv.post(
                        "",
                        reply_body,
                        app="steembasicincome/%s" % sbiversion,
                        author=account_name,
                        reply_identifier=c.identifier,
                    )
                    # c.reply(reply_body, author=account_name)
                    time.sleep(4)
                except Exception:
                    continue

        already_voted = False

        # for v in c["active_votes"]:
        #    if v["voter"] in accounts:
        #        already_voted = True

        dt_created = c["created"]
        dt_created = dt_created.replace(tzinfo=None)
        skip = False
        if (
            "tags" in c and c["tags"] is not None and type(c["tags"]) == type([])
        ):  # ensure that tags is an array
            for tag in c["tags"]:
                if tag is not None and isinstance(tag, str) and tag.lower() in blacklist_tags:
                    skip = True
        json_metadata = c.json_metadata
        if isinstance(json_metadata, str):
            try:
                json_metadata = json.loads(json_metadata)
            except Exception:
                json_metadata = {}
        if "app" in json_metadata:
            app = json_metadata["app"]
            if isinstance(app, dict) and "name" in app:
                app = app["name"]
            if app is not None and isinstance(app, str) and app.find("/") > -1:
                app = app.split("/")[0]
            if app is not None and isinstance(app, str) and app.lower() in blacklist_apps:
                skip = True
        for s in blacklist_body:
            if c.body.find(s) > -1:
                skip = True

        vote_delay = member_data.get(ops["author"], {}).get("upvote_delay", 300)
        if vote_delay is None:
            vote_delay = 300
        posts_dict[authorperm] = {
            "authorperm": authorperm,
            "author": ops["author"],
            "created": dt_created,
            "block": ops["block_num"],
            "main_post": main_post,
            "voted": already_voted,
            "skip": skip,
            "vote_delay": vote_delay,
        }

        if len(posts_dict) > 100:
            start_time = time.time()
            postTrx.add_batch(posts_dict)
            print("Adding %d post took %.2f seconds" % (len(posts_dict), time.time() - start_time))
            posts_dict = {}

        cnt += 1

    print("write member database")
    member_data_list = []
    for m in changed_member_data:
        member_data_list.append(member_data[m])

    # Use the existing db2 connection from setup_database_connections
    memberStorage = MemberDB(db2)
    memberStorage.add_batch(member_data_list)
    member_data_list = []
    if len(posts_dict) > 0:
        start_time = time.time()
        postTrx.add_batch(posts_dict)
        print("Adding %d post took %.2f seconds" % (len(posts_dict), time.time() - start_time))
        posts_dict = {}

    print(f"stream posts script run {measure_execution_time(start_prep_time):.2f} s")


if __name__ == "__main__":
    run()
