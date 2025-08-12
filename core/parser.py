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