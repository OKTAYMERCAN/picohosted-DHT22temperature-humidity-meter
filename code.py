from machine import Pin
import dht
import time
import network
import socket
import json

# DHT22 sensörü GPIO 2 pinine bağlayın
sensor = dht.DHT22(Pin(2))

# Wi-Fi erisim ağını kapat
ap = network.WLAN(network.AP_IF)
ap.active(False)
time.sleep(3)  # Bir süre bekleyin

# Wi-Fi erişim noktası oluşturma
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid='Pi-PiCO', password='TVtbFHZn2wLPkaG9Yyvrgq')

print('Wi-Fi ağı oluşturuldu. Ağa bağlanarak IP adresini öğrenin...')

# IP adresini almak için kısa bir bekleme süresi
time.sleep(2)
ip_address = ap.ifconfig()[0]
print('Erişim noktası IP adresi:', ip_address)

def read_sensor():
    try:
        sensor.measure()
        temperature = sensor.temperature()
        humidity = sensor.humidity()
        # Hissedilen sıcaklık hesaplaması
        feels_like = temperature + (0.33 * humidity) - 10.0
        
        # Sıcaklık ve nem eşiklerini kontrol et
        temp_status = "Yüksek sıcaklık" if temperature >= 30 else "Sıcaklık normal aralıkta"
        humidity_status = "Yüksek nem oranı" if humidity >= 60 else "Nem oranı normal aralıkta"

        return {
            'temperature': temperature,
            'humidity': humidity,
            'feels_like': feels_like,
            'temp_status': temp_status,
            'humidity_status': humidity_status
        }
        
    except OSError as e:
        return {'error': str(e)}

def web_page():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>DHT22 Sensor Verileri</title>
        <style>
            body {
                background-color: black;
                color: white;
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .container {
                text-align: center;
            }
        </style>
        <script>
            function fetchData() {
                fetch('/data')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('temperature').textContent = data.temperature + ' °C';
                        document.getElementById('humidity').textContent = data.humidity + ' %';
                        document.getElementById('feels_like').textContent = data.feels_like + ' °C';
                        document.getElementById('temp_status').textContent = data.temp_status;
                        document.getElementById('humidity_status').textContent = data.humidity_status;
                    });
            }
            setInterval(fetchData, 2000);  // 2 saniyede bir veriyi güncelle
            window.onload = fetchData;  // Sayfa yüklendiğinde veriyi al
        </script>
    </head>
    <body>
        <div class="container">
            <h1>DHT22 Sensor Verileri</h1>
            <p>Sıcaklık: <span id="temperature"></span></p>
            <p>Nem: <span id="humidity"></span></p>
            <p>Hissedilen Sıcaklık: <span id="feels_like"></span></p>
            <p>Sıcaklık Durumu: <span id="temp_status"></span></p>
            <p>Nem Durumu: <span id="humidity_status"></span></p>
        </div>
    </body>
    </html>
    """
    return html

def web_data():
    sensor_data = read_sensor()
    return json.dumps(sensor_data)

# Web sunucusunu başlat
addr = socket.getaddrinfo(ip_address, 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)

print('Web sunucusu çalışıyor. IP adresi: ', ip_address)

while True:
    cl, addr = s.accept()
    print('Client connected from', addr)
    request = cl.recv(1024)
    request = str(request)
    print('Request:', request)
    
    if '/data' in request:
        response = web_data()
        cl.send('HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n')
        cl.send(response)
    else:
        response = web_page()
        cl.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
        cl.send(response)
    
    cl.close()

