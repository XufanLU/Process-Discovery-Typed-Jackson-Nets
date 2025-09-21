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

# import pm4py.filtering.filter_event_attribute_values as filter_event_attribute_values
from pm4py.objects.petri_net.utils.petri_utils import (
    remove_arc,
    remove_transition,
    remove_place,
    add_arc_from_to,
    pre_set,
    post_set,
    get_arc_type,
)

from pm4py.objects.petri_net.utils.check_soundness import (
    check_source_place_presence as check_source_place_presence,
)
from pm4py.objects.petri_net.utils.check_soundness import (
    check_sink_place_presence as check_sink_place_presence,
)

from pm4py.objects.petri_net.utils.initial_marking import discover_initial_marking
from pm4py.objects.petri_net.utils.final_marking import discover_final_marking
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.log.obj import EventLog, Trace

from copy import deepcopy

import random
import string


def apply_inductive_miner(log_file_path, original_file_name=None):
    """
    apply the inductive miner( basic algorithm) to a log file

    """

    # Stream the log
    log = xes_importer.apply(log_file_path)

    # Apply the Inductive Miner algorithm Basic # TODO there's also imf and imd variants
    process_tree = im_algorithm.apply(log)

    # view_process_tree(process_tree)

    net, im, fm = pm4py.convert_to_petri_net(process_tree)

    # view_petri_net(net,im,fm)
    # save the Petri net to a file
    write_pnml(
        net,
        im,
        fm,
        f"./data/{original_file_name}/first_pnml/{log_file_path.split('/')[-1].split('.')[0]}.pnml",
    )

    return net, im, fm


def projection_based_on_organization_collectivelog(
    raw_log=None, original_file_name=None
):

    org_list = get_event_labels(
        raw_log, key="org:group"
    )  # TODO check if this is the same for all logs

    for org in org_list:
        filtered_log = pm4py.filter_event_attribute_values(
            raw_log, values=org, level="event", attribute_key="org:group"
        )
        # save the filtered log to a file
        pm4py.write_xes(
            filtered_log, f"./data/{original_file_name}/projected_xes/{org}.xes"
        )

    return org_list


def projection_based_on_organization_1(raw_log=None, original_file_name=None):

    org_list = get_event_labels(
        raw_log, key="org:resource"
    )  # TODO check if this is the same for all logs

    for org in org_list:
        filtered_log = pm4py.filter_event_attribute_values(
            raw_log, values=org, level="event", attribute_key="org:resource"
        )
        # save the filtered log to a file
        pm4py.write_xes(
            filtered_log, f"./data/{original_file_name}/projected_xes/{org}.xes"
        )

    return org_list


def projection_based_on_organization_ip2(raw_log=None, original_file_name=None):  # r

    # Define agent assignment rules
    def get_agent(concept_name):
        if concept_name.startswith("a!") or concept_name.startswith("b!"):
            return "t"
        elif concept_name.startswith("a?") or concept_name.startswith("b?"):
            return "q"
        elif concept_name.startswith("t"):
            return "t"
        elif concept_name.startswith("q"):
            return "q"
        return None

    agent_logs = {"t": EventLog(), "q": EventLog()}
    # Copy log attributes if present (update in place, do not assign)
    for agent_key in agent_logs:
        if hasattr(raw_log, "attributes"):
            agent_logs[agent_key].attributes.update(raw_log.attributes)
        if hasattr(raw_log, "extensions"):
            agent_logs[agent_key].extensions.update(raw_log.extensions)
        if hasattr(raw_log, "classifiers"):
            agent_logs[agent_key].classifiers.update(raw_log.classifiers)

    for trace in raw_log:
        trace_t = Trace()
        trace_q = Trace()
        if hasattr(trace, "attributes"):
            trace_attrs = dict(trace.attributes)
        else:
            trace_attrs = {}
        for event in trace:
            concept_name = event.get("concept:name", "")
            agent = get_agent(concept_name)
            if agent == "t":
                trace_t.append(event)
            elif agent == "q":
                trace_q.append(event)
        if len(trace_t) > 0:
            if trace_attrs:
                trace_t.attributes.update(trace_attrs)
            agent_logs["t"].append(trace_t)
        if len(trace_q) > 0:
            if trace_attrs:
                trace_q.attributes.update(trace_attrs)
            agent_logs["q"].append(trace_q)

    for agent_key, agent_log in agent_logs.items():
        pm4py.write_xes(
            agent_log, f"./data/{original_file_name}/projected_xes/{agent_key}.xes"
        )
    return [k for k in agent_logs if len(agent_logs[k]) > 0]


