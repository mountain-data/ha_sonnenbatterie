import traceback
from datetime import datetime

# pylint: disable=unused-wildcard-import
from .const import *
# pylint: enable=unused-wildcard-import
import threading
import time
import pytz

from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass
)

# pylint: disable=no-name-in-module
from .sonnenbatterie_base import sonnenbatterie
# pylint: enable=no-name-in-module

from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_IP_ADDRESS,
    EVENT_HOMEASSISTANT_STOP,
    CONF_SCAN_INTERVAL,
    CONF_TIME_ZONE
)

async def async_setup_entry(hass, config_entry,async_add_entities):
    """Set up the sensor platform."""
    LOGGER.info('SETUP_ENTRY')
    username=config_entry.data.get(CONF_USERNAME)
    password=config_entry.data.get(CONF_PASSWORD)
    ipaddress=config_entry.data.get(CONF_IP_ADDRESS)
    updateIntervalSeconds=config_entry.options.get(CONF_SCAN_INTERVAL)
    time_zone=config_entry.options.get(CONF_TIME_ZONE)
    debug_mode=config_entry.options.get(CONF_TIME_ZONE)
    def _internal_setup(_username,_password,_ipaddress):
        return sonnenbatterie(_username,_password,_ipaddress)
    sonnenInst=await hass.async_add_executor_job(_internal_setup,username,password,ipaddress);
    systemdata=await hass.async_add_executor_job(sonnenInst.get_systemdata);
    serial=systemdata["DE_Ticket_Number"]
    LOGGER.info("{0} - INTERVAL: {1}".format(DOMAIN,updateIntervalSeconds))

    device = {
        "identifiers": {(DOMAIN, config_entry.unique_id)},
        "name": config_entry.title,
        "manufacturer": "Sonnenbatterie",
        "model": f"Batterie {serial}",
        "entry_type": None
    }

    sensor = SonnenBatterieSensor(id=f"sensor.bb_{DOMAIN}_{serial}", device = device, name = f'Sonnenbatterie {serial}')
    async_add_entities([sensor])

    monitor = SonnenBatterieMonitor(hass,sonnenInst, sensor, async_add_entities,updateIntervalSeconds,debug_mode, time_zone= 'Europe/Berlin', device = device)
    hass.data[DOMAIN][config_entry.entry_id]={"monitor":monitor}
    monitor.start()

    def _stop_monitor(_event):
        monitor.stopped=True

    #hass.states.async_set
    hass.bus.async_listen(EVENT_HOMEASSISTANT_STOP, _stop_monitor)
    LOGGER.info('Init done')
    return True


