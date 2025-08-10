import csv

import board_net


class NetMapEntry:
    def __init__(self,
        board: str,
        net: str,
        component: str,
        designator: int,
        connector_name: str
    ):
        self.board = board
        self.net = net
        self.component = component
        self.designator = designator
        self.connector_name = connector_name


class NetMap:
    def __init__(self, entries: dict[board_net.BoardNet, NetMapEntry]):
        self._entries: dict[board_net.BoardNet, NetMapEntry] = entries

    def get_entry(self, board: str, net: str) -> NetMapEntry:
        board_net = board_net.BoardNet(board, net)
        return self._entries[board_net]

    @classmethod
    def from_csv(cls, file_path: str) -> 'NetMap':
        entries = {}
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
                board_net = board_net.BoardNet(entry.board, entry.net)
                entries[board_net] = entry
        return cls(entries)

