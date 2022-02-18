import os
import sys

from streamlit import cli


def deploy_streamlit():
    sys.argv = [
        "streamlit",
        "run",
        f"{os.path.dirname(os.path.realpath(__file__))}/dcr_ui.py",
        "--server.port=8080",
        "--server.address=0.0.0.0",
    ]
    sys.exit(cli.main())
