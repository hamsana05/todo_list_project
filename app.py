import streamlit as st
from todo_stack import ToDoStack

# Initialize session state
if 'todo' not in st.session_state:
    st.session_state.todo = ToDoStack()

st.title("📝 Simple To-Do List hamsana with Undo/Redo")

task_input = st.text_input("Enter a task")
if st.button("Add Task") and task_input:
    st.session_state.todo.add_task(task_input)

col1, col2 = st.columns(2)
with col1:
    if st.button("Undo"):
        st.session_state.todo.undo()
with col2:
    if st.button("Redo"):
        st.session_state.todo.redo()

st.subheader("Tasks:")
for i, task in enumerate(st.session_state.todo.tasks):
    st.write(f"{i+1}. {task}")