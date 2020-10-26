import serialCom
import sys, time, timestamp
from datetime import datetime
from PyQt5 import QtWidgets, QtCore, uic, QtGui
import pyqtgraph

class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('Chocadeira_UI.ui', self)
        
        self.HumidityArray = list()
        self.temperatureArray = list()
        self.timeArray = list()
        self.configuredSerial = False
        self.quitThread = False
        self.disableAlarm = False
        self.pci = 0

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

        axis = timestamp.DateAxisItem(orientation='bottom')
        axis.attachToPlotItem(self.graphicsView.getPlotItem())

        self.show()        
        self.configurePlot()

        self.updateValsTh = QtCore.QTimer()
        self.updateValsTh.timeout.connect(self.updateVals)
        self.updateValsTh.start(1000)

        
    def configurePlot(self):
        self.graphicsView.setBackground(QtGui.QBrush(QtGui.QColor("#f0f0f0"))) 
        self.p = self.graphicsView.getPlotItem()
        self.p.getAxis('bottom').setPen(pyqtgraph.mkPen(color='#000000', width=1))
        self.p.setLabel('left', 'Temperatura', units='°C', color='#c4380d', **{'font-size':'10pt'})
        self.p.getAxis('left').setPen(pyqtgraph.mkPen(color='#c4380d', width=1))
        self.curve = self.p.plot(x=[], y=[], pen=pyqtgraph.mkPen(color='#c4380d', width=1.5))
        self.p.showAxis('right')
        self.p.setLabel('right', 'Umidade', units="%", color='#025b94', **{'font-size':'10pt'})
        self.p.getAxis('right').setPen(pyqtgraph.mkPen(color='#025b94', width=1))

        self.p2 = pyqtgraph.ViewBox()
        self.p.scene().addItem(self.p2)
        self.p.getAxis('right').linkToView(self.p2)
        self.p2.setXLink(self.p)
        self.curve2 = pyqtgraph.PlotCurveItem(pen=pyqtgraph.mkPen(color='#025b94', width=1.5))
        self.p2.addItem(self.curve2)
        self.updateViews()
        self.p.getViewBox().sigResized.connect(self.updateViews)


    def updateViews(self):
        self.p2.setGeometry(self.p.getViewBox().sceneBoundingRect())
        self.p2.linkedViewChanged(self.p.getViewBox(), self.p2.XAxis)


    def FanSpeedAutoButtonPressed(self):
        self.confirmarPressed()
        pass


    def TimeDialChange (self) :
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
        self.temperatureArray.clear()
        self.timeArray.clear()
        self.HumidityArray.clear()
        self.curve.setData(x=self.timeArray, y=self.temperatureArray)
        self.curve2.setData(x=self.timeArray, y=self.HumidityArray)
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
            if not msg:
                return
            data = serialCom.dataParse(msg)
            if data:
                self.tempAmbInfo.display(float(data['TR']))
                self.tempRefInfo.display(float(data['TS']))
                self.FanSpeedInfo.setValue(int(int(data['FAN_SPEED'])*100.0/3.0))
                self.FanSpeedAutoButton.setChecked(int(data['FAN_STATUS']))
                self.umidadeInfo.setValue(int(float(data['HM'])))
                self.AlarmStatusInfo.setCheckState(int(data['ALM_STATUS']))
                self.SegModCBox.setCheckState(int(data['MOD_SEG']))
                self.temperatureArray.append(float(data['TR']))
                self.timeArray.append(time.time())
                self.HumidityArray.append(float(data['HM']))

                if len(self.temperatureArray) > 120:
                    del self.temperatureArray[0]
                    del self.timeArray[0]
                    del self.HumidityArray[0]

                self.statusbar.setText("HORÁRIO: {}    ALARME: {}".format(data['RTC'], data['ALM']))
                self.curve.setData(x=self.timeArray, y=self.temperatureArray)
                self.curve2.setData(x=self.timeArray, y=self.HumidityArray)
                
        except Exception as err:
            print(err)
        return 
    
    def myExitHandler (self):
        serialCom.closeSerialCom ()



app = QtWidgets.QApplication(sys.argv)
window = Ui()
app.aboutToQuit.connect(window.myExitHandler)
app.exec_()