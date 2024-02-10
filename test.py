import uuid
import pyshorteners
import qrcode

from db_config import DbHandler


def generate_unique_uuid():
    return str(uuid.uuid4())


def generate_tiny_url(original_url):
    s = pyshorteners.Shortener()
    return s.tinyurl.short(original_url)


def generate_qr_code(data, filename='qrcode.png'):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)


if __name__ == "__main__":
    # Generate a unique UUID
    unique_uuid = generate_unique_uuid()
    DbHandler.add_mapping(qr_id=unique_uuid)
    # Attach UUID with URL
    original_url = f"https://mw18r4bitd.execute-api.ap-south-1.amazonaws.com/dev/scan-qr/{unique_uuid}"

    # Generate TinyURL
    tiny_url = generate_tiny_url(original_url)
    print(f"TinyURL: {tiny_url}")

    # Generate QR Code
    generate_qr_code(tiny_url, filename=f'qrcode_{unique_uuid}.png')
    print("QR Code generated.")
