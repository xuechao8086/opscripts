#!/usr/bin/env python2.7
#coding:utf8

"""
Author:         charliezhao
Filename:       ring.py
Create Time:    2015-06-28 20:09
Description:
                
"""
import argparse
import sys

import cPickle 
from array import array
from hashlib import md5
from random import shuffle, randint
from struct import unpack_from
from time import time


NODE_COUNT = 256
NEW_NODE_COUNT = 259
PARTITION_POWER = 16
REPLICAS = 3
ZONE_COUNT = 3
RING_FILE = './.ring.dat'

class Ring(object):
    def __init__(self, nodes, part2node, replicas):
        self.nodes = nodes
        self.part2node = part2node
        self.replicas = replicas
        partition_power = 1
        while 2**partition_power < len(part2node):
            partition_power += 1
        
        if len(part2node) != 2**partition_power:
            raise Exception("part2node's length is not an"
                    "exact power of 2")
        self.partition_power = partition_power
        self.partition_shift = 32 - partition_power
    
    def get_nodes(self, data_id):
        data_id = str(data_id)
        part = unpack_from('>I',
               md5(data_id).digest())[0] >> self.partition_shift
        
        node_ids = [self.part2node[part]]
        zones = [ self.nodes[node_ids[0]]['zone'] ] 
         #print 'part={0} node_ids={1} zones={2}'.format(part, node_ids, zones)
        
        #for multi copy
        t_len = len(self.part2node)
        for replica in xrange(1, self.replicas):
            #while self.part2node[part] in node_ids and self.nodes[self.part2node[part]]['zone'] in zones:
            while ((self.part2node[part] in node_ids)
                    or (self.nodes[self.part2node[part]]['zone'] in zones)):
                part += 1 
                if part >= t_len:
                    part = 0
            
            node_ids.append(self.part2node[part])
            zones.append(self.nodes[self.part2node[part]]['zone'])
            #print 'part={0} node_ids={1} zones={2}'.format(part, node_ids, zones)
        
        #for i in node_ids:
        #    print 'node={0}'.format(self.nodes[i])
        return [self.nodes[n] for n in node_ids]


def build_ring():
    begin = time()
    
    #orgin nodes 
    try:
        with open(RING_FILE, 'r') as f:
            ring = cPickle.load(f)
            nodes = ring.nodes
            part2node = ring.part2node
            parts = 2**PARTITION_POWER
    except: 
        nodes = {}
        for i in xrange(0, NODE_COUNT): 
            zone = i%3
            nodes[i] = {'id':i, 'zone':zone,
                    'weight':1.0}

        #vnode count
        parts = 2**PARTITION_POWER
    
        total_weight = float(sum(n['weight'] for n in nodes.itervalues()))
        for node in nodes.itervalues():
            node['desired_parts'] = parts/total_weight * node['weight']
     
         #from vnode to node 
        part2node = array('H')
        for part in xrange(2**PARTITION_POWER):
            for node in nodes.itervalues():
                if node['desired_parts'] > 0:
                    node['desired_parts'] -= 1
                    part2node.append(node['id'])
                    break
    
        shuffle(part2node)
    
    #add three new nodes
    if NEW_NODE_COUNT != NODE_COUNT:
        assert (NEW_NODE_COUNT - NODE_COUNT)%ZONE_COUNT == 0
        for i in xrange(NODE_COUNT, NEW_NODE_COUNT):
            zone = i%ZONE_COUNT
            nodes[i] = {'id':i, 'zone':zone, 'weight':1.0}
        #rebalance
        vnode_to_assign = parts/NEW_NODE_COUNT
        new_node_id = NEW_NODE_COUNT - 1
        while vnode_to_assign > 0:
            for node_to_take_from in xrange(NODE_COUNT):
                for vnode_id, node_id in enumerate(part2node):
                    if node_id == node_to_take_from:
                        part2node[node_id] = new_node_id
                        vnode_to_assign -= 1
                        if vnode_to_assign <= 0:
                            break

    ring = Ring(nodes, part2node, REPLICAS)
    with open('./.ring.dat', 'w') as f:
        cPickle.dump(ring, f, 2)

    print '%.02fs to build the ring'% (time()-begin)
    return ring

def test_ring2(ring):
    begin = time()
    DATA_ID_COUNT = 10000000
    node_counts = {} 
    zone_counts = {}

    #for i in xrange(0, 10):
    #    choice = randint(0, DATA_ID_COUNT)
    #    for j in xrange(0, 3):
    #        print 'part={0} nodes={1}'.format(i, ring.get_nodes(i))

    for data_id in xrange(DATA_ID_COUNT):
        nodes = ring.get_nodes(data_id)
        
        if len(nodes) != 3:
            print 'error data_id={0} nodes={1}'.format(data_id, nodes)
            continue
        
        node_ids = set([node['id'] for node in nodes])
        if len(node_ids) != 3:
            print 'error data_id={0} nodes={1}'.format(data_id, nodes)
            continue

        zone_infos = set([node['zone'] for node in nodes])
        if len(zone_infos) != 3:
            print 'error data_id={0} nodes={1}'.format(data_id, nodes)
            continue
    

        for node in nodes:
            #print 'data_id:{0} node:{1}'.format(data_id, node)
            node_counts[node['id']] = node_counts.get(node['id'], 0)+1
            zone_counts[node['zone']] = zone_counts.get(node['zone'], 0)+1
    
    for i in zone_counts:
        if i != DATA_ID_COUNT/ZONE_COUNT:
            print 'info zone={0} count={1}'.format(i, zone_counts[i])
    
    avg_ = DATA_ID_COUNT*REPLICAS/NODE_COUNT
    max_ = max(v for k, v in node_counts.iteritems())
    min_ = min(v for k, v in node_counts.iteritems())
    print 'info avg={0} max={1} min={2}'.format(avg_, max_, min_)
    print 'info {0:.2f}s to test'.format(time()-begin)

def parse_argument():
            
    parser = argparse.ArgumentParser(
             description="const hash tools, ring data store at current diretory's .ring.dat",
             epilog="example: %(prog)s 1 2 3 4")
    
    parser.add_argument('-r', '--rebalance',
                        action='store_true',
                        help='rebalance the ring!')

    parser.add_argument('ids',
                        nargs='*',
                        type=int, default=[0],
                        metavar='dataid',
                        help='the request data id(type int), 1 2 3',
                        )
    return parser.parse_args() 


if __name__ == '__main__':
    #start here....
    args = parse_argument()
    #print args

    if args.rebalance: 
        ring = build_ring()
        test_ring2(ring) 
    else:
        begin = time()
        from pprint import pprint
        with open(RING_FILE, 'r') as f:
            ring = cPickle.load(f)
            for id in args.ids:
                print 'data_id:{0}'.format(id)
                pprint(ring.get_nodes(id))
        print 'info costs {0:.8f}s to process'.format(time()-begin)  
