# This script uses the JSON output from dump1090.
import geopy.distance
import json
import time
import traceback#

from pyfis.aegmis import MIS1Board
from pyfis.utils import TcpSerialPort

# Includes the following secret values: HOME_LAT, HOME_LON
from secret_settings import *


REFRESH_INTERVAL = 5
FILE_PATH = "/tmp/aircraft.json"
BOARD_IP = "192.168.0.222"
BOARD_PORT = 4223
BOARD_ADDR = 1
BOARD_ROWS = 24
BOARD_COLS = 60

old_lines = [""] * BOARD_ROWS


def display_clear(board):
    for row in range(BOARD_ROWS):
        # TODO: Use the proper delete command
        board.write_row(0, row, 0, " " * BOARD_COLS)
        board.set_blinker(row, 0)
    board.update_blinkers()

def display_header(board):
    print("ID     FLIGHT   SQWK SPD HDG ALT   RATE   DIST  ")
    print("-" * BOARD_COLS)
    board.write_row(0, 0, 0, "ID     FLIGHT   SQWK SPD HDG ALT   RATE   DIST  ")
    board.write_row(0, 1, 0, "-" * BOARD_COLS)

def display_aircraft(board, row, data):
    # Skip if last seen too long ago
    if data['seen'] > 60 * 3:
        return
    
    icao_id = data.get('hex', "").strip().upper()
    flight = data.get('flight', "").strip().upper()
    squawk = data.get('squawk', "").strip().upper()
    airspeed = str(data['tas']) if 'tas' in data else "" # kt
    heading = "{:03d}".format(round(data['mag_heading'])) if 'mag_heading' in data else ""
    altitude = str(data['alt_baro']) if 'alt_baro' in data else "" # ft
    vertical_speed = str(data['baro_rate']) if 'baro_rate' in data else "" # ft/min
    
    if 'lat' in data and 'lon' in data:
        distance = str(round(geopy.distance.geodesic((HOME_LAT, HOME_LON), (data['lat'], data['lon'])).m))
    else:
        distance = ""
    
    line = f"{icao_id: <6} {flight: <8} {squawk: <4} {airspeed: >3} {heading: >3} {altitude: >5} {vertical_speed: >5} {distance: >6}"
    if line.strip() == "":
        return False
    
    print(line)
    board.write_row(0, row, 0, line)
    old_lines[row] = line
    return True

def display_data(board, data):
    row = 2
    for aircraft in sorted(data['aircraft'], key=lambda ac: ac['hex']):
        if row > BOARD_ROWS:
            break
        if display_aircraft(board, row, aircraft):
            row += 1
    for _row in range(row, BOARD_ROWS):
        if old_lines[_row] != "":
            # Delete line
            # TODO: Use the proper delete command
            board.write_row(0, _row, 0, " " * BOARD_COLS)
            old_lines[_row] = ""

def main():
    port = TcpSerialPort(BOARD_IP, BOARD_PORT)
    board = MIS1Board(port, start_address=BOARD_ADDR, num_rows=BOARD_ROWS, rows_per_gcu=8, baudrate=115200, debug=False)
    last_update = 0.0
    
    display_clear(board)
    display_header(board)
    board.show_page(0)
    
    while True:
        try:
            if time.time() - last_update >= REFRESH_INTERVAL:
                with open(FILE_PATH, 'r') as f:
                    data = json.load(f)
                display_data(board, data)
                last_update = time.time()
            else:
                time.sleep(0.1)
        except KeyboardInterrupt:
            return
        except:
            traceback.print_exc()
            last_update = time.time()


if __name__ == "__main__":
    main()