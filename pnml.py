import pm4py
from pm4py.read import read_pnml

from pm4py.visualization.petri_net import visualizer
from pm4py.objects.petri_net.utils import final_marking as final_marking_discovery

net, initial_marking, final_marking = read_pnml("data/IP-1_composition_mined.pnml")

if not final_marking:
    final_marking = final_marking_discovery.discover_final_marking(net)
    print("⚠️ No final marking defined in PNML — generated a heuristic one.")


gviz = visualizer.apply(net, initial_marking, final_marking)
visualizer.save(gviz, "data/pnml_diagram_conposition_mined.png")
