import datetime
import logging
import requests

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME, ATTR_LONGITUDE, ATTR_LATITUDE)
import homeassistant.util.dt as dt_util
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

CONF_STATION_STATUS_URL = 'station_status_url'
CONF_STATION_INFO_URL = 'station_info_url'
CONF_ICON = 'icon'
CONF_ICON_ELECTRIC = 'icon_electric'
CONF_STATIONS = 'stations'
CONF_STATION_ID = 'stationid'

DEFAULT_ICON = 'mdi:bicycle'
DEFAULT_ELECTRIC_ICON = 'mdi:bicycle-electric'

ATTR_NUM_BIKES_AVAILABLE = 'num bikes available'
ATTR_NUM_EBIKES_AVAILABLE = 'num ebikes available'
ATTR_STATION_STATUS = 'station status'
ATTR_LAST_REPORTED = 'last reported'
ATTR_IS_RETURNING = 'is returning'
ATTR_IS_RENTING = 'is renting'
ATTR_STATION_NAME = 'station name'
ATTR_NUM_DOCKS_AVAILABLE = 'num docks available'

MIN_TIME_BETWEEN_UPDATES = datetime.timedelta(seconds=60)
TIME_STR_FORMAT = "%H:%M"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_STATION_STATUS_URL): cv.string,
    vol.Required(CONF_STATION_INFO_URL): cv.string,
    vol.Optional(CONF_ICON, default=DEFAULT_ICON): cv.string,
    vol.Optional(CONF_ICON_ELECTRIC, default=DEFAULT_ELECTRIC_ICON): cv.string,
    vol.Required(CONF_STATIONS): [{
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_STATION_ID): cv.string
    }]
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Get the bikeshare sensor."""
    
    data = BikeShareData(config.get(CONF_STATION_STATUS_URL), config.get(CONF_STATION_INFO_URL))
    sensors = []
    for stations in config.get(CONF_STATIONS):
        sensors.append(BikeShareSensor(
            data,
            stations.get(CONF_NAME),
            stations.get(CONF_STATION_ID),
            config.get(CONF_ICON), 
            config.get(CONF_ICON_ELECTRIC)
        ))

    add_devices(sensors)

class BikeShareSensor(Entity):
    """Implementation of a bikeshare sensor."""

    def __init__(self, data, name, station_id, icon, icon_electric):
        """Initialize the sensor."""
        self.data = data
        self._name = name
        self._icon = icon
        self._icon_electric = icon_electric
        self._station_id = station_id
        self.update()

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.data.info[self._station_id].num_bikes_available

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attrs = {
            ATTR_STATION_NAME: self.data.info[self._station_id].name,
            ATTR_STATION_STATUS: self.data.info[self._station_id].station_status,
            ATTR_NUM_BIKES_AVAILABLE: self.data.info[self._station_id].num_bikes_available,
            ATTR_NUM_EBIKES_AVAILABLE: self.data.info[self._station_id].num_ebikes_available,
            ATTR_NUM_DOCKS_AVAILABLE: self.data.info[self._station_id].num_docks_available,
            ATTR_IS_RETURNING: self.data.info[self._station_id].is_returning,
            ATTR_IS_RENTING: self.data.info[self._station_id].is_renting,
            ATTR_LAST_REPORTED: self.data.info[self._station_id].last_reported,
            ATTR_LONGITUDE: self.data.info[self._station_id].lon,
            ATTR_LATITUDE: self.data.info[self._station_id].lat,
        }
        return attrs

    @property
    def unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        return "bikes"

    @property
    def icon(self):
        return self._icon

    def update(self):
        """Get the latest data and update the states."""
        self.data.update()
        _LOGGER.debug("Sensor Update:")
        _LOGGER.debug("...Name: {0}".format(self._name))


class StationDetails:
    def __init__(self, station_id, name, lon, lat):
        self.num_bikes_available = None
        self.num_ebikes_available = None
        self.station_status = None
        self.num_docks_available = None
        self.last_reported = None
        self.is_returning = None
        self.is_renting = None
        self.name = name
        self.station_id = station_id
        self.lon = lon
        self.lat = lat

class BikeShareData(object):
    """The Class for handling the data retrieval."""

    def __init__(self, station_status_url, station_info_url):
        """Initialize the info object."""
        self._station_status_url = station_status_url
        self._station_info_url = station_info_url
        self.info = {}
        
    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        _LOGGER.info("station_status_url: {}".format(self._station_status_url))

        self._update_stations()

    def _update_info(self):
        station_data = self.info

        response = requests.get(self._station_info_url)
        if response.status_code == 200:
            _LOGGER.info("Successfully updated station info data - {}".format(response.status_code))
        else:
            _LOGGER.error("updating station info data got {}:{}".format(response.status_code,response.content))
        
        for station in response.json()['data']['stations']:
            if station['station_id'] in station_data:
                station_data[station['station_id']].station_id = station['station_id']
                station_data[station['station_id']].name = station['name']
                station_data[station['station_id']].lon = station['lon']
                station_data[station['station_id']].lat = station['lat']
            else:
                station_data[station['station_id']] = StationDetails(station['station_id'], station['name'], station['lon'], station['lat'])

        self.info = station_data

    def _update_stations(self):
        """Get the latest data."""
        
        station_data = self.info

        if len(self.info) == 0:
            self._update_info()
            

        response = requests.get(self._station_status_url)
        if response.status_code == 200:
            _LOGGER.info("Successfully updated station status data - {}".format(response.status_code))
        else:
            _LOGGER.error("updating station status data got {}:{}".format(response.status_code,response.content))
        
        update_info = False

        for station in response.json()['data']['stations']:
            if station['station_id'] in station_data:
                station_data[station['station_id']].num_bikes_available = station['num_bikes_available']
                station_data[station['station_id']].num_ebikes_available = station['num_ebikes_available']
                station_data[station['station_id']].num_docks_available = station['num_docks_available']

                station_data[station['station_id']].station_status = station['station_status']
                station_data[station['station_id']].last_reported = station['last_reported']
                
                station_data[station['station_id']].is_returning = station['is_returning']
                station_data[station['station_id']].is_renting = station['is_renting']
            else:
                update_info = True

        self.info = station_data
        self._update_info()

