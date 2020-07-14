from ..log_stuff import init_logger
from ..color import  Color, debug_colors
from ..constellations_common import *
import math
import operator
import random
from scipy.spatial import Delaunay

add_debug_colors = False
debug_color_index = 0

log = init_logger()

def get_constellations(config, sorted_master_stars, quadrants, **kwargs):
    global debug_color_index
    global nodes
        
    # Determine the number of stars to use per constellation
    star_counts = []
    const_count = random.randint(config.constellation_count_range[0], config.constellation_count_range[1])
    log.debug("Constellation count: %s"%(const_count,))
    for i in range(0, const_count):
        star_count = random.randint(config.constellation_star_count_range[0], config.constellation_star_count_range[1])
        star_counts.append(star_count)

    total_star_count = sum(star_counts)
    selected_master_stars = sorted_master_stars[-total_star_count:]
    
    # Add all child stars into the mix
    all_stars_dict = {}
    all_available_stars = []
    for ms in selected_master_stars:
        all_available_stars.append(ms)
        all_available_stars.extend(ms.childs)
        
    for star in all_available_stars:
        all_stars_dict[star.id] = star
        
    if add_debug_colors:
        for star in all_available_stars:
            star.color.set_rgb_val("#00FF00FF")
            star.size = config.star_size_range[1]
    
    available_stars = all_available_stars
    
    points_dict = {}
    for star in available_stars:
        c = (star.w, star.h)
        points_dict[c] = star
        #star.take()
        
    points = list(points_dict.keys())
        
    tri = Delaunay(points)
    
    # Draw the debug constellation with the full array of lines
    #debug_constellation = Constellation(quadrants = quadrants, name_display_style = config.constellation_name_display_style)
    #for star in available_stars:
    #    debug_constellation.add_star(star)
    #for triangle in tri.simplices:
    #    star_ids = []
    #    for index in triangle:
    #        star_ids.append(points_dict[points[index]].id)
    #    debug_constellation.draw_segment(star_ids, is_closed = True)
    #    #debug_constellation.set_as_debug_constellation()
    
    # Create a map of the valid transitions
    nodes = {}
    
    for star in available_stars:
        nodes[star.id] = Node(star)
    
    for triangle in tri.simplices:
        star_ids = []
        for index in triangle:
            star_ids.append(points_dict[points[index]].id)
        for src_star_id, dst_star_ids in ( (star_ids[0], (star_ids[1], star_ids[2])),
                                        (star_ids[1], (star_ids[2], star_ids[0])),
                                        (star_ids[2], (star_ids[0], star_ids[1]))
                                       ):
            src_star = all_stars_dict[src_star_id]
            dst_stars = [all_stars_dict[dsid] for dsid in dst_star_ids]
            node = nodes[src_star.id]
            for dst_star in dst_stars:
                node.add_valid_node(nodes[dst_star.id])
    
    constellations = []
    # fun beggins here
    #for const_num in range(0, const_count):
    const_num = -1
    
    pending_lone_star = None
    
    #    sqrt(A/(N*p)
    max_dist_takeover_stars = 2 * math.sqrt( (config.box_size.width * config.box_size.height) / (len(selected_master_stars) * math.pi) ) * (0.2 + random.random() * 0.2 )
