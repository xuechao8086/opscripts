#!/usr/bin/env python

from hashlib import md5
from struct import unpack_from
from bisect import bisect_left
import time

NODE_COUNT = 100
NEW_NODE_COUNT = NODE_COUNT + 1
DATA_ID_COUNT = 10000000
VNODE_COUNT = 10000

def comm_hash():
    node_counts = [0 for i in xrange(NODE_COUNT)]

    for data_id in xrange(DATA_ID_COUNT):
        data_id = str(data_id)
        hsh = unpack_from('>I', md5(data_id).digest())[0]
        node_id = hsh%NODE_COUNT
        node_counts[node_id] += 1

    desired_count = DATA_ID_COUNT/NODE_COUNT
    max_count = max(node_counts)
    min_count = min(node_counts)

    over = '{0:.3f}%'.format(
            100.0*(max_count - desired_count)/desired_count)
    under = '{0:.3f}%'.format(
            100.0*(desired_count - min_count)/desired_count)
    percent_moved = '{0:.3f}%'.format(0)

    print '{0:>8}{1:>8}{2:>8}{3:>8}{4:>8}{5:>8}{6:>12}{7:>10}'.format(
            NODE_COUNT, desired_count, max_count, min_count, over, under, 0, 'comm')

    moved_ids = 0
    node_counts = [0 for i in xrange(NEW_NODE_COUNT)]

    for data_id in xrange(DATA_ID_COUNT):
        data_id = str(data_id)
        hsh = unpack_from('>I', md5(data_id).digest())[0]
        node_id = hsh%NODE_COUNT
        new_node_id = hsh%NEW_NODE_COUNT
        if node_id != new_node_id:
            moved_ids += 1
        node_counts[new_node_id] += 1

    new_desired_count = DATA_ID_COUNT/NEW_NODE_COUNT
    new_max_count = max(node_counts)
    new_min_count = min(node_counts)

    new_over = '{0:.3f}%'.format(
            100.0*(new_max_count - new_desired_count)/desired_count)
    new_under = '{0:.3f}%'.format(
            100.0*(new_desired_count - new_min_count)/desired_count)
    new_percent_moved = '{0:.3f}%'.format(100.0*moved_ids/DATA_ID_COUNT)

    print '{0:>8}{1:>8}{2:>8}{3:>8}{4:>8}{5:>8}{6:>12}{7:>10}'.format(
            NEW_NODE_COUNT, new_desired_count, new_max_count, new_min_count,
            new_over, new_under, new_percent_moved, 'comm')
    print ''

def const_hash_one():
    node_range_starts = []
    for node_id in xrange(NODE_COUNT):
        node_range_starts.append(DATA_ID_COUNT/NODE_COUNT*node_id)

    new_node_range_starts = []
    for new_node_id in xrange(NEW_NODE_COUNT):
        new_node_range_starts.append(
                DATA_ID_COUNT/NEW_NODE_COUNT*new_node_id)

    node_counts = [0 for i in xrange(NODE_COUNT)]
    new_node_counts = [0 for i in xrange(NEW_NODE_COUNT)]

    moved_ids = 0
    for data_id in xrange(DATA_ID_COUNT):
        data_id = str(data_id)
        hsh = unpack_from('>I', md5(data_id).digest())[0]
        node_id = bisect_left(node_range_starts,
                  hsh%DATA_ID_COUNT)%NODE_COUNT
        new_node_id = bisect_left(new_node_range_starts,
                    hsh%DATA_ID_COUNT)%NEW_NODE_COUNT

        if node_id != new_node_id:
            moved_ids += 1

        node_counts[node_id] += 1
        new_node_counts[new_node_id] += 1

    desired_count = DATA_ID_COUNT/NODE_COUNT
    max_count = max(node_counts)
    min_count = min(node_counts)

    over = '{0:.3f}%'.format(
            100.0*(max_count - desired_count)/desired_count)
    under = '{0:.3f}%'.format(
            100.0*(desired_count - min_count)/desired_count)
    percent_moved = '{0:.3f}%'.format(0)

    new_desired_count = DATA_ID_COUNT/NEW_NODE_COUNT
    new_max_count = max(new_node_counts)
    new_min_count = min(new_node_counts)

    new_over = '{0:.3f}%'.format(
            100.0*(new_max_count - new_desired_count)/desired_count)
    new_under = '{0:.3f}%'.format(
            100.0*(new_desired_count - new_min_count)/desired_count)
    new_percent_moved = '{0:.3f}%'.format(100.0*moved_ids/DATA_ID_COUNT)

    print '{0:>8}{1:>8}{2:>8}{3:>8}{4:>8}{5:>8}{6:>12}{7:>10}'.format(
            NODE_COUNT, desired_count, max_count, min_count, over, under, 0, 'const1')
    print '{0:>8}{1:>8}{2:>8}{3:>8}{4:>8}{5:>8}{6:>12}{7:>10}'.format(
            NEW_NODE_COUNT, new_desired_count, new_max_count, new_min_count,
            new_over, new_under, new_percent_moved, 'const1')
    print ''



