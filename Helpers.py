import threading


# https://www.kite.com/python/examples/4023/threading-wait-for-either-of-two-events-to-be-set
# Define versions of set and clear that trigger a "change" callback
def or_set(self):
    self._set()
    self.changed()

def or_clear(self):
    self._clear()
    self.changed()

# Make sets and clears trigger a "changed" callback that notifies an OrEvent
# of a change. Copy original "set" and "clear" so they can still be called.
def orify(event, changed_callback):
    event._set = event.set
    event._clear = event.clear
    event.changed = changed_callback
    event.set = lambda: or_set(event)
    event.clear = lambda: or_clear(event)

# Create a unified OrEvent from a list of regular events
def OrEvent(*events):
    or_event = threading.Event()
    # any time a constituent event is set or cleared, update this one
    def changed():
        bools = [event.is_set() for event in events]
        if any(bools):
            or_event.set()
        else:
            or_event.clear()
    for event in events:
        orify(event, changed)

    # initialize
    changed()
    return or_event