#    print (max_dist_takeover_stars)
    
    while True:
        if pending_lone_star == None:
            const_num += 1
            
            # Filter out taken stars
            available_stars = get_available_stars(available_stars)
            
            master_av_stars = count_available_master_stars(available_stars)
            
            log.info("Creating constellation %i out of %i possible stars"%(const_num, master_av_stars))
            
            if master_av_stars == 0:
                break
        
        # Special case, can't have a constellation of 1 star. Need to assign it to the nearest constellation (by nearest star)
        if pending_lone_star != None or master_av_stars == 1:
            # there will be child stars from each quadrant, need to check against each one of them
            # need to make sure the proper copy of the star is added to the proper constellation, otherwise 
            # weird things happen
            # The easiest way to do that is to compare only against stars which have been assigned to a constellation
            assigned_stars = []
            for star in all_available_stars:
                if star.taken and star.constellation != None:
                    assigned_stars.append(star)
            
            star_copies_to_assing = None
            if pending_lone_star != None:
                log.info("Looking for nearby costellation for lone star %s"%(pending_lone_star,))
                star_copies_to_assing = []
                star_copies_to_assing.append(pending_lone_star.master_star)
                star_copies_to_assing.extend(pending_lone_star.master_star.childs)
            else:
                log.info("Looking for nearby constellation for last standing star %s"%(available_stars[0].master_star,))
                star_copies_to_assing = available_stars
            
            min_d = None
            min_const = None
            min_star = None
            for star in star_copies_to_assing:
                # Need to compare only against which have a valid constellation assigned
                all_neighbor_stars = [node.star for node in nodes[star.id].valid_nodes()]
                valid_neighbor_stars = []
                for ns in all_neighbor_stars:
                    if ns.taken and ns.constellation != None:
                        valid_neighbor_stars.append(ns)
                if len(valid_neighbor_stars) == 0: continue
                #print (valid_neighbor_stars)
                #print([s.master_star.id for s in valid_neighbor_stars])
                #print(star.id)
                d = get_distances_to_stars(star, valid_neighbor_stars, skip_taken_stars = False)
                #print (d)
                d_keys = list(d.keys())
                d_keys.sort()
                if min_d == None or d_keys[0] < min_d:
                    min_d = d_keys[0]
                    min_const = d[d_keys[0]][0].constellation
                    min_star = star
            
            min_star.take()
            min_const.add_star(min_star)
            
            if pending_lone_star != None:
                pending_lone_star = None
                continue
            else:
                break
                
        # pick a random star to start with
        base_star = get_random_star(available_stars, must_be_master = True)
        log.debug("base star: %s"%(base_star,))
        constellation = Constellation(quadrants = quadrants, name_display_style = config.constellation_name_display_style)
        constellation.add_star(base_star)
        
        if add_debug_colors:
            constellation.custom_color = Color(debug_colors[debug_color_index])
            debug_color_index = (debug_color_index + 1) % len(debug_colors)
        
        tgt_star_count = random.randint(config.constellation_star_count_range[0], config.constellation_star_count_range[1])
        
        while len(constellation.stars) < tgt_star_count:
            min_dist = None
            min_dist_star = None
            # Calculate the distances from every star on the constellation to any neighbor star of those stars
            for star in constellation.stars:
                neighbor_stars = [node.star for node in nodes[star.id].valid_nodes()]
                distances = get_distances_to_stars(star, neighbor_stars, skip_taken_stars = True)
            
                d_keys = list(distances.keys())
                if len(d_keys) == 0:
                    break
                d_keys.sort()
                local_min_dist = d_keys[0]
                local_min_dist_star = random.choice(distances[local_min_dist])
                
                if min_dist == None or local_min_dist < min_dist:
                    min_dist = local_min_dist
                    min_dist_star = local_min_dist_star
            
            # out of connected stars
            if min_dist == None:
                break
            
            min_dist_star.take()
            log.debug("star %i: %s"%(len(constellation.stars), min_dist_star))
            
            constellation.add_star(min_dist_star)

        if len(constellation.stars) > 1:
            # Now, we need to append any nearby stars which is not taken yet
            #segment_sizes = {}
            #for star in constellation.stars:
            #    for node_id in nodes[star.id].nodes:
            #        # If this valid node goes outside of this constellation
            #        if node_id not in constellation.star_dict:
            #            continue
            #        segment_id = [star.id, node_id]
            #        segment_id.sort()
            #        segment_id = "%s_%s"%(tuple(segment_id))
            #        if segment_id not in segment_sizes:
            #            node_star = all_stars_dict[node_id]
            #            segment_sizes[segment_id] = get_distance_star_to_star(star, node_star)
            #avg_segment_size = sum(segment_sizes.values()) / len(segment_sizes)        
            #
            #print (max_dist_takeover_stars, avg_segment_size)
            
            while True:
                taken_stars = 0
    #            for star in constellation.stars:
                stars = []
                stars.extend(constellation.stars)
                #print(len(stars))
                for star in stars:
                    #print("star %s has %i nodes"%(star.id, len(nodes[star.id].nodes)))
                    for node in nodes[star.id].valid_nodes():
                        # If this valid node goes outside of this constellation
                        if node.id in constellation.star_dict:
                            continue
                        if node.star.taken:
                            continue
                        segment_size = get_distance_star_to_star(star, node.star)
                        if segment_size < max_dist_takeover_stars:
                            node.star.take()
                            #print("Taking star %s"%(node_star.id))
                            constellation.add_star(node.star)
                            taken_stars += 1
                #print(taken_stars)
                if taken_stars == 0:
                    break
            
        
            constellations.append(constellation)
        else:
            star = constellation.stars[0]
            log.warning("No stars to connect to %s, assigning to nearest constellation"%(star,))
            star.untake()
            const_num -= 1
            pending_lone_star = star
        

    ### Draw constellations
        
    # for the time being draw all the valid connections
    _add_2_connections_per_node(constellations)
        # loop # 2, make sure all stars are connected to each other
    
    _remove_triple_connections_per_node(constellations)
        # some stuff may be missing here
    
    _connect_all_stars(constellations)
    
    # Finally, draw all the connected segments
    for constellation in constellations:
        log.debug("Drawing constellation %s"%(constellation,))
        drawn_segments = []
        for star in constellation.stars:
            node = nodes[star.id]
            for remote_node in node.connected_nodes():
                segment_ids = [node.id, remote_node.id]
                segment_ids.sort()
                segment_id = "%s_%s"%(tuple(segment_ids))
                if segment_id not in drawn_segments:
                    constellation.draw_segment(segment_ids, False)
                    drawn_segments.append(segment_id)
    
    return constellations

