from .log_stuff import init_logger
from .stars import Star
import random
#import operator
#import math
import os

log = init_logger()

DSO_GALAXY = "galaxy"
DSO_GLOBULAR_CLUSTER = "globular_cluster"
DSO_OPEN_CLUSTER = "open_cluster"

_known_dso_objects = (DSO_GALAXY,
                      DSO_GLOBULAR_CLUSTER,
                      DSO_OPEN_CLUSTER)

class DSO:
    _id_next = 0
    
    def __init__(self, 
                 dso_type,
                 w,
                 h,
                 quadrant,
                 size,
                 is_master = True,
                 params = None,
                 id = None,
                 name = None):
        if id == None:
            self.id = str(DSO._id_next)
            DSO._id_next += 1
        else:
            self.id = id
        
        self.quadrant = quadrant
        self.config = self.quadrant.config
        self.is_master = is_master
        if self.is_master:
            self.w        = w + (0 if self.quadrant == None else self.quadrant.w)
            self.h        = h + (0 if self.quadrant == None else self.quadrant.h)
        else:
            self.w        = w
            self.h        = h
        self.dso_type = dso_type
        assert self.dso_type in _known_dso_objects
        self.size = size
        self.params = params
        self.name = self.id if name == None else name
        self.stars = []
    
    def get_copies(self):
        # need to find out how many extra quadrants are added
        log.debug("Getting copies for DSO %s %s (%s)"%(self.dso_type, self.name, self.id))
        
        req_copies = []
        if self.w - self.size <= self.quadrant.w:
            req_copies.append((self.w + self.quadrant.w, self.h))
        if self.h - self.size <= self.quadrant.h:
            req_copies.append((self.w, self.h + self.quadrant.h))
        if self.w + self.size >= self.quadrant.w + self.config.box_size.width:
            req_copies.append((self.w - self.config.box_size.width, self.h))
        if self.h + self.size >= self.quadrant.h + self.config.box_size.height:
            req_copies.append((self.w, self.h - self.config.box_size.height))
        
        if len(req_copies) > 0:
            log.debug("Creating DSO copies (%i)"%(len(req_copies), ))
        
        copies = []
        for index, req_copy in enumerate(req_copies):
            log.debug("Copy %i from %s,%s to %s,%s"%(index, self.w, self.h, req_copy[0], req_copy[1]))
            dso_copy = DSO(dso_type = self.dso_type,
                           w = req_copy[0],
                           h = req_copy[1],
                           quadrant = self.quadrant,
                           size = self.size,
                           params = self.params,
                           id = self.id,
                           name = self.name,
                           is_master = False)
            
            copies.append(dso_copy)
            
        return copies
        
def get_galaxies(config, central_quadrant):
    if config.galaxies_random_seed != None:
        random.seed(config.galaxies_random_seed)
    
    count = random.randint(*config.galaxies_count_range)
    log.info("Adding %i galaxies into the chart"%(count,))
    
    size_delta = config.galaxies_size_range[1] - config.galaxies_size_range[0]
    size_min = config.galaxies_size_range[0]
    eccen_delta = config.galaxies_eccentricity_range[1] - config.galaxies_eccentricity_range[0]
    eccen_min = config.galaxies_eccentricity_range[0]
    
    max_w = config.box_size.width
    max_h = config.box_size.height
    
    galaxies = []
    for i in range(0, count):
        size = (random.random() * size_delta ) + size_min
        eccen = (random.random() * eccen_delta ) + eccen_min
        rotate = random.randint(0, 180)

        w = random.random()*max_w
        h = random.random()*max_h
        
        params = dict(eccentricity = eccen,
                      rotate = rotate,
                      )
        
        galaxy = DSO(dso_type = DSO_GALAXY,
                     w = w,
                     h = h,
                     quadrant = central_quadrant,
                     size = size,
                     params = params)
        
        galaxies.append(galaxy)
        galaxies.extend(galaxy.get_copies())
    
    return galaxies

def get_clusters(config, central_quadrant, cluster_type):
    assert cluster_type in (DSO_OPEN_CLUSTER, DSO_GLOBULAR_CLUSTER)
    
    if cluster_type == DSO_OPEN_CLUSTER:
        if config.open_clusters_random_seed != None:
            random.seed(config.open_clusters_random_seed)
        count = random.randint(*config.open_clusters_count_range)
        log.info("Adding %i open clusters into the chart"%(count, ))
        
        size_delta = config.open_clusters_size_range[1] - config.open_clusters_size_range[0]
        size_min = config.open_clusters_size_range[0]
    elif cluster_type == DSO_GLOBULAR_CLUSTER:
        if config.globular_clusters_random_seed != None:
            random.seed(config.globular_clusters_random_seed)
        count = random.randint(*config.globular_clusters_count_range)
        log.info("Adding %i globular clusters into the chart"%(count, ))
        
        size_delta = config.globular_clusters_size_range[1] - config.globular_clusters_size_range[0]
        size_min = config.globular_clusters_size_range[0]
    else:
        raise Exception("Internal error")
    
    max_w = config.box_size.width
    max_h = config.box_size.height
    
    clusters = []
    for i in range(0, count):
        size = (random.random() * size_delta ) + size_min
        
        w = random.random()*max_w
        h = random.random()*max_h
        
        open_cluster = DSO(dso_type = cluster_type,
                     w = w,
                     h = h,
                     quadrant = central_quadrant,
                     size = size,
                     params = None)
        
        clusters.append(open_cluster)
        clusters.extend(open_cluster.get_copies())
    
    return clusters

        