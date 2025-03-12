# Mesh Air Quality Control Panel

## Project Overview

The Mesh Air Quality Control Panel is designed to monitor and manage air quality metrics across multiple devices within a mesh network. This system allows for real-time data collection and visualization of environmental parameters such as temperature, humidity, and various air pollutants.

## Features

- **Mesh Networking**: Seamless communication between multiple devices to ensure comprehensive area coverage.
- **Real-Time Monitoring**: Continuous tracking of air quality metrics with instant data updates.
- **Data Visualization**: User-friendly interface to visualize historical and current air quality data.
- **Device Management**: Add, remove, or configure devices within the network effortlessly.

## Repository Structure

- **`main.py`**: The main entry point of the application.
- **`Constants.py`**: Contains constant values used across the application.
- **`Database.py`**: Manages database interactions for storing and retrieving data.
- **`DeviceController.py`**: Handles device operations within the mesh network.
- **`templates/`**: Directory containing HTML templates for the web interface.
- **`static/`**: Directory for static files like CSS, JavaScript, and images.
- **`.gitignore`**: Specifies files and directories to be ignored by Git.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/KvaksMan/Mesh-Air-Quality-Control-Panel.git
   cd Mesh-Air-Quality-Control-Panel
   ```

2. **Install Dependencies**:
   Ensure you have Python installed. Then, install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**:
   Start the application using:
   ```bash
   python main.py
   ```

   Access the web interface at `http://localhost:5000`.

## Usage

- **Accessing the Dashboard**: Navigate to `http://localhost:5000` to view real-time air quality metrics.
- **Managing Devices**: Use the main section to manage devices.
- **Viewing Historical Data**: By clicking one of the devices on main tab provides access to past air quality data and trends.
- **Setting up**: Use the settings tab to set automatic window opening and CO2/temperature alert levels

## Future development possibilities
- **Sending alerts to phone**: It is possible to add, for example, a telegram bot to use to send alerts to the phone
- **Control using the phone**: It is possible to add, for example, a telegram bot to control devices or get information from them

## Contributing

Contributions are welcome! Please fork the repository and create a pull request with your changes. Ensure that your code adheres to the project's coding standards and includes appropriate tests.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

Special thanks to all contributors and the open-source community for their invaluable support and resources.

