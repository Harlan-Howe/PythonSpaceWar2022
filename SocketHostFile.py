import math
import socket
import threading
from typing import Dict
from PlayerShipFile import PlayerShip
from BulletFile import Bullet
from RepeatTimerFile import RepeatTimer
import time

from SocketMessageIOFile import SocketMessageIO, MessageType
port = 3001

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
            if "PlayerShip" in user_dictionary[connection_id]:
                item_to_delete = user_dictionary[connection_id]['PlayerShip'].public_info()
                del user_dictionary[connection_id]
            user_dictionary_lock.release()
            broadcast_message_to_all(f"{'-'*6} {name} has left the conversation. {'-'*6} ")
            broadcast_message_to_all(item_to_delete, MessageType.DELETE_ITEMS)
            send_user_list_to_all()
            return

        # if we got here, that means that we've received a message.
        if message_type == MessageType.SUBMISSION:
            if name is None:  # this must be the first message, which is just the username.
                name = message
                manager.send_message_to_socket(f"Welcome, {name}!", connection_to_hear)
                user_dictionary_lock.acquire()
                user_dictionary[connection_id]["name"] = name
                user_dictionary[connection_id]["PlayerShip"] = PlayerShip(connection_id, name)
                user_dictionary_lock.release()
                broadcast_message_to_all(f"{'-'*6} {name} has joined the conversation. {'-'*6} ")
                send_user_list_to_all()
            else:  # it's a normal message - broadcast it to everybody.
                broadcast_message_to_all(f"{name}: {message}")
        elif message_type == MessageType.KEY_STATUS:
            update_ship_controls(connection_id, int(message))

def update_ship_controls(id: int, new_controls: int) -> None:
    user_dictionary_lock.acquire()
    user_dictionary[id]["PlayerShip"].controls = new_controls
    # print(user_dictionary)
    user_dictionary_lock.release()

def game_loop_step() -> None:
    global last_update, items_to_delete
    items_to_delete = []
    now = time.time()
    delta_t = now-last_update

    # do updates etc. for each type of object
    manage_step_for_users(delta_t)
    manage_step_for_bullets(delta_t)
    check_for_bullet_player_collisions()


    last_update = now

    # send revised contents of the world to all users.
    send_world_update_to_all_users()
    # send notification of any items that were deleted.
    send_items_to_delete_to_all_users()


def check_for_bullet_player_collisions() -> None:
    user_dictionary_lock.acquire()
    for user_id in user_dictionary:
        for b in bullet_list:
            if "PlayerShip" in user_dictionary[user_id]:
                if user_dictionary[user_id]["PlayerShip"].my_id != b.owner_id:
                    if math.fabs(user_dictionary[user_id]["PlayerShip"].x - b.x) < 8 and math.fabs(user_dictionary[user_id]["PlayerShip"].y - b.y) < 8:
                        user_dictionary[user_id]["PlayerShip"].health -= 10
                        b.lifetime = -1

    user_dictionary_lock.release()

def send_items_to_delete_to_all_users():
    deletable_items_descriptions = ""
    for item in items_to_delete:
        deletable_items_descriptions += item + "\n"
    if (len(items_to_delete) > 0):
        broadcast_message_to_all(deletable_items_descriptions, MessageType.DELETE_ITEMS)


def manage_step_for_bullets(delta_t):
    bullets_to_remove = []
    for b in bullet_list:
        b.update(delta_t)
        if b.has_expired():
            bullets_to_remove.append(b)
    for b in bullets_to_remove:
        bullet_list.remove(b)
        non_user_objects.remove(b)
        items_to_delete.append(b.public_info())


def manage_step_for_users(delta_t):
    user_dictionary_lock.acquire()
    for user_id in user_dictionary:
        if "PlayerShip" in user_dictionary[user_id]:
            user_dictionary[user_id]["PlayerShip"].update(delta_t)
            if user_dictionary[user_id]["PlayerShip"].controls & 16 == 16:
                handle_fire(user_dictionary[user_id]["PlayerShip"])


    user_dictionary_lock.release()


def handle_fire(user:PlayerShip) -> None:
    global latest_id
    if user.ok_to_fire():
        muzzle_velocity = 85
        latest_id += 1
        bullet = Bullet(x=user.x,
                        y=user.y,
                        vx=user.vx+muzzle_velocity*math.cos(user.bearing),
                        vy=user.vy+muzzle_velocity*math.sin(user.bearing),
                        owner_id=user.my_id,
                        bullet_id=latest_id,
                        lifetime=3.25
                        )
        bullet_list.append(bullet)
        non_user_objects.append(bullet)



def send_world_update_to_all_users() -> None:
    message = ""
    user_dictionary_lock.acquire()
    for user_id in user_dictionary:
        if "PlayerShip" in user_dictionary[user_id]:
            message += f"{user_dictionary[user_id]['PlayerShip'].public_info()}\n"
    user_dictionary_lock.release()
    for obj in non_user_objects:
        message += f"{obj.public_info()}\n"
        # print(f"Sending: {obj.public_info=}")
    broadcast_message_to_all(message, MessageType.WORLD_UPDATE)

if __name__ == '__main__':
    global user_dictionary, user_dictionary_lock, latest_id, broadcast_manager, last_update
    global bullet_list, non_user_objects
    bullet_list= []
    non_user_objects = []

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

    last_update = time.time()
    game_loop_timer = RepeatTimer(0.01, game_loop_step)
    game_loop_timer.start()

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
