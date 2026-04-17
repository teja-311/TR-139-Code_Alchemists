# data/phc_definitions.py

PHC_LIST = [
    {
        "id": "PHC_001",
        "name": "Lalgudi PHC",
        "district": "Tiruchirappalli",
        "lat": 10.8711,
        "lon": 78.8258,
        "capacity_liters": 150
    },
    {
        "id": "PHC_002",
        "name": "Thiruverumbur PHC",
        "district": "Tiruchirappalli",
        "lat": 10.7712,
        "lon": 78.7610,
        "capacity_liters": 120
    },
    {
        "id": "PHC_003",
        "name": "Manapparai PHC",
        "district": "Tiruchirappalli",
        "lat": 10.6069,
        "lon": 78.4168,
        "capacity_liters": 200
    },
    {
        "id": "PHC_004",
        "name": "Musiri PHC",
        "district": "Tiruchirappalli",
        "lat": 10.9416,
        "lon": 78.4503,
        "capacity_liters": 100
    },
    {
        "id": "PHC_005",
        "name": "Thottiyam PHC",
        "district": "Tiruchirappalli",
        "lat": 10.9576,
        "lon": 78.3377,
        "capacity_liters": 110
    },
    {
        "id": "PHC_006",
        "name": "Srirangam PHC",
        "district": "Tiruchirappalli",
        "lat": 10.8659,
        "lon": 78.6865,
        "capacity_liters": 250
    },
    {
        "id": "PHC_007",
        "name": "Karur PHC",
        "district": "Karur",
        "lat": 10.9601,
        "lon": 78.0766,
        "capacity_liters": 300
    },
    {
        "id": "PHC_008",
        "name": "Kulithalai PHC",
        "district": "Karur",
        "lat": 10.9387,
        "lon": 78.4184,
        "capacity_liters": 120
    },
    {
        "id": "PHC_009",
        "name": "Perambalur PHC",
        "district": "Perambalur",
        "lat": 11.2335,
        "lon": 78.8824,
        "capacity_liters": 180
    },
    {
        "id": "PHC_010",
        "name": "Ariyalur PHC",
        "district": "Ariyalur",
        "lat": 11.1396,
        "lon": 79.0768,
        "capacity_liters": 150
    },
    {
        "id": "PHC_011",
        "name": "Pudukkottai PHC",
        "district": "Pudukkottai",
        "lat": 10.3833,
        "lon": 78.8001,
        "capacity_liters": 220
    },
    {
        "id": "PHC_012",
        "name": "Thanjavur PHC",
        "district": "Thanjavur",
        "lat": 10.7870,
        "lon": 79.1378,
        "capacity_liters": 250
    }
]

def get_all_phcs():
    return PHC_LIST

def get_phc_details(phc_id):
    for phc in PHC_LIST:
        if phc["id"] == phc_id:
            return phc
    return None
