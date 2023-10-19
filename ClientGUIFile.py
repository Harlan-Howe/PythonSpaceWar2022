import math
import random
import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog
from tkinter.scrolledtext import ScrolledText
from typing import List
import os

LEFT_MASK = 1
RIGHT_MASK = 2
BACK_MASK = 4
FORWARD_MASK = 8
FIRE_MASK = 16

KEY_RELEASE_DELAY = 400

class ClientGUI:
    def __init__(self):
        print("Creating ClientGUI.")
        # Create the window
        self.root = tk.Tk()
        self.root.title("Client")
        self.root.geometry('1000x850+50+50')  # an 1000 x 850 window, offset on screen by (50, 50).
        self.build_GUI_elements()

        # setup keyboard listening system
        self.key_status = 0
        self.key_counts = {"a": 0, "s": 0, "d": 0, "w": 0, " ": 0}
        self.key_masks = {"a": LEFT_MASK, "s": BACK_MASK, "d": RIGHT_MASK, "w": FORWARD_MASK, " ": FORWARD_MASK}
        self.setup_key_listening()

        # these are two additional methods (yes, really!) that will be set by an external class so that we can call them
        # from inside this class once they have been set. But for now, they're None.
        self.shut_down_socket = None
        self.tell_my_client_to_send_message = None

    def setup_key_listening(self) -> None:
        """
        set up responses to various keyboard actions
        :return: None
        """

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
        self.increment_key_count("a")

    def a_released(self, event_info):
        self.text_field.after(KEY_RELEASE_DELAY, lambda: self.decrement_key_count("a"))

    def d_pressed(self, event_info):
        self.increment_key_count("d")

    def d_released(self, event_info):
        self.text_field.after(KEY_RELEASE_DELAY, lambda: self.decrement_key_count("d"))

    def s_pressed(self, event_info):
        self.increment_key_count("s")

    def s_released(self, event_info):
        self.text_field.after(KEY_RELEASE_DELAY, lambda: self.decrement_key_count("s"))

    def w_pressed(self, event_info):
        self.increment_key_count("w")

    def w_released(self, event_info):
        self.text_field.after(KEY_RELEASE_DELAY, lambda: self.decrement_key_count("w"))

    def space_pressed(self, event_info):
        self.increment_key_count(" ")

    def space_released(self, event_info):
        self.text_field.after(KEY_RELEASE_DELAY, lambda: self.decrement_key_count(" "))

    def increment_key_count(self, key):
        self.key_status = self.key_status | self.key_masks[key]
        self.key_counts[key] += 1
        if self.key_counts[key] == 1:
            print(f"{key} is initially pressed.")

    def decrement_key_count(self, key):
        self.key_counts[key] -= 1
        if self.key_counts[key] == 0:
            self.key_status = self.key_status & (255 - self.key_masks[key])
        if 0 == self.key_counts[key]:
            print(f"{key} is really released.")

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
        self.world_canvas = tk.Canvas(self.root, width=800, height=800, background="black")
        self.world_canvas.grid(column=1, row=0, sticky="nw")

    def run_loop(self) -> None:
        """
        identifies the method that should be called when the user closes the window, and starts the Tk GUI main loop.
        :return: None
        """
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def request_name(self) -> str:
        """
        displays a dialog box to request the player's handle
        :return: the name the user entered.
        """
        answer = simpledialog.askstring("Input", "What is your first name?", parent=self.root)
        return answer

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

    def update_world(self, world_list) -> None:
        """
        refreshes the screen with the information for each object in the world list.
        :param world_list: a list of the public_info dictionary for each item on screen.
        :return: None
        """
        # self.world_canvas.delete("all")
        # self.draw_object_count(world_list)
        self.draw_key_states()
        for item in world_list:
            if item["type"] == "PLAYER":
                self.draw_player(item)
            elif item["type"] == "BULLET":
                self.draw_bullet(item)

    def draw_object_count(self, world_list):
        tag = "OBJECT_COUNT"
        if len(self.world_canvas.find_withtag(tag)) == 0:
            self.world_canvas.create_line(20, 0, 20, min(len(world_list), 800), fill="yellow", width=4, tags=tag)
        else:
            self.world_canvas.coords(tag, 20, 0, 20, min(len(world_list), 800))

    def draw_key_states(self):
        i = 0
        for key in ("w", "a", "s", "d", " "):
            tag = f"KEY_{key}"
            rad = 5 * self.key_counts[key]
            if len(self.world_canvas.find_withtag(tag)) == 0:
                self.world_canvas.create_oval(10, 10+25*i, 10+rad, 10+25*i+rad, fill= "white", tags=tag)
            else:
                self.world_canvas.coords(tag, 10, 10+25*i, 10+rad, 10+25*i+rad)
            i += 1

    def draw_bullet(self, item) -> None:
        """
        creates or updates the information for a bullet on screen.
        :param item: a dictionary of information about this particular bullet.
        :return: None
        """
        tag = f"BULLET{item['id']}"
        x = int(float(item["x"]))
        y = int(float(item["y"]))
        if len(self.world_canvas.find_withtag(tag)) == 0:
            self.world_canvas.create_oval(x - 2, y - 2, x + 2, y + 2, fill="white", outline="", tags=tag)
        else:
            self.world_canvas.coords(tag, x - 2, y - 2, x + 2, y + 2)

    def draw_player(self, item) -> None:
        """
        creates or updates the information for a player on screen.
        :param item: a dictionary of information about this particular player.
        :return: None
        """
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
        if len(my_ship_list) == 0:  # if nothing with the tag exists on screen, make it.
            self.world_canvas.create_line(x, y, int(x - 5*math.cos(bearing)), int(y - 5 * math.sin(bearing)),
                                          fill="black", width=1, arrow='last', arrowshape=(4, 6, 2),
                                          tags=tag+"thrust")
            # ship arrow
            self.world_canvas.create_line(x, y, int(x + 5 * math.cos(bearing)), int(y + 5 * math.sin(bearing)),
                                          fill=item['color'], width=2, arrow='last', arrowshape=(7, 11, 5),
                                          tags=tag)
            # name
            self.world_canvas.create_text(x, y-15, text=item["name"], justify='center', tags=tag+"name", fill="white")
            # healthbar
            self.world_canvas.create_line(x-bar_length/2, y+10, x+bar_length/2, y+10, tags=tag+"health", fill="green")
        else:  # we found the item by its tag, so modify it, instead of recreating it.
            self.world_canvas.coords(tag+"thrust", x, y,
                                     int(x - 8 * math.cos(bearing)),
                                     int(y - 8 * math.sin(bearing)))
            self.world_canvas.coords(my_ship_list[0], x, y,
                                     int(x + 5 * math.cos(bearing)),
                                     int(y + 5 * math.sin(bearing)))

            self.world_canvas.coords(tag+"name", x, y-15)
            self.world_canvas.coords(tag+"health", x-bar_length/2, y+10, x+bar_length/2, y+10)
            # update healthbar color, based on health
            if health < 20:
                self.world_canvas.itemconfig(tag+"health", fill="red")
            else:
                self.world_canvas.itemconfig(tag + "health", fill="green")
            # update color of thruster ship, based on whether ship is thrusting.
            if is_thrusting:
                self.world_canvas.itemconfig(tag + "thrust", fill="#" + f"FF{random.randrange(64, 255):02X}00")
            else:
                self.world_canvas.itemconfig(tag + "thrust", fill="black")

    def delete_item_from_world(self, item_type: str, object_id: int) -> None:
        """
        Since the objects on screen are maintained by id number and are modified rather than recreated each stop, we
        have need to remove items when they are no longer going to be in the world.
        :param item_type: A string (e.g., "PLAYER" or "BULLET" indicating what type of thing is being deleted.)
        :param object_id: The object_id of the object we need to remove.
        :return: None
        """
        if item_type == "PLAYER":
            # the player is actually several things - the ship, the name, the healthbar, the thruster - and we need to
            #  remove them all from the world_canvas
            tag = f"PLAYER{object_id}"
            self.world_canvas.delete(tag)
            self.world_canvas.delete(tag+"name")
            self.world_canvas.delete(tag+"thrust")
            self.world_canvas.delete(tag+"health")
        if item_type == "BULLET":
            # a bullet is much simpler to delete.
            tag = f"BULLET{object_id}"
            self.world_canvas.delete(tag)
