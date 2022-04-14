import chatlib
import socket


SERVER_IP = "127.0.0.1"
SERVER_PORT = 5678
PROTOCOL_CLIENT = {
    "login_msg": "LOGIN", "logout_msg": "LOGOUT", "logged_msg": "LOGGED", "get_question_msg": "GET_QUESTION",
    "send_answer_msg": "SEND_ANSWER", "my_score_msg": "MY_SCORE", "highscore_msg": "HIGHSCORE"
}

PROTOCOL_SERVER = {
    "login_ok_msg": "LOGIN_OK", "logged_answer_msg": "LOGGED_ANSWER", "your_question_nsg": "YOUR_QUESTION",
    "correct_answer_msg": "CORRECT_ANSWER", "wrong_answer_msg": "WRONG_ANSWER", "your_score_msg": "YOUR_SCORE",
    "login_failed_msg": "ERROR"
}
MAX_MSG_LENGTH = chatlib.MAX_MSG_LENGTH


def build_and_send_message(sock, cmd, msg=''):
    """
    Builds a new message using chatlib, wanted code and message.
    Prints debug info, then sends it to the given socket.
    Parameters: sock (socket object), cmd (str), msg (str)
    Returns: Nothing
    """
    message = chatlib.build_message(cmd, msg)
    sock.send(message.encode())


def recv_message_and_parse(sock):
    """
    Receives a new message from given socket.
    Prints debug info, then parses the message using chatlib.
    Paramaters: sock (socket object)
    Returns: cmd (str) and data (str) of the received message.
    If error occured, will return None, None
    """
    data = sock.recv(MAX_MSG_LENGTH).decode()
    cmd, msg = chatlib.parse_message(data)
    return cmd, msg


def build_send_recv_parse(sock, cmd, msg=''):
    """
    Builds a new message using chatlib, wanted code and message.
    Prints debug info, then sends it to the given socket.
    Parameters: sock (socket object), cmd (str), msg (str)
    Returns: Nothing
    """
    build_and_send_message(sock, cmd, msg)
    return recv_message_and_parse(sock)


def create_socket():
    sock = socket.socket()
    sock.connect((SERVER_IP, SERVER_PORT))
    return sock


def login(sock):
    while True:
        username = input('Please enter username: \n')
        password = input('Please enter password: \n')
        cmd, msg = build_send_recv_parse(sock, "LOGIN", f"{username}#{password}")
        print(msg)
        if cmd == 'LOGIN_OK':
            break


def logout(sock):
    _ = build_send_recv_parse(sock, 'LOGOUT')


def get_logged_users(sock):
    return build_send_recv_parse(sock, 'LOGGED')[-1]


def get_score(sock):
    return build_send_recv_parse(sock, 'MY_SCORE')[-1]


def get_highscore(sock):
    return build_send_recv_parse(sock, 'HIGHSCORE')[-1]


def play_question(sock):
    cmd, msg = build_send_recv_parse(sock, 'GET_QUESTION')
    if cmd == 'NO_QUESTIONS':
        return cmd

    msg = msg.split('#')
    q_id, q, options = msg[0], msg[1], msg[2:]
    choice = input(f'''Q: {q}
1.{options[0]}
2.{options[1]}
3.{options[2]}        
4.{options[3]}
Please choose an answer [1-4]: ''')

    while choice not in ['1', '2', '3', '4']:
        choice = input('Invalid input. Please choose an answer [1-4]: ')

    cmd, answer = build_send_recv_parse(sock, 'SEND_ANSWER', f'{q_id}#{choice}')
    if cmd == 'WRONG_ANSWER':
        print(f'Nope, correct answer is #{answer}')
    elif cmd == 'CORRECT_ANSWER':
        print('YES!!!')

    return cmd


def main():
    sock = create_socket()
    print(f'connecting to {SERVER_IP} port {SERVER_PORT}')
    login(sock)
    print('Logged in!')
    while True:
        choice = input('''p        Play a trivia question
s        Get my score
h        Get high score
l        Get logged users
q        Quit
Please enter your choice: ''')

        while choice not in ['p', 's', 'h', 'l', 'q']:
            choice = input('Invalid input.\n Try again please: ')

        if choice == 'q':
            break

        if choice == 'l':
            _, logged_users = build_send_recv_parse(sock, 'LOGGED')
            print(logged_users)

        if choice == 's':
            score = get_score(sock)
            print(f'Your score is {score}')

        if choice == 'h':
            score_tbl = get_highscore(sock)
            print(score_tbl)

        if choice == 'p':
            cmd = play_question(sock)
            if cmd == 'NO_QUESTIONS':
                print('No more questions')
                break

    print('Game over')
    logout(sock)
    sock.close()


if __name__ == '__main__':
    main()
