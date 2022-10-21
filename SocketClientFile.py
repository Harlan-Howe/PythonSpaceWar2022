import random
import socket
import threading

from ClientGUIFile import ClientGUI
from RepeatTimerFile import RepeatTimer
from SocketMessageIOFile import SocketMessageIO, MessageType

host_URL = '127.0.0.1'
port = 3000
color_dictionary = {}

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
        # print(f"{message_type=}\t{message=}")
        if message_type == MessageType.SUBMISSION:
            handle_receive_submission(message)
        elif message_type == MessageType.USER_LIST:
            handle_user_list_update(message)
        elif message_type == MessageType.WORLD_UPDATE:
            handle_world_update(message)
        elif message_type == MessageType.DELETE_ITEMS:
            handle_delete_items(message)

    print("listen_for_messages is over.")

def handle_delete_items(tab_delimited_world_list_string: str) -> None:
    lines = tab_delimited_world_list_string.split("\n")
    for line in lines:
        if line == "":
            continue
        values = line.split("\t")
        print(f"deleting {values=}")
        user_id = int(values[1])
        for item in world_contents:

            try:
                print(f"Attempting match: {item['id']=} and {user_id=}; {item=}")
                if item["id"] == user_id:
                    print("matched.")
                    world_contents.remove(item)
                    client_gui.delete_item_from_world(item_type=values[0], object_id=user_id)
                    break
            except KeyError:
                print(f"Exception: {item=}")







def handle_world_update(tab_delimited_world_list_string: str) -> None:
    global world_contents
    world_contents = []
    lines = tab_delimited_world_list_string.split("\n")
    for line in lines:
        values = line.split("\t")
        game_object = {}
        game_object["type"] = values[0]
        if values[0] == "":
            continue
        if values[0] == "PLAYER":
            game_object["id"] = int(values[1])
            game_object["x"] = float(values[2])
            game_object["y"] = float(values[3])
            game_object["bearing"] = float(values[4])
            game_object["thrusting"] = (int(values[5]) == 1)
            game_object["health"] = int(values[6])
            game_object["name"] = values[7]
            if game_object["id"] not in color_dictionary:
                color_dictionary[game_object["id"]] = "#" + \
                    f"{random.randrange(64, 255):02X}{random.randrange(64, 255):02X}{random.randrange(64, 255):02X}"
            game_object["color"] = color_dictionary[game_object["id"]]
        if values[0] == "BULLET":
            # print(f"Bullet handled. {values=} ")
            game_object["id"] = int(values[1])
            game_object["x"] = float(values[2])
            game_object["y"] = float(values[3])
            game_object["owner_id"] = int(values[4])

        world_contents.append(game_object)
    client_gui.update_world(world_contents)

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

def update_keyboard() -> None:
    keyboard_code = client_gui.key_status
    # print(f"{bin(keyboard_code)}")
    manager.send_message_to_socket(keyboard_code, mySocket, message_type=MessageType.KEY_STATUS)


if __name__ == '__main__':
    global manager, user_list, client_gui, mySocket, listener_thread, keep_listening
    global world_contents
    world_contents = []
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

    keyboard_timer = RepeatTimer(0.1, update_keyboard)
    keyboard_timer.start()

    client_gui.run_loop()
    keyboard_timer.cancel()
    print("Done.")