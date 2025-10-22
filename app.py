# streamlit_todo_with_auth.py
# Single-file Streamlit app with Sign Up / Login + ToDo list with deadline + Undo/Redo
# NOTE: This is a simple demo implementation for learning purposes. Passwords are hashed
# with sha256 but this is NOT a production authentication system.

import streamlit as st
from copy import deepcopy
from datetime import datetime, date, time
import hashlib

# ---------------------------
# Helper: simple password hash
# ---------------------------

def hash_password(plain: str) -> str:
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()

# ---------------------------
# ToDoStack: tasks are dicts {"text":..., "deadline": datetime or None}
# supports undo/redo by snapshotting the tasks list
# ---------------------------
class ToDoStack:
    def __init__(self):
        self.tasks = []  # list of dicts: {"text": str, "deadline": datetime | None}
        self._undo_stack = []
        self._redo_stack = []

    def _snapshot_for_undo(self):
        self._undo_stack.append(deepcopy(self.tasks))

    def add_task(self, text: str, deadline: datetime | None):
        if not text:
            return
        self._snapshot_for_undo()
        self.tasks.append({"text": text, "deadline": deadline})
        self._redo_stack.clear()

    def remove_task(self, index: int):
        if index < 0 or index >= len(self.tasks):
            return
        self._snapshot_for_undo()
        self.tasks.pop(index)
        self._redo_stack.clear()

    def clear(self):
        if not self.tasks:
            return
        self._snapshot_for_undo()
        self.tasks = []
        self._redo_stack.clear()

    def undo(self):
        if not self._undo_stack:
            return
        self._redo_stack.append(deepcopy(self.tasks))
        self.tasks = self._undo_stack.pop()

    def redo(self):
        if not self._redo_stack:
            return
        self._undo_stack.append(deepcopy(self.tasks))
        self.tasks = self._redo_stack.pop()

# ---------------------------
# Session state initialization
# ---------------------------
if 'users' not in st.session_state:
    # store usernames -> password_hash
    st.session_state.users = {}

if 'current_user' not in st.session_state:
    st.session_state.current_user = None

if 'todo' not in st.session_state:
    st.session_state.todo = ToDoStack()

if 'show_panel' not in st.session_state:
    st.session_state.show_panel = False

# ---------------------------
# Authentication UI
# ---------------------------

def signup(username: str, password: str):
    if not username or not password:
        st.warning("Enter both username and password.")
        return False
    if username in st.session_state.users:
        st.warning("Username already exists. Choose another.")
        return False
    st.session_state.users[username] = hash_password(password)
    st.success("Sign up successful — you can now log in.")
    return True


def login(username: str, password: str):
    if username not in st.session_state.users:
        st.error("No such user. Please sign up first.")
        return False
    if st.session_state.users[username] != hash_password(password):
        st.error("Incorrect password.")
        return False
    st.session_state.current_user = username
    st.success(f"Logged in as {username}")
    return True


def logout():
    st.session_state.current_user = None
    st.experimental_rerun()

# ---------------------------
# Layout: top-left hamburger + main content
# ---------------------------

# Top bar with hamburger on the left and logout on the right
top_cols = st.columns([0.5, 9, 1])
with top_cols[0]:
    if st.button("☰", key="hamburger"):
        # toggle show_panel
        st.session_state.show_panel = not st.session_state.show_panel

with top_cols[2]:
    if st.session_state.current_user:
        if st.button("Logout", key="logout_btn"):
            logout()

# If not logged in, show sign up / login page
if not st.session_state.current_user:
    st.title("Welcome — please Sign Up or Log In")
    st.write("This demo stores user accounts in session state only (temporary).")

    auth_tabs = st.tabs(["Log in", "Sign up"])

    with auth_tabs[0]:
        with st.form("login_form"):
            uname = st.text_input("Username", key="login_uname")
            pwd = st.text_input("Password", type="password", key="login_pwd")
            submitted = st.form_submit_button("Log in")
            if submitted:
                login(uname.strip(), pwd)

    with auth_tabs[1]:
        with st.form("signup_form"):
            uname2 = st.text_input("Choose a username", key="signup_uname")
            pwd2 = st.text_input("Choose a password", type="password", key="signup_pwd")
            submitted2 = st.form_submit_button("Sign up")
            if submitted2:
                if signup(uname2.strip(), pwd2):
                    # optionally auto-login after signup
                    st.info("You can switch to Log in tab to sign in.")

    st.stop()

