# Tkinter Imports #
import tkinter as tk
from tkinter.font import *
from tkinter import *
from tkinter.ttk import *
from PIL import ImageTk, Image

# Functionality Imports #
from collections import defaultdict
import webbrowser
import numpy as np
import threading
import random
import time
import math
import os

# Internal Imports #
from r2d2.user_interface.gui_parameters import *
from r2d2.user_interface.text import *

"""
TODO:

Low priority:
- Figure out noise
- Intro link on front page
- Organize code (save for later)
"""

class RobotGUI(tk.Tk):
    
    def __init__(self, robot=None, fullscreen=False):

        # Initialize #
        super().__init__()
        self.geometry("1500x1200")
        self.attributes("-fullscreen", fullscreen)
        self.bind("<Escape>", lambda e: self.destroy())

        # Prepare Relevent Items #
        self.num_traj_saved = 0
        self.camera_order = np.arange(robot.num_cameras)
        self.time_index = None
        self.robot = robot
        self.info = {
            'user': '',
            'fixed_tasks': [],
            'new_tasks': [],
            'current_task': '',
            'action_noise': 0,
        }

        # Create Resizable Container #
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Organize Frame Dict #
        self.frames = {}
        for F in (LoginPage, RobotResetPage, CanRobotResetPage, InstructionsPage, ControllerOffPage,
                  PreferedTasksPage,SceneConfigurationPage, CameraPage, EnlargedImagePage,
                  NoisePage, RequestedBehaviorPage, SceneChangesPage, PreferedTasksPage):
            self.frames[F] = F(container, self)
            self.frames[F].grid(row=0, column=0, sticky="nsew")

        # Listen For Robot Reset #
        self.enter_presses = 0
        self.bind('<KeyPress-Return>', self.robot_reset, add='+')
        self.refresh_enter_variable()

        # Listen For Robot Controls #
        info_thread = threading.Thread(target=self.listen_for_robot_info)
        info_thread.daemon = True
        info_thread.start()

        # Update Camera Feed #
        self.camera_feed = None
        camera_thread = threading.Thread(target=self.update_camera_feed)
        camera_thread.daemon = True
        camera_thread.start()

        # Start Program! #
        self.last_frame_change = 0
        self.show_frame(LoginPage)
        self.update_time_index()
        self.mainloop()

    def show_frame(self, frame_id, refresh_page=True, wait=False):
        if time.time() - self.last_frame_change < 0.1: return
        self.focus()
        self.last_frame_change = time.time()
        self.curr_frame = self.frames[frame_id]
        if hasattr(self.curr_frame, 'initialize_page') and refresh_page:
            self.curr_frame.initialize_page()

        if wait: self.after(100, self.curr_frame.tkraise)
        else: self.curr_frame.tkraise()

    def swap_img_order(self, i, j):
        self.camera_order[i], self.camera_order[j] = \
            self.camera_order[j], self.camera_order[i]

    def set_img(self, i, widget=None, width=None, height=None):
        if self.camera_feed is None: return
        elif self.time_index is None: img = self.camera_feed[self.camera_order[i]]
        else: img = self.last_traj[self.time_index][self.camera_order[i]]
        img = Image.fromarray(img)
        if width is not None:
            img = img.resize((width, height), Image.Resampling.LANCZOS)
        img = ImageTk.PhotoImage(img)
        widget.configure(image=img)
        widget.image = img

    def enable_replay(self):
        self.time_index = 0
        self.last_traj = self.robot.get_last_trajectory()

    def disable_replay(self):
        self.time_index = None

    def update_time_index(self):
        if self.time_index is not None:
            self.time_index = (self.time_index + 1) % len(self.last_traj)
        self.after(50, self.update_time_index)

    def robot_reset(self, event):
        self.enter_presses += 1
        if self.enter_presses == 25:
            self.enter_presses = -50
            self.robot.reset_robot()
            self.frames[RobotResetPage].tkraise()
            self.after(reset_duration * 1000, lambda: self.curr_frame.tkraise())

    def refresh_enter_variable(self):
        self.enter_presses = 0
        self.after(3000, self.refresh_enter_variable)

    def listen_for_robot_info(self):
        last_was_false = True
        controller_on = True
        while True:
            time.sleep(0.1)
            info = self.robot.get_user_feedback()
            trigger = info['save_episode'] or info['delete_episode']
            if trigger and last_was_false:
                self.event_generate('<<KeyRelease-controller>>')

            if info['controller_on'] < controller_on:
                self.show_frame(ControllerOffPage)

            last_was_false = not trigger
            controller_on = info['controller_on']

    def update_camera_feed(self, sleep=0.05):
        while True:
            self.camera_feed = self.robot.get_camera_feed()
            time.sleep(sleep)

