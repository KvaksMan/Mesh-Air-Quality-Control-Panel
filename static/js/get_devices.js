{/* <tr>
    <th>Device ID</th>
    <th>Location</th>
    <th>Status</th>
    <th>Temperature</th>
    <th>Humidity</th>
    <th>CO2</th>
    <th>Last updated</th>
</tr> */}

// {
//     "id_device"          : self.id_device,
//     "id_room_group"      : self.id_room_group,
//     "id_room_group_name" : self.id_room_group_name,
//     "temperature"        : self.temperature,
//     "humidity"           : self.humidity,
//     "co2"                : self.co2,
//     "id_building"        : self.id_building,
//     "online"             : self.online,
//     "timestamp"          : self.timestamp.isoformat() if self.timestamp else None,
//     "last_updated"       : self.last_updated.isoformat() if self.last_updated else None,
// }
function get_devices() {
    fetch('/api/devices/get')
        .then(response => response.json())
        .then(data => {
            const table_devices = document.getElementById("table_devices");

            fetch('/api/co2levels/get')
                .then(response => response.json())
                .then(data_co2 => {
                    data.forEach(element => {
                        let row               = table_devices.insertRow(-1);
                        let cell_device_id    = row.insertCell(0);
                        let cell_location     = row.insertCell(1);
                        let cell_status       = row.insertCell(2);
                        let cell_temperature  = row.insertCell(3);
                        let cell_humidity     = row.insertCell(4);
                        let cell_co2          = row.insertCell(5);
                        let cell_last_updated = row.insertCell(6);
                        let cell_window       = row.insertCell(7);
                        
                        cell_device_id.innerHTML    = `<a href="${'/device/' + element.id_device}">${element.id_device}</a>`;
                        cell_location.innerHTML     = element.id_room_group_name;
                        cell_status.innerHTML       = element.online ? "Online" : "Offline";
                        cell_temperature.innerHTML  = element.temperature;
                        cell_humidity.innerHTML     = element.humidity;
                        cell_co2.innerHTML          = element.co2;
                        cell_last_updated.innerHTML = element.last_updated;
                        cell_window.innerHTML       = element.window_open ? "Opened" : "Closed";
        
                        cell_status.style.color = element.online      ? "green" : "red";
                        // cell_window.style.color = element.window_open ? "green" : "red";

                        data_co2.forEach(element_co2 => {
                            if (element_co2.from_value < element.co2) {
                                cell_co2.style.color = element_co2.color;
                                
                                if (!element.window_open && element_co2.color != "green")
                                    cell_window.style.color = element_co2.color;
                            }
                        });
                    });
                })
        })
}