# ---------------------------
# Logged-in main app
# ---------------------------

st.title(f"📝 To-Do List — {st.session_state.current_user}")
st.write("Enter tasks with a deadline (date + optional time). Use Undo / Redo.")

# Sidebar / panel for showing tasks when hamburger toggled
if st.session_state.show_panel:
    # using sidebar to appear on the left; user wanted left-up side
    st.sidebar.title("Your tasks")
    if not st.session_state.todo.tasks:
        st.sidebar.write("No tasks yet.")
    else:
        for i, t in enumerate(st.session_state.todo.tasks):
            dl = t['deadline']
            dl_str = dl.strftime('%Y-%m-%d %H:%M') if dl else 'No deadline'
            st.sidebar.write(f"{i+1}. {t['text']} — {dl_str}")

# Add task form
with st.form("add_task_form", clear_on_submit=False):
    task_text = st.text_input("Enter your task", key="task_text")
    col_date, col_time = st.columns(2)
    with col_date:
        task_date = st.date_input("Deadline date (optional)", value=None)
    with col_time:
        task_time = st.time_input("Deadline time (optional)", value=None)

    submitted_task = st.form_submit_button("Add Task")
    if submitted_task and task_text.strip():
        # combine date and time if provided; if both None -> deadline None
        deadline = None
        # streamlit date_input and time_input cannot return None by default; handle default
        try:
            # If user didn't change, Streamlit sets today's date/time; we want optional.
            # We'll treat the presence of text in task_date_input to mean user wants deadline.
            # To keep things simple: if user chooses a date (any value) we use it; otherwise None.
            if isinstance(task_date, date):
                # if user set date, use it; if not — task_date will be today (but we cannot detect easily)
                # We'll provide a checkbox to let user specify whether they want a deadline.
                pass
        except Exception:
            pass

# Better UX: ask explicitly if they want a deadline
with st.form("add_task_with_deadline", clear_on_submit=True):
    t_text = st.text_input("Task (required)", key="task_text2")
    want_deadline = st.checkbox("Add a deadline?", key="want_deadline")
    dl_date = None
    dl_time = None
    if want_deadline:
        dl_date = st.date_input("Deadline date", key="dl_date")
        dl_time = st.time_input("Deadline time", key="dl_time")
    add_pressed = st.form_submit_button("Add")
    if add_pressed and t_text.strip():
        deadline_dt = None
        if want_deadline and dl_date:
            # combine date and time (if time not set, default midnight)
            if isinstance(dl_time, time):
                deadline_dt = datetime.combine(dl_date, dl_time)
            else:
                deadline_dt = datetime.combine(dl_date, time(0, 0))
        st.session_state.todo.add_task(t_text.strip(), deadline_dt)
        st.success("Task added")

# Undo / Redo / Clear buttons
cols = st.columns([1,1,1,6])
with cols[0]:
    if st.button("Undo", key="undo_btn_main"):
        st.session_state.todo.undo()
with cols[1]:
    if st.button("Redo", key="redo_btn_main"):
        st.session_state.todo.redo()
with cols[2]:
    if st.button("Clear all", key="clear_all_main"):
        st.session_state.todo.clear()

# Show tasks in main area with delete option and deadline display
st.subheader("Tasks")
if not st.session_state.todo.tasks:
    st.info("No tasks. Add a task above.")
else:
    for idx, item in enumerate(st.session_state.todo.tasks):
     dl = item['deadline']
     dl = item['deadline']
     dl_str = dl.strftime('%Y-%m-%d %H:%M') if dl else 'No deadline'
    row_cols = st.columns([8,1])
    with row_cols[0]:
        st.markdown(f"""
        **{idx+1}. {item['text']}**  
        _Deadline:_ {dl_str}
        """)
    with row_cols[1]:
        if st.button("Delete", key=f"del_{idx}"):
            st.session_state.todo.remove_task(idx)
            st.experimental_rerun()

# small footer showing undo/redo availability
can_undo = bool(st.session_state.todo._undo_stack)
can_redo = bool(st.session_state.todo._redo_stack)
st.write(f"Undo available: {can_undo} - Redo available: {can_redo}")

# End of file


