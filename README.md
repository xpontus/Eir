# Eir - STPA Tool

A Systems-Theoretic Process Analysis (STPA) tool with graph editing capabilities, undo/redo system, and AI assistance.

## Quick Start

### Download Pre-built Applications

Visit the [Releases page](https://github.com/xpontus/Eir/releases) to download ready-to-run applications for:
- **macOS**: Download the `.dmg` file
- **Windows**: Download the `.zip` file

### Building from Source

#### Requirements
- Python 3.9 or later
- Virtual environment recommended

#### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/xpontus/Eir.git
   cd Eir
   ```

2. Create and activate virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python eir.py
   ```

## Build System

Use the Python build script for project management:

```bash
python build.py install    # Install dependencies
python build.py test       # Run tests
python build.py build      # Build distributable
python build.py run        # Run in development mode
```

## Features

- **Interactive STPA Analysis**: Create and edit control structures, losses, hazards, and unsafe control actions
- **Graph Editor**: Visual control structure editor with drag-and-drop functionality
- **AI Integration**: Get assistance with STPA methodology and analysis
- **Document Management**: Attach and manage supporting documents
- **Export/Import**: Save and load projects in JSON format
- **Cross-platform**: Works on macOS, Windows, and Linux

## Documentation

See the `documents/` folder for detailed documentation:
- [Installation Guide](documents/INSTALLATION.md)
- [Developer Guide](documents/DEVELOPER.md)
- [Build Instructions](documents/BUILD_DISTRIBUTION.md)

## Contact

Questions: pontus.svenson@ri.se

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Version

Current version: 0.4.6