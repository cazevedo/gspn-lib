#! /usr/bin/env python3
from gspn_lib import gspn as pn
import xml.etree.ElementTree as et  # XML parser
from graphviz import Digraph

class GSPNtools(object):
    @staticmethod
    def import_xml(file):
        list_gspn = []  # list of parsed GSPN objects
        gspn = pn.GSPN()

        tree = et.parse(file)  # parse XML with ElementTree
        root = tree.getroot()

        for petrinet in root.iter('net'):
            n_places = len(list(petrinet.iter('place')))
            place_name = ['']*n_places
            place_marking = [0]*n_places
            id2place = {}

            # iterate over all places of the petri net
            for i, pl in enumerate(petrinet.iter('place')):
                # get place name encoded as 'id' in the pnml structure
                place_name[i] = pl.find('./name/value').text

                text = pl.find('./initialMarking/value').text
                # get place marking encoded inside 'initalMarking', as the 'text' of the key 'value'
                place_marking[i] = int(text.split(',')[-1])

                id2place[pl.get('id')] = place_name[i]

            # add the list of places to the gspn object
            gspn.add_places(name=list(place_name), ntokens=place_marking, set_initial_marking=True)

            n_transitions = len(list(petrinet.iter('transition')))
            transition_name = ['']*n_transitions
            transition_type = ['']*n_transitions
            transition_rate = [0]*n_transitions
            id2transition= {}

            # iterate over all transitions of the petri net
            for i, tr in enumerate(petrinet.iter('transition')):
                # get transition name encoded as 'id' in the pnml structure
                transition_name[i] = tr.find('./name/value').text

                # get the transition type either exponential ('exp') or immediate ('imm')
                if tr.find('./timed/value').text == 'true':
                    transition_type[i] = 'exp'
                else:
                    transition_type[i] = 'imm'

                # get the transition fire rate or weight
                transition_rate[i] = float(tr.find('./rate/value').text)

                id2transition[tr.get('id')] = transition_name[i]

            # add the list of transitions to the gspn object
            gspn.add_transitions(list(transition_name), transition_type, transition_rate)

            arcs_in = {}
            arcs_out = {}

            # iterate over all arcs of the petri net
            for arc in petrinet.iter('arc'):
                source = arc.get('source')
                target = arc.get('target')

                # IN arc connection (from place to transition)
                if source in id2place:
                    pl = id2place[source]
                    tr = id2transition[target]

                    if pl in arcs_in:
                        arcs_in[pl].append(tr)
                    else:
                        arcs_in[pl] = [tr]

                # OUT arc connection (from transition to place)
                elif source in id2transition:
                    tr = id2transition[source]
                    pl = id2place[target]

                    if tr in arcs_out:
                        arcs_out[tr].append(pl)
                    else:
                        arcs_out[tr] = [pl]

            gspn.add_arcs(arcs_in, arcs_out)

            list_gspn.append(gspn)

        return list_gspn

    @staticmethod
    def import_greatspn(file):
        list_gspn = []  # list of parsed GSPN objects

        tree = et.parse(file)  # parse XML with ElementTree
        root = tree.getroot()

        for proj in root.iter('project'):
            for petri_net in proj.iter('gspn'):
                gspn = pn.GSPN()

                for node in petri_net.iter('nodes'):
                    n_places = len(list(node.iter('place')))
                    place_name = [''] * n_places
                    place_marking = [0] * n_places

                    for i, place in enumerate(node.iter('place')):
                        place_name[i] = place.get('name')
                        pm = place.get('marking')
                        if pm != None:
                            place_marking[i] = int(pm)

                    # print(place_name)
                    # print(place_marking)
                    gspn.add_places(name=list(place_name), ntokens=place_marking, set_initial_marking=True)

                    n_transitions = len(list(node.iter('transition')))
                    transition_name = [''] * n_transitions
                    transition_type = [''] * n_transitions
                    transition_rate = [0.0] * n_transitions

                    for i, transition in enumerate(node.iter('transition')):
                        transition_name[i] = transition.get('name')

                        tr_type = transition.get('type')
                        if tr_type == 'IMM':
                            transition_type[i] = 'imm'
                            if transition.get('weight') != None:
                                transition_rate[i] = float(transition.get('weight'))
                        elif tr_type == 'EXP':
                            transition_type[i] = 'exp'
                            if transition.get('delay') != None:
                                transition_rate[i] = float(transition.get('delay'))
                        else:
                            raise Exception(tr_type+' is an incorrect transition type.')

                    # print(transition_name, transition_type, transition_rate)
                    gspn.add_transitions(list(transition_name), transition_type, transition_rate)

                for edge in petri_net.iter('edges'):
                    # IN arc connection (from place to transition)
                    arcs_in = {}
                    # OUT arc connection (from transition to place)
                    arcs_out = {}

                    for arc in edge.iter('arc'):
                        # future implementations that may require multiple arc weights should use: arc.get('mult')
                        if arc.get('kind') == 'INPUT':
                            if arc.get('tail') in place_name and arc.get('head') in transition_name:
                                if arc.get('tail') in arcs_in:
                                    arcs_in[arc.get('tail')].append(arc.get('head'))
                                else:
                                    arcs_in[arc.get('tail')] = [arc.get('head')]
                            else:
                                raise Exception('Incorrect order in INPUT arc '+arc.get('head')+' to '+arc.get('tail'))
                        elif arc.get('kind') == 'OUTPUT':
                            if  arc.get('tail') in transition_name and arc.get('head') in place_name:
                                if arc.get('tail') in arcs_out:
                                    arcs_out[arc.get('tail')].append(arc.get('head'))
                                else:
                                    arcs_out[arc.get('tail')] = [arc.get('head')]
                            else:
                                raise Exception(
                                    'Incorrect order in OUTPUT arc ' + arc.get('head') + ' to ' + arc.get('tail'))
                        else:
                            raise Exception(arc.get('kind')+' is an incorrect arc type.')

                    # print(arcs_in)
                    # print(arcs_out)
                    gspn.add_arcs(arcs_in, arcs_out)

                list_gspn.append(gspn)

        return list_gspn

    @staticmethod
    def draw_enabled_transitions(gspn, gspn_draw, file='gspn_default', show=True):
        enabled_exp_transitions, random_switch = gspn.get_enabled_transitions()

        if random_switch:
            for transition in random_switch.keys():
                gspn_draw.node(transition, shape='rectangle', style='filled', color='red', label='', xlabel=transition, height='0.2', width='0.6', fixedsize='true')

            gspn_draw.render(file + '.gv', view=show)
        elif enabled_exp_transitions:
            for transition in enabled_exp_transitions.keys():
                gspn_draw.node(transition, shape='rectangle', color='red', label='', xlabel=transition, height='0.2', width='0.6', fixedsize='true')

            gspn_draw.render(file + '.gv', view=show)

        return gspn_draw

    @staticmethod
    def draw_gspn(gspn, file='gspn_default', show=True):

        # ref: https://www.graphviz.org/documentation/
        gspn_draw = Digraph(engine='dot')

        gspn_draw.attr('node', forcelabels='true')

        # draw places and marking
        plcs = gspn.get_current_marking()
        for place, marking in plcs.items():
            if int(marking) == 0:
                gspn_draw.node(place, shape='circle', label='', xlabel=place, height='0.6', width='0.6', fixedsize='true')
            else:
                # places with more than 4 tokens cannot fit all of them inside it
                if int(marking) < 5:
                    lb = '<'
                    for token_number in range(1, int(marking)+1):
                        lb = lb + '&#9899; '
                        if token_number % 2 == 0:
                            lb = lb + '<br/>'
                    lb = lb + '>'
                else:
                    lb = '<&#9899; x ' + str(int(marking)) + '>'

                gspn_draw.node(place, shape='circle', label=lb, xlabel=place, height='0.6', width='0.6', fixedsize='true')

        # draw transitions
        trns = gspn.get_transitions()
        for transition, value in trns.items():
            if value[0] == 'exp':
                gspn_draw.node(transition, shape='rectangle', color='black', label='', xlabel=transition, height='0.2', width='0.6', fixedsize='true')
            else:
                gspn_draw.node(transition, shape='rectangle', style='filled', color='black', label='', xlabel=transition, height='0.2', width='0.6', fixedsize='true')

        # draw edges
        edge_in, edge_out = gspn.get_arcs()
        for iterator, place_index in enumerate(edge_in.coords[0]):
            transition_index = edge_in.coords[1][iterator]
            gspn_draw.edge(gspn.index_to_places[place_index], gspn.index_to_transitions[transition_index])
        for iterator, transition_index in enumerate(edge_out.coords[0]):
            place_index = edge_out.coords[1][iterator]
            gspn_draw.edge(gspn.index_to_transitions[transition_index], gspn.index_to_places[place_index])

        gspn_draw.render(file+'.gv', view=show)

        return gspn_draw