def projection_based_on_organization_ip4(
    raw_log=None, original_file_name=None
):  # a!: t . b!: e

    # Define agent assignment rules
    def get_agent(concept_name):
        if concept_name.startswith("a!") or concept_name.startswith("b?"):
            return "t"
        elif concept_name.startswith("a?") or concept_name.startswith("b!"):
            return "e"
        elif concept_name.startswith("t"):
            return "t"
        elif concept_name.startswith("e"):
            return "e"

        return None

    agent_logs = {"t": EventLog(), "e": EventLog()}
    # Copy log attributes if present (update in place, do not assign)
    for agent_key in agent_logs:
        if hasattr(raw_log, "attributes"):
            agent_logs[agent_key].attributes.update(raw_log.attributes)
        if hasattr(raw_log, "extensions"):
            agent_logs[agent_key].extensions.update(raw_log.extensions)
        if hasattr(raw_log, "classifiers"):
            agent_logs[agent_key].classifiers.update(raw_log.classifiers)

    for trace in raw_log:
        trace_t = Trace()
        trace_e = Trace()
        if hasattr(trace, "attributes"):
            trace_attrs = dict(trace.attributes)
        else:
            trace_attrs = {}
        for event in trace:
            concept_name = event.get("concept:name", "")
            agent = get_agent(concept_name)
            if agent == "t":
                trace_t.append(event)
            elif agent == "e":
                trace_e.append(event)
        if len(trace_t) > 0:
            if trace_attrs:
                trace_t.attributes.update(trace_attrs)
            agent_logs["t"].append(trace_t)
        if len(trace_e) > 0:
            if trace_attrs:
                trace_e.attributes.update(trace_attrs)
            agent_logs["e"].append(trace_e)

    for agent_key, agent_log in agent_logs.items():
        pm4py.write_xes(
            agent_log, f"./data/{original_file_name}/projected_xes/{agent_key}.xes"
        )
    return [k for k in agent_logs if len(agent_logs[k]) > 0]


def projection_based_on_organization_ip5(
    raw_log=None, original_file_name=None
):  # a!: t . b!: e

    # Define agent assignment rules
    def get_agent(concept_name):
        if (
            concept_name.startswith("a!")
            or concept_name.startswith("b!")
            or concept_name.startswith("c?")
            or concept_name.startswith("d?")
        ):
            return "t"
        elif (
            concept_name.startswith("a?")
            or concept_name.startswith("b?")
            or concept_name.startswith("c!")
            or concept_name.startswith("d!")
        ):
            return "q"
        elif concept_name.startswith("t"):
            return "t"
        elif concept_name.startswith("q"):
            return "q"

        return None

    agent_logs = {"t": EventLog(), "q": EventLog()}
    # Copy log attributes if present (update in place, do not assign)
    for agent_key in agent_logs:
        if hasattr(raw_log, "attributes"):
            agent_logs[agent_key].attributes.update(raw_log.attributes)
        if hasattr(raw_log, "extensions"):
            agent_logs[agent_key].extensions.update(raw_log.extensions)
        if hasattr(raw_log, "classifiers"):
            agent_logs[agent_key].classifiers.update(raw_log.classifiers)

    for trace in raw_log:
        trace_t = Trace()
        trace_q = Trace()
        if hasattr(trace, "attributes"):
            trace_attrs = dict(trace.attributes)
        else:
            trace_attrs = {}
        for event in trace:
            concept_name = event.get("concept:name", "")
            agent = get_agent(concept_name)
            if agent == "t":
                trace_t.append(event)
            elif agent == "q":
                trace_q.append(event)
        if len(trace_t) > 0:
            if trace_attrs:
                trace_t.attributes.update(trace_attrs)
            agent_logs["t"].append(trace_t)
        if len(trace_q) > 0:
            if trace_attrs:
                trace_q.attributes.update(trace_attrs)
            agent_logs["q"].append(trace_q)

    for agent_key, agent_log in agent_logs.items():
        pm4py.write_xes(
            agent_log, f"./data/{original_file_name}/projected_xes/{agent_key}.xes"
        )
    return [k for k in agent_logs if len(agent_logs[k]) > 0]


def projection_based_on_organization_ip6(
    raw_log=None, original_file_name=None
):  # a!: t . b!: e

    # Define agent assignment rules
    def get_agent(concept_name):
        if (
            concept_name.startswith("a!")
            or concept_name.startswith("b")
            or concept_name.startswith("c?")
            or concept_name.startswith("d")
        ):
            return "t"
        elif concept_name.startswith("a?") or concept_name.startswith("c!"):
            return "q"
        elif concept_name.startswith("t"):
            return "t"
        elif concept_name.startswith("q"):
            return "q"

        return None

    agent_logs = {"t": EventLog(), "q": EventLog()}
    # Copy log attributes if present (update in place, do not assign)
    for agent_key in agent_logs:
        if hasattr(raw_log, "attributes"):
            agent_logs[agent_key].attributes.update(raw_log.attributes)
        if hasattr(raw_log, "extensions"):
            agent_logs[agent_key].extensions.update(raw_log.extensions)
        if hasattr(raw_log, "classifiers"):
            agent_logs[agent_key].classifiers.update(raw_log.classifiers)

    for trace in raw_log:
        trace_t = Trace()
        trace_q = Trace()
        if hasattr(trace, "attributes"):
            trace_attrs = dict(trace.attributes)
        else:
            trace_attrs = {}
        for event in trace:
            concept_name = event.get("concept:name", "")
            agent = get_agent(concept_name)
            if agent == "t":
                trace_t.append(event)
            elif agent == "q":
                trace_q.append(event)
        if len(trace_t) > 0:
            if trace_attrs:
                trace_t.attributes.update(trace_attrs)
            agent_logs["t"].append(trace_t)
        if len(trace_q) > 0:
            if trace_attrs:
                trace_q.attributes.update(trace_attrs)
            agent_logs["q"].append(trace_q)

    for agent_key, agent_log in agent_logs.items():
        pm4py.write_xes(
            agent_log, f"./data/{original_file_name}/projected_xes/{agent_key}.xes"
        )
    return [k for k in agent_logs if len(agent_logs[k]) > 0]


