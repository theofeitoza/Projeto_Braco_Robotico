// --- BIBLIOTECAS ---
// Inclui a biblioteca Wire, necessária para a comunicação I2C (padrão de comunicação usado pelo driver PCA9685)
#include <Wire.h>
// Inclui a biblioteca da Adafruit para controlar o driver PWM/Servo PCA9685
#include <Adafruit_PWMServoDriver.h>

// --- INICIALIZAÇÃO DO DRIVER ---
// Cria um objeto 'pwm' para interagir com o driver PCA9685
// O endereço I2C padrão (0x40) é usado.
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// --- CONSTANTES DE CALIBRAÇÃO DOS SERVOS ---
// Define os valores mínimos e máximos de pulso (largura de pulso) para os servos.
// Estes valores determinam os ângulos de 0° e 180°.
// Você pode precisar "tunar" (ajustar) esses valores para os seus servos específicos.
#define SERVO_MIN  150  // Pulso mínimo (para 0°)
#define SERVO_MAX  600  // Pulso máximo (para 180°)

// --- MAPEAMENTO DOS CANAIS DO DRIVER ---
// Define qual pino (canal) do PCA9685 controla cada servo motor.
// O PCA9685 tem 16 canais (0-15).
int servo1Channel = 15; // Canal para o Servo 1 (Base)
int servo2Channel = 14; // Canal para o Servo 2 (Ombro)
int servo3Channel = 13; // Canal para o Servo 3 (Cotovelo)
int servo4Channel = 12; // Canal para o Servo 4 (Mão)
int servo5Channel = 11; // Canal para o Servo 5 (Garra)

// --- VARIÁVEIS DE ESTADO ---
// Armazena o ângulo atual de cada servo para evitar movimentos desnecessários.
int servo1Angle = 0; // Ângulo inicial do Servo 1
int servo2Angle = 0; // Ângulo inicial do Servo 2
int servo3Angle = 0; // Ângulo inicial do Servo 3
int servo4Angle = 0; // Ângulo inicial do Servo 4
int servo5Angle = 0; // Ângulo inicial do Servo 5 (Garra)

// --- FUNÇÃO DE CONFIGURAÇÃO (SETUP) ---
// É executada apenas uma vez, quando o Arduino é ligado ou resetado.
void setup() {
  // Inicializa a comunicação serial com o computador (9600 bits por segundo)
  // É assim que ele recebe os comandos da interface Python.
  Serial.begin(9600);
  
  // Inicializa o driver PCA9685
  pwm.begin();
  // Configura a frequência do PWM para 60 Hz. Esta é uma frequência padrão e ideal para servos analógicos.
  pwm.setPWMFreq(60);
  
  // Imprime mensagens de instrução no Monitor Serial (útil para debug)
  Serial.println("Insira um identificador de servo (1-5) seguido de um valor para mover o servo:");
  Serial.println("Para o servo 5, insira um valor entre 0 e 90.");
  Serial.println("Para os outros servos, insira um valor entre 0 e 180.");
}

// --- FUNÇÃO DE CONVERSÃO (HELPER) ---
// Converte um ângulo (ex: 90°) em um valor de pulso (ex: 400) que o servo entende.
int angleToPulse(int angle, int servoID) {
  // A função 'map' re-escala um número de um intervalo para outro.
  
  // Caso especial: Servo 1 (Garra) - Mapeado para 0-90 graus
  if (servoID == 1) { 
    // O ID 1 (Garra) tem um mapeamento diferente, de 0-90 graus
    return map(angle, 0, 90, SERVO_MIN, 600); 
  } 
  // Caso especial: Servo 3 - Mapeamento invertido
  else if(servoID == 3) { 
    // Este servo se move na direção oposta, então invertemos o mapeamento
    return map(angle, 0, 180, SERVO_MAX, SERVO_MIN);
  }
  // Demais servos (2, 4, 5)
  else {
    // Mapeamento padrão de 0-180 graus
    return map(angle, 0, 180, SERVO_MIN, SERVO_MAX);
  }
}