class SonnenBatterieSensor(SensorEntity):
    def __init__(self,id,name=None,state_class:str=None,
                 localtz = pytz.timezone('Europe/Berlin'),
                 device: DeviceInfo = None):
        self._attributes = {}
        self._state ="NOTRUN"
        self.entity_id=id
        if name is None:
            name=id
        self._name=name
        self._device: DeviceInfo = device
        self.localtz = localtz
        if state_class == 'total_increasing':
            self.reset = datetime.now().astimezone(self.localtz)
        else:
            self.reset = False
        self.last_update = datetime.now().astimezone(self.localtz)
        LOGGER.info("Create Sensor {0}".format(id))

    def mignight_passed(self, old_time : datetime) -> bool:
        """ did midnight pass since the last update?"""
        #LOGGER.warn(f'current time is {datetime.now().astimezone(self.localtz)}')
        days = (datetime.now().astimezone(self.localtz).date() - old_time.date()).days
        if days > 0:
            return True
        else:
            return False

    def set_state(self, state, new_update : datetime = None):
        """Set the state."""
        if new_update is None:
            new_update = datetime.now().astimezone(self.localtz)

        if self.last_update == new_update:
            # we already have this update
            return


        if self.state_class == 'total_increasing' or self.state_class == 'total':
            if self.mignight_passed(self.last_update):
                self._state = 0
                self.reset = new_update
                self.last_update = new_update
                LOGGER.info(f'Reset total sensor {self.name}')
            else:
                # get time delta in hours
                delta_t_h = (new_update - self.last_update).total_seconds()/3600
                if delta_t_h < 0:
                    # can happen if the time from the system is taken and not from the input sensor
                    delta_t_h = 0

                #LOGGER.warn(f'{new_update} > {self.last_update} > {new_update - self.last_update} > {(new_update - self.last_update).total_seconds()} > {delta_t_h}')

                try:
                    new_value = float(state)
                except:
                    new_value = 0
                    LOGGER.warning(f"New value not a number")

                try:
                    old_value = float(self._state)
                except:
                    LOGGER.warning(f"Old value not a number")
                    self._state = round((new_value*delta_t_h), 1)
                    self.last_update = new_update
                    old_value = None

                # do we have something to add to the value?
                if new_value==0 and old_value != 0:
                    return

                # check if we had a valid old value
                if old_value is not None:
                    self._state = round((new_value*delta_t_h) + old_value, 1)
                    self.last_update = new_update

                #LOGGER.warn(f'{new_update}|{delta_t_h}|{self.entity_id}|{self.state_class}|{state}|{self._state}')

        else:
            #LOGGER.warn(f'{new_update}|N/A|{self.entity_id}|{self.state_class}|{state}|{self._state}')
            if self._state==state:
                return
            self._state = state
            self.last_update = new_update

        try:
            self.schedule_update_ha_state()
        except:
            LOGGER.error("Failing sensor: "+self.name)
            #raise

    def set_attributes(self, attributes):
        """Set the state attributes."""
        self._attributes = attributes

    @property
    def device_info(self) -> DeviceInfo:
        """Device info."""
        return self._device

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this sensor."""
        return self.entity_id

    @property
    def should_poll(self):
        """Only poll to update phonebook, if defined."""
        return False

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    def update(self):
        LOGGER.info("update "+self.entity_id)
        """Update the phonebook if it is defined."""
        #self.powermeter=self._sbInst.getpowermeter()
        #self.state=self.powermeter[0]['v_l1_l2']

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._attributes.get("unit_of_measurement",None)

    @property
    def device_class(self):
        """Return the device_class."""
        return self._attributes.get("device_class",None)

    @property
    def state_class(self):
        """Return the unit of measurement."""
        return self._attributes.get("state_class",None)


class SonnenBatterieMonitor:
    def __init__(self,
                 hass,
                 sbInst,
                 sensor,
                 async_add_entities,
                 updateIntervalSeconds,
                 debug_mode,
                 time_zone,
                 device: DeviceInfo = None):
        self.hass=hass;
        self._device: DeviceInfo = device
        self.localtz = pytz.timezone('Europe/Berlin')
        self.latestData={}
        self.disabledSensors=[""]
        #self.IsHybrid=False;
        self.MinimumKeepBatteryPowerPecentage=7.0#is this valid for all batteries? 7% Eigenbehalt?
        self.NormalBatteryVoltage=50.0#real? dunno

        self.stopped = False
        self.sensor=sensor
        self.sbInst: sonnenbatterie = sbInst
        self.meterSensors={}
        self.updateIntervalSeconds=updateIntervalSeconds
        self.async_add_entities=async_add_entities
        #self.setupEntities()
        self.debug=debug_mode
        self.fullLogsAlreadySent = False
        self.last_updte = None

    def start(self):
        threading.Thread(target=self.watcher).start()

    def updateData(self):
        try:
            self.latestData["systemdata"]=self.sbInst.get_systemdata()
            self.latestData["status"]=self.sbInst.get_status()
            self.latestData["powermeter"]=self.sbInst.get_powermeter()
            last_update = datetime.strptime(self.latestData["status"]['Timestamp'], '%Y-%m-%d %H:%M:%S')
            self.last_update = pytz.timezone('UTC').localize(last_update).astimezone(self.localtz)
        except:
            e = traceback.format_exc()
            LOGGER.error(e)
            return

    def setupEntities(self):
        self.updateData();
        self.AddOrUpdateEntities()

    @property
    def device_info(self) -> DeviceInfo:
        """Device info."""
        return self._device

    def watcher(self):
        LOGGER.info('Start Watcher Thread:')

        while not self.stopped:
            try:
                self.updateData()
                self.parse()

                statedisplay="standby"
                if self.latestData["status"]["BatteryCharging"]:
                    statedisplay="charging"
                elif self.latestData["status"]["BatteryDischarging"]:
                    statedisplay="discharging"

                self.sensor.set_state(statedisplay)
                self.AddOrUpdateEntities()
                #self.sensor.set_attributes(self.latestData["systemdata"])
            except:
                e = traceback.format_exc()
                LOGGER.error(e)
            if self.updateIntervalSeconds is None:
                self.updateIntervalSeconds=10

            time.sleep(max(1,self.updateIntervalSeconds))

    def parse(self):
        pass

    def _AddOrUpdateEntity(self,id,friendlyname,value,unit,device_class,state_class:str='measurement'):
        if id in self.meterSensors:
            sensor=self.meterSensors[id]
            sensor.set_state(value, self.last_update)
        else:
            sensor=SonnenBatterieSensor(id,friendlyname,state_class, device=self._device)
            sensor.set_attributes({"unit_of_measurement":unit,"device_class":device_class,"friendly_name":friendlyname,"state_class":state_class})
            self.async_add_entities([sensor])
            self.meterSensors[id]=sensor

    def AddOrUpdateEntities(self):
        systemdata=self.latestData["systemdata"]
        status=self.latestData["status"]
        powermeter=self.latestData["powermeter"]

        """systemdata defines the serialnumber of the battery"""
        serial=systemdata["DE_Ticket_Number"]
        allSensorsPrefix="sensor.bb_"+DOMAIN+"_"+serial+"_"
        self._AddOrUpdateEntity(
            allSensorsPrefix+"state_netfrequency",
            "Net Frequency",
            round(status['Fac'],2),
            "Hz",
            SensorDeviceClass.FREQUENCY
        )

        """grid input/output"""
        val=status['GridFeedIn_W']
        val_in=0
        val_out=0
        if val>=0:
            val_out=val
        else:
            val_in=abs(val)

        sensorname=allSensorsPrefix+"state_grid_input"
        unitname="W"
        friendlyname="Grid Input Power (buy)"
        self._AddOrUpdateEntity(sensorname,friendlyname,val_in,unitname,SensorDeviceClass.POWER)

        sensorname=allSensorsPrefix+"state_grid_output"
        unitname="W"
        friendlyname="Grid Output Power (sell)"
        self._AddOrUpdateEntity(sensorname,friendlyname,val_out,unitname,SensorDeviceClass.POWER)

        sensorname=allSensorsPrefix+"state_grid_inout"
        unitname="W"
        friendlyname="Grid In/Out Power"
        self._AddOrUpdateEntity(sensorname,friendlyname,val,unitname,SensorDeviceClass.POWER)

        sensorname=allSensorsPrefix+"state_grid_inout_energy"
        unitname="Wh"
        friendlyname="Grid In/Out Energy (day)"
        self._AddOrUpdateEntity(sensorname,friendlyname,val,unitname,SensorDeviceClass.ENERGY, state_class = 'total')

        sensorname=allSensorsPrefix+"state_grid_out_energy"
        unitname="Wh"
        friendlyname="Grid Output Energy (sell) (day)"
        self._AddOrUpdateEntity(sensorname,friendlyname,val_out,unitname,SensorDeviceClass.ENERGY, state_class = 'total_increasing')

        sensorname=allSensorsPrefix+"state_grid_in_energy"
        unitname="Wh"
        friendlyname="Grid Input Energy (buy) (day)"
        self._AddOrUpdateEntity(sensorname,friendlyname,val_in,unitname,SensorDeviceClass.ENERGY, state_class = 'total_increasing')

        val=status['Production_W']
        sensorname=allSensorsPrefix+"pv_energy_produced"
        unitname="Wh"
        friendlyname="PV Energy produced (day)"
        self._AddOrUpdateEntity(sensorname,friendlyname,val,unitname,SensorDeviceClass.ENERGY, state_class = 'total_increasing')

        sensorname=allSensorsPrefix+"pv_power_produced"
        unitname="W"
        friendlyname="PV Power produced"
        self._AddOrUpdateEntity(sensorname,friendlyname,val,unitname,SensorDeviceClass.ENERGY)


        """battery states"""
        """battery load percent"""
        val=status['USOC']
        sensorname=allSensorsPrefix+"state_charge_user"
        unitname="%"
        friendlyname="Charge Percentage User"
        self._AddOrUpdateEntity(sensorname,friendlyname,val,unitname,SensorDeviceClass.BATTERY)

        val_rsoc=status['RSOC']
        sensorname=allSensorsPrefix+"state_charge_real"
        unitname="%"
        friendlyname="Charge Percentage Real"
        self._AddOrUpdateEntity(sensorname,friendlyname,val_rsoc,unitname,SensorDeviceClass.BATTERY)

        """battery input/output"""
        val=status['Pac_total_W']
        val_in=0
        val_out=0
        if val>=0:
            val_out=val
        else:
            val_in=abs(val)
        sensorname=allSensorsPrefix+"battery_power_input"
        unitname="W"
        friendlyname="Battery Power In"
        self._AddOrUpdateEntity(sensorname,friendlyname,val_in,unitname,SensorDeviceClass.POWER)

        sensorname=allSensorsPrefix+"battery_power_output"
        unitname="W"
        friendlyname="Battery Power Out"
        self._AddOrUpdateEntity(sensorname,friendlyname,val_out,unitname,SensorDeviceClass.POWER)

        sensorname=allSensorsPrefix+"battery_power_inout"
        unitname="W"
        friendlyname="Battery Power In/Out"
        self._AddOrUpdateEntity(sensorname,friendlyname,val,unitname,SensorDeviceClass.POWER)

        sensorname=allSensorsPrefix+"battery_energy_input"
        unitname="Wh"
        friendlyname="Battery Energy In (day)"
        self._AddOrUpdateEntity(sensorname,friendlyname,val_in,unitname,SensorDeviceClass.ENERGY, state_class = 'total_increasing')

        sensorname=allSensorsPrefix+"batterie_energy_output"
        unitname="Wh"
        friendlyname="Battery Energy Out (day)"
        self._AddOrUpdateEntity(sensorname,friendlyname,val_out,unitname,SensorDeviceClass.ENERGY, state_class = 'total_increasing')

        sensorname=allSensorsPrefix+"batterie_energy_inout"
        unitname="Wh"
        friendlyname="Battery Energy In/Out (day)"
        self._AddOrUpdateEntity(sensorname,friendlyname,val,unitname,SensorDeviceClass.ENERGY, state_class = 'total')

        """ House consumption """
        val = status['Consumption_W']
        sensorname = allSensorsPrefix+'house_power'
        unitname = "W"
        friendlyname = "Current house consumption"
        self._AddOrUpdateEntity(sensorname,friendlyname,val,unitname,SensorDeviceClass.POWER)

        sensorname = allSensorsPrefix+'house_energy'
        unitname = "Wh"
        friendlyname = "House consumption (day)"
        self._AddOrUpdateEntity(sensorname,friendlyname,val,unitname,SensorDeviceClass.ENERGY, state_class = 'total')

        """" average consumption """
        val = status['Consumption_Avg']
        sensorname = allSensorsPrefix+'consumption_avg'
        unitname = "W"
        friendlyname = "Average grid consumption"
        self._AddOrUpdateEntity(sensorname,friendlyname,val,unitname,SensorDeviceClass.POWER)

        val = status['RemainingCapacity_Wh']
        sensorname=allSensorsPrefix+"state_remaining_capacity_usable"
        unitname="Wh"
        friendlyname="Remaining Capacity"
        self._AddOrUpdateEntity(sensorname,friendlyname,val,unitname,SensorDeviceClass.ENERGY)

        val = round(powermeter[0]['kwh_imported'],2)
        sensorname = allSensorsPrefix+'_powermeter_production_kwh_imported'
        unitname = "kWh"
        friendlyname = "Powermeter production Imported"
        self._AddOrUpdateEntity(sensorname,friendlyname,val,unitname,SensorDeviceClass.ENERGY)

        val = round(powermeter[1]['kwh_imported'],2)
        sensorname = allSensorsPrefix+'_powermeter_consumption_kwh_imported'
        unitname = "kWh"
        friendlyname = "Powermeter consumption Imported"
        self._AddOrUpdateEntity(sensorname,friendlyname,val,unitname,SensorDeviceClass.ENERGY)

