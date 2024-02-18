import requests

from homeassistant_api import Client
from pyfis.aegmis import MIS1Board
from pyfis.utils import TcpSerialPort

from fra_arrivals import display_fra_arrivals
from secret_settings import *


def main():
    port = TcpSerialPort(BOARD_IP, 4223)
    board = MIS1Board(port, start_address=1, num_rows=24, rows_per_gcu=8, baudrate=115200, debug=True)
    hass = Client(HASS_API_URL, HASS_TOKEN)
    fixed_text_bool = hass.get_state(entity_id=HASS_FIXED_TEXT_INPUT_BOOLEAN_ID)
    if fixed_text_bool.state == "on":
        fixed_text_url = hass.get_state(entity_id=HASS_FIXED_TEXT_URL_INPUT_TEXT_ID).state
        resp = requests.get(fixed_text_url)
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP status code {resp.status_code}")
        board.write_text(page=0, start_row=0, start_col=0, text=resp.text.upper())
        board.show_page(0)
        for row in range(24):
            board.set_blinker(row, 0)
        board.update_blinkers()
    else:
        display_fra_arrivals(board)


if __name__ == "__main__":
    main()