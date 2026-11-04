# Capital Rift Local AI

A local Ollama assistant for observing Capital Rift, proposing actions, and applying reviewed mouse and keyboard actions through a Linux desktop.

This repository contains the editable Python code and custom model instructions. Base model weights are downloaded separately with Ollama. The model is configured with a system prompt; it is not a separately trained foundation model.

## Components

- `capital-rift-manager.Modelfile`: Llama 3.1 8B planner instructions and dated game reference notes.
- `capital-rift-screen-reader.py`: local Qwen vision observations and Llama advice.
- `capital-rift-controller.py`: observation, proposal validation, reviewed execution, and bounded exploration.
- `capital-rift-controller-ui.py`: desktop task, review, and stop interface.
- `test_rift_controller.py`: existing controller guard tests.

## Setup

Target environment: Ubuntu/Linux with an X11 desktop, Chrome, Python 3, and Ollama. Windows and Wayland execution have not been validated.

Install system dependencies using your distribution's package manager: Python venv support, Tk, Tesseract, wmctrl, x11-utils, and scrot. Install Ollama separately and start its local service.

The current scripts expect to live in your home directory. From this checkout:

```bash
cp capital-rift-controller.py capital-rift-controller-ui.py capital-rift-screen-reader.py "$HOME/"
python3 -m venv "$HOME/capital-rift-env"
"$HOME/capital-rift-env/bin/pip" install -r requirements.txt
ollama pull llama3.1:8b
ollama pull qwen3-vl:2b
ollama pull qwen3-vl:2b-instruct
ollama create capital-rift-manager -f capital-rift-manager.Modelfile
python3 "$HOME/capital-rift-controller-ui.py"
```

Keep your existing game session open in Chrome on the same unlocked desktop. The UI currently assumes display `:0` and `~/.Xauthority`; adjust `ENV` in the UI script if your desktop uses different values.

Enter a task, observe, review the proposed action, and apply it only when appropriate. Explore performs a bounded sequence of camera and information actions. Use STOP to halt pending actions. Inspect the actual game after every change; input execution does not establish that the intended outcome occurred.

## Tests and limitations

Run on Linux with the dependencies installed:

```bash
python3 test_rift_controller.py
```

This publication was prepared from saved local source copies dated October 2026. It has not yet been compared byte-for-byte with the running Proxmox guest. Python syntax was checked during preparation; live model, desktop, and game behavior was not revalidated.

Small local models can misread text, quantities, ownership, and objects. Unattended construction and complete logistics repair are not validated. Reference notes in the Modelfile are dated; verify current mechanics before relying on them. Screenshots and observation logs remain local and may contain private information.

## Contributing

Issues and pull requests are welcome. Include your Linux/Python/Ollama versions, a minimal reproduction, and expected versus actual behavior. Remove account details from screenshots and logs. Useful contributions include portable configuration, dependency version pinning, better tests, and improved visual grounding.

Model and third-party package licenses remain their own. No additional open-source license has been selected for this project yet.
