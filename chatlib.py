# Protocol Constants

CMD_FIELD_LENGTH = 16  # Exact length of cmd field (in bytes)
LENGTH_FIELD_LENGTH = 4  # Exact length of length field (in bytes)
MAX_DATA_LENGTH = 10 ** LENGTH_FIELD_LENGTH - 1  # Max size of data field according to protocol
MSG_HEADER_LENGTH = CMD_FIELD_LENGTH + 1 + LENGTH_FIELD_LENGTH + 1  # Exact size of header (CMD+LENGTH fields)
MAX_MSG_LENGTH = MSG_HEADER_LENGTH + MAX_DATA_LENGTH  # Max size of total message
DELIMITER = "|"  # Delimiter character in protocol

# Protocol Messages
# In this dictionary we will have all the client and server command names

PROTOCOL_CLIENT = {
    "login_msg": "LOGIN", "logout_msg": "LOGOUT", "logged_msg": "LOGGED", "get_question_msg": "GET_QUESTION",
    "send_answer_msg": "SEND_ANSWER", "my_score_msg": "MY_SCORE", "highscore_msg": "HIGHSCORE"
}

PROTOCOL_SERVER = {
    "login_ok_msg": "LOGIN_OK", "logged_answer_msg": "LOGGED_ANSWER", "your_question_nsg": "YOUR_QUESTION",
    "correct_answer_msg": "CORRECT_ANSWER", "wrong_answer_msg": "WRONG_ANSWER", "your_score_msg": "YOUR_SCORE",
    "login_failed_msg": "ERROR"
}
COMMANDS = ["LOGIN", "LOGOUT", "LOGGED", "GET_QUESTION", "SEND_ANSWER", "MY_SCORE", "HIGHSCORE", "LOGIN_OK", "ALL_SCORE",
            "LOGGED_ANSWER", "YOUR_QUESTION", "CORRECT_ANSWER", "WRONG_ANSWER", "YOUR_SCORE", "ERROR", "NO_QUESTIONS"]
ERROR_RETURN = None  # What is returned in case of an error


def build_message(cmd, data=''):
    """
    Gets command name and data field and creates a valid protocol message
    Returns: str, or None if error occured
    """
    # check if the command is valid and if data is valid
    if cmd not in COMMANDS or len(data) > MAX_DATA_LENGTH:
        return ERROR_RETURN

    # pad with space bar when necessary
    return f'{cmd.ljust(CMD_FIELD_LENGTH)}|{str(len(data)).ljust(LENGTH_FIELD_LENGTH)}|{data}'


def parse_message(data):
    """
    Parses protocol message and returns command name and data field
    Returns: cmd (str), data (str). If some error occured, returns None, None
    """
    if data.count('|') < 2:
        return ERROR_RETURN, ERROR_RETURN

    output = [data.split('|')[0], data.split('|')[1], '|'.join(data.split('|')[2:])]
    # check lengths of fields
    if len(output[0]) != CMD_FIELD_LENGTH or len(output[1]) != LENGTH_FIELD_LENGTH:
        return ERROR_RETURN, ERROR_RETURN

    # check if length_field is a number
    try:
        int(output[1])

    except Exception:
        return ERROR_RETURN, ERROR_RETURN

    # check if msg_field's length is legal and equal to length_field
    if len(output[2]) != int(output[1]) or len(output[2]) > MAX_MSG_LENGTH:
        return ERROR_RETURN, ERROR_RETURN

    # check if command is legal
    if output[0].strip() not in COMMANDS:
        return ERROR_RETURN, ERROR_RETURN

    return output[0].strip(), output[2]


def split_msg(msg, delimiter):
    """
    Helper method. gets a string and a delimiter. Splits the string using the given delimiter.
    Returns: list of fields
    """
    return msg.split(delimiter)


def join_msg(msg_fields, delimiter):
    """
    Helper method. Gets a list, joins all of it's fields to one string divided by the delimiter.
    Returns: string that looks like cell1|cell2|cell3
    """
    return delimiter.join(msg_fields)
