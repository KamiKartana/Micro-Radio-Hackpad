# hackpad_windows_with_song.py
import asyncio
import serial
import time
from threading import Thread
from pynput.keyboard import Controller, Key
from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as Manager
from winrt.windows.media.control import GlobalSystemMediaTransportControlsSession
from winrt.windows.foundation import TypedEventHandler

SERIAL_PORT = "COM5"   # <- change this to your XIAO COM port
BAUD = 115200
POLL_INTERVAL = 1.0    # seconds between song checks

keyboard = Controller()

# media actions (same as before)
def send_next_track():
    print("Next Track")
    keyboard.press(Key.media_next)
    keyboard.release(Key.media_next)

def send_prev_track():
    print("Previous Track")
    keyboard.press(Key.media_previous)
    keyboard.release(Key.media_previous)

def send_vol_up():
    print("Volume Up")
    keyboard.press(Key.media_volume_up)
    keyboard.release(Key.media_volume_up)

def send_vol_down():
    print("Volume Down")
    keyboard.press(Key.media_volume_down)
    keyboard.release(Key.media_volume_down)

def send_f1():
    print("F1")
    keyboard.press(Key.f1); keyboard.release(Key.f1)

def send_f2():
    print("F2")
    keyboard.press(Key.f2); keyboard.release(Key.f2)

def send_f3():
    print("F3")
    keyboard.press(Key.f3); keyboard.release(Key.f3)

def send_f4():
    print("F4")
    keyboard.press(Key.f4); keyboard.release(Key.f4)

ACTIONS = {
    "ENC1_R": send_next_track,
    "ENC1_L": send_prev_track,
    "ENC2_R": send_vol_up,
    "ENC2_L": send_vol_down,
    "BTN1": send_f1,
    "BTN2": send_f2,
    "BTN3": send_f3,
    "BTN4": send_f4,
}

# read serial lines from device and dispatch actions
def serial_reader_loop(ser):
    while True:
        try:
            raw = ser.readline()
            if not raw:
                continue
            try:
                line = raw.decode(errors='ignore').strip()
            except:
                continue
            if not line:
                continue
            print("Received:", line)
            if line in ACTIONS:
                ACTIONS[line]()
        except serial.SerialException as e:
            print("Serial error:", e)
            time.sleep(1)
        except Exception as e:
            print("Serial loop exception:", e)
            time.sleep(0.1)

# Use winrt to get currently playing session and its media properties
async def get_current_song_text(manager):
    # get current sessions
    sessions = manager.get_sessions()
    # choose the current session (Spotify will normally be the one with playback)
    for s in sessions:
        try:
            controls = s.get_media_properties()
            # controls.title, controls.artist
            title = controls.title or ""
            artist = controls.artist or ""
            if title or artist:
                return f"{title} - {artist}"
        except Exception:
            continue
    return ""

# Main async loop to poll song and send SONG:... commands over serial
async def song_poller(ser):
    manager = await Manager.request_async()
    last_song = ""
    while True:
        try:
            song = await get_current_song_text(manager)
            if not song:
                # no active song; optionally send placeholder or clear
                song = ""
            if song != last_song:
                last_song = song
                payload = f"SONG:{song}\n"
                try:
                    ser.write(payload.encode('utf-8'))
                    print("Sent to device:", payload.strip())
                except Exception as e:
                    print("Serial write failed:", e)
            await asyncio.sleep(POLL_INTERVAL)
        except Exception as e:
            print("Polling error:", e)
            await asyncio.sleep(1)

def start_async_loop(ser):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(song_poller(ser))

def main():
    # open serial
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD, timeout=1)
    except Exception as e:
        print(f"Failed to open {SERIAL_PORT}: {e}")
        return

    # start serial read thread (buttons/encoders)
    t = Thread(target=serial_reader_loop, args=(ser,), daemon=True)
    t.start()

    # start async song poller in main thread's event loop
    try:
        start_async_loop(ser)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
