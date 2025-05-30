# ROSBuddy

A modern, visual ROS 2 development environment that makes robot software development accessible and efficient.

## Features

- Visual Node Builder: Create and connect ROS 2 nodes through an intuitive graphical interface
- Parameter Configuration: Manage ROS 2 parameters with a user-friendly table interface
- Launch File Builder: Create and edit launch files visually
- Package Explorer: Browse and manage ROS 2 packages
- Output Console: Monitor logs and system output
- Modern UI: Dark theme and responsive interface

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/rosbuddy.git
cd rosbuddy
```

2. Install the package:
```bash
pip install -e .
```

## Usage

1. Start ROSBuddy:
```bash
rosbuddy
```

2. Or run with a specific workspace:
```bash
rosbuddy --workspace /path/to/your/ros2_ws
```

## Development

1. Install development dependencies:
```bash
pip install -e ".[dev]"
```

2. Run tests:
```bash
pytest
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 