// --- FUNÇÃO PRINCIPAL (LOOP) ---
// É executada continuamente, lendo a porta serial e movendo os servos.
void loop() {
  // Verifica se há dados (bytes) disponíveis vindos da porta serial (enviados pelo Python)
  if (Serial.available() > 0) {
    
    // --- LEITURA DO COMANDO SERIAL ---
    // Lê o primeiro número inteiro: o ID do servo (de 1 a 5)
    int servoID = Serial.parseInt();
    // Lê o segundo número inteiro: o ângulo desejado (ex: 90)
    int inputValue = Serial.parseInt();
    
    // Verifica se o ID do servo é válido (entre 1 e 5)
    if ((servoID >= 1 && servoID <= 5)) {
      
      // Converte o ângulo recebido (inputValue) em um valor de pulso
      int pulse = angleToPulse(inputValue, servoID);
      
      // --- ESTRUTURA DE CONTROLE (SWITCH/CASE) ---
      // Executa o código correspondente ao 'servoID' recebido
      
      // NOTA: O 'servoID' aqui é o ID enviado pelo Python (1-5).
      // A lógica no Python mapeia:
      // Slider Garra (0-90) -> ID 1
      // Slider Mão (0-180) -> ID 2
      // Slider Cotovelo (0-180) -> ID 3
      // Slider Ombro (0-180) -> ID 4
      // Slider Base (0-180) -> ID 5
      
      // Este mapeamento PARECE estar invertido em relação aos nomes das variáveis
      // (ex: ID 5 controla 'servo1Channel'). Apenas siga a lógica:
      
      switch (servoID) {
        
        // --- SERVO ID 5 (Base) ---
        case 5:
          // Validação: ângulo entre 0-180 e diferente do ângulo atual
          if (inputValue >= 0 && inputValue <= 180 && inputValue != servo1Angle) {
            servo1Angle = inputValue; // Atualiza o ângulo atual
            // Envia o comando final ao driver PCA9685:
            // (canal, início do pulso (sempre 0), fim do pulso (valor calculado))
            pwm.setPWM(servo1Channel, 0, pulse);
            Serial.print("Servo 1 (Base) movido para: ");
            Serial.println(servo1Angle);
          } else if (inputValue < 0 || inputValue > 180) {
            Serial.println("Insira um ângulo válido entre 0 e 180.");
          }
          break; // Sai do switch

        // --- SERVO ID 4 (Ombro) ---
        case 4:
          if (inputValue >= 0 && inputValue <= 180 && inputValue != servo2Angle) {
            servo2Angle = inputValue;
            pwm.setPWM(servo2Channel, 0, pulse);
            Serial.print("Servo 2 (Ombro) movido para: ");
            Serial.println(servo2Angle);
          } else if (inputValue < 0 || inputValue > 180) {
            Serial.println("Insira um ângulo válido entre 0 e 180.");
          }
          break;

        // --- SERVO ID 3 (Cotovelo) ---
        case 3:
          if (inputValue >= 0 && inputValue <= 180 && inputValue != servo3Angle) {
            servo3Angle = inputValue;
            pwm.setPWM(servo3Channel, 0, pulse);
            Serial.print("Servo 3 (Cotovelo) movido para: ");
            Serial.println(servo3Angle);
          } else if (inputValue < 0 || inputValue > 180) {
            Serial.println("Insira um ângulo válido entre 0 e 180.");
          }
          break;

        // --- SERVO ID 2 (Mão) ---
        case 2:
          if (inputValue >= 0 && inputValue <= 180 && inputValue != servo4Angle) {
            servo4Angle = inputValue;
            pwm.setPWM(servo4Channel, 0, pulse);
            Serial.print("Servo 4 (Mão) movido para: ");
            Serial.println(servo4Angle);
          } else if (inputValue < 0 || inputValue > 180) {
            Serial.println("Insira um ângulo válido entre 0 e 180.");
          }
          break;

        // --- SERVO ID 1 (Garra) ---
        case 1:
          // Validação: ângulo entre 0-90 (conforme definido na interface e em 'angleToPulse')
          if (inputValue >= 0 && inputValue <= 90 && inputValue != servo5Angle) {
            servo5Angle = inputValue;
            pwm.setPWM(servo5Channel, 0, pulse);
            Serial.print("Servo 5 (Garra) movido para: ");
            Serial.println(servo5Angle);
          } else if (inputValue < 0 || inputValue > 90) {
            Serial.println("Para o servo 5 (Garra), insira um ângulo válido entre 0 e 90.");
          }
          break;
      }
    } else {
      // Mensagem de erro se o ID do servo (primeiro número) não for 1, 2, 3, 4 ou 5
      Serial.println("Insira um identificador de servo válido (1-5).");
    }
  }
  // O loop reinicia imediatamente
}
