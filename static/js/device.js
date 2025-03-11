function update_chart(id_device, fake_automatic_window_opening = 0) {
    const chart_update_status = document.getElementById("chart_update_status");
    const section_chart       = document.getElementById('section_chart');

    console.log(chart_update_status);

    chart_update_status.style.display = 'block';
    section_chart      .style.display = 'none';

    const refreshIntervalId = setInterval(function() {
        if (chart_update_status.innerHTML != 'Updating...')
            chart_update_status.innerHTML += '.';
        else
            chart_update_status.innerHTML = 'Updating';
    }, 1000);

    fetch(`/api/devices/${id_device}`)
        .then(response => response.json())
        .then(data => {
            console.log(data);

            fetch('/api/co2levels/get')
                .then(response => response.json())
                .then(data_co2 => {
                    console.log(data_co2);
                    
                    clearInterval(refreshIntervalId);
                    chart_update_status.style.display = 'none';
                    section_chart      .style.display = 'block';
                    
                    data.forEach(d => {
                        d.timestamp = new Date(d.timestamp);
                    });

                    const margin = { top: 20, right: 40, bottom: 40, left: 30 };
                    const width = section_chart.offsetWidth - margin.left - margin.right;
                    // const width = 1000 - margin.left - margin.right;
                    const height = 500 - margin.top - margin.bottom;

                    const svg = d3.select("#chart_container").append("svg")
                        .attr("width", width + margin.left + margin.right)
                        .attr("height", height + margin.top + margin.bottom)
                    .append("g")
                        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

                    const x = d3.scaleTime().range([0, width]);
                    const y1 = d3.scaleLinear().range([height, 0]);  // Temperature and Humidity
                    const y2 = d3.scaleLinear().range([height, 0]);  // CO2

                    const line1 = d3.line()
                        .x(d => x(d.timestamp))
                        .y(d => y1(d.temperature));

                    const line2 = d3.line()
                        .x(d => x(d.timestamp))
                        .y(d => y1(d.humidity));

                    const line3 = d3.line()
                        .x(d => x(d.timestamp))
                        .y(d => y2(d.co2));

                    x.domain(d3.extent(data, d => d.timestamp));
                    y1.domain([Math.ceil((d3.min(data, d => Math.min(d.temperature, d.humidity)) - 6) / 5) * 5, d3.max(data, d => Math.max(d.temperature, d.humidity))]);
                    y2.domain([Math.ceil((d3.min(data, d => Math.min(d.co2)) - 250) / 200) * 200, Math.ceil((d3.max(data, d => Math.max(d.co2)) + 100) / 200) * 200]);

                    svg.append("g")
                        .attr("class", "x axis")
                        .attr("transform", "translate(0," + height + ")")
                        .call(d3.axisBottom(x)
                            .ticks(d3.timeHour.every(12))
                            .tickFormat(d => {
                                return d.getHours() === 0 ? d3.timeFormat("%d %b")(d) : d3.timeFormat("%H:%M")(d);
                            })
                        );

                    // Temperature and humidity
                    svg.append("g")
                        .attr("class", "y axis")
                        .call(d3.axisLeft(y1)
                            .ticks(20)
                        );

                    // CO2
                    svg.append("g")
                        .attr("class", "y2 axis")
                        .attr("transform", "translate(" + width + " ,0)")
                        .call(d3.axisRight(y2));


                    svg.append("path")
                        .data([data])
                        .attr("class", "line temperature")
                        .attr("d", line1)
                        .style("stroke", "black");

                    svg.append("path")
                        .data([data])
                        .attr("class", "line humidity dotted")
                        .attr("d", line2)
                        .style("stroke", "black");


                    let domain = [];
                    let range  = [];
                    data_co2.forEach(element_co2 => {
                        domain.push(element_co2.from_value);
                        range.push(element_co2.color);
                    })

                    const colorScale = d3.scaleLinear()
                        .domain(domain)
                        .range(range);

                    const co2Segments = svg.selectAll(".co2")
                        .data(data)
                        .enter().append("path")
                        .attr("class", "line co2")
                        .attr("d", (d, i) => {
                            const nextData = data[i + 1];
                            if (nextData) {
                                return line3([d, nextData]);
                            }
                            return null;
                        })
                        .style("stroke", (d) => colorScale(d.co2))
                        .style("stroke-width", 2);

                    flatpickr("#date_range", {
                        mode: "range",
                        onChange: function(selectedDates, dateStr, instance) {
                            const startDate = selectedDates[0];
                            const endDate = selectedDates[1];

                            const filteredData = data.filter(d => d.timestamp >= startDate && d.timestamp <= endDate);

                            x.domain(d3.extent(filteredData, d => d.timestamp));
                            y1.domain([Math.ceil((d3.min(filteredData, d => Math.min(d.temperature, d.humidity)) - 6) / 5) * 5, d3.max(filteredData, d => Math.max(d.temperature, d.humidity))]);
                            y2.domain([Math.ceil((d3.min(filteredData, d => Math.min(d.co2)) - 250) / 200) * 200, Math.ceil((d3.max(filteredData, d => Math.max(d.co2)) + 100) / 200) * 200]);


                            svg.selectAll(".line").remove();
                            svg.selectAll(".x.axis").remove();
                            svg.selectAll(".y.axis").remove();
                            svg.selectAll(".y2.axis").remove();


                            let deltaHours = (endDate - startDate) / 36e5;
                            let deltaDays = Math.floor(deltaHours / 24);
                            let ticks =
                                deltaDays < 3 ? deltaDays :
                                deltaDays < 4 ? 3 :
                                deltaDays < 7 ? 6 : 12;
                            
                            svg.append("g")
                                .attr("class", "x axis")
                                .attr("transform", "translate(0," + height + ")")
                                .call(d3.axisBottom(x)
                                    .ticks(d3.timeHour.every(ticks))
                                    .tickFormat(d => {
                                        return d.getHours() === 0 ? d3.timeFormat("%d %b")(d) : d3.timeFormat("%H:%M")(d);
                                    })
                                );


                            // Temperature and humidity
                            svg.append("g")
                                .attr("class", "y axis")
                                .call(d3.axisLeft(y1)
                                    .ticks(20)
                                );

                            // CO2
                            svg.append("g")
                                .attr("class", "y2 axis")
                                .attr("transform", "translate(" + width + " ,0)")
                                .call(d3.axisRight(y2));



                            svg.append("path")
                                .data([filteredData])
                                .attr("class", "line temperature")
                                .attr("d", line1)
                                .style("stroke", "black");

                            svg.append("path")
                                .data([filteredData])
                                .attr("class", "line humidity dotted")
                                .attr("d", line2)
                                .style("stroke", "black");

                            const co2Segments = svg.selectAll(".co2")
                                .data(filteredData)
                                .enter().append("path")
                                .attr("class", "line co2")
                                .attr("d", (d, i) => {
                                    const nextData = filteredData[i + 1];
                                    if (nextData) {
                                        return line3([d, nextData]);
                                    }
                                    return null;
                                })
                                .style("stroke", (d) => colorScale(d.co2))
                                .style("stroke-width", 2);
                        }
                    });
                })
        })
}

