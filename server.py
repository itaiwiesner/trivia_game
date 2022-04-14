import socket
import select
import chatlib
import random
import requests


# GLOBALS
users = {}
questions = {}
logged_users = {}  # a dictionary of client hostnames to usernames
messages_to_send = {}

ERROR_MSG = "Error! "
SERVER_PORT = 5678
SERVER_IP = "127.0.0.1"
MAX_MSG_LENGTH = chatlib.MAX_MSG_LENGTH
API_URL = 'https://opentdb.com/api.php?amount=50&type=multiple'


def load_questions():
    """
    Loads questions bank from api
    Receives: -
    Returns: questions dictionary
    """
    global questions
    response = requests.get(API_URL)
    data = response.json()['results']
    for index, question in enumerate(data):
        correct = question['correct_answer']
        options = [correct] + question['incorrect_answers']
        random.shuffle(options)
        questions[index+1] = {'question': question['question'], 'answers': options, 'correct': options.index(correct)}

    return questions


def load_user_database():
    """
    Loads users list from file
    Receives: nothing
    Returns: user dictionary
    """
    global users
    users = {}
    with open('users.txt') as f:
        lines = f.readlines()
        for line in lines:
            line = ''.join(line).split('|')
            username, password, score, questions_asked = line[0], line[1], line[2], line[3].split(',')
            users[username] = {'password': password, 'score': score, 'questions_asked': [i for i in questions_asked]}
            if '\n' in users[username]['questions_asked']:
                users[username]['questions_asked'].remove('\n')

    return users


def build_and_send_message(sock, cmd, msg=''):
    """
    Builds a new message using chatlib, wanted code and message.
    Prints debug info, then sends it to the given socket.
    Parameters: sock (socket object), cmd (str), msg (str)
    Returns: Nothing
    """
    global messages_to_send
    message = chatlib.build_message(cmd, msg)
    print(f'[SERVER]  ({SERVER_IP}, {SERVER_PORT}) msg: {message}')
    messages_to_send[sock] = message


def recv_message_and_parse(sock):
    """
    Receives a new message from given socket.
    Prints debug info, then parses the message using chatlib.
    Parameters: sock (socket object)
    Returns: cmd (str) and data (str) of the received message.
    If error occurred, will return None, None
    """
    data = sock.recv(MAX_MSG_LENGTH).decode()
    print(f'[CLIENT]  {sock.getpeername()} msg: {data}')
    cmd, msg = chatlib.parse_message(data)
    return cmd, msg


def print_client_sockets(sock_lst):
    for sock in sock_lst:
        print(sock.getpeername())


