
import json
import os
import sys

# Ensure we can import from 'birdid' package
sys.path.append(os.getcwd())

try:
    from birdid.avonet_filter import AvonetFilter, REGION_BOUNDS
except ImportError:
    print("Error: Could not import AvonetFilter. Run this script from the project root.")
    sys.exit(1)

def validate_country_data():
    json_path = 'birdid/data/ebird_regions.json'
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Total Countries in JSON: {len(data['countries'])}")
    print(f"Boundaries defined in AvonetFilter: {len(REGION_BOUNDS)}")
    
    # Initialize filter (opens DB)
    avonet = AvonetFilter()
    if not avonet.is_available():
        print("Error: Avonet database not available.")
        return

    print("\n--- Validating Country Data ---")
    
    supported_countries = []
    unsupported_countries = []
    no_data_countries = []
    
    for country in data['countries']:
        code = country.get('code', '')
        name = country.get('name', '')
        
        # Check if boundary exists
        if code in REGION_BOUNDS:
            # Query DB for species count in this boundary
            bounds = REGION_BOUNDS[code]
            # bounds: (south, north, west, east)
            species = avonet._get_species_by_bounds(*bounds)
            count = len(species)
            
            if count > 0:
                supported_countries.append({'code': code, 'name': name, 'count': count})
                print(f"✅ {code} ({name}): {count} species")
            else:
                no_data_countries.append({'code': code, 'name': name})
                print(f"❌ {code} ({name}): 0 species found in Avonet DB!")
        else:
            unsupported_countries.append({'code': code, 'name': name})
            # print(f"⚠️ {code} ({name}): No boundary definition (Offline Unsupported)")

    print("\n--- Summary ---")
    print(f"Supported (Valid Data): {len(supported_countries)}")
    print(f"Supported but No Data: {len(no_data_countries)}")
    print(f"Unsupported (No Boundary): {len(unsupported_countries)}")
    
    if no_data_countries:
        print("\nCountries with 0 species:")
        for c in no_data_countries:
            print(f"  - {c['code']} {c['name']}")

    # Suggest removing unsupported countries?
    print(f"\nRecommendation: Can remove {len(unsupported_countries) + len(no_data_countries)} countries from the list.")

if __name__ == "__main__":
    validate_country_data()
