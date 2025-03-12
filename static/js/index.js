function get_devices() {
    fetch('/api/devices/get')
        .then(response => response.json())
        .then(data => {
            const table_devices = document.getElementById("table_devices");

            fetch('/api/co2levels/get')
                .then(response => response.json())
                .then(data_co2 => {
                    fetch('/api/templevels/get')
                        .then(response => response.json())
                        .then(data_templevels => {
                            data.forEach(element => {
                                let row               = table_devices.insertRow(-1);
                                let cell_device_id    = row.insertCell(0);
                                let cell_status       = row.insertCell(1);
                                let cell_location     = row.insertCell(2);
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

                                data_co2.forEach(element_co2 => {
                                    if (element_co2.from_value < element.co2) {
                                        cell_co2.style.color = element_co2.color;
                                        
                                        if (!element.window_open && element_co2.color != "green")
                                            cell_window.style.color = element_co2.color;
                                    }
                                });

                                data_templevels.forEach(element_templevels => {
                                    if (element_templevels.from_value < element.temperature) {
                                        cell_temperature.style.color = element_templevels.color;
                                    }
                                });
                            });
                        })
                })
        })
}