import math
import random
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from typing import List
import time


class ClientGUI:
    def __init__(self):

        self.root = tk.Tk()
        self.root.title("Client")
        self.root.geometry('1000x850+50+50')  # an 1000 x 850 window, offset on screen by (50, 50).

        self.user_entry_string = None
        self.text_field = None
        self.user_list_text = None
        self.chat_so_far = ""
        self.chat_response_text = None

        self.key_status = 0
        self.setup_key_listening()

        self.build_GUI_elements()

        # these are two additional methods (yes, really!) that will be set by an external class so that we can call them
        # from inside this class once they have been set. But for now, they're None.
        self.shut_down_socket = None
        self.tell_my_client_to_send_message = None


    def setup_key_listening(self):
        self.root.bind("<KeyPress-a>", self.a_pressed)
        self.root.bind("<KeyRelease-a>", self.a_released)
        self.root.bind("<KeyPress-d>", self.d_pressed)
        self.root.bind("<KeyRelease-d>", self.d_released)
        self.root.bind("<KeyPress-s>", self.s_pressed)
        self.root.bind("<KeyRelease-s>", self.s_released)
        self.root.bind("<KeyPress-w>", self.w_pressed)
        self.root.bind("<KeyRelease-w>", self.w_released)
        self.root.bind("<KeyPress-space>", self.space_pressed)
        self.root.bind("<KeyRelease-space>", self.space_released)

    def a_pressed(self, event_info):
        self.key_status = self.key_status | 1
        # print(f"{self.key_status}\t{recent-self.last_key_update}")

    def a_released(self, event_info):
        self.key_status = self.key_status & 254
        # print(f"{self.key_status}\t{recent - self.last_key_update}")

    def d_pressed(self, event_info):
        self.key_status = self.key_status | 2
        # print(self.key_status)

    def d_released(self, event_info):
        self.key_status = self.key_status & 253
        # print(self.key_status)

    def s_pressed(self, event_info):
        self.key_status = self.key_status | 4
        # print(f"{self.key_status}\t{recent - self.last_key_update}")

    def s_released(self, event_info):
        self.key_status = self.key_status & 251
        # print(f"{self.key_status}\t{recent - self.last_key_update}")

    def w_pressed(self, event_info):
        self.key_status = self.key_status | 8
        # print(self.key_status)

    def w_released(self, event_info):
        self.key_status = self.key_status & 247
        # print(self.key_status)

    def space_pressed(self, event_info):
        self.key_status = self.key_status | 16
        # print(self.key_status)

    def space_released(self, event_info):
        self.key_status = self.key_status & 239
        # print(self.key_status)

    def build_GUI_elements(self) -> None:
        """
        builds and arranges the GUI items for the window.
        :return: None
        """
        # set the relative sizes of the columns and rows in this grid
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=3)
        self.root.rowconfigure(0, weight=6)
        self.root.rowconfigure(1, weight=1)

        # the bottom frame is where the user is prompted to type something, along with the text field to type it.
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.columnconfigure(1, weight=6)
        bottom_frame.grid(column=0, row=1, columnspan=2, sticky='new')
        entry_label = ttk.Label(bottom_frame, text='Enter what you want to say here:')
        entry_label.grid(column=0, row=0, sticky='e')
        self.user_entry_string = tk.StringVar()
        self.text_field = ttk.Entry(bottom_frame, textvariable=self.user_entry_string)
        self.text_field.grid(column=1, row=0, sticky='ew')
        self.text_field.bind('<Return>', self.respond_to_text_entry)

        # This is where the user list is kept.
        self.user_list_text = ScrolledText(self.root, width=20, background="black", foreground="white")
        self.user_list_text.grid(column=0, row=0, sticky='ns')
        self.user_list_text['state'] = 'disabled'  # not editable by user

        # this is where the transcript of the chat is kept.
        # self.chat_response_text = ScrolledText(self.root, background='#bbbbbb')
        # self.chat_response_text.grid(column=1, row=0, sticky='ns')
        # self.chat_response_text['state'] = 'disabled'  # not editable by user

        # This is where the graphics will go...
        self.world_canvas = tk.Canvas(self.root, width = 800, height = 800, background = "black")
        self.world_canvas.grid(column=1, row=0, sticky="nw")


    def run_loop(self) -> None:
        """
        identifies the method that should be called when the user closes the window, and starts the Tk GUI main loop.
        :return: None
        """
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self) -> None:
        """
        when it is time to close the window, shut down the socket to the host (gracefully) and then close the window.
        :return: None
        """
        self.shut_down_socket()
        self.root.destroy()

    def set_user_list(self, users: List[str]) -> None:
        """
        updates the onscreen list of users with the given list of strings.
        :param users: a list of usernames
        :return: None
        """
        names = ""
        for user in users:
            names += f"{user}\n"

        self.user_list_text['state'] = 'normal'
        self.user_list_text.replace(1.0, 'end', names)
        self.user_list_text['state'] = 'disabled'

    def add_to_chat(self, entry: str) -> None:
        """
        appends the given entry to the list of items in the chat_so_far and updates the chat_response_text GUI text
        area, accordingly.
        :param entry: the string to append to the chat_so_far.
        :return: None
        """
        # self.chat_so_far += entry+"\n"
        # self.chat_response_text['state'] = 'normal'
        # self.chat_response_text.replace(1.0, 'end', self.chat_so_far)
        # self.chat_response_text['state'] = 'disabled'
        self.user_entry_string.set(entry)

    def respond_to_text_entry(self, event_info):
        """
        the user has pressed return when the cursor is in the textfield, so send the submission contained there (if any)
        and clear the textfield for the next time.
        :param event_info: not used, but required for callback.
        :return: None
        """
        message = self.user_entry_string.get()
        if message != "":
            self.tell_my_client_to_send_message(message)
            self.user_entry_string.set("")

    def update_world(self, world_list):
        # self.world_canvas.delete("all")
        for item in world_list:
            if item["type"] == "PLAYER":
                self.draw_player(item)
            elif item["type"] == "BULLET":
                self.draw_bullet(item)

    def draw_bullet(self, item):
        tag = f"BULLET{item['id']}"
        x = int(float(item["x"]))
        y = int(float(item["y"]))
        if len(self.world_canvas.find_withtag(tag)) == 0:
            self.world_canvas.create_oval(x-1, y-1, x+1, y+1, fill="white", outline="", tag=tag)
        else:
            self.world_canvas.coords(tag, x-1, y-1, x+1, y+1)

    def draw_player(self, item):
        # pull info from item dictionary
        user_id = int(item["id"])
        x = int(float(item["x"]))
        y = int(float(item["y"]))
        bearing = float(item["bearing"])
        is_thrusting = item["thrusting"]

        health = int(item["health"])
        bar_length = int(health*25/100)
        # construct tag used to identify the object in the canvas
        tag = f"PLAYER{user_id}"
        # find the object, if it exists.
        my_ship_list = self.world_canvas.find_withtag(tag)
        if len(my_ship_list) == 0: # if nothing with the tag exists on screen, make it.
            self.world_canvas.create_line(x, y, int(x - 5*math.cos(bearing)), int(y- 5 * math.sin(bearing)),
                                          fill="black", width=1, arrow='last', arrowshape=(4, 6, 2),
                                          tag=tag+"thrust")
            # ship arrow
            self.world_canvas.create_line(x, y, int(x + 5 * math.cos(bearing)), int(y + 5 * math.sin(bearing)),
                                          fill=item['color'], width=2, arrow='last', arrowshape=(7, 11, 5),
                                          tag=tag)
            # name
            self.world_canvas.create_text(x, y-15, text=item["name"], justify='center', tag=tag+"name", fill="white")
            # healthbar
            self.world_canvas.create_line(x-bar_length/2, y+10, x+bar_length/2, y+10, tag=tag+"health", fill="green")
        else: # we found the item by its tag, so modify it.
            self.world_canvas.coords(tag+"thrust", x, y,
                                     int(x - 8 * math.cos(bearing)),
                                     int(y - 8 * math.sin(bearing)))
            self.world_canvas.coords(my_ship_list[0], x, y,
                                     int(x + 5 * math.cos(bearing)),
                                     int(y + 5 * math.sin(bearing)))

            self.world_canvas.coords(tag+"name", x, y-15)
            self.world_canvas.coords(tag+"health", x-bar_length/2, y+10, x+bar_length/2, y+10)
            if health < 20:
                self.world_canvas.itemconfig(tag+"health", fill="red")
            else:
                self.world_canvas.itemconfig(tag + "health", fill="green")
            if is_thrusting:
                self.world_canvas.itemconfig(tag+ "thrust", fill= "#" + \
                    f"FF{random.randrange(64, 255):02X}00")
            else:
                self.world_canvas.itemconfig(tag+ "thrust", fill="black")

    def delete_item_from_world(self, item_type: str, object_id: int) -> None:
        if item_type == "PLAYER":
            tag = f"PLAYER{object_id}"
            self.world_canvas.delete(tag)
            self.world_canvas.delete(tag+"name")
            self.world_canvas.delete(tag+"thrust")
            self.world_canvas.delete(tag+"health")
        if item_type == "BULLET":
            tag = f"BULLET{object_id}"
            self.world_canvas.delete(tag)