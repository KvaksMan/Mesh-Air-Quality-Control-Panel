from Constants import DELAY_DATABASE_UPDATE

import logging
import os
import requests
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, joinedload
from sqlalchemy.sql import func
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
# from json import JSONEncoder

Base : declarative_base = declarative_base()

class Device(Base):
    __tablename__ : str = 'Devices'

    id_device          : int        = Column(Integer, primary_key=True)
    id_room_group      : int        = Column(Integer)
    id_room_group_name : str        = Column(String)
    temperature        : float      = Column(Float)
    humidity           : int        = Column(Integer)
    co2                : int        = Column(Integer)
    id_building        : int        = Column(Integer)
    online             : bool       = Column(Boolean)
    timestamp          : DateTime   = Column(DateTime)
    last_updated       : DateTime   = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id_device"          : self.id_device,
            "id_room_group"      : self.id_room_group,
            "id_room_group_name" : self.id_room_group_name,
            "temperature"        : self.temperature,
            "humidity"           : self.humidity,
            "co2"                : self.co2,
            "id_building"        : self.id_building,
            "online"             : self.online,
            "timestamp"          : self.timestamp.isoformat() if self.timestamp else None,
            "last_updated"       : self.last_updated.isoformat() if self.last_updated else None
        }

class Record(Base):
    __tablename__      : str        = 'Records'

    id_record          : int        = Column(Integer, primary_key=True)
    id_device          : int        = Column(Integer)
    temperature        : float      = Column(Float)
    humidity           : int        = Column(Integer)
    co2                : int        = Column(Integer)
    timestamp          : DateTime   = Column(DateTime)
    last_updated       : DateTime   = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id_record"    : self.id_record,
            "id_device"    : self.id_device,
            "temperature"  : self.temperature,
            "humidity"     : self.humidity,
            "co2"          : self.co2,
            "timestamp"    : self.timestamp.isoformat() if self.timestamp else None,
            "last_updated" : self.last_updated.isoformat() if self.last_updated else None
        }

class WarningLevel(Base):
    __tablename__ : str = 'WarningLevels'
    
    id_warning_level : int = Column(Integer, primary_key=True)
    type             : str = Column(String)
    name             : str = Column(String)
    from_value       : int = Column(Integer)
    color            : str = Column(String)
    
    def to_dict(self):
        return {
            "id_warning_level" : self.id_warning_level,
            "type"             : self.type,
            "name"             : self.name,
            "from_value"       : self.from_value,
            "color"            : self.color
        }

class WindowOpeningHistory(Base):
    __tablename__ : str = 'WindowOpeningHistory'
    
    id_window_opening_history : int = Column(Integer, primary_key=True)
    id_device                 : int = Column(Integer)
    timestamp_open            : DateTime = Column(DateTime)
    timestamp_close           : DateTime = Column(DateTime)
    last_updated              : DateTime = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id_window_opening_history" : self.id_window_opening_history,
            "id_device"                 : self.id_device,
            "timestamp_open"            : self.timestamp_open.isoformat() if self.timestamp_open else None,
            "timestamp_close"           : self.timestamp_close.isoformat() if self.timestamp_close else None,
            "last_updated"              : self.last_updated.isoformat() if self.last_updated else None,
            "open_duration"             : (self.timestamp_close - self.timestamp_open).total_seconds() if self.timestamp_close else None,
            "is_open"                   : self.timestamp_close is None
        }

class Settings(Base):
    __tablename__ : str = 'Settings'

    id_setting : int = Column(Integer, primary_key=True)
    name       : str = Column(String)
    value      : str = Column(String)
    last_updated : DateTime = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id_setting" : self.id_setting,
            "name"       : self.name,
            "value"      : self.value,
            "last_updated" : self.last_updated.isoformat() if self.last_updated else None,
        }

