import socket
import qrcode
import io
import base64
from urllib.parse import urlparse

def get_url_metadata(url: str):
    """Extracts domain and attempts to resolve IP."""
    domain = urlparse(url).netloc
    try:
        ip_address = socket.gethostbyname(domain)
    except socket.gaierror:
        ip_address = "Unknown"
    return domain, ip_address

def check_url_safety(url: str):
    """
    Simulates a safety check. 
    In production, use Google Safe Browsing API or VirusTotal here.
    """
    suspicious_keywords = ["malware", "phishing", "scam"]
    return not any(keyword in url.lower() for keyword in suspicious_keywords)

def generate_qr_base64(url: str):
    """Generates a QR code and returns it as a base64 string."""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()
