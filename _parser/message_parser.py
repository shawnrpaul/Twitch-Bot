def parse_message(message):
    parsed_message = {
        "tags": None,
        "source": None,
        "command": None,
        "parameters": None,
    }

    idx = 0

    raw_tags_component = None
    raw_source_component = None
    raw_command_component = None
    raw_parameters_component = None

    if message[idx] == "@":
        end_idx = message.find(" ")
        raw_tags_component = message[1:end_idx]
        idx = end_idx + 1

    if message[idx] == ":":
        idx += 1
        end_idx = message.find(" ", idx)
        raw_source_component = message[idx:end_idx]
        idx = end_idx + 1

    end_idx = message.find(":", idx)

    if end_idx == -1:
        end_idx = len(message)

    raw_command_component = message[idx:end_idx].strip()

    if end_idx != len(message):
        idx = end_idx + 1
        raw_parameters_component = message[idx:]

    parsed_message["command"] = parse_command(raw_command_component)

    if raw_tags_component is not None:
        parsed_message["tags"] = parse_tags(raw_tags_component)

    parsed_message["source"] = parse_source(raw_source_component)

    parsed_message["parameters"] = raw_parameters_component
    if raw_parameters_component and raw_parameters_component[0] == "*":
        parsed_message["command"] = parse_parameters(
            raw_parameters_component, parsed_message["command"]
        )
    return parsed_message


# Define the parse_command, parse_tags, parse_source, and parse_parameters functions as needed.
def parse_tags(tags):
    tags_to_ignore = {"client-nonce": None, "flags": None}

    dict_parsed_tags = {}
    parsed_tags = tags.split(";")

    for tag in parsed_tags:
        parsed_tag = tag.split("=")
        tag_value = None if parsed_tag[1] == "" else parsed_tag[1]

        if parsed_tag[0] in ["badges", "badge-info"]:
            if tag_value:
                badge_dict = {}
                badges = tag_value.split(",")
                for pair in badges:
                    badge_parts = pair.split("/")
                    badge_dict[badge_parts[0]] = badge_parts[1]
                dict_parsed_tags[parsed_tag[0]] = badge_dict
            else:
                dict_parsed_tags[parsed_tag[0]] = None
        elif parsed_tag[0] == "emotes":
            if tag_value:
                emotes_dict = {}
                emotes = tag_value.split("/")
                for emote in emotes:
                    emote_parts = emote.split(":")

                    text_positions = []
                    positions = emote_parts[1].split(",")
                    for position in positions:
                        position_parts = position.split("-")
                        text_positions.append(
                            {
                                "startPosition": position_parts[0],
                                "endPosition": position_parts[1],
                            }
                        )

                    emotes_dict[emote_parts[0]] = text_positions
                dict_parsed_tags[parsed_tag[0]] = emotes_dict
            else:
                dict_parsed_tags[parsed_tag[0]] = None
        elif parsed_tag[0] == "emote-sets":
            emote_set_ids = tag_value.split(",")
            dict_parsed_tags[parsed_tag[0]] = emote_set_ids
        elif parsed_tag[0] not in tags_to_ignore:
            dict_parsed_tags[parsed_tag[0]] = tag_value

    return dict_parsed_tags


def parse_source(raw_source_component):
    if raw_source_component is None:  # Not all messages contain a source
        return None
    else:
        source_parts = raw_source_component.split("!")
        return {
            "nick": source_parts[0] if len(source_parts) == 2 else None,
            "host": source_parts[1] if len(source_parts) == 2 else source_parts[0],
        }


def parse_command(raw_command_component):
    parsed_command = None
    command_parts = raw_command_component.split(" ")

    switch_command = command_parts[0]

    if switch_command in [
        "JOIN",
        "PART",
        "NOTICE",
        "CLEARCHAT",
        "HOSTTARGET",
        "PRIVMSG",
        "CLEARMSG",
    ]:
        parsed_command = {"command": switch_command, "channel": command_parts[1]}
    elif switch_command == "PING":
        parsed_command = {"command": switch_command}
    elif switch_command == "CAP":
        parsed_command = {
            "command": switch_command,
            "isCapRequestEnabled": True if command_parts[2] == "ACK" else False
            # The parameters part of the messages contains the enabled capabilities.
        }
    elif switch_command in ["GLOBALUSERSTATE", "USERSTATE", "ROOMSTATE"]:
        parsed_command = {"command": switch_command, "channel": command_parts[1]}
    elif switch_command == "RECONNECT":
        print(
            "The Twitch IRC server is about to terminate the connection for maintenance."
        )
        parsed_command = {"command": switch_command}
    elif switch_command == "421":
        return None
    elif switch_command == "001":
        parsed_command = {"command": switch_command, "channel": command_parts[1]}
    elif switch_command in ["002", "003", "004", "353", "366", "372", "375", "376"]:
        return None
    else:
        return None

    return parsed_command


def parse_parameters(raw_parameters_component, command):
    idx = 0
    command_parts = raw_parameters_component[idx + 1 :].strip()
    params_idx = command_parts.find(" ")

    if params_idx == -1:  # no parameters
        command["botCommand"] = command_parts[:]
    else:
        command["botCommand"] = command_parts[:params_idx]
        command["botCommandParams"] = command_parts[params_idx:].strip()
        # TODO: remove extra spaces in parameters string

    return command