def const_hash_two(VNODE_COUNT):
    """
        include virtual node
    """
    vnode_range_starts = []
    vnode2node = []
    for vnode_id in xrange(VNODE_COUNT):
        vnode_range_starts.append(
                DATA_ID_COUNT/VNODE_COUNT*vnode_id)
        vnode2node.append(vnode_id%NODE_COUNT)

    new_vnode2node = list(vnode2node)
    new_node_id = NODE_COUNT

    vnodes_to_assign = VNODE_COUNT/NEW_NODE_COUNT
    while vnodes_to_assign>0:
        for node_to_take_from in xrange(NODE_COUNT):
            for vnode_id, node_id in enumerate(new_vnode2node):
                if node_id == node_to_take_from:
                    new_vnode2node[vnode_id] = new_node_id
                    vnodes_to_assign -= 1
                    if vnodes_to_assign <=0:
                        break

            if vnodes_to_assign <=0:
                break

    node_counts = [0 for i in xrange(NODE_COUNT)]
    new_node_counts = [0 for i in xrange(NEW_NODE_COUNT)]

    moved_ids = 0
    for data_id in xrange(DATA_ID_COUNT):
        data_id = str(data_id)
        hsh = unpack_from('>I', md5(data_id).digest())[0]
        #vnode_id = bisect_left(vnode_range_starts,
        #           hsh%DATA_ID_COUNT)%VNODE_COUNT
        vnode_id = hsh%VNODE_COUNT

        node_id = vnode2node[vnode_id]
        new_node_id = new_vnode2node[vnode_id]
        if node_id != new_node_id:
            moved_ids += 1

        node_counts[node_id] += 1
        new_node_counts[new_node_id] += 1


    desired_count = DATA_ID_COUNT/NODE_COUNT
    max_count = max(node_counts)
    min_count = min(node_counts)

    over = '{0:.3f}%'.format(
            100.0*(max_count - desired_count)/desired_count)
    under = '{0:.3f}%'.format(
            100.0*(desired_count - min_count)/desired_count)
    percent_moved = '{0:.3f}%'.format(0)

    new_desired_count = DATA_ID_COUNT/NEW_NODE_COUNT
    new_max_count = max(new_node_counts)
    new_min_count = min(new_node_counts)

    new_over = '{0:.3f}%'.format(
            100.0*(new_max_count - new_desired_count)/desired_count)
    new_under = '{0:.3f}%'.format(
            100.0*(new_desired_count - new_min_count)/desired_count)
    new_percent_moved = '{0:.3f}%'.format(100.0*moved_ids/DATA_ID_COUNT)

    print '{0:>8}{1:>8}{2:>8}{3:>8}{4:>8}{5:>8}{6:>12}{7:>10}{8:>10}'.format(
            NODE_COUNT, desired_count, max_count, min_count, over, under, 0, 'const2', VNODE_COUNT)
    print '{0:>8}{1:>8}{2:>8}{3:>8}{4:>8}{5:>8}{6:>12}{7:>10}{8:>10}'.format(
            NEW_NODE_COUNT, new_desired_count, new_max_count, new_min_count,
            new_over, new_under, new_percent_moved, 'const2', VNODE_COUNT)
    print ''




if __name__ == '__main__':
    #start here....
    begin_time = time.time()

    print '{0:>8}{1:>8}{2:>8}{3:>8}{4:>8}{5:>8}{6:>12}{7:>10}{8:>10}'.format(
            'nodecnt', 'desire', 'max', 'min', 'over', 'under', 'movecnt', 'type','vnodecnt')

    comm_hash()
    const_hash_one()
    for vnode_count in (1000, 10000, 100000):
        const_hash_two(vnode_count)

    end_time = time.time()


    print 'cost {0}s'.format(
            int(end_time - begin_time))






