from numpy import save
from pm4py.algo.discovery.inductive import algorithm as im_algorithm
from pm4py.algo.discovery.inductive.variants import im, imd, imf
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py import view_petri_net, view_process_tree, read_pnml, write_pnml
import pm4py
from pm4py.objects.log.util.log import get_event_labels
import graphviz
import tempfile
import os
import xml.etree.ElementTree as ET
#import pm4py.filtering.filter_event_attribute_values as filter_event_attribute_values
from pm4py.objects.petri_net.utils.petri_utils import remove_arc, remove_transition, remove_place, add_arc_from_to, pre_set, post_set, get_arc_type

from pm4py.objects.petri_net.utils.check_soundness import check_source_place_presence as check_source_place_presence
from pm4py.objects.petri_net.utils.check_soundness import check_sink_place_presence as check_sink_place_presence    

from pm4py.objects.petri_net.utils.initial_marking import discover_initial_marking
from pm4py.objects.petri_net.utils.final_marking import discover_final_marking
from pm4py.objects.petri_net.obj import PetriNet, Marking


def apply_inductive_miner(log_file_path):
    '''
    apply the inductive miner( basic algorithm) to a log file

    '''
  
    # Stream the log
    log = xes_importer.apply(log_file_path)
   

    # Apply the Inductive Miner algorithm Basic # TODO there's also imf and imd variants
    process_tree = im_algorithm.apply(log)

    #view_process_tree(process_tree)

    net,im,fm=pm4py.convert_to_petri_net(process_tree)

   # view_petri_net(net,im,fm) 
    #save the Petri net to a file
    write_pnml(net, im, fm, f"./data/first_pnml/{log_file_path.split('/')[-1].split('.')[0]}.pnml")

    return net, im, fm


def projection_based_on_organization(raw_log=None):

    org_list= get_event_labels(raw_log, key="org:resource")# TODO check if this is the same for all logs 

    for org in org_list:
        filtered_log = pm4py.filter_event_attribute_values(raw_log, values=org, level='event', attribute_key="org:resource")
        # save the filtered log to a file
        pm4py.write_xes(filtered_log, f"./data/projected_xes/filtered_log_{org}.xes")

    return org_list



def post_processing(log_file_path):
    '''Remove the Source and Sink from the Petri net
    
    ''' 
    # https://pm4py-source.readthedocs.io/en/stable/pm4py.objects.petri.html#module-pm4py.objects.petri.utils
    #TODO impliment the rules that's in def 10 
    net,im,fm=read_pnml(log_file_path)

    source = check_source_place_presence(net)
    sink = check_sink_place_presence(net)

    net_edited=net
    print(sink)


    if source is not None:
        # remove the source place and its outgoing arcs
        net_edited=remove_place(net,source)
    if sink is not None: 
        net_edited=remove_place(net,sink)

    # identify the initial and final markings for the Petri net withour source and sink
    im_edited=discover_initial_marking(net_edited)
    fm_edited=discover_final_marking(net_edited)

  #  view_petri_net(net_edited,im_edited,fm_edited)
    # Save the edited Petri net to a file
    new_path=f'./data/post_processed/{log_file_path.split("/")[-1].split(".")[0]}.pnml'
    write_pnml(net_edited, im_edited, fm_edited, new_path)

    return net_edited, im_edited, fm_edited

def post_processing_customized(log_file_path):
        try:
            tree = ET.parse(log_file_path   )
            root = tree.getroot()
            for net in root.findall('.//net'):
                for fm in net.findall('finalmarkings'):
                    net.remove(fm)
                for im in net.findall('initialmarkings'):
                    net.remove(im)

                for page in net.findall('page'):
                    # Remove source/sink places
                    for place in page.findall('place'):
                        if place.get('id') in ['source', 'sink']:
                            page.remove(place)

                    # Remove arcs linked to source/sink
                    for arc in page.findall('arc'):
                        if arc.get('source') in ['source', 'sink'] or arc.get('target') in ['source', 'sink']:
                            page.remove(arc)
            
            pnml_file_path = f'./data/post_processed_pnml/{log_file_path.split("/")[-1].split(".")[0]}_edited.pnml'  

            tree.write(pnml_file_path, encoding='UTF-8', xml_declaration=True)
            return True
        except Exception as e:
            print(f"Failed to add type properties to {pnml_file_path}: {e}")
            return False


    
