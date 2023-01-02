# Home Assistant


inspired by https://github.com/mark1foley/ha-gtfs-rt-v2


Example for NYC Citybike
```
sensor:
  - platform: gbfs
    station_status_url: 'https://gbfs.citibikenyc.com/gbfs/en/station_status.json'
    station_info_url: 'https://gbfs.citibikenyc.com/gbfs/en/station_information.json'
    stations:
      - name: 'CitiBike Dock Old Slip'
        stationid: '4248'
      - name: 'CitiBike Dock Water St'
        stationid: '4660'
      - name: 'CitiBike Dock Hanover'
        stationid: '415'
      - name: 'CitiBike Dock William'
        stationid: '360'
      - name: 'CitiBike Dock Maiden'
        stationid: '264'
```

