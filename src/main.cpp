#include <Arduino.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <DHT.h>

#define DHTPIN 2
#define DHTTYPE DHT22   // Using DHT22 sensor
#define BUZZER_PIN 3
#define HEAT_INDEX_THRESHOLD 41.0  // Early alert risk threshold in Celsius

DHT dht(DHTPIN, DHTTYPE);
LiquidCrystal_I2C lcd(0x27, 16, 2);

// Edge ML Model Weights (Trained offline via Scikit-Learn Ridge Regression)
// Edge ML Model Weights (Trained offline via Scikit-Learn Ridge Regression)
const float WEIGHT_TEMP    = 1.051f;      // w1: Temperature contribution
const float WEIGHT_HUM     = 0.121f;      // w2: Humidity contribution
const float WEIGHT_DELTA_T = 2.277f;      // w3: Temperature gradient sensitivity
const float WEIGHT_DELTA_H = 0.400f;      // w4: Humidity gradient sensitivity
const float MODEL_BIAS     = -2.172f;     // Intercept bias (b)

// Historical states for temporal gradient calculation
float previous_temperature = 0.0f;
float previous_humidity = 0.0f;
bool is_first_reading = true;

// Edge AI Local Inference Routine (O(1) complexity, executes in microseconds)
float predict_future_heat_index(float current_t, float current_h, float delta_t, float delta_h) {
  float predicted_hi = (WEIGHT_TEMP * current_t) + 
                       (WEIGHT_HUM * current_h) + 
                       (WEIGHT_DELTA_T * delta_t) + 
                       (WEIGHT_DELTA_H * delta_h) + 
                       MODEL_BIAS;
  return predicted_hi;
}

void setup() {
  Serial.begin(9600);
  dht.begin();
  
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("EcoPulse Edge AI");
  lcd.setCursor(0, 1);
  lcd.print("Model Loaded OK");
  
  // Audio startup verification beep
  digitalWrite(BUZZER_PIN, HIGH);
  delay(100);
  digitalWrite(BUZZER_PIN, LOW);
  
  delay(1500);
  lcd.clear();
}

void loop() {
  float current_t = dht.readTemperature();
  float current_h = dht.readHumidity();

  // Validate sensor stream
  if (isnan(current_t) || isnan(current_h)) {
    Serial.println("ERROR: Sensor read failed");
    lcd.setCursor(0, 0);
    lcd.print("Sensor Error!   ");
    delay(2000);
    return;
  }

  // Initialize baseline states on first boot
  if (is_first_reading) {
    previous_temperature = current_t;
    previous_humidity = current_h;
    is_first_reading = false;
  }

  // 1. Feature Engineering: Compute Rate of Change (Gradients)
  float delta_t = current_t - previous_temperature;
  float delta_h = current_h - previous_humidity;

  // 2. Edge AI Model Execution
  float predicted_hi = predict_future_heat_index(current_t, current_h, delta_t, delta_h);

  // Update memory states
  previous_temperature = current_t;
  previous_humidity = current_h;

  // 3. Formatted Serial Stream for Web Dashboard (Temp,Hum,Predicted_HI)
  Serial.print(current_t, 2);
  Serial.print(",");
  Serial.print(current_h, 2);
  Serial.print(",");
  Serial.println(predicted_hi, 2);

  // 4. Multi-modal LCD Output
  lcd.setCursor(0, 0);
  lcd.print("T:");
  lcd.print(current_t, 1);
  lcd.print("C H:");
  lcd.print(current_h, 0);
  lcd.print("%   ");

  lcd.setCursor(0, 1);
  lcd.print("Pred HI:");
  lcd.print(predicted_hi, 1);
  lcd.print((char)223);
  lcd.print("C ");

  // 5. Proactive Risk Alert Trigger
  if (predicted_hi >= HEAT_INDEX_THRESHOLD) {
    digitalWrite(BUZZER_PIN, HIGH);
  } else {
    digitalWrite(BUZZER_PIN, LOW);
  }

  delay(2000); // 2-second telemetry window
}