def custom_petri_net_visualization(net, im, fm, org, title="Petri Net with Organization Labels"):
    """
    Create a custom Petri net visualization using Graphviz that shows arc identifiers and place types
    """
    try:
        print(f"Creating custom Petri net visualization for {org}...")
        # Create a new directed graph
        dot = graphviz.Digraph(comment=f'Petri Net for {org}')
        dot.attr(rankdir='LR')
        dot.attr('graph', label=f'{title} - {org}', labelloc='t', fontsize='16')
        
        # Add places (circles)
        for place in net.places:

            type = place.properties.get('type', [])

            # Create label with place name and organization info
            place_name = place.name
           # place_label = f"{place_name}\\n{type}"
            place_label = f"{','.join( type)}" if type else f"no type"
            place_label = f"{place_name}\\n{place_label}"

            # Style for places
            dot.node(
                str(id(place)), 
                label=place_label,
                shape='circle',
                style='solid',
                fontsize='10',
                width='1.2'
            )
        
        # Add transitions (rectangles)
        for transition in net.transitions:
            label = transition.label if transition.label else "τ"
            dot.node(
                str(id(transition)), 
                label=label,
                shape='box',
                style='solid',
                fontsize='10',
                width='1.0'
            )
        
        # Add arcs with labels
        for arc in net.arcs:
            identifiers = arc.properties.get('identifiers', [])
            arc_label = f"{','.join(identifiers)}" if identifiers else f"no identifier"
            
            dot.edge(
                str(id(arc.source)),
                str(id(arc.target)),
                label=arc_label,
                fontsize='8',
                color='black',
                fontcolor='black'
            )
        
        # Save to data directory for SVG
        output_dir = "./data/edited_processed_pnml"
        #output_dir="./data"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        output_file = os.path.join(output_dir, f'filtered_log_{org}')
        
        # Render as SVG and open automatically
        dot.render(output_file, format='svg', view=True, cleanup=True)

        # O
        # I want to save the dot file to pnml 
        # Save PNML format to edited_processed_pnml directory

    #     # Save PNML format to edited_processed_pnml directory
    #     edited_dir = "./data/edited_processed_pnml"
    #     if not os.path.exists(edited_dir):
    #         os.makedirs(edited_dir)
        
    #     pnml_output_file = os.path.join(edited_dir, f'filtered_log_{org}.pnml')
    #     write_pnml(net, im, fm, pnml_output_file)
    # #     #view_petri_net(net, im, fm)
        
    #     # Add type properties to places in the PNML file
    #    # add_type_properties_to_pnml(pnml_output_file, org)
        
    #     print(f"Custom Petri net visualization saved: {output_file}.svg and {pnml_output_file}")
        return True
        
    except Exception as e:
        print(f"Custom visualization failed for {org}: {e}")
        return False




def t_jn_check():
    '''check if the Workflow is t-JN '''
    #TODO impliment the rules that's in def 10 



    pass 



def add_identifiers(log_file_path, org):
        '''
        Add types / identifiers for each place (circle) and arc (arrow) in the Petri net
        place: place type (jn_type)
        arc: multi set of identifiers
        '''
        
        add_type_properties_to_pnml(log_file_path, org)
        add_identifier_properties_to_pnml(log_file_path, org)
        #net, im, fm=post_processing(log_file_path) todo customize post processing 
        post_processing_customized(log_file_path)

        net, im, fm = read_pnml(log_file_path)

        # 
        # Add identifiers to arcs
        for arc in net.arcs:
            if "identifiers" not in arc.properties:
                arc.properties["identifiers"] = []
            arc.properties["identifiers"].append(org)

        # Add type (type) directly to place properties
        for place in net.places:
            if "type" not in place.properties:
                place.properties["type"] = []
            place.properties["type"].append(org)


        success = custom_petri_net_visualization(net, im, fm, org)

        if not success:
            view_petri_net(net, im, fm, debug=True)

        return net, im, fm


def add_type_properties_to_pnml(pnml_file_path, org):
        """
        Add <type> properties to places in a PNML file (for tools that read PNML directly)
        """
        try:
            tree = ET.parse(pnml_file_path)
            root = tree.getroot()
            for place in root.findall('.//place'):
                type_elem = ET.SubElement(place, 'type')
                type_text = ET.SubElement(type_elem, 'text')
                type_text.text = org
            tree.write(pnml_file_path, encoding='UTF-8', xml_declaration=True)
            return True
        except Exception as e:
            print(f"Failed to add type properties to {pnml_file_path}: {e}")
            return False


