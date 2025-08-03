import csv

# Board,Net,Component,Designator,Connector Name,,
# a_box,GND,P6,1,BMS,,

class NetMapEntry:
    def __init__(self, board: str, net: str, component: str, designator: int, connector_name: str):
        self.board = board
        self.net = net
        self.component = component
        self.designator = designator
        self.connector_name = connector_name

class NetMap:
    def __init__(self, entries: list[NetMapEntry]):
        self.entries = entries

    def get_entry(self, board: str, net: str) -> NetMapEntry:
        for entry in self.entries:
            if entry.board == board and entry.net == net:
                return entry
        raise ValueError(f"No entry found for board '{board}' and net '{net}'")

    @classmethod
    def from_csv(cls, file_path: str) -> 'NetMap':
        entries = []
        with open(file_path, newline='', encoding='utf-8') as net_map_file:
            reader = csv.DictReader(net_map_file)
            for row in reader:
                entry = NetMapEntry(
                    board=row['Board'],
                    net=row['Net'],
                    component=row['Component'],
                    designator=int(row['Designator']),
                    connector_name=row['Connector Name']
                )
                entries.append(entry)
        return cls(entries)

