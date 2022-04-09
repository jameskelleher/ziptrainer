import termios, fcntl, sys, os, time, sched

from enum import Enum

# config globals - feel free to change
INPUT_DELAY_SEC = 3
INPUT_WINDOW_SEC = 1
FPS = 60

# nonconfig globals, used to help other functions
GAME_STATE = None
TIME_START_SEC = None
MAX_STR = 0


class State(Enum):
    STANDBY = 1
    TIMING = 2
    GAME_OVER = 3


def set_game_state(state):
    global GAME_STATE
    GAME_STATE = state


def get_game_state():
    global GAME_STATE
    return GAME_STATE


def handle_standby(key):
    if trigger_key_detected(key):
        start_new_game()


def handle_timing(key):
    global TIME_START_SEC
    global INPUT_DELAY_SEC
    global INPUT_WINDOW_SEC

    time_elapsed = time.time() - TIME_START_SEC
    time_left = INPUT_DELAY_SEC - time_elapsed

    if time_elapsed < INPUT_DELAY_SEC:
        pr("%.2f" % time_left)

        if trigger_key_detected(key):
            pr("Too early!")
            set_game_state(State.STANDBY)

    elif time_elapsed < INPUT_DELAY_SEC + INPUT_WINDOW_SEC:
        pr("Now!")

        if trigger_key_detected(key):
            pr("Perfect!")
            set_game_state(State.GAME_OVER)

    else:
        pr("You were too slow!")
        set_game_state(State.GAME_OVER)


def handle_game_over(key):
    if trigger_key_detected(key):
        start_new_game()


def start_new_game():
    global TIME_START_SEC

    TIME_START_SEC = time.time()
    set_game_state(State.TIMING)


def trigger_key_detected(key):
    try:
        return key.upper() == "W"
    except:
        return False


def handle_input(scheduler):
    game_state = get_game_state()
    key = sys.stdin.read(1)

    if game_state == State.STANDBY:
        handle_standby(key)
    elif game_state == State.TIMING:
        handle_timing(key)
    elif game_state == State.GAME_OVER:
        handle_game_over(key)
    else:
        raise ValueError("unknown game state detected")

    scheduler.enter(1.0 / FPS, 1, handle_input, (scheduler,))


def pr(str_):
    global MAX_STR

    MAX_STR = max(MAX_STR, len(str_))
    diff = MAX_STR - len(str_)
    str_ += " " * diff
    print("\r" + str_, end="")


def main():
    set_game_state(State.STANDBY)
    pr("press W to start")

    fd = sys.stdin.fileno()

    oldterm = termios.tcgetattr(fd)
    newattr = termios.tcgetattr(fd)
    newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, newattr)

    oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

    scheduler = sched.scheduler(time.time, time.sleep)

    scheduler.enter(1.0 / FPS, 1, handle_input, (scheduler,))
    scheduler.run()

    termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)


main()
