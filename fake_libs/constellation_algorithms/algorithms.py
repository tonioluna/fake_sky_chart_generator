from ..log_stuff import init_logger
from .basic                import get_constellations as _get_constellations_basic
from .median_neighbors     import get_constellations as _get_constellations_median_neighbors

log = init_logger()

ALGORITHM_BASIC = "basic"
ALGORITHM_MEDIAN_NEIGHBORS = "median_neighbors"

_algoritm_callers = {ALGORITHM_BASIC:               _get_constellations_basic,
                     ALGORITHM_MEDIAN_NEIGHBORS:    _get_constellations_median_neighbors,
                    }

KNOWN_ALGORITHMS = (ALGORITHM_BASIC, 
                    ALGORITHM_MEDIAN_NEIGHBORS
                   )

def call_algorithm(algorithm, config, sorted_master_stars, quadrants, **kwargs):
    log.info("Building constellations using algorithm %s"%(repr(algorithm),))
    assert algorithm in KNOWN_ALGORITHMS, "Invalid algorithm: %s (known %s)"%(algorithm, ", ".join(KNOWN_ALGORITHMS))
    return _algoritm_callers[algorithm](config, sorted_master_stars, quadrants, **kwargs)