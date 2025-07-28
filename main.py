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
        pm4py.write_xes(filtered_log, f"./data/projected_xes/{org}.xes")

    return org_list





def custom_petri_net_visualization(file_name,title="Petri Net with Organization Labels"):
    try:
        print(f"Creating custom Petri net visualization for ...")

        tree = ET.parse(file_name)
        root = tree.getroot()

        dot = graphviz.Digraph(comment=f'Petri Net for ')
        dot.attr(rankdir='LR')
        dot.attr('graph', label=f'{title} - ', labelloc='t', fontsize='16')

        # Visualize Places
        for place in root.findall(".//place"):
            place_id = place.get("id")

            # Get name
            name_node = place.find("name/text")
            place_name = name_node.text if name_node is not None else place_id

            # Get type (if any)
            type_node = place.find("type/text")
            type_text = type_node.text if type_node is not None else "no type"

            label = f"{place_name}\\n{type_text}"

            dot.node(
                place_id,
                label=label,
                shape='circle',
                style='solid',
                fontsize='10',
                width='1.2'
            )

        # Visualize Transitions
        for transition in root.findall(".//transition"):
            trans_id = transition.get("id")

            label_node = transition.find("name/text")
            label = label_node.text if label_node is not None else "τ"

            dot.node(
                trans_id,
                label=label,
                shape='box',
                style='solid',
                fontsize='10',
                width='1.0'
            )

        # Visualize Arcs
        for arc in root.findall(".//arc"):
            arc_id = arc.get("id")
            source = arc.get("source")
            target = arc.get("target")

            id_node = arc.find("identifier/text")
            arc_label = id_node.text if id_node is not None else "no identifier"

            dot.edge(
                source,
                target,
                label=arc_label,
                fontsize='8',
                color='black',
                fontcolor='black'
            )

        # Save SVG and DOT
        output_dir = "./data/edited_processed_pnml"
        os.makedirs(output_dir, exist_ok=True)
        base_filename = os.path.splitext(os.path.basename(file_name))[0]
        output_file = os.path.join(output_dir, f"{base_filename}_")

        dot.render(output_file, format='svg', view=True, cleanup=True)
        dot.save(f"{output_file}.dot")

        print(f"Visualization saved to: {output_file}.svg and .dot")
        return True

    except Exception as e:
        print(f"Custom visualization failed for : {e}")
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
        post_processing_customized(log_file_path)

        return True






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
            
            pnml_file_path = f'./data/post_processed_pnml/{log_file_path.split("/")[-1].split(".")[0]}.pnml'  

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

    parameters = {
            'MAX_TRACES': 100
        }
    raw_log = xes_importer.apply('data/IP-1_initial_log.xes')
    orgs=projection_based_on_organization(raw_log)

    print(f"Processing {len(orgs)} organizations: {orgs}")
    
    for org in orgs:
        print(f"\n--- Processing {org} ---")
        net,im, fm =apply_inductive_miner(log_file_path=f"./data/projected_xes/{org}.xes")
        
        add_identifiers(log_file_path=f"./data/first_pnml/{org}.pnml", org=org)
        custom_petri_net_visualization(file_name=f"./data/post_processed_pnml/{org}.pnml", title=f"Petri Net for {org}")