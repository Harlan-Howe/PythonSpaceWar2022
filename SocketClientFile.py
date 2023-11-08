import random
import socket
import threading
import time
from typing import Optional

from ClientGUIFile import ClientGUI
from RepeatTimerFile import RepeatTimer
from SocketMessageIOFile import SocketMessageIO, MessageType

host_URL = '127.0.0.1'
port = 3001
color_dictionary = {}


class SocketClient:

    def __init__(self):
        self.world_contents = []
        self.world_contents_lock = threading.Lock()
        self.client_gui = ClientGUI()
        self.user_list = []
        self.my_socket = socket.socket()
        self.manager = SocketMessageIO()
        # name = input("What is your name? ")
        self.name = self.client_gui.request_name()

        self.my_socket.connect((host_URL, port))
        self.manager.send_message_to_socket(self.name, self.my_socket)
        self.keep_listening = True
        listener_thread = threading.Thread(target=self.listen_for_messages, args=(self.my_socket,))
        listener_thread.start()

        # telling the GUI about two methods in this class that it can call.
        self.client_gui.tell_my_client_to_send_message = self.send_message
        self.client_gui.shut_down_socket = self.close_socket

        keyboard_timer = RepeatTimer(0.05, self.update_keyboard)
        keyboard_timer.start()

        self.world_update_count = 0
        self.last_world_update_time = time.time()

        GUI_update_thread = threading.Thread(target=self.do_world_update)
        GUI_update_thread.start()

        # animation_timer = RepeatTimer(0.1, self.refresh_canvas)
        # animation_timer.start()

        self.latest_update_info_string = None
        self.latest_update_info_string_lock = threading.Lock()

        self.client_gui.run_loop()
        keyboard_timer.cancel()
        self.keep_listening = False
        print("Done.")

    def listen_for_messages(self, connection: socket) -> None:
        """
        the loop that waits to receive information from the host socket and routes messages to the appropriate handler
        :param connection: the socket to which to listen
        :return: None
        """

        while self.keep_listening:
            try:
                message_type, message = self.manager.receive_message_from_socket(connection)
            except (ConnectionAbortedError, OSError) as Err:  # if the socket is dropped, bail out.
                print(Err)
                self.keep_listening = False
                break
            # print(f"{message_type=}\t{message=}")
            if message_type == MessageType.SUBMISSION:
                self.handle_receive_submission(message)
            elif message_type == MessageType.USER_LIST:
                self.handle_user_list_update(message)
            elif message_type == MessageType.WORLD_UPDATE:
                self.handle_world_update(message)
            elif message_type == MessageType.DELETE_ITEMS:
                self.handle_delete_items(message)

        print("listen_for_messages is over.")

    def handle_delete_items(self, tab_delimited_world_list_string: str) -> None:
        lines = tab_delimited_world_list_string.split("\n")
        for line in lines:
            if line == "":
                continue
            values = line.split("\t")
            user_id = int(values[1])
            self.client_gui.delete_item_from_world(values[0], user_id)

    def handle_world_update(self, tab_delimited_world_list_string: str) -> None:

        self.latest_update_info_string_lock.acquire()
        self.latest_update_info_string = tab_delimited_world_list_string
        self.latest_update_info_string_lock.release()

    def do_world_update(self):
        time_steps = []
        while self.keep_listening:
            this_time = time.time()
            time_steps.clear()
            time_steps.append(("A",this_time))
            world_update_delta_t = this_time - self.last_world_update_time

            # if self.world_update_count % 100 == 0:
            #     print(f"Handle_world_update delta t = {world_update_delta_t}")
            if world_update_delta_t > 1:
                print(f"Long delay... {world_update_delta_t:3.2f} seconds")
            if world_update_delta_t < 0.0333:
                continue

            time_steps.append(("B", time.time()))
            lines: Optional[str] = None
            self.latest_update_info_string_lock.acquire()
            if self.latest_update_info_string is not None:
                lines = self.latest_update_info_string.split("\n")
                self.latest_update_info_string = None
            self.latest_update_info_string_lock.release()

            time_steps.append(("C", time.time()))
            if lines is None:
                continue

            self.world_contents_lock.acquire()
            self.world_contents = []
            for line in lines:
                values = line.split("\t")
                game_object = {"type": values[0]}
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

                self.world_contents.append(game_object)
            time_steps.append(("D", time.time()))

            self.client_gui.update_world(self.world_contents)
            time_steps.append(("E", time.time()))

            self.world_contents_lock.release()
            self.last_world_update_time = this_time
            if time.time() - this_time > 1:
                print(f"Long time to finish: {time.time() - this_time} seconds")
                print(time_steps)
    def handle_user_list_update(self, tab_delimited_user_list_string: str) -> None:
        """
        The host has sent a tab-delimited string describing an updated user list; update the user_list in memory and
        onscreen.
        :param tab_delimited_user_list_string: new information about the list of users from the host socket
        :return: None
        """
        self.update_user_list(tab_delimited_user_list_string)
        print("------------------")
        for i in range(len(self.user_list)):
            print(f"{i}\t{self.user_list[i]}")
        print("------------------")
        self.client_gui.set_user_list(self.user_list)

    def handle_receive_submission(self, submission: str) -> None:
        """
        The host has sent a string from one of the users (or the host, itself) that should be posted; do so!
        :param submission: the string to post
        :return: None
        """
        print(f"MSG: {submission}")
        self.client_gui.add_to_chat(submission)

    def update_user_list(self, tab_delimited_user_list_string: str) -> None:
        """
        parse the tab-delimited string that contains the current list of users, replacing the information currently held
        in user_list.
        :param tab_delimited_user_list_string: a tab-delimited string that holds a number of users and then the list of
        usernames
        :return: None
        """

        print(f"{tab_delimited_user_list_string=}")

        parts = tab_delimited_user_list_string.split("\t")
        print(f"{parts=}")
        self.user_list.clear()
        num_users = int(parts[0])
        for i in range(1, num_users+1):
            self.user_list.append(parts[i])
        self.client_gui.set_user_list(parts[1:0])

    def send_message(self, message: str) -> None:
        """
        forwards the given string on to the socketMessageIO manager to send to the host in the appropriate format
        :param message: the string to send
        :return: None
        """
        self.manager.send_message_to_socket(message, self.my_socket)

    def close_socket(self, ) -> None:
        """
        cease listening for the socket and shut down the socket.
        :return: None
        """
        self.keep_listening = False
        self.my_socket.close()

    def update_keyboard(self, ) -> None:
        keyboard_code = self.client_gui.key_status
        # print(f"{bin(keyboard_code)}")
        self.manager.send_message_to_socket(keyboard_code, self.my_socket, message_type=MessageType.KEY_STATUS)

    def refresh_canvas(self):
        if self.world_contents_editable:
            self.world_contents_editable = False
            self.client_gui.update_world(self.world_contents)
            self.world_contents_editable = True


if __name__ == '__main__':
    client = SocketClient()
