import mercantile, mapbox_vector_tile, requests, json
from vt2geojson.tools import vt_bytes_to_geojson
import os
from tqdm import tqdm
from joblib import Parallel, delayed
from geopy.geocoders import Nominatim


class MapillaryScraper:

    ACCESS_TOKEN = 'MLY|5096221127130822|022b0002491b69101c2125cf14a4b187'

    def __init__(self, path_to_output: str,
                 coordinates_bounding_box: list,
                 multiprocessing: bool = True,
                 verbose: bool = False):
        """
        Simple scraper using Mapillary API to gather user-created, geotagged images.

        :param path_to_output: str, path to storing scraped images
        :param coordinates_bounding_box: list, coordinates in a format [ west_lng, south_lat, east_lng, north_lat ]
                                        Take caution when copying coordinates from google maps (they are reversed)
        :param verbose: bool
        """
        self.path_to_output = path_to_output
        self.coordinates_bounding_box = coordinates_bounding_box
        self.multiprocessing = multiprocessing
        self.verbose = verbose

    def print_scraping_endpoints(self):
        west, south, east, north = self.coordinates_bounding_box
        geolocator = Nominatim(user_agent="geoapiExercises")
        first_location = geolocator.reverse(str(south)+","+str(west))
        second_location = geolocator.reverse(str(north)+","+str(east))

        print("Bounding points endpoint locations: ")
        print(f"south, west point: {first_location}")
        print(f"north, east point: {second_location}")

    def scrape(self):
        if self.verbose:
            self.print_scraping_endpoints()
        tile_coverage = 'mly1_public'
        tile_layer = "image"

        west, south, east, north = self.coordinates_bounding_box
        tiles = list(mercantile.tiles(west, south, east, north, 14))
        print(f"Tiles found: {len(tiles)}")
        _ = Parallel(n_jobs=-1)(delayed(self.process_tile)(tile, west, south,
                                                           east, north,
                                                           tile_coverage,
                                                           tile_layer) for tile in tqdm(tiles))

    def process_tile(self, tile, west, south, east, north, tile_coverage, tile_layer):
        tile_url = 'https://tiles.mapillary.com/maps/vtp/{}/2/{}/{}/{}?access_token={}'.format(tile_coverage,
                                                                                               tile.z,
                                                                                               tile.x, tile.y,
                                                                                               self.ACCESS_TOKEN)
        response = requests.get(tile_url)
        data = vt_bytes_to_geojson(response.content, tile.x, tile.y, tile.z, layer=tile_layer)
        for j, feature in enumerate(data['features']):
            # get lng,lat of each feature
            lng = feature['geometry']['coordinates'][0]
            lat = feature['geometry']['coordinates'][1]

            if west < lng < east and south < lat < north:
                sequence_id = feature['properties']['sequence_id']
                if not os.path.exists(f"{self.path_to_output}/{sequence_id}"):
                    os.makedirs(f"{self.path_to_output}/{sequence_id}")

                image_id = feature['properties']['id']
                header = {'Authorization': 'OAuth {}'.format(self.ACCESS_TOKEN)}
                url = 'https://graph.mapillary.com/{}?fields=thumb_2048_url'.format(image_id)
                r = requests.get(url, headers=header)
                data = r.json()
                image_url = data['thumb_2048_url']

                # save each image with ID as filename to directory by sequence ID
                with open('{}/{}/{}.jpg'.format(self.path_to_output, sequence_id, image_id), 'wb') as handler:
                    image_data = requests.get(image_url, stream=True).content
                    handler.write(image_data)