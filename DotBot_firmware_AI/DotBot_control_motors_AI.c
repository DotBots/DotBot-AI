#include <stdio.h>
#include <stdint.h>
#include <nrf.h>
#include "board.h"
#include "board_config.h"
#include "uart.h"
#include "motors.h"
//=========================== defines ==========================================
#define DB_UART_MAX_BYTES 64          ///< Maximum UART buffer size
#define DB_UART_BAUDRATE 115200       ///< UART Baudrate
#define BASE_SPEED 70
#define MAX_SPEED 80
#define CENTER_THRESHOLD 30 // To consider that the object is centered
typedef enum {
    STATE_IDLE = 0,
    STATE_DETECTED = 1,
    STATE_CENTER_Y = 2,
    STATE_READY = 3,
} receive_state_t;
typedef struct {
    receive_state_t state;
    uint8_t detected;
    uint8_t center_y; // center_y is used instead of center_x because the Nicla Vision is placed on its side, so the camera is rotated 90 degrees.
} uart_vars_t;
//=========================== variables ========================================
static uart_vars_t _uart_vars = { 0 };
//=========================== callbacks ========================================
static void uart_callback(uint8_t byte) {
    if ((_uart_vars.state == STATE_IDLE) && (byte == 255)) {
        // waiting for start byte
        _uart_vars.state = STATE_DETECTED;
        return;
    } else if (_uart_vars.state == STATE_DETECTED) {
        // Detected byte
        _uart_vars.detected = byte;
        _uart_vars.state = STATE_CENTER_Y;
        return;
    } else if (_uart_vars.state == STATE_CENTER_Y) {
        // Center y byte
        _uart_vars.center_y = byte;
        // Ready to be processed
        _uart_vars.state = STATE_READY;
        return;
    }
}
//====================== Control Motors ========================================
void control_motors(uint8_t center_y) {
    int vel_left = BASE_SPEED; // Initial speed of the left wheel
    int vel_right = BASE_SPEED; // Initial speed of the right wheel
    int extra_speed = 0;
    if (center_y < 120 - CENTER_THRESHOLD) {
        // Left
        extra_speed = (120 - center_y) * (MAX_SPEED - BASE_SPEED) / 120;
        vel_left = BASE_SPEED;
        vel_right = BASE_SPEED + extra_speed;
        printf("Turn Left - Left: %d, Right: %d\n", vel_left, vel_right);
    } else if (center_y > 120 + CENTER_THRESHOLD) {
        // Right
        extra_speed = (center_y - 120) * (MAX_SPEED - BASE_SPEED) / 120;
        vel_left = BASE_SPEED + extra_speed;
        vel_right = BASE_SPEED;
        printf("Turn Right - Left: %d, Right: %d\n", vel_left, vel_right);
    } else {
        // Center
        vel_left = BASE_SPEED;
        vel_right = BASE_SPEED;
        printf("Move Forward - Left: %d, Right: %d\n", vel_left, vel_right);
    }
    // Applies the calculated speeds to the motors
    db_motors_set_speed(vel_left, vel_right);
}
//=========================== main =============================================

int main(void) {
    // Initialize the board and the UART
    db_board_init();
    static const gpio_t uart_rx = { .port = 0, .pin = 20 };
    static const gpio_t uart_tx = { .port = 0, .pin = 25 };
    db_uart_init(0, &uart_rx, &uart_tx, DB_UART_BAUDRATE, &uart_callback);
    db_motors_init();
    printf("System started. Waiting for data...\n");
    while (1) {
        __WFE();  // Wait for event
        if (_uart_vars.state == STATE_READY) {
            printf("New data - detected: %d, center Y: %d\n", _uart_vars.detected, _uart_vars.center_y);
            if (_uart_vars.detected == 1) {
                // Call control_motors with the received center_x value
                control_motors(_uart_vars.center_y);
            } else {
                db_motors_set_speed(0, 0); // Stop the motors
            }
            _uart_vars.state = STATE_IDLE; // Reset the state
        }
    }
}



