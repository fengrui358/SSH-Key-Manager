"""Entry point for SSH Key Manager."""

from __future__ import annotations

from .ui.main_window import App


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
