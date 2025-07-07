from pm4py.algo.discovery.inductive import algorithm as im_algorithm
from pm4py.algo.discovery.inductive.variants import im, imd, imf
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py import view_petri_net, view_process_tree, read_pnml, write_pnml
import pm4py
from pm4py.objects.log.util.log import get_event_labels
#import pm4py.filtering.filter_event_attribute_values as filter_event_attribute_values
from pm4py.objects.petri_net.utils.petri_utils import remove_arc, remove_transition, remove_place, add_arc_from_to, pre_set, post_set, get_arc_type

from pm4py.objects.petri_net.utils.check_soundness import check_source_place_presence as check_source_place_presence
from pm4py.objects.petri_net.utils.check_soundness import check_sink_place_presence as check_sink_place_presence    

from pm4py.objects.petri_net.utils.initial_marking import discover_initial_marking
from pm4py.objects.petri_net.utils.final_marking import discover_final_marking


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

    view_petri_net(net,im,fm) 
    #save the Petri net to a file
    write_pnml(net, im, fm, f"./data/projected_pnml/petri_net_{log_file_path.split('/')[-1].split('.')[0]}.pnml")

    return net, im, fm


def projection_based_on_organization(raw_log=None):

    org_list= get_event_labels(raw_log, key="org:resource")# TODO check if this is the same for all logs 
    print(org_list)

    for org in org_list:
        filtered_log = pm4py.filter_event_attribute_values(raw_log, values=org, level='event', attribute_key="org:resource")
        # save the filtered log to a file
        pm4py.write_xes(filtered_log, f"./data/filtered_log_{org}.xes")
        print(f"Filtered log for organization {org}:")


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


    if source is not None:
        # remove the source place and its outgoing arcs
        net_edited=remove_place(net,source)
    if sink is not None: 
        net_edited=remove_place(net,sink)

    # identify the initial and final markings for the Petri net withour source and sink
    im_edited=discover_initial_marking(net_edited)
    fm_edited=discover_final_marking(net_edited)

    view_petri_net(net_edited,im_edited,fm_edited)
    write_pnml(net, im, fm, f"./data/post_processed_pnml/petri_net_{log_file_path.split('/')[-1].split('.')[0]}.pnml")

    return net
    

def t_jn_check():
    '''check if the Workflow is t-JN '''
    #TODO impliment the rules that's in def 10 
    pass 


def add_identifiers():
    '''add identifiers for each place (circle) and arc (arrow) in the Petri net'''
    #TODO 
    pass


def compose():
    '''compose the sub models into a single model'''
    #TODO 
    # first compose the petrinet together
    # find out the shared places and arcs
    #add the shared places and arcs to the new Petri net
    #remove the minor places and arcs
    #final model


    pass



if __name__ == "__main__":

    parameters = {
            'MAX_TRACES': 100
        }
    raw_log = xes_importer.apply('data/IP-1_initial_log.xes')
    orgs=projection_based_on_organization(raw_log)

    for org in orgs:
        print(f"Applying inductive miner for organization {org}")
        net,im, fm =apply_inductive_miner(log_file_path=f"./data/filtered_log_{org}.xes")
        post_processing(log_file_path=f"./data/projected_pnml/petri_net_filtered_log_{org}.pnml")