def projection_based_on_organization_ip7(
    raw_log=None, original_file_name=None
):  # a!: t . b!: e

    # Define agent assignment rules
    def get_agent(concept_name):
        if (
            concept_name.startswith("a?")
            or concept_name.startswith("b!")
            or concept_name.startswith("c!")
        ):
            return "t"
        elif (
            concept_name.startswith("a!")
            or concept_name.startswith("b?")
            or concept_name.startswith("c?")
        ):
            return "q"
        elif concept_name.startswith("t"):
            return "t"
        elif concept_name.startswith("q"):
            return "q"

        return None

    agent_logs = {"t": EventLog(), "q": EventLog()}
    # Copy log attributes if present (update in place, do not assign)
    for agent_key in agent_logs:
        if hasattr(raw_log, "attributes"):
            agent_logs[agent_key].attributes.update(raw_log.attributes)
        if hasattr(raw_log, "extensions"):
            agent_logs[agent_key].extensions.update(raw_log.extensions)
        if hasattr(raw_log, "classifiers"):
            agent_logs[agent_key].classifiers.update(raw_log.classifiers)

    for trace in raw_log:
        trace_t = Trace()
        trace_q = Trace()
        if hasattr(trace, "attributes"):
            trace_attrs = dict(trace.attributes)
        else:
            trace_attrs = {}
        for event in trace:
            concept_name = event.get("concept:name", "")
            agent = get_agent(concept_name)
            if agent == "t":
                trace_t.append(event)
            elif agent == "q":
                trace_q.append(event)
        if len(trace_t) > 0:
            if trace_attrs:
                trace_t.attributes.update(trace_attrs)
            agent_logs["t"].append(trace_t)
        if len(trace_q) > 0:
            if trace_attrs:
                trace_q.attributes.update(trace_attrs)
            agent_logs["q"].append(trace_q)

    for agent_key, agent_log in agent_logs.items():
        pm4py.write_xes(
            agent_log, f"./data/{original_file_name}/projected_xes/{agent_key}.xes"
        )
    return [k for k in agent_logs if len(agent_logs[k]) > 0]


def projection_based_on_organization_ip8(raw_log=None, original_file_name=None):  #

    # Define agent assignment rules
    def get_agent(concept_name):
        if (
            concept_name.startswith("a!")
            or concept_name.startswith("ackA?")
            or concept_name.startswith("bR?")
            or concept_name.startswith("a?_u")
        ):
            return "t"
        elif (
            concept_name.startswith("aR?")
            or concept_name.startswith("ackB?")
            or concept_name.startswith("b?_u")
        ):
            return "r"
        elif (
            concept_name.startswith("a?")
            or concept_name.startswith("b?")
            or concept_name.startswith("ackA!")
            or concept_name.startswith("ackB!")
            or concept_name.startswith("aR!")
            or concept_name.startswith("bR!")
        ):
            return "q"
        elif concept_name.startswith("t"):
            return "t"
        elif concept_name.startswith("q"):
            return "q"
        elif concept_name.startswith("r"):
            return "r"

        return None

    agent_logs = {"t": EventLog(), "q": EventLog(), "r": EventLog()}
    # Copy log attributes if present (update in place, do not assign)
    for agent_key in agent_logs:
        if hasattr(raw_log, "attributes"):
            agent_logs[agent_key].attributes.update(raw_log.attributes)
        if hasattr(raw_log, "extensions"):
            agent_logs[agent_key].extensions.update(raw_log.extensions)
        if hasattr(raw_log, "classifiers"):
            agent_logs[agent_key].classifiers.update(raw_log.classifiers)

    for trace in raw_log:
        trace_t = Trace()
        trace_q = Trace()
        trace_r = Trace()
        if hasattr(trace, "attributes"):
            trace_attrs = dict(trace.attributes)
        else:
            trace_attrs = {}
        for event in trace:
            concept_name = event.get("concept:name", "")
            agent = get_agent(concept_name)
            if agent == "t":
                trace_t.append(event)
            elif agent == "q":
                trace_q.append(event)
            elif agent == "r":
                trace_r.append(event)
        if len(trace_t) > 0:
            if trace_attrs:
                trace_t.attributes.update(trace_attrs)
            agent_logs["t"].append(trace_t)
        if len(trace_q) > 0:
            if trace_attrs:
                trace_q.attributes.update(trace_attrs)
            agent_logs["q"].append(trace_q)
        if len(trace_r) > 0:
            if trace_attrs:
                trace_r.attributes.update(trace_attrs)
            agent_logs["r"].append(trace_r)

    for agent_key, agent_log in agent_logs.items():
        pm4py.write_xes(
            agent_log, f"./data/{original_file_name}/projected_xes/{agent_key}.xes"
        )
    return [k for k in agent_logs if len(agent_logs[k]) > 0]


