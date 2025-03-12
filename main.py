from Constants import DELAY_WINDOW_AUTOMATION

from Database import Database, Device, Record, WarningLevel
db : Database = Database()

import DeviceController

import threading
from time import sleep
def window_automation() -> None:
    while True:
        sleep(DELAY_WINDOW_AUTOMATION)
        automatic_window_opening_data = {
            'status_co2'    : int(db.get_setting_value('automatic_window_opening_status_by_co2')),
            'on_co2_level'  : int(db.get_setting_value('automatic_window_opening_open_on_co2_level')),
            'status_temp'   : int(db.get_setting_value('automatic_window_opening_status_by_temp')),
            'on_temp_level' : int(db.get_setting_value('automatic_window_opening_open_on_temp_level'))
        }

        if not automatic_window_opening_data['status_co2'] and not automatic_window_opening_data['status_temp']:
            continue
        
        devices   : list[Device] = db.get_all_devices()
        co2level  : WarningLevel = db.get_warning_level_by_id(automatic_window_opening_data['on_co2_level'])
        templevel : WarningLevel = db.get_warning_level_by_id(automatic_window_opening_data['on_temp_level'])
        
        func = None
        if automatic_window_opening_data['status_co2'] and automatic_window_opening_data['status_temp']:
            func = lambda device: co2level.from_value <= device.co2 or templevel.from_value <= device.temperature
        elif automatic_window_opening_data['status_co2']:
            func = lambda device: co2level.from_value <= device.co2
        elif automatic_window_opening_data['status_temp']:
            func = lambda device: templevel.from_value <= device.temperature
        
        for device in devices:
            dwo : DeviceController.Device = DeviceController.DeviceWindowOpener(
                    device=device,
                    db=db
                )
            dwo.state = func(device)

thread_window_automation = threading.Thread(target=window_automation)
thread_window_automation.start()

from flask import Flask, render_template, jsonify, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/settings')
def settings():
    co2levels  = [co2_level.to_dict() for co2_level in db.get_co2_levels()]
    templevels = [templevel.to_dict() for templevel in db.get_temperature_levels()]
    
    automatic_window_opening_data = {
        'status_co2'    : db.get_setting_value('automatic_window_opening_status_by_co2'),
        'on_co2_level'  : db.get_setting_value('automatic_window_opening_open_on_co2_level'),
        'status_temp'   : db.get_setting_value('automatic_window_opening_status_by_temp'),
        'on_temp_level' : db.get_setting_value('automatic_window_opening_open_on_temp_level')
    }
    try:
        automatic_window_opening_data['status_co2']    = int(automatic_window_opening_data['status_co2'])
        automatic_window_opening_data['on_co2_level']  = int(automatic_window_opening_data['on_co2_level'])
        automatic_window_opening_data['status_temp']   = int(automatic_window_opening_data['status_temp'])
        automatic_window_opening_data['on_temp_level'] = int(automatic_window_opening_data['on_temp_level'])
    except:
        pass
    return render_template('settings.html', co2levels=co2levels, templevels=templevels, automatic_window_opening_data=automatic_window_opening_data)

@app.route('/settings/set/co2levels', methods=['POST'])
def settings_set_co2levels():
    for co2_level, value in request.form.items():
        db.set_co2_level_value(co2_level, value)
    return redirect(url_for('settings'))

@app.route('/settings/set/templevels', methods=['POST'])
def settings_set_templevels():
    for templevel, value in request.form.items():
        db.set_temperature_level_value(templevel, value)
    return redirect(url_for('settings'))

@app.route('/settings/set/automatic_window_opening/<type>', methods=['POST'])
def settings_set_automatic_window_opening(type):
    automatic_window_opening_status  = request.form.get(f'automatic_window_opening_status_by_{type}') == 'on'
    automatic_window_opening_open_on = request.form.get(f'automatic_window_opening_open_on_{type}_level')
    
    db.set_setting_value(f'automatic_window_opening_status_by_{type}', automatic_window_opening_status)
    db.set_setting_value(f'automatic_window_opening_open_on_{type}_level', automatic_window_opening_open_on)
    
    return redirect(url_for('settings'))

@app.route('/device/<device_id>')
def device(device_id):
    device = db.get_device_by_id(device_id).to_dict()
    
    automatic_window_opening_data = {
        'status'       : db.get_setting_value('automatic_window_opening_status_co2'),
        'on_co2_level' : db.get_setting_value('automatic_window_opening_open_on_co2_level')
    }
    
    return render_template('device.html', device=device, automatic_window_opening_data=automatic_window_opening_data)

@app.route('/api/devices/<device_id>', methods=['GET'])
def devices(device_id):
    if device_id == 'get':
        db.fetch_devices()
        devices_with_state = db.get_devices_with_window_state()
        return jsonify(devices_with_state)

    try:
        device_id = int(device_id)
    except ValueError:
        return jsonify({"error": "Device ID must be an integer."}), 400

    records = db.get_records_by_device(device_id)
    return jsonify([record.to_dict() for record in records])

@app.route('/api/co2levels/get')
def co2levels_get():
    co2_levels = db.get_co2_levels()
    return jsonify([co2_level.to_dict() for co2_level in co2_levels])

@app.route('/api/templevels/get')
def templevels_get():
    temperature_levels = db.get_temperature_levels()
    return jsonify([temperature_level.to_dict() for temperature_level in temperature_levels])

@app.route('/api/history/window_opening/<type>/<device_id>')
def history_window_opening(type, device_id):
    try:
        device_id = int(device_id)
    except:
        return "Device ID must be an integer.", 400
    
    records = []
    if type == 'all':
        records = db.get_window_opening_history(device_id)
    elif type == 'last':
        records = [db.get_window_opening_last_record(device_id)]
    
    return jsonify([record.to_dict() for record in records])

@app.route('/api/devices/<device_id>/<action>')
def device_action(device_id, action):
    try:
        device_id = int(device_id)
    except:
        return "Device ID must be an integer.", 400
    
    cmd = action.split('_')
    
    if len(cmd) == 0:
        return "Invalid action.", 400
    
    if cmd[0] == 'window':
        if len(cmd) != 2:
            return "Invalid action.", 400
        
        device : DeviceController.Device = DeviceController.DeviceWindowOpener(
            device=db.get_device_by_id(device_id),
            db=db
        )
        
        if cmd[1] == 'open':
            device.state = True
        elif cmd[1] == 'close':
            device.state = False
        else:
            return "Invalid action.", 400
        
        return 'OK'

if __name__ == '__main__':
    app.run()