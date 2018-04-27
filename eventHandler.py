class EventHandler:
    def __init__(self):
        self.handlers = {}

    def call(self, event, *args, **kwargs):
        if event in self.handlers:
            for h in self.handlers[event]:
                h(*args, **kwargs)

    def get(self, event):
        if event in self.handlers:
            return self.handlers[event]

    def gen(self, event, *args, **kwargs):
        if event in self.handlers:
            for h in self.handlers[event]:
                yield h(*args, **kwargs)

    def event(self, event):
        def register_handler(handler):
            if event in self.handlers:
                self.handlers[event].append(handler)
            else:
                self.handlers[event] = [handler]
            return handler

        return register_handler
