class ToDoStack:
    def __init__(self):
        self.tasks = []
        self.undo_stack = []
        self.redo_stack = []

    def add_task(self, task):
        self.undo_stack.append(list(self.tasks))
        self.tasks.append(task)
        self.redo_stack.clear()

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(list(self.tasks))
            self.tasks = self.undo_stack.pop()

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(list(self.tasks))
            self.tasks = self.redo_stack.pop()