def add_identifier_properties_to_pnml(pnml_file_path, org):
        """
        Add <identifier> properties to arcs in a PNML file (for tools that read PNML directly)
        """
        try:
            tree = ET.parse(pnml_file_path)
            root = tree.getroot()
            for arc in root.findall('.//arc'):
                type_elem = ET.SubElement(arc, 'identifier')
                type_text = ET.SubElement(type_elem, 'text')
                type_text.text = org
            tree.write(pnml_file_path, encoding='UTF-8', xml_declaration=True)
            return True
        except Exception as e:
            print(f"Failed to add type properties to {pnml_file_path}: {e}")
            return False




def get_shared_places_and_arcs(pnml_files):
    """
    Identify shared places and arcs across multiple PNML files
    """
    shared_places = set()
    shared_arcs = set()

    for file_path in pnml_files:
        net, im, fm = read_pnml(file_path)
        for place in net.places:
            shared_places.add(place.name)
        for arc in net.arcs:
            shared_arcs.add((arc.source.name, arc.target.name))

    return shared_places, shared_arcs   


def compose(pnml_files,org):
    '''Compose the sub models into a single model.'''
    # Combine the Petri nets together.
    # Find out the shared places and arcs.
    # Add the shared places and arcs to the new Petri net.
    # Remove the minor places and arcs.
    # Final model.

    # When you compose them together, you could also
    # find out those arcs that are not unique.
    # Then find out the arcs with the same source and
    # target.

    total_places = set()
    total_arcs = set()
    total_transitions = set()

    for file_path in pnml_files:
        net, marking_in, marking_out = read_pnml(file_path)
        # Process the net, marking_in, marking_out as needed.
        # For example, you can print the places and transitions.
        print(f"Processing {file_path}:")
        print(f"Places: {[place.name for place in net.places]}")
        print(f"Transitions: {[transition.label for transition in net.transitions]}")
        total_places.update(place for place in net.places)
        total_arcs.update(arc for arc in net.arcs)
        total_transitions.update(transition for transition in net.transitions)

    # Create a new Petri net with the combined places, transitions, and arcs.
    new_net = PetriNet("composed_net")
    for place in total_places:
        new_net.places.add(place)
    for transition in total_transitions:
        new_net.transitions.add(transition)
    for arc in total_arcs:
        new_net.arcs.add(arc)

    # Collect initial and final markings from all nets.
    composed_initial_marking = Marking()
    composed_final_marking = Marking()
    for file_path in pnml_files:
        _, marking_in, marking_out = read_pnml(file_path)
        if marking_in is not None:
            for place, tokens in marking_in.items():
                composed_initial_marking[place] = composed_initial_marking.get(place, 0) + tokens
        if marking_out is not None:
            for place, tokens in marking_out.items():
                composed_final_marking[place] = composed_final_marking.get(place, 0) + tokens

    write_pnml(new_net, composed_initial_marking, composed_final_marking, f"./data/composed_pnml/composed_net.pnml")

   

    
    return new_net, composed_initial_marking, composed_final_marking

    return new_net, initial_marking, final_marking



if __name__ == "__main__":

    # first: projected_xes
    # second: base_pnml
    # third: edited_processed_pnml

    # parameters = {
    #         'MAX_TRACES': 100
    #     }
    # raw_log = xes_importer.apply('data/IP-1_initial_log.xes')
    # orgs=projection_based_on_organization(raw_log)

    # print(f"Processing {len(orgs)} organizations: {orgs}")
    
    # for org in orgs:
    #     print(f"\n--- Processing {org} ---")
    #     net,im, fm =apply_inductive_miner(log_file_path=f"./data/projected_xes/filtered_log_{org}.xes")
        
    #     net_with_ids, im_with_ids, fm_with_ids = add_identifiers(log_file_path=f"./data/first_pnml/filtered_log_{org}.pnml", org=org)
    #    # net, im,fm=  post_processing(log_file_path=f"./data/first_pnml/filtered_log_{org}.pnml")
     #   custom_petri_net_visualization(net,im,fm,org)
     #   save_files(dot, net, im, fm, org)
    # orgs = ['Agent 1', 'Agent 2']  # Example organizations
        
    # compose_pnml_files = [f"./data/edited_processed_pnml/filtered_log_{org}.pnml" for org in orgs]
    # composed_net, initial_marking, final_marking = compose(compose_pnml_files, orgs)  
    post_processing_customized(log_file_path=f"./data/first_pnml/filtered_log_Agent 1.pnml")