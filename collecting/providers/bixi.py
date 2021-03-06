import requests

from collecting import util


def stations(city):
    url = 'https://{}.bixi.com/data/bikeStations.xml'.format(city)
    response = requests.get(url)
    data = util.load_xml(response.content)
    return normalize(data)


def normalize(stations):
    extract = util.extract_element
    normalized = lambda station: {
        'name': extract(station, 'name'),
        'address': extract(station, 'name'),
        'latitude': float(extract(station, 'lat')),
        'longitude': float(extract(station, 'long')),
        'status': 'OPEN' if extract(station, 'locked') == 'false' else 'CLOSED',
        'bikes': int(extract(station, 'nbbikes')),
        'stands': int(extract(station, 'nbemptydocks')),
        # 'update': util.epoch_to_datetime(int(extract(station,
        #                                      'latestupdatetime')),
        #                                  divisor=1000).isoformat()
    }
    return [
        normalized(station)
        for station in stations.find_all('station')
    ]
