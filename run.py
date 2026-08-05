import socket

from python import create_app

app = create_app()


def _ip_local() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


if __name__ == "__main__":
    ip = _ip_local()
    url_lan = f"http://{ip}:5000"
    app.config["LAN_URL"] = url_lan
    print("\n== Gestion de Taller ==")
    print("  En este equipo:  http://127.0.0.1:5000")
    print(f"  Desde tablets:   {url_lan}   (mismo Wi-Fi)\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
