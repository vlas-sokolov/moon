"""Per-feature classes and helper methods"""

import os
import csv
from moon.config import Paths


def read_iau_csv(fname):
    """Reads Lunar feature csv file into a list of dictionaries"""

    with open(fname, newline='') as csvfile:
        csv_row_reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        column_names = [c_n.lower() for c_n in next(csv_row_reader)]
        for row_data in csv_row_reader:
            row_dict = dict(zip(column_names, row_data))
            yield row_dict['feature_name'], row_dict


class Crater(dict):
    """A skeleton class for a crater object"""

    def __init__(self, dict_data):
        dict_data.pop('', None)
        # Ofc this will diverge the moment you start changing the attributes!
        # Useful mainly for the inheritance of the __repr__ method
        super().__init__(dict_data)

        for key, value in dict_data.items():
            # A type conversion of sorts
            try:
                value = float(value)
            except ValueError:
                pass

            setattr(self, key.lower(), value)


class LunarFeatures:
    """Helper class assisting in finding lunar features"""

    # Keeping as class attribute?
    # Pros: gets executed at import time
    # Cons: gets executed at import time
    iau_data = {
        name.lower(): Crater(feature)
        for name, feature in read_iau_csv(
            os.path.join(Paths.table_dir, Paths.iau_features_fname))
        }

    def __getitem__(self, crater_name):
        """x.__getitem__(y) <==> x.iau_data[y.lower()]"""

        return self.iau_data[crater_name.lower()]

    def crater_position_size(self, crater_name):
        """A helper shortcut for extracting lat/lon/diameter tuple"""

        return (self[crater_name].center_latitude,
                self[crater_name].center_longitude,
                self[crater_name].diameter)
