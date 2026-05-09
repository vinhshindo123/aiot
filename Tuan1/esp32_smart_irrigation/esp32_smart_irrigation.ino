#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// ==================== CONFIGURATION ====================
#define WIFI_SSID "your_wifi_ssid"
#define WIFI_PASSWORD "your_wifi_password"

#define MQTT_BROKER "broker.emqx.io"
#define MQTT_PORT 1883
#define MQTT_TOPIC_TELEMETRY "smart_irrigation/telemetry"
#define MQTT_TOPIC_COMMAND "smart_irrigation/command"
#define MQTT_TOPIC_ACK "smart_irrigation/ack"

// Pin definitions
#define PIN_SOIL 34      // Cảm biến độ ẩm đất (ADC)
#define PIN_DHT 15       // DHT11
#define PIN_LDR 35       // Cảm biến ánh sáng
#define PIN_RELAY 4      // Relay điều khiển bơm

// Constants
#define SOIL_DRY 2800    // Giá trị ADC khi đất khô (calibrate)
#define SOIL_WET 1500    // Giá trị ADC khi đất ướt

// ==================== GLOBAL VARIABLES ====================
WiFiClient espClient;
PubSubClient mqttClient(espClient);
DHT dht(PIN_DHT, DHT11);

String deviceId = "NODE_01";
String nodeRole = "LEADER";
bool pumpState = false;
unsigned long pumpStartTime = 0;
int pumpDuration = 0;

// ==================== WIFI CONNECTION ====================
void setupWiFi() {
    Serial.print("Connecting to WiFi");
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi connected! IP: " + WiFi.localIP().toString());
}

// ==================== MQTT CALLBACK ====================
void mqttCallback(char* topic, byte* payload, unsigned int length) {
    String message;
    for (unsigned int i = 0; i < length; i++) {
        message += (char)payload[i];
    }
    
    Serial.print("Command received on topic: ");
    Serial.print(topic);
    Serial.print(" | Message: ");
    Serial.println(message);
    
    // Parse JSON command
    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, message);
    
    if (!error) {
        String command = doc["command"];
        int duration = doc["duration"] | 0;
        
        if (command == "ON") {
            pumpState = true;
            pumpDuration = duration;
            pumpStartTime = millis();
            digitalWrite(PIN_RELAY, HIGH);
            Serial.printf("PUMP TURNED ON for %d seconds\n", duration);
            
            // Send ACK
            sendAck("ON", duration, "success");
        } 
        else if (command == "OFF") {
            pumpState = false;
            pumpDuration = 0;
            digitalWrite(PIN_RELAY, LOW);
            Serial.println("PUMP TURNED OFF");
            
            // Send ACK
            sendAck("OFF", 0, "success");
        }
    }
}

// ==================== SEND ACKNOWLEDGMENT ====================
void sendAck(String command, int duration, String status) {
    StaticJsonDocument<200> ackDoc;
    ackDoc["device_id"] = deviceId;
    ackDoc["command"] = command;
    ackDoc["duration"] = duration;
    ackDoc["status"] = status;
    ackDoc["timestamp"] = millis();
    
    String ackMsg;
    serializeJson(ackDoc, ackMsg);
    
    if (mqttClient.publish(MQTT_TOPIC_ACK, ackMsg.c_str())) {
        Serial.println("ACK sent successfully");
    } else {
        Serial.println("Failed to send ACK");
    }
}

// ==================== READ SENSORS ====================
float readSoilMoisture() {
    int raw = analogRead(PIN_SOIL);
    // Convert to percentage (0% = dry, 100% = wet)
    float percentage = map(raw, SOIL_DRY, SOIL_WET, 0, 100);
    percentage = constrain(percentage, 0, 100);
    return percentage;
}

float readTemperature() {
    return dht.readTemperature();
}

float readHumidity() {
    return dht.readHumidity();
}

int readLight() {
    int raw = analogRead(PIN_LDR);
    return map(raw, 0, 4095, 0, 100);
}

// ==================== SEND TELEMETRY ====================
void sendTelemetry() {
    StaticJsonDocument<512> doc;
    
    doc["device_id"] = deviceId;
    doc["timestamp"] = getISO8601Timestamp();
    doc["soil_moisture"] = readSoilMoisture();
    doc["temperature"] = readTemperature();
    doc["humidity"] = readHumidity();
    doc["light"] = readLight();
    doc["pump_state"] = pumpState ? "ON" : "OFF";
    doc["rssi"] = WiFi.RSSI();
    doc["node_role"] = nodeRole;
    doc["mesh_link_quality"] = -65; // Simulated
    
    // Add mesh links
    JsonArray links = doc.createNestedArray("mesh_links");
    JsonObject link1 = links.createNestedObject();
    link1["neighbor"] = "NODE_02";
    link1["rssi"] = -65;
    link1["quality"] = "medium";
    
    JsonObject link2 = links.createNestedObject();
    link2["neighbor"] = "NODE_03";
    link2["rssi"] = -82;
    link2["quality"] = "poor";
    
    String telemetryMsg;
    serializeJson(doc, telemetryMsg);
    
    if (mqttClient.publish(MQTT_TOPIC_TELEMETRY, telemetryMsg.c_str())) {
        Serial.println("Telemetry sent: " + telemetryMsg);
    } else {
        Serial.println("Failed to send telemetry");
    }
}

// ==================== HELPER: ISO8601 Timestamp ====================
String getISO8601Timestamp() {
    time_t now = time(nullptr);
    struct tm* timeinfo = localtime(&now);
    char buffer[30];
    strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%S+07:00", timeinfo);
    return String(buffer);
}

// ==================== PUMP AUTO OFF ====================
void checkPumpAutoOff() {
    if (pumpState && pumpDuration > 0) {
        if ((millis() - pumpStartTime) >= (pumpDuration * 1000UL)) {
            pumpState = false;
            pumpDuration = 0;
            digitalWrite(PIN_RELAY, LOW);
            Serial.println("PUMP AUTO OFF (duration expired)");
            sendAck("OFF", 0, "auto_off");
        }
    }
}

// ==================== SETUP ====================
void setup() {
    Serial.begin(115200);
    
    // Pin setup
    pinMode(PIN_SOIL, INPUT);
    pinMode(PIN_LDR, INPUT);
    pinMode(PIN_RELAY, OUTPUT);
    digitalWrite(PIN_RELAY, LOW);
    
    // Initialize DHT
    dht.begin();
    
    // Connect WiFi
    setupWiFi();
    
    // MQTT setup
    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    mqttClient.setCallback(mqttCallback);
    
    // Connect to MQTT
    while (!mqttClient.connected()) {
        if (mqttClient.connect(deviceId.c_str())) {
            Serial.println("MQTT connected");
            mqttClient.subscribe(MQTT_TOPIC_COMMAND);
        } else {
            Serial.print("MQTT failed, rc=");
            Serial.print(mqttClient.state());
            delay(5000);
        }
    }
    
    // Sync time for timestamp
    configTime(25200, 0, "pool.ntp.org"); // GMT+7
    Serial.println("System ready!");
}

// ==================== LOOP ====================
void loop() {
    mqttClient.loop();
    
    static unsigned long lastSend = 0;
    unsigned long now = millis();
    
    // Send telemetry every 25 seconds
    if (now - lastSend >= 25000) {
        lastSend = now;
        sendTelemetry();
    }
    
    // Check for pump auto off
    checkPumpAutoOff();
    
    delay(100);
}