def projection_based_on_organization_ip_9(
    raw_log=None, original_file_name=None
):  # a!: t . b!: e

    # Define agent assignment rules
    def get_agent(concept_name):
        if concept_name.startswith("a!") or concept_name.startswith("b?"):
            return "t"
        elif concept_name.startswith("a?") or concept_name.startswith("b!"):
            return "q"
        elif concept_name.startswith("t"):
            return "t"
        elif concept_name.startswith("q"):
            return "q"

        return None

    agent_logs = {"t": EventLog(), "q": EventLog()}
    # Copy log attributes if present (update in place, do not assign)
    for agent_key in agent_logs:
        if hasattr(raw_log, "attributes"):
            agent_logs[agent_key].attributes.update(raw_log.attributes)
        if hasattr(raw_log, "extensions"):
            agent_logs[agent_key].extensions.update(raw_log.extensions)
        if hasattr(raw_log, "classifiers"):
            agent_logs[agent_key].classifiers.update(raw_log.classifiers)

    for trace in raw_log:
        trace_t = Trace()
        trace_q = Trace()
        if hasattr(trace, "attributes"):
            trace_attrs = dict(trace.attributes)
        else:
            trace_attrs = {}
        for event in trace:
            concept_name = event.get("concept:name", "")
            agent = get_agent(concept_name)
            if agent == "t":
                trace_t.append(event)
            elif agent == "q":
                trace_q.append(event)
        if len(trace_t) > 0:
            if trace_attrs:
                trace_t.attributes.update(trace_attrs)
            agent_logs["t"].append(trace_t)
        if len(trace_q) > 0:
            if trace_attrs:
                trace_q.attributes.update(trace_attrs)
            agent_logs["q"].append(trace_q)

    for agent_key, agent_log in agent_logs.items():
        pm4py.write_xes(
            agent_log, f"./data/{original_file_name}/projected_xes/{agent_key}.xes"
        )
    return [k for k in agent_logs if len(agent_logs[k]) > 0]


def projection_based_on_organization_ip_11_12(
    raw_log=None, original_file_name=None
):  # a!: t . b!: e

    # Define agent assignment rules
    def get_agent(concept_name):
        if concept_name.startswith("a!") or concept_name.startswith("b?"):
            return "t"
        elif concept_name.startswith("a?") or concept_name.startswith("b!"):
            return "q"
        elif concept_name.startswith("t"):
            return "t"
        elif concept_name.startswith("q"):
            return "q"
        elif concept_name.startswith("s"):  # hwere, needs to be added to both agents
            return "s"
        return None

    agent_logs = {"t": EventLog(), "q": EventLog()}
    # Copy log attributes if present (update in place, do not assign)
    for agent_key in agent_logs:
        if hasattr(raw_log, "attributes"):
            agent_logs[agent_key].attributes.update(raw_log.attributes)
        if hasattr(raw_log, "extensions"):
            agent_logs[agent_key].extensions.update(raw_log.extensions)
        if hasattr(raw_log, "classifiers"):
            agent_logs[agent_key].classifiers.update(raw_log.classifiers)

    for trace in raw_log:
        trace_t = Trace()
        trace_q = Trace()
        if hasattr(trace, "attributes"):
            trace_attrs = dict(trace.attributes)
        else:
            trace_attrs = {}
        for event in trace:
            concept_name = event.get("concept:name", "")
            agent = get_agent(concept_name)
            if agent == "t":
                trace_t.append(event)
            elif agent == "q":
                trace_q.append(event)
            elif agent == "s":
                trace_t.append(event)
                trace_q.append(event)

        if len(trace_t) > 0:
            if trace_attrs:
                trace_t.attributes.update(trace_attrs)
            agent_logs["t"].append(trace_t)
        if len(trace_q) > 0:
            if trace_attrs:
                trace_q.attributes.update(trace_attrs)
            agent_logs["q"].append(trace_q)

    for agent_key, agent_log in agent_logs.items():
        pm4py.write_xes(
            agent_log, f"./data/{original_file_name}/projected_xes/{agent_key}.xes"
        )
    return [k for k in agent_logs if len(agent_logs[k]) > 0]


