from enum import Enum
from Database import Database
from Database import Device as DeviceDB

class DeviceType(Enum):
    WINDOW_OPENER   = 0
    AIR_CONDITIONER = 1
    # ...

class Device:
    def __init__(self, id : int, id_room_group : int, name : str, type : DeviceType, data : dict, db : Database = None) -> None:
        self._id            = id
        self._id_room_group = id_room_group
        self._name          = name
        self._type          = type
        self._data          = data
        self._db            = db
    
    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def type(self) -> DeviceType:
        return self._type

    @property
    def data(self) -> dict:
        return self._data

    def convert_to(self, new_type: DeviceType):
        if new_type == DeviceType.WINDOW_OPENER:
            return DeviceWindowOpener(self._id, self._id_room_group, self._name, self._data.get("state", False))
        else:
            raise ValueError(f"Can't convert {self._type} to {new_type}!")
    
    def convert_to_general(self):
        pass

class DeviceWindowOpener(Device):    
    def __init__(self, device : DeviceDB = None, id : int = None, id_room_group : int = None, name : str = None, state : bool = False, db : Database = None) -> None:
        if (not id or not id_room_group or not name):
            if not device:
                raise ValueError("Invalid arguments!")
            
            id            = device.id_device
            id_room_group = device.id_room_group
            name          = device.id_room_group_name
            
        super().__init__(id, id_room_group, name, DeviceType.WINDOW_OPENER, None, db)
        self._state = state
    
    def convert_to_general(self):
        return Device(self._id, self._id_room_group, self._name, self._type, {"state": self._state})
    
    @property
    def state(self) -> bool:
        return self._state
    
    @state.setter
    def state(self, new_state : bool):
        try:
            if self._state == new_state:
                return
            
            # send command to device
            # ...
            
            self._state = new_state
            if not self._db is None:
                with self._db.get_session() as session:
                    if new_state:
                        self._db.add_window_opening_record_open(session, self._id)
                    else:
                        self._db.add_window_opening_record_close(session, self._id)
        except Exception as e:
            # exception handling
            pass

