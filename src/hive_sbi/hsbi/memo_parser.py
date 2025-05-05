import json
import re


def parse_memo(memo):
    """
    Parse a memo to extract commands and parameters

    Args:
        memo (str): Memo text

    Returns:
        dict: Parsed memo data
    """
    memo = memo.strip()
    memo_data = {"command": None, "params": {}}

    # Check for JSON format
    if memo.startswith("{") and memo.endswith("}"):
        try:
            json_data = json.loads(memo)
            if "command" in json_data:
                memo_data["command"] = json_data["command"]
                memo_data["params"] = {k: v for k, v in json_data.items() if k != "command"}
            return memo_data
        except json.JSONDecodeError:
            pass

    # Check for command format
    command_match = re.match(r"^([a-zA-Z0-9_]+)\s*(.*)$", memo)
    if command_match:
        command = command_match.group(1).lower()
        params_str = command_match.group(2).strip()
        memo_data["command"] = command

        # Parse parameters
        if params_str:
            # Key-value pairs
            kv_pairs = re.findall(r"([a-zA-Z0-9_]+)\s*=\s*([^\s]+)", params_str)
            for key, value in kv_pairs:
                memo_data["params"][key.lower()] = value

            # Positional parameters
            if not kv_pairs:
                memo_data["params"]["value"] = params_str

    return memo_data


def parse_transfer_memo(memo):
    """
    Parse a transfer memo to extract commands and parameters

    Args:
        memo (str): Transfer memo text

    Returns:
        dict: Parsed transfer memo data
    """
    memo_data = parse_memo(memo)

    # Handle specific transfer commands
    if memo_data["command"] == "sponsor":
        # Sponsor command
        if "value" in memo_data["params"]:
            memo_data["params"]["account"] = memo_data["params"].pop("value")
    elif memo_data["command"] == "delegate":
        # Delegate command
        if "value" in memo_data["params"]:
            memo_data["params"]["account"] = memo_data["params"].pop("value")
    elif memo_data["command"] == "undelegate":
        # Undelegate command
        if "value" in memo_data["params"]:
            memo_data["params"]["account"] = memo_data["params"].pop("value")
    elif memo_data["command"] == "staking":
        # Staking command
        if "value" in memo_data["params"]:
            memo_data["params"]["amount"] = memo_data["params"].pop("value")
    elif memo_data["command"] == "upvote":
        # Upvote command
        if "value" in memo_data["params"]:
            # Parse @author/permlink format
            value = memo_data["params"].pop("value")
            author_permlink_match = re.match(r"^@([a-zA-Z0-9\.-]+)/([a-zA-Z0-9\-]+)$", value)
            if author_permlink_match:
                memo_data["params"]["author"] = author_permlink_match.group(1)
                memo_data["params"]["permlink"] = author_permlink_match.group(2)

    return memo_data


def parse_command_json(json_str):
    """
    Parse a command JSON string

    Args:
        json_str (str): Command JSON string

    Returns:
        dict: Parsed command data
    """
    try:
        data = json.loads(json_str)
        return data
    except json.JSONDecodeError:
        return None
