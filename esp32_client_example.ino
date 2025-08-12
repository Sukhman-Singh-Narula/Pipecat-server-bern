/*
 * ESP32 WebRTC AI Assistant Client
 * 
 * This example demonstrates how to connect an ESP32 device to the WebRTC AI server
 * for real-time audio conversation with an AI assistant.
 * 
 * Hardware Requirements:
 * - ESP32 development board
 * - I2S microphone (e.g., INMP441)
 * - I2S audio amplifier with speaker (e.g., MAX98357A)
 * - WiFi connection
 * 
 * Libraries Required:
 * - ESP32-WebRTC library
 * - WiFi library
 * - HTTPClient library
 * - ArduinoJson library
 * - I2S library for audio
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <WebSocketsClient.h>
#include <driver/i2s.h>

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Server configuration
const char* server_host = "192.168.1.100";  // Replace with your server IP
const int server_port = 8000;
const char* device_id = "esp32_001";  // Unique device identifier

// I2S configuration for audio
#define I2S_WS 15
#define I2S_SD 32
#define I2S_SCK 14
#define I2S_PORT I2S_NUM_0
#define I2S_SAMPLE_RATE 16000
#define I2S_SAMPLE_BITS 16
#define I2S_READ_LEN (2 * 1024)
#define I2S_CHANNEL_NUM 1
#define I2S_CHANNEL_FMT I2S_CHANNEL_FMT_ONLY_LEFT

// Audio buffer
uint8_t i2s_read_buff[I2S_READ_LEN] = {0};
int16_t* audio_buffer = (int16_t*)i2s_read_buff;

// WebRTC and WebSocket
WebSocketsClient webSocket;
bool webrtc_connected = false;
bool audio_streaming = false;

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("ESP32 WebRTC AI Assistant Client");
  Serial.println("================================");
  
  // Initialize I2S for audio input
  initI2S();
  
  // Connect to WiFi
  connectToWiFi();
  
  // Register device with server
  registerDevice();
  
  // Initialize WebRTC connection
  initWebRTC();
}

void loop() {
  webSocket.loop();
  
  if (webrtc_connected && audio_streaming) {
    // Read audio from microphone and send to server
    processAudio();
  }
  
  delay(10);
}

void connectToWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println();
  Serial.print("WiFi connected! IP address: ");
  Serial.println(WiFi.localIP());
}

void registerDevice() {
  HTTPClient http;
  String url = String("http://") + server_host + ":" + server_port + "/api/device/register";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  // Create registration payload
  DynamicJsonDocument doc(1024);
  doc["device_id"] = device_id;
  doc["device_name"] = "ESP32 AI Assistant";
  doc["device_type"] = "esp32";
  
  JsonObject capabilities = doc.createNestedObject("capabilities");
  capabilities["audio_input"] = true;
  capabilities["audio_output"] = true;
  capabilities["sample_rate"] = I2S_SAMPLE_RATE;
  capabilities["channels"] = I2S_CHANNEL_NUM;
  
  String payload;
  serializeJson(doc, payload);
  
  int httpResponseCode = http.POST(payload);
  
  if (httpResponseCode == 200) {
    String response = http.getString();
    Serial.println("Device registered successfully");
    Serial.println("Response: " + response);
  } else {
    Serial.print("Error registering device. HTTP code: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
}

void initI2S() {
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = I2S_SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 1024,
    .use_apll = false,
    .tx_desc_auto_clear = false,
    .fixed_mclk = 0
  };
  
  i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_SCK,
    .ws_io_num = I2S_WS,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = I2S_SD
  };
  
  esp_err_t result = i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
  if (result != ESP_OK) {
    Serial.println("Error installing I2S driver");
    return;
  }
  
  result = i2s_set_pin(I2S_PORT, &pin_config);
  if (result != ESP_OK) {
    Serial.println("Error setting I2S pins");
    return;
  }
  
  Serial.println("I2S initialized successfully");
}

void initWebRTC() {
  // For this example, we'll use WebSocket for signaling
  // In a full implementation, you would use proper WebRTC signaling
  
  String ws_url = String("ws://") + server_host + ":" + server_port + "/ws/" + device_id;
  
  // Note: This is a simplified example. For full WebRTC implementation,
  // you would need to use a proper WebRTC library for ESP32
  
  webSocket.begin(server_host, server_port, "/ws");
  webSocket.onEvent(webSocketEvent);
  webSocket.setReconnectInterval(5000);
  
  Serial.println("WebSocket connection initiated");
}

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case WStype_DISCONNECTED:
      Serial.println("WebSocket Disconnected");
      webrtc_connected = false;
      audio_streaming = false;
      break;
      
    case WStype_CONNECTED:
      Serial.printf("WebSocket Connected to: %s\n", payload);
      webrtc_connected = true;
      
      // Send device info
      sendDeviceInfo();
      break;
      
    case WStype_TEXT:
      Serial.printf("Received: %s\n", payload);
      handleServerMessage((char*)payload);
      break;
      
    case WStype_BIN:
      // Handle binary audio data from server
      handleAudioData(payload, length);
      break;
      
    default:
      break;
  }
}

void sendDeviceInfo() {
  DynamicJsonDocument doc(512);
  doc["type"] = "device_info";
  doc["device_id"] = device_id;
  doc["timestamp"] = millis();
  
  String message;
  serializeJson(doc, message);
  webSocket.sendTXT(message);
}

void handleServerMessage(const char* message) {
  DynamicJsonDocument doc(1024);
  deserializeJson(doc, message);
  
  String type = doc["type"];
  
  if (type == "start_audio") {
    audio_streaming = true;
    Serial.println("Audio streaming started");
  } else if (type == "stop_audio") {
    audio_streaming = false;
    Serial.println("Audio streaming stopped");
  } else if (type == "config_update") {
    // Handle configuration updates
    Serial.println("Configuration updated");
  }
}

void handleAudioData(uint8_t* data, size_t length) {
  // Play audio data through I2S output
  // This would require additional I2S configuration for output
  Serial.printf("Received audio data: %d bytes\n", length);
  
  // TODO: Implement I2S audio output to speaker
}

void processAudio() {
  size_t bytes_read = 0;
  esp_err_t result = i2s_read(I2S_PORT, i2s_read_buff, I2S_READ_LEN, &bytes_read, portMAX_DELAY);
  
  if (result == ESP_OK && bytes_read > 0) {
    // Send audio data to server
    webSocket.sendBIN(i2s_read_buff, bytes_read);
  }
}

void sendHeartbeat() {
  DynamicJsonDocument doc(256);
  doc["type"] = "heartbeat";
  doc["device_id"] = device_id;
  doc["timestamp"] = millis();
  doc["wifi_rssi"] = WiFi.RSSI();
  doc["free_heap"] = ESP.getFreeHeap();
  
  String message;
  serializeJson(doc, message);
  webSocket.sendTXT(message);
}

/*
 * Additional helper functions for a complete implementation:
 * 
 * 1. Audio Processing:
 *    - Voice Activity Detection (VAD)
 *    - Audio compression/decompression
 *    - Echo cancellation
 *    - Noise reduction
 * 
 * 2. WebRTC Features:
 *    - STUN/TURN server support for NAT traversal
 *    - ICE candidate handling
 *    - DTLS handshake for secure communication
 *    - RTP/RTCP packet handling
 * 
 * 3. Device Management:
 *    - OTA updates
 *    - Configuration management
 *    - Error handling and recovery
 *    - Power management
 * 
 * 4. Security:
 *    - Device authentication
 *    - Encrypted communication
 *    - Certificate management
 */
