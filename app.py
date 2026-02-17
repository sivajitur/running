"""
Main entry point for Running Analytics application.
"""

from src.ui import StreamlitApp


def main():
    """Run the Streamlit application."""
    app = StreamlitApp()
    app.run()


if __name__ == "__main__":
    main()