def custom_petri_net_visualization(
    file_name, title="Petri Net with Organization Labels", original_file_name=None
):
    try:
        print(f"Creating custom Petri net visualization for ...")

        tree = ET.parse(file_name)
        root = tree.getroot()

        dot = graphviz.Digraph(comment=f"Petri Net for ")
        dot.attr(rankdir="LR")
        dot.attr(
            "graph",
            label=f"{title} - {original_file_name}",
            labelloc="t",
            fontsize="16",
        )

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
                shape="circle",
                style="solid",
                fontsize="10",
                width="1.2",
            )

        # Visualize Transitions
        for transition in root.findall(".//transition"):

            trans_id = transition.get("id")

            label_node = transition.find("name/text")
            label = label_node.text if label_node is not None else "τ"

            if "tau" in transition.get("id") or "tau" in label_node:
                label = "τ"

                dot.node(
                    trans_id,
                    label=label,
                    shape="box",
                    style="filled",
                    fillcolor="black",
                    fontsize="10",
                    width="1.0",
                )
            else:
                dot.node(
                    trans_id,
                    label=label,
                    shape="box",
                    style="solid",
                    fontsize="10",
                    width="1.0",
                )

        # Visualize Arcs
        for arc in root.findall(".//arc"):
            arc_id = arc.get("id")
            source = arc.get("source")
            target = arc.get("target")

            # Collect all identifier values for this arc
            identifier_elems = arc.findall("identifier/text")
            if identifier_elems:
                arc_label = ", ".join(
                    [elem.text for elem in identifier_elems if elem.text is not None]
                )
            else:
                arc_label = "no identifier"

            dot.edge(
                source,
                target,
                label=arc_label,
                fontsize="8",
                color="black",
                fontcolor="black",
            )

        # Save SVG and DOT
        output_dir = f"./data/{original_file_name}/images"
        os.makedirs(output_dir, exist_ok=True)
        base_filename = os.path.splitext(os.path.basename(file_name))[0]
        output_file = os.path.join(output_dir, f"{base_filename}")

        dot.render(output_file, format="svg", view=True, cleanup=True)

        print(f"Visualization saved to: {output_file}.svg and .dot")
        return True

    except Exception as e:
        print(f"Custom visualization failed for : {e}")
        return False


def t_jn_check():
    """
    The net disc(N) is obtained from a WF-net by removing the unique source
    place and the unique sink place, together with all their incident arcs.
    Since the WF-net is discovered using the Inductive Miner, it is sound by construction.
    This means that before removing the source and sink places, the WF-net already has the
    properties required by a Typed Jackson Net. As the WF-net has exactly one source and one sink,
     these are the only places that can appear on the external boundary. After their removal,
     all boundary nodes that remain are transitions. Therefore, disc(N) is a transitions-bordered WF-net.
     Removing the source and sink does not affect the properties needed for the net to be interpreted as a Typed Jackson Net.
    """

    pass


def add_identifiers(log_file_path, org, original_file_name):
    """
    Add types / identifiers for each place (circle) and arc (arrow) in the Petri net
    place: place type (jn_type)
    arc: multi set of identifiers
    """
    add_type_properties_to_pnml(log_file_path, org)
    add_identifier_properties_to_pnml(log_file_path, org)
    post_processing_customized(log_file_path, original_file_name)
    return True


def add_type_properties_to_pnml(pnml_file_path, org):
    """
    Add <type> properties to places in a PNML file (for tools that read PNML directly)
    """
    try:
        tree = ET.parse(pnml_file_path)
        root = tree.getroot()
        for place in root.findall(".//place"):
            type_elem = ET.SubElement(place, "type")
            type_text = ET.SubElement(type_elem, "text")
            type_text.text = org
        tree.write(pnml_file_path, encoding="UTF-8", xml_declaration=True)
        return True
    except Exception as e:
        print(f"Failed to add type properties to {pnml_file_path}: {e}")
        return False


