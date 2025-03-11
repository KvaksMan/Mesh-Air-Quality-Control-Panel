from Constants import DELAY_WINDOW_AUTOMATION

from Database import Database, Device, Record, WarningLevel
db : Database = Database()

# with db.get_session() as session:
#     db.save_co2_levels(
#         session,
#         [
#             { 'id' : 0, 'name' : 'Good', 'from_value' : 0, 'color' : 'green' },
#             { 'id' : 1, 'name' : 'Moderate', 'from_value' : 1000, 'color' : 'orange' },
#             { 'id' : 2, 'name' : 'Unhealthy', 'from_value' : 2000, 'color' : 'red' }
#         ]
#     )

import DeviceController

import threading
from time import sleep
def window_automation() -> None:
    while True:
        sleep(DELAY_WINDOW_AUTOMATION)
        automatic_window_opening_data = {
            'status'       : db.get_setting_value('automatic_window_opening_status'),
            'on_co2_level' : db.get_setting_value('automatic_window_opening_open_on_co2_level')
        }
        if not automatic_window_opening_data['status']:
            continue
        devices  : list[Device] = db.get_all_devices()
        co2level : WarningLevel     = db.get_warning_level_by_id(automatic_window_opening_data['on_co2_level'])
        
        for device in devices:
            dwo : DeviceController.Device = DeviceController.DeviceWindowOpener(
                    device=device,
                    db=db
                )
            dwo.state = co2level.from_value <= device.co2

thread_window_automation = threading.Thread(target=window_automation)
thread_window_automation.start()

from flask import Flask, render_template, jsonify, request, redirect, url_for

app = Flask(__name__)
# app.json_encoder = CustomJSONEncoder

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/settings')
def settings():
    co2levels = [co2_level.to_dict() for co2_level in db.get_co2_levels()]
    automatic_window_opening_data = {
        'status'       : db.get_setting_value('automatic_window_opening_status'),
        'on_co2_level' : db.get_setting_value('automatic_window_opening_open_on_co2_level')
    }
    try:
        automatic_window_opening_data['on_co2_level'] = int(automatic_window_opening_data['on_co2_level'])
    except:
        pass
    print('automatic_window_opening_data', automatic_window_opening_data)
    return render_template('settings.html', co2levels=co2levels, automatic_window_opening_data=automatic_window_opening_data)

@app.route('/settings/set/co2levels', methods=['POST'])
def settings_set_co2levels():
    print(request.form)
    for co2_level, value in request.form.items():
        db.set_co2_level_value(co2_level, value)
    return redirect(url_for('settings'))

@app.route('/settings/set/automatic_window_opening', methods=['POST'])
def settings_set_automatic_window_opening():
    automatic_window_opening_status            = request.form.get('automatic_window_opening_status') == 'on'
    automatic_window_opening_open_on_co2_level = request.form.get('automatic_window_opening_open_on_co2_level')
    
    db.set_setting_value('automatic_window_opening_status', automatic_window_opening_status)
    db.set_setting_value('automatic_window_opening_open_on_co2_level', automatic_window_opening_open_on_co2_level)
    
    return redirect(url_for('settings'))

@app.route('/device/<device_id>')
def device(device_id):
    device = db.get_device_by_id(device_id).to_dict()
    
    automatic_window_opening_data = {
        'status'       : db.get_setting_value('automatic_window_opening_status'),
        'on_co2_level' : db.get_setting_value('automatic_window_opening_open_on_co2_level')
    }
    
    return render_template('device.html', device=device, automatic_window_opening_data=automatic_window_opening_data)

# @app.route('/api/devices/<device_id>')
# def devices(device_id):
#     if device_id == 'get':
#         db.fetch_devices()
#         devices = db.get_all_devices()
#         return jsonify([device.to_dict() for device in devices])

#     try:
#         device_id = int(device_id)
#     except:
#         return "Device ID must be an integer.", 400
    
#     records = db.get_records_by_device(device_id)
#     return jsonify([record.to_dict() for record in records])

@app.route('/api/devices/<device_id>', methods=['GET'])
def devices(device_id):
    if device_id == 'get':
        db.fetch_devices()
        devices_with_state = db.get_devices_with_window_state()
        return jsonify([
            {**device.to_dict(), "window_open": window_open} 
            for device, window_open in devices_with_state
        ])

    try:
        device_id = int(device_id)
    except ValueError:
        return jsonify({"error": "Device ID must be an integer."}), 400

    records = db.get_records_by_device(device_id)
    return jsonify([record.to_dict() for record in records])

@app.route('/api/co2levels/get')
def co2levels_get():
    co2_levels = db.get_co2_levels()
    print(co2_levels)
    return jsonify([co2_level.to_dict() for co2_level in co2_levels])

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