def _connect_all_stars(constellations):
    global discovered_node_ids
    for constellation in constellations:
        base_node = nodes[constellation.stars[0].id]
        while True:
            discovered_node_ids = []
            _discover_connected_nodes(base_node)
            if len(discovered_node_ids) == len(constellation.stars):
                log.debug("All nodes are connected for %s"%(constellation,))
                break
            else:
                log.debug("%i nodes are still not connected for constellation %s"%(-len(discovered_node_ids) + len(constellation.stars), 
                                                                                   constellation))
                disconnected_nodes = []
                # Make a list if disconnected nodes
                for star in constellation.stars:
                    if star.id not in discovered_node_ids:
                        disconnected_nodes.append(nodes[star.id])
                
                # need to make one connection from the disconnected to the connected group
                connection_made = False
                for discovered_node_id in discovered_node_ids:
                    discovered_node = nodes[discovered_node_id]
                    for disconnected_node in disconnected_nodes:
                        if discovered_node.is_valid_node(disconnected_node):
                            discovered_node.connect_to(disconnected_node)
                            connection_made = True
                            break
                    if connection_made:
                        break
            
def _discover_connected_nodes(node):
    global discovered_node_ids
    if node.id in discovered_node_ids: 
        return
    discovered_node_ids.append(node.id)
    for child in node.connected_nodes():
        _discover_connected_nodes(child)

def _remove_triple_connections_per_node(constellations):
    for constellation in constellations:
        # Finally, remove triple connections (which happen from both sides)
        for star in constellation.stars:
            node = nodes[star.id]
            remote_nodes = node.connected_nodes()

            index = 0
            while node.count_connected_nodes() > 2 and index < len(remote_nodes):
                remote_node = remote_nodes[index]
                if remote_node.count_connected_nodes() > 2:
                    node.disconnect_from(remote_node)
                index += 1
                
def _add_2_connections_per_node(constellations):
    for constellation in constellations:
        log.debug("loop 1 for constellation %s (which contains stars %s)"%(constellation, ", ".join(str(star.id) for star in constellation.stars)))
        # loop 1. Make sure all stars have at least two connections        
        for star in constellation.stars:
            log.debug("Checking star %s"%(star.id, ))
            remote_nodes = {}
            node = nodes[star.id]

            # previous stars in the loop may have been already connected to this node
            if node.count_connected_nodes() < 2:
                for remote_node in node.valid_nodes():
                    # If this valid node goes outside of this constellation
                    if remote_node.id not in constellation.star_dict:
                        continue

                    if remote_node.count_connected_nodes() == 0:
                        node.connect_to(remote_node)
                    
                    # just in case we needed, keep a list of local nodes
                    c = remote_node.count_connected_nodes()
                    if c not in remote_nodes: remote_nodes[c] = []
                    remote_nodes[c].append(remote_node)
                    
                    if node.count_connected_nodes() >= 2:
                        break

            # Did not find a remote node with no connection
            # then just add connections until the quota is meet or runs out of nodes
            # Add first from the list of nodes which only have one remove connection
            sorted_remote_nodes = []
            remote_counts = list(remote_nodes.keys())
            remote_counts.sort()
            for c in remote_counts:
                random.shuffle(remote_nodes[c])
                sorted_remote_nodes.extend(remote_nodes[c])

            index = 0
            while node.count_connected_nodes() <= 2 and index < len(sorted_remote_nodes):
                # Then just chose a random node to connect to
                remote_node = sorted_remote_nodes[index]
                node.connect_to(remote_node)
                index += 1



class Node:
    def __init__(self, star):
        self.star = star
        self._valid_nodes = {}
        self.id = self.star.id
        self._connected_nodes = {}
    
    def is_valid_node(self, node):
        return node.id in self._valid_nodes
    
    def add_valid_node(self, node):
        if node.id not in self._valid_nodes:
            self._valid_nodes[node.id] = node
            node.add_valid_node(self)
    
    def disconnect_from(self, node):
        assert node.id in self._valid_nodes
        if node.id in self._connected_nodes:
            log.debug("Disconnectin node %s from %s"%(self.id, node.id))
            self._connected_nodes.pop(node.id)
            node.disconnect_from(self)
        #else:
        #    log.warning("Node %s is already connected to node %s"%(self.id, node.id))
    
    def connect_to(self, node):
        assert node.id in self._valid_nodes
        if node.id not in self._connected_nodes:
            log.debug("Connecting node %s to %s"%(self.id, node.id))
            self._connected_nodes[node.id] = node
            node.connect_to(self)
        #else:
        #    log.warning("Node %s is already connected to node %s"%(self.id, node.id))
    
    def count_connected_nodes(self):
        return len(self._connected_nodes)

    def connected_nodes(self):
        return list(self._connected_nodes.values())    
    
    def valid_nodes(self):
        return list(self._valid_nodes.values())