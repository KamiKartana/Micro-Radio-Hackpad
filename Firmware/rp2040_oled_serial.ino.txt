// rp2040_oled_serial.ino
#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 32
#define OLED_RESET    -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// --- Pin definitions (match your schematic) ---
#define ENC1_A 2
#define ENC1_B 3

#define ENC2_A 4
#define ENC2_B 5

#define BTN1 6
#define BTN2 7
#define BTN3 8
#define BTN4 9

// --- Encoder state tracking ---
int last1 = HIGH;
int last2 = HIGH;

// --- Display / scrolling state ---
String song_text = "";
unsigned long last_scroll_time = 0;
int scroll_x = 0;
int text_width = 0;
int scroll_delay = 30; // ms between pixel scroll steps
bool need_scroll = false;
int padding = 4; // small gap after text before repeating

void setup() {
  Serial.begin(115200);
  Wire.begin();

  pinMode(ENC1_A, INPUT_PULLUP);
  pinMode(ENC1_B, INPUT_PULLUP);
  pinMode(ENC2_A, INPUT_PULLUP);
  pinMode(ENC2_B, INPUT_PULLUP);

  pinMode(BTN1, INPUT_PULLUP);
  pinMode(BTN2, INPUT_PULLUP);
  pinMode(BTN3, INPUT_PULLUP);
  pinMode(BTN4, INPUT_PULLUP);

  last1 = digitalRead(ENC1_A);
  last2 = digitalRead(ENC2_A);

  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    // OLED not found
    for(;;);
  }
  display.clearDisplay();
  display.setTextWrap(false);
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.display();
  update_display_text("Ready");
}

// Helper to update displayed string and recompute scroll params
void update_display_text(const String &s) {
  song_text = s;
  display.clearDisplay();
  display.setCursor(0, 0);
  display.setTextSize(1);
  // compute pixel width via measuring (naive: 6 px per char at size 1)
  text_width = song_text.length() * 6;
  if (text_width > SCREEN_WIDTH) need_scroll = true;
  else need_scroll = false;
  scroll_x = 0;
  draw_now();
}

void draw_now() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setCursor(0 - scroll_x, 12); // vertical centering tweak
  display.print(song_text);
  if (need_scroll) {
    // draw a second copy to create the repeating scroll effect
    display.setCursor(text_width + padding - scroll_x, 12);
    display.print(song_text);
  }
  display.display();
}

void process_serial_line(String &line) {
  if (line.startsWith("SONG:")) {
    String payload = line.substring(5);
    // sanitize and trim
    payload.trim();
    if (payload.length() == 0) payload = "No song";
    update_display_text(payload);
  }
  // else ignore other incoming strings (the PC script only sends SONG:)
}

String read_serial_line_nonblocking() {
  static String buf = "";
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (buf.length() > 0) {
        String out = buf;
        buf = "";
        return out;
      } else {
        // ignore empty line
        buf = "";
        continue;
      }
    } else {
      buf += c;
      if (buf.length() > 240) { // cap
        buf = buf.substring(buf.length()-200);
      }
    }
  }
  return String("");
}

void loop() {
  // --- read serial lines ---
  String line = read_serial_line_nonblocking();
  if (line.length()) {
    process_serial_line(line);
  }

  // --- encoder 1 (top) ---
  int r1 = digitalRead(ENC1_A);
  if (r1 != last1) {
    if (digitalRead(ENC1_B) != r1) {
      Serial.println("ENC1_R"); // rotate right
    } else {
      Serial.println("ENC1_L"); // rotate left
    }
    last1 = r1;
  }

  // --- encoder 2 (bottom) ---
  int r2 = digitalRead(ENC2_A);
  if (r2 != last2) {
    if (digitalRead(ENC2_B) != r2) {
      Serial.println("ENC2_R");
    } else {
      Serial.println("ENC2_L");
    }
    last2 = r2;
  }

  // --- buttons ---
  if (digitalRead(BTN1) == LOW) { Serial.println("BTN1"); delay(200); }
  if (digitalRead(BTN2) == LOW) { Serial.println("BTN2"); delay(200); }
  if (digitalRead(BTN3) == LOW) { Serial.println("BTN3"); delay(200); }
  if (digitalRead(BTN4) == LOW) { Serial.println("BTN4"); delay(200); }

  // --- scrolling ---
  if (need_scroll) {
    unsigned long now = millis();
    if (now - last_scroll_time >= scroll_delay) {
      last_scroll_time = now;
      scroll_x++;
      if (scroll_x > text_width + padding) scroll_x = 0;
      draw_now();
    }
  } else {
    // if no scroll needed, ensure static text shown (only redraw when changed)
    // small idle delay
    delay(10);
  }
}
