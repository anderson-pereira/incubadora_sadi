#include <DHT.h>
#include <Wire.h>
#include "RTClib.h"
#include <string.h>

/////////////////////////////////////////////////////////////////////////

#define DHTPIN 7
#define DHTTYPE DHT22
#define BUZZERPIN 9
#define RELAY 4

#define FAN1 10
#define FAN2 11
#define FAN3 12

/////////////////////////////////////////////////////////////////////////

DHT dht(DHTPIN, DHTTYPE);
RTC_DS1307 rtc;

float hum;   //Stores humidity value
float temp;  //Stores temperature value
float temph; //Holds temperature value
float fan;
int alm_time = 0;
float T,temp1, temp2;
int ALM1, ALM2, ALM3;
int RTC1, RTC2, RTC3;
uint32_t count = 3590;
char buff[50];
int alm_h, alm_m, alm_s;
int times=0;
/////////////////////////////////////////////////////////////////////////

void setup()
{

  pinMode(BUZZERPIN, OUTPUT);
  pinMode(RELAY, OUTPUT);
  pinMode(FAN1, OUTPUT);
  pinMode(FAN2, OUTPUT);
  pinMode(FAN3, OUTPUT);
  digitalWrite(RELAY, HIGH);

  Serial.begin(9600);
  while (!Serial)
  {
    ; // wait for serial port to connect. Needed for native USB port only
  }

  dht.begin();
  if (!rtc.begin())
  {
    while (1)
      ;
  }
  if (!rtc.isrunning())
  {
    // Aktuelles Datum und Zeit setzen, falls die Uhr noch nicht läuft
    rtc.adjust(DateTime(__DATE__, __TIME__));
  }
  delay(2000);
  temph = dht.readTemperature();
  T = 37.5;
}

/////////////////////////////////////////////////////////////////////////

void ParseData() // split the data into its parts
{
  char *Data; // this is used by strtok() as an index

  Data = strtok(buff, " :");

  T = atof(Data); //Temp

  Data = strtok(NULL, " :");
  ALM1 = atoi(Data); // Hora

  Data = strtok(NULL, " :");
  ALM2 = atoi(Data); // Min

  Data = strtok(NULL, " :");
  ALM3 = atoi(Data); // Seg

  Data = strtok(NULL, " :");
  RTC1 = atoi(Data); // Hora

  Data = strtok(NULL, " :");
  RTC2 = atoi(Data); // Min

  Data = strtok(NULL, " :");
  RTC3 = atoi(Data); // Seg
  DateTime tempoRTC = rtc.now();
  rtc.adjust(DateTime(tempoRTC.year(),tempoRTC.month(),tempoRTC.day(),RTC1, RTC2,RTC3));
 } // T H:M:S H:M:S

/////////////////////////////////////////////////////////////////////////

void loop()
{

  if (Serial.available())
  { //Teste papra recebimendo de dados da interface
    static uint8_t pos = 0;
    while (Serial.available())
    {
      if ((buff[pos++] = Serial.read()) == '\n')
      {
        buff[pos - 1] = 0; // Remove o '/n' do fim da string
        pos = 0;

        ParseData();
        alm_time = 0;

        while (Serial.available())
          Serial.read(); // Esvazia o resto do buffer que tiver
        break;
      }
    }
  }
   delay(2000);

  //Read data and store it to variables hum and temp
  char buffer_v[50];
  hum = dht.readHumidity();
  temp = dht.readTemperature();
   
  if (FAN1 == HIGH)
  {
    if (FAN2 == HIGH)
    {
      if (FAN3 == HIGH)
        fan = 100;
      else
        fan = 2 * 100 / 3;
    }
    else
      fan = 100 / 3;
  }
  else
    fan = 0;
  DateTime tempoRTC = rtc.now();
  sprintf(buff, "TS:%d.%02d", (int)T, (int)(T * 100) % 100);
  Serial.println(buff);
  sprintf(buff, "TR:%d.%02d", (int)temp, (int)(temp * 100) % 100);
  Serial.println(buff);
  sprintf(buff, "HM:%d.%02d", (int)hum, (int)(hum * 100) % 100);
  Serial.println(buff);
  sprintf(buff, "FAN:%d.%02d", (int)fan, (int)(fan * 100) % 100);
  Serial.println(buff);
  sprintf(buff, "ALM:%.02d:%.02d:%.02d", ALM1, ALM2, ALM3);
  Serial.println(buff);
  sprintf(buff, "RTC:%.02d:%.02d:%.02d", tempoRTC.hour(), tempoRTC.minute(), tempoRTC.second());
  Serial.println(buff);

  if (alm_time == 0)
  {
    alm_h = RTC1 + ALM1;
    alm_m = RTC2 + ALM2;
    alm_s = RTC3 + ALM3;

    if (alm_s >= 60)
    {
      alm_h = alm_h - 60;
      alm_m = alm_m + 1;
    }
    if (alm_m >= 60)
    {
      alm_m = alm_m - 60;
      alm_h = alm_h + 1;
    }
    if (alm_h >= 24)
    {
      alm_h = alm_h - 24;
    }

    alm_time = 1;
  }

  temp1 = T - 0.5;
  temp2 = T + 0.5;

  if (temp < temp1)
  { //Temperatua baixa
    if (temp > temp1 - 0.5)
    { //Próximo ao valor ideal
      if (temp > temph)
      { //Temperatura aumentando, esperar
        delay(1000);
      }
      else
      { //Temperatura Diminuindo, ligar lâmpada
        digitalWrite(RELAY, LOW);
        delay(1000);
      }
    }
    else
    { // Temperatura muito baixa, desligar ventilador, ligar lâmpada
      digitalWrite(RELAY, LOW);
      delay(1000);
      digitalWrite(FAN1, LOW);
      digitalWrite(FAN2, LOW);
      digitalWrite(FAN3, LOW);
      delay(1000);
    }
  }
  else if (temp > temp2)
  { //Temperatura alta
    if (temp < temp2 + 0.5)
    { //Próximo ao valor ideal
      if (temp < temph)
      { //Temperatura diminuindo, esperar
        delay(1000);
      }
      else
      { //Temperatura Aumentando, desligar lâmpada
        digitalWrite(RELAY, HIGH);
        delay(1000);
      }
    }
    else
    { // Temperatura muito alta, ligar ventilador, desligar lâmpada
      digitalWrite(RELAY, HIGH);
      delay(1000);
      digitalWrite(FAN1, HIGH);
      digitalWrite(FAN2, HIGH);
      digitalWrite(FAN3, HIGH);
      delay(1000);
    }
  }
  else
  {
    if (temp > temph)
    { // Temperatura aumentando
      digitalWrite(FAN1, HIGH);
      digitalWrite(FAN2, LOW);
      digitalWrite(FAN3, LOW);
      delay(1000);
    }
    if (temp < temph)
    { // Temperatura diminuindo
      digitalWrite(RELAY, LOW);
      delay(1000);
    }
  }
  if (tempoRTC.hour() == alm_h)
  {
    if (tempoRTC.minute() <= 2 + alm_m)
    {
      times=times+1;
      if(times==10){
      tone(BUZZERPIN, 1000);
      delay(1000);
      noTone(BUZZERPIN);
      delay(1000);
      times=0;
      }
      if (tempoRTC.second()<= 10+alm_s)
    {
      tone(BUZZERPIN, 1000);
      delay(2000);
      noTone(BUZZERPIN);
      delay(1000);
      }
    }
  }
  temph = temp;
}

/////////////////////////////////////////////////////////////////////////