function update_window_opening_history(device_id) {
    fetch(`/api/history/window_opening/all/${device_id}`)
        .then(response => response.json())
        .then(data => {
            const table_window_opening_history = document.getElementById("window_opening_history");

            data.forEach(element => {
                let row            = table_window_opening_history.insertRow(-1);
                let cell_opened_at = row.insertCell(0);
                let cell_closed_at = row.insertCell(1);
                let cell_duration  = row.insertCell(2);

                console.log("element", element);
                
                let duration = "";
                if (element.open_duration) {
                    let seconds = element.open_duration % 60;
                    element.open_duration = Math.floor(element.open_duration / 60);
                    // console.log("element.open_duration", element.open_duration);
                    duration = `${seconds.toFixed(2)} sec`;
                    if (element.open_duration != 0) {
                        let minutes = element.open_duration;
                        // element.open_duration = Math.floor(element.open_duration / 60); // hours
                        // console.log("element.open_duration", element.open_duration);
                        duration = `${minutes} min ${duration}`;
                    }
                }

                console.log(`element.timestamp_close | ""`, element.timestamp_close);
                

                cell_opened_at.innerHTML = element.timestamp_open;
                cell_closed_at.innerHTML = element.timestamp_close || "";
                cell_duration.innerHTML  = duration || "";
            })
        })
}