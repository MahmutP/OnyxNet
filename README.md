# OnyxNet

![OnyxNet Banner](https://via.placeholder.com/800x200.png?text=OnyxNet+Secure+Chat)

**[English]** | [Türkçe](#türkçe)

## 🇬🇧 English

**OnyxNet** is a secure, end-to-end encrypted (E2EE) chat application capable of running in both terminal and web environments. It is designed to provide maximum privacy with a trace-free "dumb relay" server architecture.

### 🛡 Features

*   **End-to-End Encryption (E2EE):** Messages are encrypted with AES-256-GCM and keys are exchanged securely using 2048-bit RSA. Only the recipient can read the message.
*   **Hybrid Architecture:** Interoperability between Python Terminal Client and Web Browser Client via WebSocket and TCP Relay.
*   **No-Log Policy:** The relay server only forwards packets; it intentionally does not store any logs or keys.
*   **Terminal Interface:** A hacker-style, keyboard-driven TUI (Text User Interface) for improved focus.
*   **Web Interface:** A modern, responsive web client for ease of access.

### 🚀 Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/MahmutP/OnyxNet.git
    cd OnyxNet
    ```

2.  **Install Dependencies:**
    ```bash
    # It is recommended to use a Virtual Environment
    python3 -m venv venv
    source venv/bin/activate
    
    pip install -r requirements.txt
    ```

### 💻 Usage

You can start the main launcher to access all tools:

```bash
python3 OnyxNet.py
```

Or run modules individually:

*   **Server:** `python3 -m server.main --port 8888`
*   **Terminal Client:** `python3 -m client.main`
*   **Web Client:** `python3 start_web.py`

---

## 🇹🇷 Türkçe

**OnyxNet**, hem terminal hem de web ortamında çalışabilen, uçtan uca şifreli (E2EE) güvenli bir sohbet uygulamasıdır. İz bırakmayan "aptal aktarıcı" (dumb relay) sunucu mimarisi ile maksimum gizlilik sağlamak üzere tasarlanmıştır.

### 🛡 Özellikler

*   **Uçtan Uca Şifreleme (E2EE):** Mesajlar AES-256-GCM ile şifrelenir ve anahtarlar 2048-bit RSA kullanılarak güvenli bir şekilde değiştirilir. Mesajı sadece alıcı okuyabilir.
*   **Hibrit Mimari:** Python Terminal İstemcisi ile Web Tarayıcı İstemcisi arasında WebSocket ve TCP Relay üzerinden tam uyumluluk.
*   **Kayıt Tutmama (No-Log):** Aktarıcı sunucu sadece paketleri yönlendirir; kasıtlı olarak hiçbir log veya anahtar saklamaz.
*   **Terminal Arayüzü:** Odaklanmayı artıran, klavye kontrollü hacker tarzı TUI (Metin Tabanlı Arayüz).
*   **Web Arayüzü:** Erişim kolaylığı sağlayan modern ve duyarlı web istemcisi.

### 🚀 Kurulum

1.  **Depoyu Klonlayın:**
    ```bash
    git clone https://github.com/MahmutP/OnyxNet.git
    cd OnyxNet
    ```

2.  **Gereksinimleri Yükleyin:**
    ```bash
    # Sanal ortam (venv) kullanılması önerilir
    python3 -m venv venv
    source venv/bin/activate
    
    pip install -r requirements.txt
    ```

### 💻 Kullanım

Tüm araçlara erişmek için ana başlatıcıyı kullanabilirsiniz:

```bash
python3 OnyxNet.py
```

Veya modülleri tek tek çalıştırabilirsiniz:

*   **Sunucu (Server):** `python3 -m server.main --port 8888`
*   **Terminal İstemci:** `python3 -m client.main`
*   **Web İstemci:** `python3 start_web.py`

---

### 👤 Author / Yazar

Developed by **[MahmutP](https://github.com/MahmutP)**
