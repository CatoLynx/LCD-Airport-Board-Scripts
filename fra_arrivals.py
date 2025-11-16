import datetime

from pyfis.data_sources import FraportAPI
from unidecode import unidecode


MODE = "LIST"
#MODE = "DETAIL"


status_map = {
    #"": "UNTERWEGS",
    "Gepäckausgabe": "Gepaeck",
    "Gepäckausgabe beendet": "Gepaeck Ende",
    "verspäteter Abflug": "Versp. Abflug",
}

landed_statuses = [
    "gelandet",
    "auf Position",
    "Gepäckausgabe",
    "Gepäckausgabe beendet"
]

def prepare_text(text):
    text = text.upper()
    text = text.replace("Ä", "AE")
    text = text.replace("Ö", "OE")
    text = text.replace("Ü", "UE")
    text = unidecode(text).upper()
    return text


def format_row(flight):
    fl_num_parts = flight['flight_number'].split()
    ap_name = prepare_text(flight['airport_name'])
    sched_arr = flight['scheduled_arrival'].strftime('%H:%M') if flight['scheduled_arrival'] else ""
    est_arr = flight['estimated_arrival'].strftime('%H:%M') if flight['estimated_arrival'] else ""
    terminal = flight['terminal']
    #print(flight['status'])
    status = prepare_text(status_map.get(flight['status'], flight['status']))
    return f"{fl_num_parts[0]:<3.3} {fl_num_parts[1]:<5.5} {ap_name:<20.20} {sched_arr:<5.5} {est_arr:<5.5} T{terminal:<1.1} {status:<14.14}"


def format_detail(flight):
    lines = []
    lines.append(format_row(flight))
    lines.append("")
    
    fl_num_line = f"FLUG:     {flight['flight_number']}"
    airline_name_len = 60 - (len(fl_num_line) + 1)
    airline_name = prepare_text(flight['airline_name'])
    airline_name = airline_name[:airline_name_len].rjust(airline_name_len)
    fl_num_line += " " + airline_name
    lines.append(fl_num_line)
    
    ap_name = prepare_text(flight['airport_name'])
    lines.append(f"VON:      {ap_name} ({flight['airport_iata']})")
    
    sched_dep = flight['scheduled_departure'].strftime('%H:%M') if flight['scheduled_departure'] else ""
    lines.append(f"ABFLUG:   {sched_dep}")
    
    sched_arr = flight['scheduled_arrival'].strftime('%H:%M') if flight['scheduled_arrival'] else ""
    est_arr = flight['estimated_arrival'].strftime('%H:%M') if flight['estimated_arrival'] else ""
    arr_line = f"ANKUNFT:  {sched_arr}"
    if est_arr:
        arr_line += f" (HEUTE {est_arr})"
    lines.append(arr_line)
    
    lines.append(f"          TERMINAL {flight['terminal']}")
    lines.append(f"          HALLE    {flight['hall']}")
    lines.append(f"          AUSGANG  {flight['exit']}")
    lines.append(f"FLUGZEUG: {flight['aircraft_registration']} ({flight['aircraft_icao']})")
    
    hours = flight['duration'].seconds // 3600
    minutes = (flight['duration'].seconds - (hours * 3600)) // 60
    duration_line = f"FLUGZEIT:"
    if hours:
        duration_line += f" {hours} STUNDE"
        if hours != 1:
            duration_line += "N"
    if minutes:
        duration_line += f" {minutes} MINUTE"
        if minutes != 1:
            duration_line += "N"
    lines.append(duration_line)
    
    status = prepare_text(status_map.get(flight['status'], flight['status']))
    lines.append(f"STATUS:   {status}")
    
    lines.append("")
    lines.append("CODESHARES:")
    
    if not flight['codeshares']:
        lines.append("KEINE")
    else:
        for cs in flight['codeshares'][:10]:
            cs_parts = cs.split()
            lines.append(f"{cs_parts[0]:<3.3} {cs_parts[1]:<5.5}")
    
    lines.extend([""] * (24 - len(lines)))
    return "\n".join(lines)


def display_fra_arrivals(board):
    api = FraportAPI()
    ts = datetime.datetime.utcnow() - datetime.timedelta(minutes=30)

    flights = []
    counter = 0
    while len(flights) < 24 and counter < 3:
        new_flights = api.get_flights(flight_type='arrivals', count=24, lang='de', page=counter+1, timestamp=ts)['flights']
        flights.extend([flight for flight in new_flights if flight['status'] != "Zug"])
        counter += 1

    if MODE == "LIST":
        for row, f in enumerate(flights[:24]):
            #print(format_row(f))
            board.write_row(0, row, 0, format_row(f))
        board.show_page(0)

        for row, f in enumerate(flights[:24]):
            if f['status'] in landed_statuses:
                #print("B ", end="")
                board.set_blinker(row, True)
            else:
                #print("  ", end="")
                board.set_blinker(row, False)
        board.update_blinkers()
    elif MODE == "DETAIL":
        flight = [f for f in flights if f['status'] not in landed_statuses][0]
        detail = format_detail(flight)
        lines = detail.splitlines()
        lines.extend([""] * (24 - len(lines)))
        for row, line in enumerate(lines):
            board.write_row(0, row, 0, line)
        board.set_blinker(0, flight['status'] in landed_statuses)
        board.update_blinkers()
        #print(detail)
