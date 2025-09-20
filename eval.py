'''
Firness,precision.... metrics for the Petri net

'''


import pm4py
from pm4py.algo.conformance.alignments.petri_net import algorithm as alignments
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.conversion.process_tree import converter as pt_converter
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.petri_net.importer import importer as pnml_importer
from pm4py.algo.conformance.tokenreplay import algorithm as token_replay
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.utils.final_marking import discover_final_marking
from pm4py.objects.petri_net.utils.initial_marking import discover_initial_marking


# from pm4py.algo.evaluation.replay_fitness.variants import entropy as entropy_fitness
# from pm4py.algo.evaluation.precision.variants import entropy as entropy_precision

# Load event log
def eval(xes,pnml):

    log = pm4py.read_xes(xes)

    # Load Petri net model
    net, im, fm = pm4py.read_pnml(pnml)

    im =discover_initial_marking(net)
    print("Initial marking:", im )
    print("Length of initial marking:", len(im))

    fm = discover_final_marking(net)   
    print("Discovered final marking:", fm)
    print(len(fm))

    print(im)

    fitness=pm4py.fitness_alignments(log, net, im, fm)

    precision=pm4py.precision_alignments(log, net, im, fm,multi_processing=False)
    print('Fitness:', fitness)
    print('Precision:', precision)




# maybe add back and try

if __name__ == "__main__":
    # for number_ in range(1,6):
    #     print(f'###############{number_}###############')

        xes_file=f'/Users/xufanlu/Projects/Process Mining/Process-Discovery-Typed-Jackson-Nets/data/original_xes_file/healthcare_collectivelog.xes'
        pnml_file=f'/Users/xufanlu/Projects/Process Mining/Process-Discovery-Typed-Jackson-Nets/data/healthcare_collectivelog/fully_composed_pnml/composed_healthcare_collectivelog.pnml'

        eval(xes_file, pnml_file)
    # pnml_file="/Users/xufanlu/Projects/Process Mining/Process-Discovery-Typed-Jackson-Nets/data/art1_collectivelog/fully_composed_pnml/composed_art1_collectivelog.pnml"
    # xes_file="/Users/xufanlu/Projects/Process Mining/Process-Discovery-Typed-Jackson-Nets/data/original_xes_file/art1_collectivelog.xes"
    # eval(xes_file, pnml_file)