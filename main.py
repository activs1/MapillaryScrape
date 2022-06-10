from MapillaryScraper import MapillaryScraper

def main():
    path_to_output = r"E:\projects\data2"
    # [west_lng, south_lat, east_lng, north_lat]
    #coords = [20.546080, 50.480777, 20.892955,  50.688041]
    coords = [16.942697, 51.065460, 17.110307, 51.161052]
    scraper = MapillaryScraper(path_to_output, coords, verbose=True)
    scraper.scrape()


if __name__ == '__main__':
    main()