class Database:
    def __init__(self, db_url="sqlite:///mesh_air_quality.db") -> None:
        self.engine : object = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal : sessionmaker = sessionmaker(bind=self.engine)
        self._setup_logger()

    def _setup_logger(self) -> None:
        log_dir : str = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        self.logger : logging.Logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        console_handler : logging.StreamHandler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter : logging.Formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)

        file_handler : TimedRotatingFileHandler = TimedRotatingFileHandler(os.path.join(log_dir, 'app.log'), when='H', interval=1, backupCount=24)
        file_handler.setLevel(logging.DEBUG)
        file_formatter : logging.Formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def get_session(self) -> Session:
        return self.SessionLocal()
    
    def fetch_devices(self) -> list:
        url  : str  = "https://co2.mesh.lv/api/device/list"
        data : dict = {"buildingId": "640", "captchaToken": None}
        self.logger.info(f"Sending request to {url} with data: {data}")
        response : requests.Response = requests.post(url, json=data)
        
        if response.status_code == 200:
            devices : dict = response.json()
            self.logger.info(f"Received {len(devices)} devices.")
            with self.get_session() as session:
                for device in devices:
                    self.save_device(session, device)
        else:
            self.logger.error(f"Error while fetching devices: {response.status_code}")
            return []

    def fetch_device_data(self, device_id) -> dict:
        url  : str  = "https://co2.mesh.lv/api/device/chart/"
        data : dict = {"deviceId": device_id, "week": 1, "captchaToken": "-1"}
        self.logger.info(f"Sending request to {url} for device {device_id} with data: {data}")
        response : requests.Response = requests.post(url, json=data)
        
        if response.status_code == 200:
            device_data : dict = response.json()
            self.logger.info(f"Received data for device {device_id}.")
            with self.get_session() as session:
                self.save_records(session, device_data)
        else:
            self.logger.error(f"Error while fetching data for device {device_id}: {response.status_code}")
            return {}

    def save_co2_levels(self, session : Session, co2_levels : list[dict]) -> None:
        for co2_level in co2_levels:
            existing_co2_level : object = session.query(WarningLevel).filter(WarningLevel.id_warning_level == co2_level['id']).first()
            if existing_co2_level is None:
                new_co2_level : WarningLevel = WarningLevel(
                    id_warning_level = co2_level['id'],
                    type             = 'CO2',
                    name             = co2_level['name'],
                    from_value       = co2_level['from_value'],
                    color            = co2_level['color']
                )
                session.add(new_co2_level)
                self.logger.debug(f"CO2 Level {co2_level['id']} saved to the database.")
            else:
                existing_co2_level.name       = co2_level['name']
                existing_co2_level.from_value = co2_level['from_value']
                existing_co2_level.color      = co2_level['color']
                existing_co2_level.last_updated = datetime.utcnow()
                self.logger.debug(f"CO2 Level {co2_level['id']} updated in the database.")
        session.commit()
    
    def save_device(self, session : Session, device_data : dict) -> None:
        existing_device : object = session.query(Device).filter(Device.id_device == device_data['id']).first()
        if existing_device is None:
            new_device : Device = Device(
                id_device          = device_data['id'],
                id_room_group      = device_data.get('roomGroupId', None),
                id_room_group_name = device_data.get('roomGroupName', ''),
                temperature        = device_data.get('temperature', 0),
                humidity           = device_data.get('humidity', 0),
                co2                = device_data.get('co2', 0),
                id_building        = device_data.get('buildingId', None),
                online             = device_data.get('online', False),
                last_updated       = datetime.utcnow()
            )
            timestamp_str = device_data.get('timestamp', None)
            if timestamp_str:
                new_device.timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ")
            else:
                new_device.timestamp = None
            session.add(new_device)
            self.logger.debug(f"Device {device_data['id']} saved to the database.")
        else:
            existing_device.id_room_group      = device_data.get('roomGroupId', None)
            existing_device.id_room_group_name = device_data.get('roomGroupName', '')
            existing_device.temperature        = device_data.get('temperature', 0)
            existing_device.humidity           = device_data.get('humidity', 0)
            existing_device.co2                = device_data.get('co2', 0)
            existing_device.id_building        = device_data.get('buildingId', None)
            existing_device.online             = device_data.get('online', False)
            existing_device.last_updated       = datetime.utcnow()
            
            timestamp_str = device_data.get('timestamp', None)
            if timestamp_str:
                existing_device.timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ")
            else:
                existing_device.timestamp = None
            
            self.logger.info(f"Device {device_data['id']} updated in the database.")
        
        session.commit()
    
    def save_records(self, session : Session, device_data : dict) -> None:
        for co2, temperature, humidity, timestamp in zip(device_data['data']['co2'], device_data['data']['temperature'], device_data['data']['humidity'], device_data['data']['timestamp']):
            timestamp_dt    : datetime = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
            existing_record : object   = session.query(Record).filter(
                Record.timestamp == timestamp_dt, Record.id_device == device_data['device']['id']
            ).first()
            
            if existing_record is None:
                new_record : Record = Record(
                    id_device    = device_data['device']['id'],
                    temperature  = temperature,
                    humidity     = humidity,
                    co2          = co2,
                    timestamp    = timestamp_dt,
                    last_updated = datetime.utcnow()
                )
                session.add(new_record)
                self.logger.debug(f"Record for device {device_data['device']['id']} with timestamp {timestamp} saved.")
            else:
                self.logger.debug(f"Record for device {device_data['device']['id']} with timestamp {timestamp} already exists.")
        session.commit()
    
    def add_window_opening_record_open(self, session : Session, device_id : int) -> None:
        new_record : WindowOpeningHistory = WindowOpeningHistory(
            id_device      = device_id,
            timestamp_open = datetime.utcnow(),
            last_updated   = datetime.utcnow()
        )
        session.add(new_record)
        session.commit()
    
    def add_window_opening_record_close(self, session : Session, device_id : int) -> None:
        existing_record : object = session.query(WindowOpeningHistory).filter(
            WindowOpeningHistory.id_device == device_id, WindowOpeningHistory.timestamp_close == None
        ).first()
        if existing_record:
            existing_record.timestamp_close = datetime.utcnow()
            existing_record.last_updated = datetime.utcnow()
            session.commit()
    
    def set_setting_value(self, setting_name : str, setting_value : str) -> None:
        with self.get_session() as session:
            setting : Settings = session.query(Settings).filter(Settings.name == setting_name).first()
            if setting is None:
                new_setting : Settings = Settings(
                    name  = setting_name,
                    value = setting_value
                )
                session.add(new_setting)
                self.logger.info(f"Setting {setting_name} saved to the database (setting_value).")
            else:
                if setting.value != setting_value:
                    setting.value = setting_value
                    setting.last_updated = datetime.utcnow()
                    self.logger.info(f"Setting {setting_name} updated in the database (from {setting.value} to {setting_value}).")
            session.commit()
    
    def set_co2_level_value(self, co2_level_id : int, co2_level_value : int) -> None:
        with self.get_session() as session:
            co2_level : WarningLevel = session.query(WarningLevel).filter(WarningLevel.id_warning_level == co2_level_id).first()
            if co2_level is None:
                self.logger.error(f"CO2 Level {co2_level_id} not found in the database.")
                return
            if co2_level.from_value != co2_level_value:
                co2_level.from_value = co2_level_value
                co2_level.last_updated = datetime.utcnow()
                self.logger.info(f"CO2 Level {co2_level_id} updated in the database (from {co2_level.from_value} to {co2_level_value}).")
            session.commit()
    
    def get_all_devices(self) -> list[Device]:
        with self.get_session() as session:
            lastUpdate = session.query(Device).first().last_updated
            if (datetime.utcnow() - lastUpdate).total_seconds() > DELAY_DATABASE_UPDATE:
                self.fetch_devices()
            return session.query(Device).all()
    
    def get_device_by_id(self, device_id : int) -> Device:
        with self.get_session() as session:
            device : Device = session.query(Device).filter(Device.id_device == device_id).first()
            if device is None:
                self.fetch_devices()
                device : Device = session.query(Device).filter(Device.id_device == device_id).first()
            
            return device

    def get_records_by_device(self, device_id : int) -> Record:
        with self.get_session() as session:
            records : list = session.query(Record).filter(Record.id_device == device_id).order_by(Record.timestamp).all()            
            if len(records) == 0 or (datetime.utcnow() - records[-1].last_updated).total_seconds() > DELAY_DATABASE_UPDATE:
                self.fetch_device_data(device_id)
                records = session.query(Record).filter(Record.id_device == device_id).order_by(Record.timestamp).all()       
            return records
    
    def get_co2_levels(self) -> list[WarningLevel]:
        with self.get_session() as session:
            return session.query(WarningLevel).filter(WarningLevel.type == 'CO2').all()
    
    def get_warning_level_by_id(self, id_co2_level : int) -> WarningLevel:
        with self.get_session() as session:
            return session.query(WarningLevel).filter(WarningLevel.id_warning_level == id_co2_level).first()
    
    def get_window_opening_history(self, device_id : int) -> list[WindowOpeningHistory]:
        with self.get_session() as session:
            return session.query(WindowOpeningHistory).filter(Record.id_device == device_id).all()
    
    def get_window_opening_last_record(self, device_id : int) -> WindowOpeningHistory:
        with self.get_session() as session:
            return session.query(WindowOpeningHistory).filter(WindowOpeningHistory.id_device == device_id).first()
    
    def get_window_state(self, device_id : int) -> bool:
        with self.get_session() as session:
            record : WindowOpeningHistory = session.query(WindowOpeningHistory).filter(WindowOpeningHistory.id_device == device_id).first()
            return record.timestamp_close is None if record else False
        
    def get_setting_value(self, setting_name : str) -> str:
        with self.get_session() as session:
            setting : Settings = session.query(Settings).filter(Settings.name == setting_name).first()
            return setting.value if setting else None
    
    def get_devices_with_window_state(self) -> list[tuple[Device, bool]]:
        with self.get_session() as session:
            subquery = (
                session.query(
                    WindowOpeningHistory.id_device,
                    func.max(WindowOpeningHistory.id_window_opening_history).label("latest_id")
                )
                .group_by(WindowOpeningHistory.id_device)
                .subquery()
            )

            devices = (
                session.query(Device, WindowOpeningHistory.timestamp_close)
                .outerjoin(subquery, Device.id_device == subquery.c.id_device)
                .outerjoin(WindowOpeningHistory, WindowOpeningHistory.id_window_opening_history == subquery.c.latest_id)
                .all()
            )

            return [(device, timestamp_close is None if timestamp_close is not None else False) for device, timestamp_close in devices]