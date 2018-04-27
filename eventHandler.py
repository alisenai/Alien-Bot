handlers = {}


def call(event, *args, **kwargs):
    if event in handlers:
        for h in handlers[event]:
            h(*args, **kwargs)


def get(event):
    if event in handlers:
        return handlers[event]


def gen(event, *args, **kwargs):
    if event in handlers:
        for h in handlers[event]:
            yield h(*args, **kwargs)


def event(event):
    def register_handler(handler):
        if event in handlers:
            handlers[event].append(handler)
        else:
            handlers[event] = [handler]
        return handler

    return register_handler