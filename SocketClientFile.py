import socket
import threading

from ClientGUIFile import ClientGUI
from SocketMessageIOFile import SocketMessageIO, MessageType

host_URL = '127.0.0.1'
port = 3000


def listen_for_messages(connection: socket) -> None:
    """
    the loop that waits to receive information from the host socket and routes messages to the appropriate handler
    :param connection: the socket to which to listen
    :return: None
    """
    global keep_listening
    while keep_listening:
        try:
            message_type, message = manager.receive_message_from_socket(connection)
        except (ConnectionAbortedError, OSError) as Err: # if the socket is dropped, bail out.
            # print(Err)
            keep_listening = False
            break
        print(f"{message_type=}\t{message=}")
        if message_type == MessageType.SUBMISSION:
            handle_receive_submission(message)
        elif message_type == MessageType.USER_LIST:
            handle_user_list_update(message)

    print("listen_for_messages is over.")


def handle_user_list_update(tab_delimited_user_list_string:str) -> None:
    """
    The host has sent a tab-delimited string describing an updated user list; update the user_list in memory and
    onscreen.
    :param tab_delimited_user_list_string: new information about the list of users from the host socket
    :return: None
    """
    update_user_list(tab_delimited_user_list_string)
    print("------------------")
    for i in range(len(user_list)):
        print(f"{i}\t{user_list[i]}")
    print("------------------")
    client_gui.set_user_list(user_list)


def handle_receive_submission(submission:str) -> None:
    """
    The host has sent a string from one of the users (or the host, itself) that should be posted; do so!
    :param submission: the string to post
    :return: None
    """
    print(f"MSG: {submission}")
    client_gui.add_to_chat(submission)


def update_user_list(tab_delimited_user_list_string: str) -> None:
    """
    parse the tab-delimited string that contains the current list of users, replacing the information currently held
    in user_list.
    :param tab_delimited_user_list_string: a tab-delimited string that holds a number of users and then the list of usernames
    :return: None
    """
    global user_list
    print(f"{tab_delimited_user_list_string=}")

    parts = tab_delimited_user_list_string.split("\t")
    print(f"{parts=}")
    user_list.clear()
    num_users = int(parts[0])
    for i in range(1, num_users+1):
        user_list.append(parts[i])
    client_gui.set_user_list(parts[1:0])


def send_message(message: str) -> None:
    """
    forwards the given string on to the socketMessageIO manager to send to the host in the appropriate format
    :param message: the string to send
    :return: None
    """
    manager.send_message_to_socket(message, mySocket)


def close_socket()  -> None:
    """
    cease listening for the socket and shut down the socket.
    :return: None
    """
    global keep_listening
    keep_listening = False
    mySocket.close()


if __name__ == '__main__':
    global manager, user_list, client_gui, mySocket, listener_thread, keep_listening
    client_gui = ClientGUI()
    user_list = []
    mySocket = socket.socket()
    manager = SocketMessageIO()
    name = input("What is your name? ")

    mySocket.connect((host_URL, port))
    manager.send_message_to_socket(name, mySocket)
    keep_listening = True
    listener_thread = threading.Thread(target=listen_for_messages, args=(mySocket,))
    listener_thread.start()

    # telling the GUI about two methods in this class that it can call.
    client_gui.tell_my_client_to_send_message = send_message
    client_gui.shut_down_socket = close_socket

    client_gui.run_loop()
