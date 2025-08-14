def parse_create_args(parts: list[str]) -> dict:
        """Parse arguments for the 'create' command into a structured dictionary.

        Args:
            parts (list[str]): Tokenized command arguments.

        Returns:
            dict: Parsed node creation parameters.
        """
        data = {
            "type": None,
            "name": None,
            "short_desc": "",
            "full_desc": "",
            "deadline": "",
            "parent_id": None
        }

        if len(parts) < 3:
            raise ValueError("Usage: create <type> <name> [--desc ...] [--full ...] [--deadline ...] [--parent <id>]")

        data["type"] = parts[1]
        data["name"] = parts[2]

        i = 3
        while i < len(parts):
            if parts[i] == "--desc":
                i += 1
                data["short_desc"] = parts[i]
            elif parts[i] == "--full":
                i += 1
                data["full_desc"] = parts[i]
            elif parts[i] == "--deadline":
                i += 1
                data["deadline"] = parts[i]
            elif parts[i] == "--parent":
                i += 1
                data["parent_id"] = parts[i]
            else:
                raise ValueError(f"Unknown argument: {parts[i]}")
            i += 1

        return data



def parse_edit_args(parts: list[str]) -> dict:
    """Parse arguments for the 'edit' command into a structured dictionary.

        Args:
            parts (list[str]): Tokenized command arguments.

        Returns:
            dict: Parsed node editing parameters.
        """
    data = {
        "id": None,
        "name": None,
        "short_desc": None,
        "full_desc": None,
        "deadline": None
    }

    if len(parts) < 2:
        raise ValueError("Usage: edit <id> [--name ...] [--desc ...] [--full ...] [--deadline ...]")

    data["id"] = parts[1]

    i = 2
    while i < len(parts):
        if parts[i] == "--name":
            i += 1
            data["name"] = parts[i]
        elif parts[i] == "--desc":
            i += 1
            data["short_desc"] = parts[i]
        elif parts[i] == "--full":
            i += 1
            data["full_desc"] = parts[i]
        elif parts[i] == "--deadline":
            i += 1
            data["deadline"] = parts[i]
        else:
            raise ValueError(f"Unknown argument: {parts[i]}")
        i += 1

    return data



def parse_search_args(parts: list[str]) -> dict:
    """Parse arguments for the 'search' command into a structured dictionary.

        Args:
            parts (list[str]): Tokenized command arguments.

        Returns:
            dict: Parsed node searching parameters.
        """
    if len(parts) < 2:
        raise ValueError("Usage: search <substring> | search name <substring> | search id <prefix-or-exact>")

    data = {"mode": "name", "query": None}

    if parts[1] in ("name", "id"):
        if len(parts) < 3:
            raise ValueError("Usage: search name <substring> | search id <prefix-or-exact>")
        data["mode"] = parts[1]
        data["query"] = parts[2]
    else:
        # shorthand: search <substring>  -> name search
        data["mode"] = "name"
        data["query"] = parts[1]

    return data