def setup_socket():
    """
    Creates new listening socket and returns it
    Receives: -
    Returns: the socket object
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen()
    return server_socket


def send_error(sock, error_msg):
    """
    Send error message with given message
    Receives: socket, message error string from called function
    Returns: None
    """
    build_and_send_message(sock, 'ERROR', error_msg)


def create_random_question(username):
    """
    Returns a random question which the user hasn't been asked yet.
    If there are no more valid questions, '' is returned
    """
    global users, questions
    valid_questions = [q_id for q_id in questions if q_id not in users[username]['questions_asked']]

    if not valid_questions:
        return ''

    index = random.randint(0, len(valid_questions) - 1)
    index = valid_questions[index]
    fields = [str(index), questions[index]['question']]
    for option in questions[index]['answers']:
        fields.append(option)

    return chatlib.join_msg(fields, '#')


def handle_question_message(sock, username):
    """
    If there are any questions left, sends a random one to the client
    Receives: client's socket and username
    Returns: None
    """
    msg_field = create_random_question(username)
    if msg_field == '':
        cmd = 'NO_QUESTIONS'
    else:
        cmd = 'YOUR_QUESTION'
    build_and_send_message(sock, cmd, msg_field)


def handle_answer_message(sock, username, answer):
    global questions, users
    answer = answer.split('#')
    q_id, choice = int(answer[0]), int(answer[-1])

    if questions[q_id]['correct'] == choice:
        cmd = 'CORRECT_ANSWER'
        msg = ''
        users[username]['score'] = str(int(users[username]['score']) + 5)
    else:
        cmd = 'WRONG_ANSWER'
        msg = str(questions[q_id]['correct'])

    users[username]['questions_asked'].append(q_id)
    build_and_send_message(sock, cmd, msg)


def handle_get_score_message(sock, username):
    global users
    build_and_send_message(sock, 'YOUR_SCORE', users[username]['score'])


def handle_highscore_message(sock):
    """
    Creates a HIGHCORE message according to the protocol.
    a list of all users sorted by their score
    """
    global users
    scores = [f'{key}: {val["score"]}' for key, val in users.items()]
    scores.sort(key=lambda x: int(x.split(':')[-1]), reverse=True)
    scores = '\n'.join(scores)
    build_and_send_message(sock, 'ALL_SCORE', scores)


def handle_logged_message(sock):
    global logged_users
    users_list = [user for user in logged_users.values()]
    build_and_send_message(sock, 'LOGGED_ANSWER', ', '.join(users_list))


def handle_logout_message(sock):
    """
    Closes the given socket (in later chapters, also remove user from logged_users dictionary)
    Receives: socket
    Returns: None
    """
    global logged_users
    logged_users.pop(sock.getpeername())
    sock.close()


def handle_login_message(sock, data):
    """
    Gets socket and message data of login message. Checks user and pass exists and match.
    If not - sends error and finished. If all ok, sends OK message and adds user and address to logged_users
    Receives: socket, message code and data
    Returns: None (sends answer to client)
    """
    global users, logged_users
    username, password = data.split('#')[0], data.split('#')[-1]
    if username not in users:
        send_error(sock, "Error! username doesn't exist")

    elif password != users[username]['password']:
        send_error(sock, "Error! password doesn't match")

    elif username in logged_users.values():
        send_error(sock, 'Error! user is already connected')

    else:
        logged_users[sock.getpeername()] = username
        build_and_send_message(sock, 'LOGIN_OK')


def handle_client_message(current_socket, cmd, msg, client_sockets):
    """
    Gets message code and data and calls the right function to handle command
    Receives: socket, message code and data
    Returns: None
    """
    global logged_users

    # legal commands for a logged-in user
    if current_socket.getpeername() in logged_users:
        if cmd == 'LOGOUT' or cmd == '':
            client_sockets.remove(current_socket)
            handle_logout_message(current_socket)
        elif cmd == 'MY_SCORE':
            handle_get_score_message(current_socket, logged_users[current_socket.getpeername()])
        elif cmd == 'HIGHSCORE':
            handle_highscore_message(current_socket)
        elif cmd == 'LOGGED':
            handle_logged_message(current_socket)
        elif cmd == 'GET_QUESTION':
            handle_question_message(current_socket, logged_users[current_socket.getpeername()])
        elif cmd == 'SEND_ANSWER':
            handle_answer_message(current_socket, logged_users[current_socket.getpeername()], msg)

    # legal command for a logged-out user
    elif cmd == 'LOGIN':
        handle_login_message(current_socket, msg)

    else:
        send_error(current_socket, 'Invalid command')


def main():
    # Initializes global users and questions dictionaries using load functions, will be used later
    global users, questions, logged_users, messages_to_send
    users = load_user_database()
    questions = load_questions()

    print("Setting up server...")
    server_socket = setup_socket()
    print("Listening for clients...")
    client_sockets = []
    while True:
        # using select to create 2 lists. ready_to_read - a list of sockets which sent something
        # ready_to_write - a list of client sockets ready to receive data from the server
        ready_to_read, ready_to_write, in_error = select.select([server_socket] + client_sockets, client_sockets, [])
        for current_socket in ready_to_read:
            # handle a new client connecting
            if current_socket is server_socket:
                (client_socket, client_address) = current_socket.accept()
                print(f"New client joined! {client_address}")
                client_sockets.append(client_socket)
                print_client_sockets(client_sockets)
            else:
                # handle an existing user sensing something. taking user who crashed under consideration
                try:
                    cmd, msg = recv_message_and_parse(current_socket)
                except Exception:
                    client_sockets.remove(current_socket)
                    handle_logout_message(current_socket)

                else:
                    handle_client_message(current_socket, cmd, msg, client_sockets)

        # looping over the client sockets which are ready to receive data,
        # using global variable - messages_to_send
        for current_socket in ready_to_write:
            if current_socket in messages_to_send:
                current_socket.send(messages_to_send[current_socket].encode())
                messages_to_send.pop(current_socket)


if __name__ == '__main__':
    main()
