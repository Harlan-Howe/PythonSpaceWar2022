import socket
import threading
from typing import Dict

from SocketMessageIOFile import SocketMessageIO, MessageType
port = 3000

def broadcast_message_to_all(message: str, message_type=MessageType.SUBMISSION) -> None:
    """
    sends the following message to all the users for whom I have sockets.
    :param message: the message to send
    :param message_type: the type of message being sentm, defaults to a "SUBMISSION" - this precedes the message,
    itself.
    :return: None
    """
    global user_dictionary_lock, user_dictionary, broadcast_manager
    if broadcast_manager is None:
        broadcast_manager = SocketMessageIO()

    user_dictionary_lock.acquire()
    for user_id in user_dictionary:
        broadcast_manager.send_message_to_socket(message, user_dictionary[user_id]["connection"], message_type=message_type)
    user_dictionary_lock.release()


def send_user_list_to_all() -> None:
    """
    compiles a list of all the users, and the number of users. Builds this as a tab delimited string in format:
         num_users-->user0Name-->user1Name-->user2Name...
    and sends this to all current sockets.
    :return: None
    """
    global user_dictionary_lock, user_dictionary, broadcast_manager
    if broadcast_manager is None:
        broadcast_manager = SocketMessageIO()

    # develop list of online users
    user_dictionary_lock.acquire()
    list_info = f"{len(user_dictionary)}"
    for user_id in user_dictionary:
        print(f"{user_id=}\t{user_dictionary[user_id]}\t{user_dictionary[user_id]['name']=}")
        list_info += f"\t{user_dictionary[user_id]['name']}"
    user_dictionary_lock.release()
    # send that message to every user.
    broadcast_message_to_all(list_info, message_type=MessageType.USER_LIST)


def listen_to_connection(connection_to_hear: socket, connection_id: int, connection_address: str = None) -> None:
    """
    a loop intended for a Thread to monitor the given socket and handle any messages that come from it. In this case,
    it is assumed that the first message received will be the name of the connection, in the format of a packed length
    of the name and then the name itself. All messages should be in the format of packed length + message.
    :param connection_to_hear: the socket that will be read from
    :param connection_id: the unique id number of this user.
    :param connection_address: the address of the socket (not currently used)
    :return: None
    """
    name = None
    manager = SocketMessageIO()
    while True:
        try:
            message_type, message = manager.receive_message_from_socket(connection_to_hear)
        except (ConnectionAbortedError, ConnectionResetError):
            print(f"{name} just disconnected.")
            user_dictionary_lock.acquire()
            del user_dictionary[connection_id]
            user_dictionary_lock.release()
            broadcast_message_to_all(f"{'-'*6} {name} has left the conversation. {'-'*6} ")
            send_user_list_to_all()
            return

        # if we got here, that means that we've received a message.
        if name is None:  # this must be the first message, which is just the username.
            name = message
            manager.send_message_to_socket(f"Welcome, {name}!", connection_to_hear)
            user_dictionary_lock.acquire()
            user_dictionary[connection_id]["name"] = name
            user_dictionary_lock.release()
            broadcast_message_to_all(f"{'-'*6} {name} has joined the conversation. {'-'*6} ")
            send_user_list_to_all()
        else:  # it's a normal message - broadcast it to everybody.
            broadcast_message_to_all(f"{name}: {message}")


if __name__ == '__main__':
    global user_dictionary, user_dictionary_lock, latest_id, broadcast_manager
    broadcast_manager = None
    latest_id = 0

    # the user_dictionary is a dictionary of dictionaries of all the connected user's names & connections, keyed on
    # unique id numbers.
    # for example, user_dictionary might be {1: {"name":"Steve", "connection": some_socket_connection1},
    #                                        3: {"name":"Milo", "connection": some_socket_connection2},
    #                                        4: {"name":"Opus", "connection": some_socket_connection3}}
    user_dictionary: Dict[int, Dict] = {}
    user_dictionary_lock = threading.Lock()

    mySocket = socket.socket()

    mySocket.bind(('', port))
    mySocket.listen(5)
    print("Socket is listening.")
    while True:
        connection, address = mySocket.accept()  # wait to receive a new socket connection.

        print(f"Got connection from {address}")

        # start a new thread that will continuously listen for communication from this socket connection.
        latest_id += 1
        connectionThread = threading.Thread(target=listen_to_connection, args=(connection, latest_id, address))

        user_dictionary_lock.acquire()
        user_dictionary[latest_id] = {"name": "unknown", "connection": connection}
        user_dictionary_lock.release()
        connectionThread.start()