def add_identifier_properties_to_pnml(pnml_file_path, org):
    """
    Add <identifier> properties to arcs in a PNML file (for tools that read PNML directly)
    """

    try:
        # Split orgs by comma and strip whitespace
        org_list = [o.strip() for o in org.split(",")]

        # Map each org to a deterministic letter
        if not hasattr(add_identifier_properties_to_pnml, "org_map"):
            add_identifier_properties_to_pnml.org_map = {}
            add_identifier_properties_to_pnml.letters = list(
                "xyzmnabcdefghijklopqrstuvw"
            )
            random.shuffle(add_identifier_properties_to_pnml.letters)
            add_identifier_properties_to_pnml.next_idx = 0

        org_map = add_identifier_properties_to_pnml.org_map
        letter_map = {}
        for o in org_list:
            if o not in org_map:
                idx = add_identifier_properties_to_pnml.next_idx
                if idx >= len(add_identifier_properties_to_pnml.letters):
                    letter = add_identifier_properties_to_pnml.letters[
                        idx % len(add_identifier_properties_to_pnml.letters)
                    ] + str(idx // len(add_identifier_properties_to_pnml.letters))
                else:
                    letter = add_identifier_properties_to_pnml.letters[idx]
                org_map[o] = letter
                add_identifier_properties_to_pnml.next_idx += 1
            else:
                letter = org_map[o]
            letter_map[o] = letter

        tree = ET.parse(pnml_file_path)
        root = tree.getroot()
        for arc in root.findall(".//arc"):
            # Add an identifier element for each org
            for o in org_list:
                type_elem = ET.SubElement(arc, "identifier")
                type_text = ET.SubElement(type_elem, "text")
                type_text.text = letter_map[o]
        tree.write(pnml_file_path, encoding="UTF-8", xml_declaration=True)
        return True
    except Exception as e:
        print(f"Failed to add type properties to {pnml_file_path}: {e}")
        return False


def post_processing_customized(log_file_path, original_file_name):
    try:
        tree = ET.parse(log_file_path)
        root = tree.getroot()
        for net in root.findall(".//net"):
            for fm in net.findall("finalmarkings"):
                net.remove(fm)
            for im in net.findall("initialmarkings"):
                net.remove(im)

            for page in net.findall("page"):
                # Remove source/sink places
                for place in page.findall("place"):
                    if place.get("id") in ["source", "sink"]:
                        page.remove(place)

                # Remove arcs linked to source/sink
                for arc in page.findall("arc"):
                    if arc.get("source") in ["source", "sink"] or arc.get("target") in [
                        "source",
                        "sink",
                    ]:
                        page.remove(arc)

        pnml_file_path = f'./data/{original_file_name}/post_processed_pnml/{log_file_path.split("/")[-1].split(".")[0]}.pnml'

        tree.write(pnml_file_path, encoding="UTF-8", xml_declaration=True)
        return True
    except Exception as e:
        print(f"Failed to add type properties to {pnml_file_path}: {e}")
        return False


def get_shared_arcs(pnml_files):
    """
    Detect arcs with same source and target but different identifier values.
    """
    arc_map = {}  # key: (source, target), value: set of identifiers

    for file_path in pnml_files:
        tree = ET.parse(file_path)
        root = tree.getroot()
        arcs = root.findall(".//arc")

        for arc in arcs:
            source = arc.get("source")
            target = arc.get("target")
            key = (source, target)

            # Get identifier value
            identifier_node = arc.find("identifier/text")
            identifier = (
                identifier_node.text.strip() if identifier_node is not None else "no_id"
            )

            if key not in arc_map:
                arc_map[key] = set()
            arc_map[key].add(identifier)

    # Report duplicates
    conflicts = {k: v for k, v in arc_map.items() if len(v) > 1}

    if conflicts:
        print(" Common arcs found (same source & target, different identifiers):")
        for (src, tgt), ids in conflicts.items():
            print(f"  {src} -> {tgt}: {ids}")
    else:
        print(" No common arcs with same source and target found.")

    return conflicts


def parse_pnml_et(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    net = root.find(".//net")
    return net


def compose(pnml_files, original_file_name="composed"):
    """Compose the submodels into a single PNML Petri net using ET (no PM4Py).

    This function merges multiple PNML files by:
    1. Sharing transitions with the same name across different agents
    2. Keeping places separate (maintaining agent-specific identifiers)
    3. Updating arcs to connect to shared transitions
    """
    if not pnml_files:
        print("No PNML files provided for composition")
        return False

    print(f"Composing {len(pnml_files)} PNML files...")

    # Parse all input files and extract agent names
    trees = []
    nets = []
    agent_names = []
    for file_path in pnml_files:
        tree = ET.parse(file_path)
        trees.append(tree)
        net = tree.getroot().find(".//net")
        nets.append(net)

        # Extract agent name from file path (e.g., "Agent 1.pnml" -> "Agent_1")
        agent_name = os.path.splitext(os.path.basename(file_path))[0].replace(" ", "_")
        agent_names.append(agent_name)

    # Create the root structure for composed PNML
    composed_root = ET.Element("pnml")
    composed_net = ET.SubElement(composed_root, "net")
    composed_net.set("id", f"composed_{original_file_name}")
    composed_net.set("type", "http://www.pnml.org/version-2009/grammar/pnmlcoremodel")

    # Add net name
    net_name = ET.SubElement(composed_net, "name")
    net_name_text = ET.SubElement(net_name, "text")
    net_name_text.text = f"composed_{original_file_name}"

    # Add page
    composed_page = ET.SubElement(composed_net, "page")
    composed_page.set("id", "composed_page")

    # Collect all transitions and group by name
    transition_groups = {}  # transition_name -> [(transition_element, agent_name), ...]
    all_places = []  # (place_element, agent_name)
    all_arcs = []  # (arc_element, agent_name)

    for agent_name, net in zip(agent_names, nets):
        page = net.find("page")
        if page is None:
            continue

        # Collect places (keep all separate)
        for place in page.findall("place"):
            all_places.append((place, agent_name))

        # Collect transitions and group by name
        for transition in page.findall("transition"):
            name_elem = transition.find("name/text")
            # if "tau" in name_elem.text.lower():
            #     continue

            trans_name = (
                name_elem.text
                if name_elem is not None
                else f"unnamed_{transition.get('id')}"
            )

            if trans_name not in transition_groups:
                transition_groups[trans_name] = []

            transition_groups[trans_name].append((transition, agent_name))

        # Collect arcs
        for arc in page.findall("arc"):
            all_arcs.append((arc, agent_name))

    # Add all places to composed model (keeping them separate)
    place_id_mapping = {}  # (original_id, agent_name) -> new_id
    for place, agent_name in all_places:
        new_place = ET.SubElement(composed_page, "place")
        original_id = place.get("id")
        new_id = f"{original_id}_{agent_name}"
        new_place.set("id", new_id)

        place_id_mapping[(original_id, agent_name)] = new_id

        # Copy all child elements (name, type, etc.)
        for child in place:
            new_place.append(deepcopy(child))

    # Create shared transitions and mapping
    shared_transition_mapping = (
        {}
    )  # (original_id, agent_name) -> shared_id # TODO: apart from tau !!!

    for trans_name, transition_list in transition_groups.items():
        if "tau" in trans_name or "tau" in transition_list[0][0].get("id"):
            for transition, agent_name in transition_list:

                new_transition = ET.SubElement(composed_page, "transition")
                original_id = transition.get("id")
                new_id = f"{original_id}_{agent_name}"
                new_transition.set("id", new_id)

                shared_transition_mapping[(original_id, agent_name)] = new_id

                # Copy all child elements
                for child in transition:
                    new_transition.append(deepcopy(child))

        elif len(transition_list) > 1:
            # This transition appears in multiple files - create shared transition
            shared_id = f"shared_{trans_name}"
            shared_transition = ET.SubElement(composed_page, "transition")
            shared_transition.set("id", shared_id)

            # Use the first transition as template
            first_transition = transition_list[0][0]
            for child in first_transition:
                shared_transition.append(deepcopy(child))

            # Map all instances to this shared transition
            for transition, agent_name in transition_list:
                original_id = transition.get("id")
                shared_transition_mapping[(original_id, agent_name)] = shared_id

            agent_list = [agent_name for _, agent_name in transition_list]
            print(
                f"Created shared transition '{trans_name}' (used by agents: {', '.join(agent_list)})"
            )

        else:
            # This transition appears in only one file - keep it separate
            transition, agent_name = transition_list[0]
            new_transition = ET.SubElement(composed_page, "transition")
            original_id = transition.get("id")
            new_id = f"{original_id}_{agent_name}"
            new_transition.set("id", new_id)

            shared_transition_mapping[(original_id, agent_name)] = new_id

            # Copy all child elements
            for child in transition:
                new_transition.append(deepcopy(child))

    # Add arcs with updated source/target references
    for arc, agent_name in all_arcs:
        new_arc = ET.SubElement(composed_page, "arc")
        original_source = arc.get("source")
        original_target = arc.get("target")
        original_id = arc.get("id")

        # Generate new arc ID
        new_arc_id = f"{original_id}_{agent_name}"
        new_arc.set("id", new_arc_id)

        # Update source reference
        if (original_source, agent_name) in place_id_mapping:
            new_source = place_id_mapping[(original_source, agent_name)]
        elif (original_source, agent_name) in shared_transition_mapping:
            new_source = shared_transition_mapping[(original_source, agent_name)]
        else:
            new_source = f"{original_source}_{agent_name}"

        # Update target reference
        if (original_target, agent_name) in place_id_mapping:
            new_target = place_id_mapping[(original_target, agent_name)]
        elif (original_target, agent_name) in shared_transition_mapping:
            new_target = shared_transition_mapping[(original_target, agent_name)]
        else:
            new_target = f"{original_target}_{agent_name}"

        new_arc.set("source", new_source)
        new_arc.set("target", new_target)

        # Copy all child elements (identifier, etc.)
        for child in arc:
            new_arc.append(deepcopy(child))

    # Write the composed PNML file
    # output_path = f"./data/{original_file_name}/fully_composed_pnml/composed_{original_file_name}.pnml"
    output_path = (
        f"./data/{original_file_name}/composed_pnml/composed_{original_file_name}.pnml"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    remove_minor_places(composed_page)

    composed_tree = ET.ElementTree(composed_root)

    composed_tree.write(output_path, encoding="UTF-8", xml_declaration=True)

    print(f"Composed PNML saved to: {output_path}")
    print(
        f"Total shared transitions: {sum(1 for transitions in transition_groups.values() if len(transitions) > 1)}"
    )
    print(f"Total places: {len(all_places)}")
    print(f"Total arcs: {len(all_arcs)}")

    return True


def remove_minor_places(composed_page):
    """
    Remove minor places from the composed PNML page based on 3 conditions.
    """

    # Collect place data
    place_data = {}  # place_id -> {inputs, outputs, type, arc_vars}
    arcs = list(composed_page.findall("arc"))

    # Build quick arc lookup
    incoming = {}
    outgoing = {}
    for arc in arcs:
        src = arc.get("source")
        tgt = arc.get("target")
        arc_id = arc.get("id")
        # Collect variable/label text if exists
        var_texts = []
        for child in arc.findall(".//text"):
            if child.text:
                var_texts.append(child.text.strip())
        var_set = set(var_texts)

        if tgt not in incoming:
            incoming[tgt] = []
        incoming[tgt].append((src, var_set))

        if src not in outgoing:
            outgoing[src] = []
        outgoing[src].append((tgt, var_set))

    # Collect info for each place
    for place in composed_page.findall("place"):
        pid = place.get("id")
        # find type (if exists)
        type_elem = place.find("type/text")
        place_type = type_elem.text.strip() if type_elem is not None else ""

        inputs = set(src for src, _ in incoming.get(pid, []))
        outputs = set(tgt for tgt, _ in outgoing.get(pid, []))
        arc_vars = set()
        for _, vs in incoming.get(pid, []):
            arc_vars.update(vs)
        for _, vs in outgoing.get(pid, []):
            arc_vars.update(vs)

        place_data[pid] = {
            "inputs": inputs,
            "outputs": outputs,
            "type": place_type,
            "arc_vars": arc_vars,
            "element": place,
        }

    # Detect minor places
    minor_places = set()
    for p, pdata in place_data.items():
        for q, qdata in place_data.items():
            if p == q:
                continue

            # Condition 1: same inputs & outputs
            if pdata["inputs"] != qdata["inputs"]:
                continue
            if pdata["outputs"] != qdata["outputs"]:
                continue

            # Condition 2: type subset
            if pdata["type"] == "" or qdata["type"] == "":
                continue
            if pdata["type"] == qdata["type"]:
                continue
            if pdata["type"] not in qdata["type"]:
                continue

            # Condition 3: arc_vars subset
            if not pdata["arc_vars"].issubset(qdata["arc_vars"]):
                continue

            # ✅ p is minor to q
            minor_places.add(p)

    # Remove minor places and their arcs
    for pid in minor_places:
        place_elem = place_data[pid]["element"]
        composed_page.remove(place_elem)

        # remove arcs connected to it
        for arc in arcs:
            if arc.get("source") == pid or arc.get("target") == pid:
                if arc in composed_page:
                    composed_page.remove(arc)

    print(f"Removed {len(minor_places)} minor places: {', '.join(minor_places)}")


if __name__ == "__main__":

    # generation order: projected_xes, first_pnml, post_processed_pnml, composed_pnml, images

    original_file_path = "/Users/xufanlu/Projects/Process Mining/Process-Discovery-Typed-Jackson-Nets/data/original_xes_file/TASE_EM_log.xes"
    # original_file_path= "./data/original_xes_file/IP-4_init_log.xes"

    original_file_name = original_file_path.split("/")[-1].split(".")[0]

    # Create necessary directories
    if not os.path.exists(f"./data/{original_file_name}/first_pnml"):
        os.makedirs(f"./data/{original_file_name}/first_pnml")
    if not os.path.exists(f"./data/{original_file_name}/post_processed_pnml"):
        os.makedirs(f"./data/{original_file_name}/post_processed_pnml")
    if not os.path.exists(f"./data/{original_file_name}/projected_xes"):
        os.makedirs(f"./data/{original_file_name}/projected_xes")
    if not os.path.exists(f"./data/{original_file_name}/composed_pnml"):
        os.makedirs(f"./data/{original_file_name}/composed_pnml")
    if not os.path.exists(f"./data/{original_file_name}/fully_composed_pnml"):
        os.makedirs(f"./data/{original_file_name}/fully_composed_pnml")
    if not os.path.exists(f"./data/{original_file_name}/images"):
        os.makedirs(f"./data/{original_file_name}/images")

    raw_log = xes_importer.apply(original_file_path)
    orgs = projection_based_on_organization_1(
        raw_log, original_file_name=original_file_name
    )  # this method needs to be changed

    print(f"Processing {len(orgs)} organizations: {orgs}")
    composed_pnml_files = []

    for org in orgs:
        print(f"\n--- Processing {org} ---")
        net, im, fm = apply_inductive_miner(
            log_file_path=f"./data/{original_file_name}/projected_xes/{org}.xes",
            original_file_name=original_file_name,
        )

        add_identifiers(
            log_file_path=f"./data/{original_file_name}/first_pnml/{org}.pnml",
            org=org,
            original_file_name=original_file_name,
        )
        custom_petri_net_visualization(
            file_name=f"./data/{original_file_name}/post_processed_pnml/{org}.pnml",
            title=f"Petri Net for {org}",
            original_file_name=original_file_name,
        )
        composed_pnml_files.append(
            f"./data/{original_file_name}/post_processed_pnml/{org}.pnml"
        )

    compose(composed_pnml_files, original_file_name=original_file_name)
    custom_petri_net_visualization(
        file_name=f"./data/{original_file_name}/composed_pnml/composed_{original_file_name}.pnml",
        title="Composed Petri Net",
        original_file_name=original_file_name,
    )
    get_shared_arcs(composed_pnml_files)

    # no removement if the sind and source
    # for org in orgs:
    #     print(f"\n--- Processing {org} ---")
    #     net,im, fm =apply_inductive_miner(log_file_path=f"./data/{original_file_name}/projected_xes/{org}.xes", original_file_name=original_file_name)

    #     add_identifiers(log_file_path=f"./data/{original_file_name}/first_pnml/{org}.pnml", org=org,original_file_name=original_file_name)
    #   #  custom_petri_net_visualization(file_name=f"./data/{original_file_name}/post_processed_pnml/{org}.pnml", title=f"Petri Net for {org}", original_file_name=original_file_name)
    #     composed_pnml_files.append(f"./data/{original_file_name}/first_pnml/{org}.pnml")

    # compose(composed_pnml_files, original_file_name=original_file_name)
#    # custom_petri_net_visualization(file_name=f"./data/{original_file_name}/composed_pnml/composed_{original_file_name}.pnml", title="Composed Petri Net", original_file_name=original_file_name)
# get_shared_arcs(composed_pnml_files)
