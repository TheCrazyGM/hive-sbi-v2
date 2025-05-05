from nectar.amount import Amount


def parse_transfer_op(op, timestamp):
    """
    Parse a transfer operation

    Args:
        op (dict): Transfer operation data
        timestamp (str): Operation timestamp

    Returns:
        dict: Parsed transfer data
    """
    transfer_data = {
        "from": op[1]["from"],
        "to": op[1]["to"],
        "amount": Amount(op[1]["amount"]).amount,
        "symbol": Amount(op[1]["amount"]).symbol,
        "memo": op[1]["memo"],
        "timestamp": timestamp,
    }
    return transfer_data


def parse_delegate_vesting_shares_op(op, timestamp):
    """
    Parse a delegate vesting shares operation

    Args:
        op (dict): Delegate vesting shares operation data
        timestamp (str): Operation timestamp

    Returns:
        dict: Parsed delegation data
    """
    delegation_data = {
        "delegator": op[1]["delegator"],
        "delegatee": op[1]["delegatee"],
        "vesting_shares": Amount(op[1]["vesting_shares"]).amount,
        "timestamp": timestamp,
    }
    return delegation_data


def parse_comment_op(op, timestamp):
    """
    Parse a comment operation

    Args:
        op (dict): Comment operation data
        timestamp (str): Operation timestamp

    Returns:
        dict: Parsed comment data
    """
    comment_data = {
        "author": op[1]["author"],
        "permlink": op[1]["permlink"],
        "parent_author": op[1]["parent_author"],
        "parent_permlink": op[1]["parent_permlink"],
        "title": op[1]["title"],
        "body": op[1]["body"],
        "json_metadata": op[1]["json_metadata"],
        "timestamp": timestamp,
    }
    return comment_data


def parse_vote_op(op, timestamp):
    """
    Parse a vote operation

    Args:
        op (dict): Vote operation data
        timestamp (str): Operation timestamp

    Returns:
        dict: Parsed vote data
    """
    vote_data = {
        "voter": op[1]["voter"],
        "author": op[1]["author"],
        "permlink": op[1]["permlink"],
        "weight": op[1]["weight"],
        "timestamp": timestamp,
    }
    return vote_data


def parse_custom_json_op(op, timestamp):
    """
    Parse a custom json operation

    Args:
        op (dict): Custom json operation data
        timestamp (str): Operation timestamp

    Returns:
        dict: Parsed custom json data
    """
    import json

    custom_json_data = {
        "required_auths": op[1]["required_auths"],
        "required_posting_auths": op[1]["required_posting_auths"],
        "id": op[1]["id"],
        "json": json.loads(op[1]["json"]),
        "timestamp": timestamp,
    }
    return custom_json_data


def parse_hist_op(op, timestamp):
    """
    Parse a history operation

    Args:
        op (dict): History operation data
        timestamp (str): Operation timestamp

    Returns:
        dict: Parsed operation data
    """
    op_type = op[0]
    if op_type == "transfer":
        return parse_transfer_op(op, timestamp)
    elif op_type == "delegate_vesting_shares":
        return parse_delegate_vesting_shares_op(op, timestamp)
    elif op_type == "comment":
        return parse_comment_op(op, timestamp)
    elif op_type == "vote":
        return parse_vote_op(op, timestamp)
    elif op_type == "custom_json":
        return parse_custom_json_op(op, timestamp)
    else:
        return None
