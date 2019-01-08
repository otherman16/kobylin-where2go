import googlemaps
import os


class Map:

    GOOGLEMAPS_API_KEY = os.environ.get('GOOGLEMAPS_API_KEY')
    map = googlemaps.Client(GOOGLEMAPS_API_KEY)

    @staticmethod
    def geocode_from_location(location):
        result = Map.map.reverse_geocode(location, language='ru')
        if len(result):
            return {
                'address': result[0]['formatted_address'],
                'location': (result[0]['geometry']['location']['lat'], result[0]['geometry']['location']['lng'])
            }
        return {
                'address': '',
                'location': location
        }

    @staticmethod
    def geocode_from_address(address):
        result = Map.map.geocode(address, language='ru')
        if len(result):
            return {
                'address': result[0]['formatted_address'],
                'location': (result[0]['geometry']['location']['lat'], result[0]['geometry']['location']['lng'])
            }
        return {
                'address': address,
                'location': (0.0, 0.0)
        }

    @staticmethod
    def distances(origins, destinations):
        result = Map.map.distance_matrix(origins, destinations, mode='walking', units='metric', language='ru')
        if len(result['rows'][0]['elements']):
            return [
                distance['distance']['value'] if distance['status'] == 'OK' else -1
                for distance in result['rows'][0]['elements']
            ]
        return [-1 for _ in destinations]
