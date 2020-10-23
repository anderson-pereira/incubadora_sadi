import serialCom
import sys, time, timestamp
from datetime import datetime
from PyQt5 import QtWidgets, QtCore, uic, QtGui
import pyqtgraph

class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('Chocadeira_UI.ui', self)
        
        self.configuredSerial = False
        self.quitThread = False
        self.disableAlarm = False

        self.temperatureArray = list()
        self.timeArray = list()

        self.statusLabel = QtWidgets.QLabel("HORÁRIO: 00:00:00    ALARME: 00:00:00")

        self.confirmar.clicked.connect(self.confirmarPressed)
        self.connectarButton.clicked.connect(self.connectSerialPort)
        self.redefinir.clicked.connect(self.redefinirConfigs)
        self.DesAlarmButton.clicked.connect(self.DisableAlarm)
        
        self.FanSpeedAutoButton.clicked.connect(self.FanSpeedAutoButtonPressed)

        self.TimeDial.valueChanged.connect(self.TimeDialChange)

        self.tempDial.valueChanged.connect(self.tempDialChange)

        self.tempRef.valueChanged.connect(self.tempRefChange)

        self.FanSpeedMan.valueChanged.connect(self.FanSpeedManChanged)
        self.fanSpeedDial.valueChanged.connect(self.fanSpeedDialChanged)

        for port in serialCom.getSerialPorts():
            self.serialPort.addItem(port)

        self.statusLabel.setAlignment(QtCore.Qt.AlignRight)
        self.statusbar.addWidget(self.statusLabel,1)
        
        self.graphicsView.setBackground(QtGui.QBrush(QtGui.QColor("#f0f0f0"))) 
        
        
        axis = timestamp.DateAxisItem(orientation='bottom')
        self.graphicsView.setLabel('left', "Temperatura (°C)")
        axis.attachToPlotItem(self.graphicsView.getPlotItem())
        self.graphicsView.showGrid(x=True,y=True)
        self.show()

        self.updateValsTh = QtCore.QTimer()
        self.updateValsTh.timeout.connect(self.updateVals)
        self.updateValsTh.start(2000)

    def FanSpeedAutoButtonPressed(self):
        self.confirmarPressed()
        pass

    def TimeDialChange (self) :
        # self.periodoAlerta.setTime(QtCore.QTime(int(self.fanSpeedDial.value()/60),int(self.fanSpeedDial.value()%60),0,0))
        self.FanStatusInfo.setText(str(self.TimeDial.value()))
        self.periodoAlerta.setTime(QtCore.QTime(int(self.TimeDial.value()/2), int(self.TimeDial.value()%2*30)))

    def FanSpeedManChanged(self) :
        self.fanSpeedDial.setValue(int(self.FanSpeedMan.value()))

    def fanSpeedDialChanged(self) :
        self.FanSpeedMan.setValue(self.fanSpeedDial.value())


    def tempRefChange (self) :
        self.tempDial.setValue(int(self.tempRef.value()*10))

    def tempDialChange (self) :
        self.tempRef.setValue(self.tempDial.value()/10)

    def redefinirConfigs(self) :
        self.b = QtWidgets.QPushButton("click here")
        self.statusbar.addWidget(self.b)
        pass

    def DisableAlarm (self) :
        self.disableAlarm = True
        self.confirmarPressed()

    def connectSerialPort(self) :
        self.serialPort.setEnabled(False)
        self.connectarButton.setEnabled(False)
        serialCom.initSerialCom(self.serialPort.currentText())
        time.sleep(1)
        self.configuredSerial = True


    def confirmarPressed(self):
            
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        
        if not self.configuredSerial :
            msg.setWindowTitle("Comando Inválido")
            msg.setText("Conecte-se primeiro a uma porta serial.")
            msg.exec_()
            return

        msg.setWindowTitle("Valores digitados")
        
        RTC = datetime.now().strftime("%H:%M:%S")
        # TS(FLOAT) FAN_AUTO(BOOL) FAN_SPEED(INT) ALM_DISABLE(BOOL) ALM(TIME) RTC(TIME)

        strToUpdate = '{} {} {} {} {} {}\n'.format(
                self.tempRef.text(), 
                1 if self.FanSpeedAutoButton.isChecked() else 0,
                self.FanSpeedMan.value(),
                1 if self.disableAlarm else 0,
                self.periodoAlerta.text(), 
                RTC
            )

        self.disableAlarm = False

        serialCom.sendDataToSerial(strToUpdate)
        msg.setText(strToUpdate)
        msg.exec_()
    

    def updateVals (self):
        if not self.configuredSerial :
            return 

        try:
            msg = serialCom.readDataFromSerial()
            data = serialCom.dataParse(msg)
            if data:
                self.tempAmbInfo.display(float(data['TR']))
                self.tempRefInfo.display(float(data['TS']))
                self.FanSpeedInfo.setValue(int(int(data['FAN_SPEED'])*100.0/3.0))

                self.FanSpeedAutoButton.setChecked(int(data['FAN_STATUS']))

                self.umidadeInfo.display(float(data['HM']))
                self.AlarmStatusInfo.setCheckState(int(data['ALM_STATUS']))

                self.SegModCBox.setCheckState(int(data['MOD_SEG']))

                self.temperatureArray.append(float(data['TR']))
                self.timeArray.append(time.time())
                
                self.statusbar.removeWidget(self.statusLabel)

                self.statusLabel = QtWidgets.QLabel("HORÁRIO: {}    ALARME: {}".format(data['RTC'], data['ALM']))

                self.statusLabel.setAlignment(QtCore.Qt.AlignRight)
                self.statusbar.addWidget(self.statusLabel,1)

                self.graphicsView.clear()
                self.graphicsView.plot(self.timeArray, self.temperatureArray, pen=pyqtgraph.mkPen('k', width=2, style=QtCore.Qt.SolidLine))

        except Exception as err:
            print(err)
        return 



app = QtWidgets.QApplication(sys.argv)
window = Ui()
# app.aboutToQuit.connect(window.myExitHandler)
app.exec_()