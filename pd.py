from pm4py.objects.log.importer.xes import importer as xes_importer

from pm4py.algo.discovery.dfg import algorithm as dfg_discovery
from pm4py.visualization.dfg import visualizer as dfg_visualization
import graphviz


# Parameters for streaming (chunk size)
parameters = {
    'MAX_TRACES': 5
}

# Stream the log
log = xes_importer.apply('data/IP-1_initial_log.xes', parameters=parameters)

limited_log = log[:1]  # take only first 5 traces
dfg = dfg_discovery.apply(limited_log)
gviz = dfg_visualization.apply(dfg, log=limited_log, variant=dfg_visualization.Variants.FREQUENCY)

# Save the diagram to a file (e.g., PNG and PDF)
dfg_visualization.save(gviz, "data/dfg_diagram1.png")

limited_log = log[1:2]

dfg = dfg_discovery.apply(limited_log)
gviz = dfg_visualization.apply(dfg, log=limited_log, variant=dfg_visualization.Variants.FREQUENCY)
# Save the diagram to a file (e.g., PNG and PDF)
dfg_visualization.save(gviz, "data/dfg_diagram2.png")

limited_log = log[2:3]
dfg = dfg_discovery.apply(limited_log)
gviz = dfg_visualization.apply(dfg, log=limited_log, variant=dfg_visualization.Variants.FREQUENCY)
# Save the diagram to a file (e.g., PNG and PDF)
dfg_visualization.save(gviz, "data/dfg_diagram3.png")


# Optionally, view the diagram
dfg_visualization.view(gviz)