# Start up page
class LoginPage(tk.Frame):

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Title #
        title_lbl = Label(self, text = "Login Page", font=Font(size=30, weight='bold'))
        title_lbl.place(relx=0.5, rely=0.1, anchor='n')

        # Request Name #
        self.user = StringVar()
        name_lbl = Label(self, text="Please Enter Your Full Name (Be Consistent!)", font=Font(size=15, underline=True))
        name_lbl.place(relx=0.5, rely=0.32, anchor='n')
        self.name_entry = tk.Entry(self, textvariable=self.user, font=Font(size=15))
        self.name_entry.place(relx=0.5, rely=0.35, anchor='n')


        # Begin Button #
        begin_btn = tk.Button(self, text ='BEGIN', highlightbackground='green',
            font=Font(size=30, weight='bold'), padx=3, pady=5, borderwidth=10,
            command=self.check_completeness)
        begin_btn.place(relx=0.5, rely=0.8, anchor=CENTER)

    def check_completeness(self):
        name = self.user.get()
        num_words = len([x for x in name.split(' ') if x != ''])
        correct_name = (num_words >= 2) and (missing_name_text not in name)
        if correct_name:
            self.controller.info['user'] = name
            self.controller.show_frame(SceneConfigurationPage)
        else:
            self.user.set(missing_name_text)

    def initialize_page(self):
        self.name_entry.focus()

class RobotResetPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        title_lbl = Label(self, text = "Resetting Robot...", font=Font(size=30, weight='bold'))
        title_lbl.pack(pady=15)

        description_lbl = Label(self, text='Please stand by :)', font=Font(size=18))
        description_lbl.pack(pady=5)

class CanRobotResetPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.controller.bind("<<KeyRelease-controller>>", self.moniter_keys, add="+")

        title_lbl = Label(self, text = "Proceed With Robot Reset?", font=Font(size=30, weight='bold'))
        title_lbl.pack(pady=15)

        description_lbl = Label(self, text="Press 'A' when ready", font=Font(size=18))
        description_lbl.pack(pady=5)

    def set_next_page(self, page):
        self.next_page = page

    def moniter_keys(self, event):
        if self.controller.curr_frame != self: return

        info_thread = threading.Thread(target=self.controller.robot.reset_robot)
        info_thread.daemon = True
        info_thread.start()

        self.controller.show_frame(self.next_page)

class ControllerOffPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.controller.bind("<KeyRelease-space>", self.moniter_keys, add="+")

        title_lbl = Label(self, text = "WARNING: Controller off", font=Font(size=30, weight='bold'))
        title_lbl.pack(pady=15)

        description_lbl = Label(self, text=controller_off_msg, font=Font(size=18))
        description_lbl.pack(pady=5)

    def moniter_keys(self, event):
        if self.controller.curr_frame != self: return
        self.controller.show_frame(LoginPage)

class InstructionsPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        # How To Text #
        how_to_tile_lbl = Label(self, text = "How To Prepare A Scene:", font=Font(size=30, weight='bold'))
        how_to_tile_lbl.pack(pady=15)

        how_to_text_lbl = Label(self, text=how_to_text, font=Font(size=18))
        how_to_text_lbl.pack(pady=5)

        # Data Collection Text #
        data_collection_lbl = Label(self, text = "Data Collection Notes:", font=Font(size=30, weight='bold'))
        data_collection_lbl.pack(pady=15)

        data_collection_text_lbl = Label(self, text=data_collection_text, font=Font(size=18))
        data_collection_text_lbl.pack(pady=5)

        # Warning Text #
        warnings_title_lbl = Label(self, text = "Warnings:", font=Font(size=30, weight='bold'))
        warnings_title_lbl.pack(pady=15)

        warnings_text_lbl = Label(self, text=warnings_text, font=Font(size=18))
        warnings_text_lbl.pack(pady=5)

        # Debugging Doc #
        bx, by = 0.12, 0.045
        box_lbl = tk.Button(self, text =' ' * 12, highlightbackground='blue',
            font=Font(slant='italic', weight='bold') , padx=50, pady=6)
        box_lbl.place(relx=bx, rely=by, anchor='n')

        debugging_lbl = tk.Button(self, text = "Debugging + Q&A", font=Font(weight='bold'))
        debugging_lbl.place(relx=bx, rely=by + 0.005, anchor='n')
        debugging_lbl.bind("<Button-1>", lambda e: webbrowser.open_new(debugging_link))

        # Back Button #
        back_btn = tk.Button(self, text ='BACK', highlightbackground='red',
            font=Font(size=30, weight='bold'), padx=3, pady=5, borderwidth=10,
            command=lambda: controller.show_frame(SceneConfigurationPage))
        back_btn.place(relx=0.85, rely=0.85)


class PreferedTasksPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.controller.bind("<KeyRelease>", self.moniter_keys, add="+")

        # Title #
        title_lbl = Label(self, text = "Prefered Tasks", font=Font(size=30, weight='bold'))
        title_lbl.place(relx=0.5, rely=0.05, anchor='n')


        # Shift Instructions #
        instr_lbl = tk.Label(self, text=prefered_task_text, font=Font(size=20, slant='italic'))
        instr_lbl.place(relx=0.5, rely=0.1, anchor='n')

        # Fixed Task Selection #
        pos_dict = {'Articulated Tasks': (0.05, 0.2),
                    'Free Object Tasks': (0.05, 0.4),
                    'Tool Usage Tasks': (0.55, 0.2),
                    'Deformable Object Tasks': (0.55, 0.4)}

        for key in prefered_tasks.keys():
            x_pos, y_pos = pos_dict[key]
            group_lbl = tk.Label(self, text=key + ":", font=Font(size=20, underline=True))
            group_lbl.place(relx=x_pos, rely=y_pos)
            for i, task in enumerate(prefered_tasks[key]):
                task_ckbox = tk.Checkbutton(self, text=task, font=Font(size=15), variable=BooleanVar())
                task_ckbox.place(relx=x_pos + 0.01, rely=y_pos + (i + 1) * 0.04)

        # Free Response Tasks #
        notes_lbl = tk.Label(self, text='Personal Notes:', font=Font(size=20, underline=True))
        notes_lbl.place(relx=0.05, rely=0.6)
        
        self.notes_txt = tk.Text(self, height=15, width=65, font=Font(size=15))
        self.notes_txt.place(relx=0.05, rely=0.64)

        # Back Button #
        back_btn = tk.Button(self, text ='BACK', highlightbackground='red',
            font=Font(size=30, weight='bold'), padx=3, pady=5, borderwidth=10,
            command=lambda: controller.show_frame(SceneConfigurationPage))
        back_btn.place(relx=0.7, rely=0.75)

    def moniter_keys(self, event):
        if self.controller.curr_frame != self: return

        # Toggle Camera View
        if event.keysym in ['Shift_L', 'Shift_R']:
            self.controller.frames[CameraPage].set_home_frame(PreferedTasksPage)
            self.controller.show_frame(CameraPage, wait=True)

    def initialize_page(self):
        self.notes_txt.focus()

class NoisePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.action_noise = IntVar()
        self.noise_str = StringVar()
        self.max_amount = 100

        # Title #
        title_lbl = Label(self, text = "Action Noise", font=Font(size=30, weight='bold'))
        title_lbl.place(relx=0.5, rely=0.05, anchor='n')

        # Shift Instructions #
        instr_lbl = tk.Label(self, text=noise_text, font=Font(size=20, slant='italic'))
        instr_lbl.place(relx=0.5, rely=0.1, anchor='n')

        # Slider #
        scale = Scale(self, from_=0, to=self.max_amount, orient=HORIZONTAL, length=500,
            variable=self.action_noise, command=self.update_info)
        scale.place(relx=0.5, rely=0.4, anchor=CENTER)

        # Noise Visualizer #
        noise_lbl = tk.Label(self, textvariable=self.noise_str, font=Font(size=20, slant='italic'))
        noise_lbl.place(relx=0.5, rely=0.35, anchor='n')

        # Back Button #
        back_btn = tk.Button(self, text ='BACK', highlightbackground='red',
            font=Font(size=30, weight='bold'), padx=3, pady=5, borderwidth=10,
            command=lambda: controller.show_frame(RequestedBehaviorPage))
        back_btn.place(relx=0.5, rely=0.7, anchor=CENTER)

        # Initialize String #
        self.update_info(None)

    def update_info(self, e):
        noise = self.action_noise.get()
        self.controller.info['action_noise'] = noise / self.max_amount
        self.noise_str.set('{0}%'.format(noise))


class SceneConfigurationPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Update Based Off Activity #
        self.controller.bind("<KeyRelease>", self.moniter_keys, add="+")
        self.controller.bind("<ButtonRelease-1>", self.moniter_keys, add="+")

        # Title #
        title_lbl = Label(self, text = "Scene Configuration", font=Font(size=30, weight='bold'))
        title_lbl.place(relx=0.5, rely=0.05, anchor='n')

        # Button Box #
        bx, by = 0.12, 0.045
        box_lbl = tk.Button(self, text =' ' * 25, highlightbackground='blue',
            font=Font(slant='italic', weight='bold'), padx=20, pady=55)
        box_lbl.place(relx=bx, rely=by, anchor='n')

        # Instructions Button #
        instructions_btn = tk.Button(self, text="Instructions", font=Font(weight="bold"), padx=10,
            command=lambda: controller.show_frame(InstructionsPage))
        instructions_btn.place(relx=bx, rely=by + 0.005, anchor='n')

        # Task Ideas Button #
        ideas_btn = tk.Button(self, text="Task Ideas", font=Font(weight="bold"), padx=15)
        ideas_btn.bind("<Button-1>", lambda e: webbrowser.open_new(task_ideas_link))
        ideas_btn.place(relx=bx, rely=by + 0.035, anchor='n')

        # Prefered Tasks Button #
        prefered_tasks_btn = tk.Button(self, text="Prefered Tasks", font=Font(weight="bold"),
            command=lambda: controller.show_frame(PreferedTasksPage))
        prefered_tasks_btn.place(relx=bx, rely=by + 0.065, anchor='n')

        # Franka Website Button #
        franka_btn = tk.Button(self, text="Franka Website", font=Font(weight="bold"))
        franka_btn.bind("<Button-1>", lambda e: webbrowser.open_new(franka_website))
        franka_btn.place(relx=bx, rely=by + 0.095, anchor='n')

        # Shift Instructions #
        instr_lbl = tk.Label(self, text=shift_text, font=Font(size=20, slant='italic'))
        instr_lbl.place(relx=0.5, rely=0.1, anchor='n')

        # Fixed Task Selection #
        self.task_dict = defaultdict(BooleanVar)
        pos_dict = {'Articulated Tasks': (0.05, 0.2),
                    'Free Object Tasks': (0.05, 0.4),
                    'Tool Usage Tasks': (0.55, 0.2),
                    'Deformable Object Tasks': (0.55, 0.4)}

        for key in all_tasks.keys():
            x_pos, y_pos = pos_dict[key]
            group_lbl = tk.Label(self, text=key + ":", font=Font(size=20, underline=True))
            group_lbl.place(relx=x_pos, rely=y_pos)
            for i, task in enumerate(all_tasks[key]):
                task_ckbox = tk.Checkbutton(self, text=task, font=Font(size=15), variable=self.task_dict[task])
                task_ckbox.place(relx=x_pos + 0.01, rely=y_pos + (i + 1) * 0.04)

        # Free Response Tasks #
        group_lbl = tk.Label(self, text=freewrite_text, font=Font(size=20, underline=True))
        group_lbl.place(relx=0.05, rely=0.6)
        
        self.task_txt = tk.Text(self, height=15, width=65, font=Font(size=15))
        self.task_txt.place(relx=0.05, rely=0.64)

        # Practice Button #
        practice_btn = tk.Button(self, text ='PRACTICE', highlightbackground='red',
            font=Font(size=30, weight='bold'), padx=3, pady=5, borderwidth=10,
            command=self.practice_robot)
        practice_btn.place(relx=0.6, rely=0.75)

        # Ready Button #
        ready_btn = tk.Button(self, text ='DONE', highlightbackground='green',
            font=Font(size=30, weight='bold'), padx=3, pady=5, borderwidth=10,
            command=self.finish_setup)
        ready_btn.place(relx=0.8, rely=0.75)

    def moniter_keys(self, event):
        if self.controller.curr_frame != self: return

        # Toggle Camera View
        if event.keysym in ['Shift_L', 'Shift_R']:
            self.controller.frames[CameraPage].set_home_frame(SceneConfigurationPage)
            self.controller.show_frame(CameraPage, wait=True)

        # Update Fixed Tasks #
        self.controller.info['fixed_tasks'] = []
        for task, val in self.task_dict.items():
            if val.get(): self.controller.info['fixed_tasks'].append(task)

        # Update New Tasks #
        self.controller.info['new_tasks'] = self.get_new_tasks()

    def finish_setup(self):
        fixed_tasks = self.controller.info['fixed_tasks']
        new_tasks = self.controller.info['new_tasks']
        if len(fixed_tasks) + len(new_tasks) == 0:
            self.task_txt.delete('1.0', END)
            self.task_txt.insert(1.0, no_tasks_text)
        else:
            self.controller.show_frame(RequestedBehaviorPage)

    def get_new_tasks(self):
        new_tasks = self.task_txt.get("1.0", END).replace('\n', "")
        new_tasks = new_tasks.replace(no_tasks_text, '').split(';')
        new_tasks = [t for t in new_tasks if (not t.isspace() and len(t))]
        return new_tasks

    def practice_robot(self):
        self.controller.frames[CameraPage].set_mode('practice_traj')
        self.controller.show_frame(CameraPage, wait=True)

    def initialize_page(self):
        self.controller.frames[CameraPage].set_mode('live')
        self.task_txt.focus()

class RequestedBehaviorPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.keep_task = False

        # Title #
        title_lbl = Label(self, text="Requested Behavior", font=Font(size=30, weight='bold'))
        title_lbl.place(relx=0.5, rely=0.05, anchor='n')

        # Task #
        self.task_text = StringVar()
        task_lbl = Label(self, textvariable=self.task_text, font=Font(size=30))
        task_lbl.place(relx=0.5, rely=0.4, anchor='center')

        # Resample Button #
        resample_btn = tk.Button(self, text ='RESAMPLE', highlightbackground='red',
            font=Font(size=30, weight='bold'), padx=3, pady=5, borderwidth=10,
            command=self.initialize_page)
        resample_btn.place(relx=0.44, rely=0.7)

        # Instructions #
        instr_lbl = tk.Label(self, text="Press 'A' on the controller to begin", font=Font(size=20, slant='italic'))
        instr_lbl.place(relx=0.5, rely=0.1, anchor='n')

        # Bounding Box #
        bx, by = 0.12, 0.045
        box_lbl = tk.Button(self, text =' ' * 25, highlightbackground='blue',
            font=Font(slant='italic', weight='bold') , padx=50, pady=39)
        box_lbl.place(relx=bx, rely=by, anchor='n')

        # Noise Button #
        noise_btn = tk.Button(self, text="Adjust Action Noise", font=Font(weight="bold"), padx=10,
            command=lambda: self.controller.show_frame(NoisePage))
        noise_btn.place(relx=bx, rely=by + 0.005, anchor='n')

        # Replay Button #
        replay_btn = tk.Button(self, text="Replay Last Trajectory", font=Font(weight="bold"),
            command=self.replay_traj)
        replay_btn.place(relx=bx, rely=by + 0.035, anchor='n')

        # Return Button #
        return_btn = tk.Button(self, text="Scene Configuration", font=Font(weight="bold"), padx=8,
            command=lambda: self.controller.show_frame(SceneConfigurationPage))
        return_btn.place(relx=bx, rely=by + 0.065, anchor='n')

        # Update Based Off Activity #
        controller.bind("<<KeyRelease-controller>>", self.start_trajectory, add="+")

    def initialize_page(self):
        self.controller.frames[CameraPage].set_mode('traj')
        if not self.keep_task: self.sample_new_task()
        else: self.keep_task = False

    def sample_new_task(self):
        if np.random.uniform() < compositional_task_prob:
            task = self.sample_compositional_task()
        else:
            task = self.sample_single_task()

        self.controller.info['current_task'] = task
        self.task_text.set(task)
        self.controller.update_idletasks()

    def sample_compositional_task(self):
        assert len(compositional_tasks) == 4
        comp_type = np.random.randint(4)
        tasks = [self.sample_single_task() for i in range(comp_type)]
        return compositional_tasks[comp_type](*tasks)

    def sample_single_task(self):
        fixed_tasks = self.controller.info['fixed_tasks']
        ft_weight = np.array([self.get_task_weight(t) for t in fixed_tasks])
        ft_weight = (ft_weight / ft_weight.sum()) * (1 - new_task_prob)

        new_tasks = self.controller.info['new_tasks']
        nt_weight = (np.ones(len(new_tasks)) / len(new_tasks)) * new_task_prob

        tasks = fixed_tasks + new_tasks
        weights = np.concatenate([ft_weight, nt_weight])

        return random.choices(tasks, weights=weights)[0]

    def get_task_weight(self, task):
        task_type = [t for t in task_weights.keys() if t in task]
        assert len(task_type) == 1
        return task_weights[task_type[0]]

    def start_trajectory(self, event):
        if self.controller.curr_frame != self: return
        self.controller.show_frame(CameraPage, wait=True)

    def replay_traj(self):
        if self.controller.robot.traj_data is None: return
        self.controller.frames[CameraPage].set_mode('replay')
        self.controller.show_frame(CameraPage, wait=True)

    def keep_last_task(self):
        self.keep_task = True


class SceneChangesPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Title #
        title_lbl = Label(self, text ="Requested Scene Changes", font=Font(size=30, weight='bold'))
        title_lbl.place(relx=0.5, rely=0.05, anchor='n')

        # Shift Instructions #
        instr_lbl = tk.Label(self, text=shift_text, font=Font(size=20, slant='italic'))
        instr_lbl.place(relx=0.5, rely=0.1, anchor='n')
        self.controller.bind("<KeyRelease>", self.show_camera_feed, add="+")

        # Changes #
        self.change_text = StringVar()
        change_lbl = Label(self, textvariable=self.change_text, font=Font(size=30))
        change_lbl.place(relx=0.5, rely=0.4, anchor='center')

        # Resample Button #
        resample_btn = tk.Button(self, text='RESAMPLE', highlightbackground='red',
            font=Font(size=30, weight='bold'), padx=3, pady=5, borderwidth=10,
            command=self.sample_change)
        resample_btn.place(relx=0.34, rely=0.7)

        # Ready Button #
        ready_btn = tk.Button(self, text='DONE', highlightbackground='green',
            font=Font(size=30, weight='bold'), padx=3, pady=5, borderwidth=10,
            command=lambda: self.controller.show_frame(SceneConfigurationPage))
        ready_btn.place(relx=0.54, rely=0.7)

    def show_camera_feed(self, event):
        if self.controller.curr_frame != self: return
        if event.keysym in ['Shift_L', 'Shift_R']:
            self.controller.frames[CameraPage].set_home_frame(SceneChangesPage)
            self.controller.show_frame(CameraPage, wait=True)

    def sample_change(self):
        num_traj = self.controller.num_traj_saved
        move_robot = (num_traj % move_robot_frequency == 0) and (num_traj > 0)
        
        if move_robot: curr_text = move_robot_text
        else: curr_text = random.choice(scene_changes)
        self.change_text.set(curr_text)
        self.controller.update_idletasks()

    def initialize_page(self):
        self.controller.frames[CameraPage].set_mode('live')
        self.sample_change()

class CameraPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.n_rows = 1 if len(self.controller.camera_order) <= 2 else 2
        self.n_cols = math.ceil(len(self.controller.camera_order) / self.n_rows)

        # Moniter Key Events #
        self.controller.bind("<KeyRelease>", self.moniter_keys, add="+")
        self.controller.bind("<<KeyRelease-controller>>", self.moniter_keys, add="+")

        # Page Variables #
        self.title_str = StringVar()
        self.instr_str = StringVar()
        self.mode = 'live'

        # Title #
        title_lbl = Label(self, textvariable=self.title_str, font=Font(size=30, weight='bold'))
        title_lbl.place(relx=0.5, rely=0.02, anchor='n')

        # Instructions #
        instr_lbl = tk.Label(self, textvariable=self.instr_str, font=Font(size=24, slant='italic'))
        instr_lbl.place(relx=0.5, rely=0.06, anchor='n')

        # Save / Delete Buttons #
        self.save_btn = tk.Button(self, text ='SAVE', highlightbackground='green',
            font=Font(size=30, weight='bold'), padx=3, pady=5, borderwidth=10,
            command=lambda save=True: self.edit_trajectory(save))
        self.delete_btn = tk.Button(self, text ='DELETE', highlightbackground='red',
            font=Font(size=30, weight='bold'), padx=3, pady=5, borderwidth=10,
            command=lambda save=False: self.edit_trajectory(save))

        # Timer #
        self.timer_on = False
        self.time_str = StringVar()
        self.timer = tk.Button(self, textvariable=self.time_str, highlightbackground='black',
            font=Font(size=40, weight='bold'), padx=3, pady=5, borderwidth=10)

        # Image Variables #
        self.clicked_id = None
        self.image_boxes = []

        # Create Image Grid #
        for i in range(self.n_rows):
            self.rowconfigure(i, weight=1)
            for j in range(self.n_cols):
                if (i * self.n_cols + j) >= len(self.controller.camera_order): continue
                self.columnconfigure(j, weight=1)

                # Add Image Box #
                button = tk.Button(self, height=0, width=0, command=\
                    lambda idx=(i*self.n_cols + j): self.update_image_grid(idx))
                button.grid(row=i, column=j, sticky="s" if self.n_rows > 1 else '')
                self.image_boxes.append(button)

                # Start Image Thread #
                camera_thread = threading.Thread(
                    target=lambda idx=(i*self.n_cols + j): self.update_camera_feed(idx))
                camera_thread.daemon = True
                camera_thread.start()

    def update_image_grid(self, i):
        if self.clicked_id is None:
            # Get Image Of Interest
            self.clicked_id = i
        elif self.clicked_id == i:
            # If Double Clicked, Enlarge It
            self.controller.frames[EnlargedImagePage].set_image_index(i)
            self.controller.show_frame(EnlargedImagePage, wait=True)
            self.clicked_id = None
        else:
            # If Alternate Image Clicked, Swap Them
            self.controller.swap_img_order(self.clicked_id, i)
            self.clicked_id = None

    def update_camera_feed(self, i, w_coeff=0.5, h_coeff=0.75):
        while True:
            w, h = max(self.winfo_width(), 100), max(self.winfo_height(), 100)
            img_w = int(w / self.n_cols * w_coeff)
            img_h = int(h / self.n_cols * h_coeff)

            self.controller.set_img(i, widget=self.image_boxes[i], width=img_w, height=img_h)

    def moniter_keys(self, event):
        zoom = self.controller.frames[EnlargedImagePage]
        page_inactive = self.controller.curr_frame not in [self, zoom]
        if page_inactive: return
        
        shift = event.keysym in ['Shift_L', 'Shift_R']
        space = event.keysym == 'controller'

        if self.mode == 'live' and shift:
            self.controller.show_frame(self.home_frame, refresh_page=False)
        if ('traj' in self.mode) and space:
            self.end_trajectory()

    def initialize_page(self):

        # Clear Widges #
        self.controller.disable_replay()
        self.save_btn.place_forget()
        self.delete_btn.place_forget()
        self.timer.place_forget()

        # Update Text #
        self.title_str.set(camera_page_title[self.mode])
        self.instr_str.set(camera_page_instr[self.mode])

        # Add Mode Specific Stuff #
        if self.mode == 'replay':
            self.controller.enable_replay()
            self.save_btn.place(relx=0.79, rely=0.02)
            self.delete_btn.place(relx=0.11, rely=0.02)
        elif 'traj' in self.mode:
            # Pass in 0 action noise for practice, action noise for real thing
            self.timer.place(relx=0.79, rely=0.01)
            self.update_timer(time.time())

            traj_thread = threading.Thread(target=self.collect_trajectory)
            traj_thread.daemon = True
            traj_thread.start()

    def collect_trajectory(self):
        info = self.controller.info.copy()
        action_noise = self.controller.info['action_noise']
        practice = self.mode == 'practice_traj'
        self.controller.robot.set_action_noise(action_noise)
        self.controller.robot.collect_trajectory(info=info, practice=practice)
        self.end_trajectory()

    def update_timer(self, start_time):
        time_passed = time.time() - start_time
        zoom = self.controller.frames[EnlargedImagePage]
        page_inactive = self.controller.curr_frame not in [self, zoom]
        hide_timer = 'traj' not in self.mode
        if page_inactive or hide_timer: return

        minutes_str = str(int(time_passed / 60))
        curr_seconds = int(time_passed) % 60

        if curr_seconds < 10: seconds_str = '0{0}'.format(curr_seconds)
        else: seconds_str = str(curr_seconds)

        if not self.controller.robot.traj_running: start_time = time.time()

        self.time_str.set('{0}:{1}'.format(minutes_str, seconds_str))
        self.controller.after(100, lambda: self.update_timer(start_time))

    def end_trajectory(self):
        save = self.controller.robot.traj_saved
        practice = self.mode == 'practice_traj'

        # Update Based Off Success / Failure #
        if practice: pass
        elif save: self.controller.num_traj_saved += 1
        else: self.controller.frames[RequestedBehaviorPage].keep_last_task()

        # Check For Scene Changes #
        num_traj = self.controller.num_traj_saved
        move_robot = (num_traj % move_robot_frequency == 0) and (num_traj > 0)
        scene_change = (np.random.uniform() < scene_change_prob) or move_robot

        # Move To Next Page
        time.sleep(0.1) # Prevents bug where robot doesnt wait to reset
        if practice: post_reset_page = SceneConfigurationPage
        elif scene_change: post_reset_page = SceneChangesPage
        else: post_reset_page = RequestedBehaviorPage
        self.controller.frames[CanRobotResetPage].set_next_page(post_reset_page)
        self.controller.show_frame(CanRobotResetPage)

    def set_home_frame(self, frame):
        self.home_frame = frame

    def set_mode(self, mode):
        self.mode = mode

    def edit_trajectory(self, save):
        if save: self.controller.robot.save_trajectory()
        else: self.controller.robot.delete_trajectory()
        self.controller.show_frame(RequestedBehaviorPage)

class EnlargedImagePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Return When Double Clicked #
        controller.bind('<Button-1>', self.return_to_camera_grid, add="+")

        # Image Variables #
        self.image_box = Label(self)
        self.image_box.pack(fill=BOTH, expand=YES)
        self.img_index = 0

        # Camera Feed Thread #
        camera_thread = threading.Thread(target=self.update_camera_feed)
        camera_thread.daemon = True
        camera_thread.start()

    def set_image_index(self, img_index):
        self.img_index = img_index

    def return_to_camera_grid(self, e):
        if self.controller.curr_frame != self: return
        self.controller.show_frame(CameraPage, refresh_page=False, wait=True)

    def update_camera_feed(self):
        while True:
            #w, h = 250, 250
            w, h = max(self.winfo_width(), 250), max(self.winfo_height(), 250)
            self.controller.set_img(self.img_index, widget=self.image_box, width=w, height=h)
