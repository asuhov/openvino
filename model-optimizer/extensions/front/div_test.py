"""
 Copyright (C) 2018-2020 Intel Corporation

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

import unittest

import numpy as np

from extensions.front.div import Div
from mo.utils.ir_engine.compare_graphs import compare_graphs
from mo.utils.unittest.graph import build_graph, result, regular_op_with_shaped_data, valued_const_with_data, connect, \
    connect_data

nodes = {
    **regular_op_with_shaped_data('placeholder_1', [1, 227, 227, 3], {'type': 'Parameter'}),
    **regular_op_with_shaped_data('placeholder_2', [1, 227, 227, 3], {'type': 'Parameter'}),
    **regular_op_with_shaped_data('div', None, {'op': 'Div', 'type': 'Divide', 'name': 'my_div'}),

    **regular_op_with_shaped_data('reciprocal', [1, 227, 227, 3], {'type': 'Power'}),
    **valued_const_with_data('minus_one', np.array(-1.)),
    **regular_op_with_shaped_data('mul', None, {'type': 'Multiply'}),

    **result(),
}


class TestDiv(unittest.TestCase):
    def test_div_test_1(self):
        # Test with two different inputs from two placeholders
        graph = build_graph(nodes, [
            *connect('placeholder_1', '0:div'),
            *connect('placeholder_2', '1:div'),
            *connect('div', 'output'),
        ], nodes_with_edges_only=True)
        Div().find_and_replace_pattern(graph)

        graph_ref = build_graph(nodes, [
            *connect('placeholder_1', '0:mul'),
            *connect('placeholder_2', '0:reciprocal'),
            *connect('minus_one', '1:reciprocal'),
            *connect('reciprocal', '1:mul'),
            *connect('mul', 'output'),
        ], nodes_with_edges_only=True)

        (flag, resp) = compare_graphs(graph, graph_ref, 'output', check_op_attrs=True)
        self.assertTrue(flag, resp)
        self.assertTrue(graph.node[graph.get_nodes_with_attributes(type='Multiply')[0]]['name'] == 'my_div')

    def test_div_test_2(self):
        # Test with two same inputs from one placeholder
        graph = build_graph(nodes, [
            *connect('placeholder_1:0', '0:div'),
            *connect_data('placeholder_1:0', '1:div'),
            *connect('div', 'output'),
        ], nodes_with_edges_only=True)
        Div().find_and_replace_pattern(graph)

        graph_ref = build_graph(nodes, [
            *connect('placeholder_1:0', '0:mul'),
            *connect_data('placeholder_1:0', '0:reciprocal'),
            *connect('minus_one', '1:reciprocal'),
            *connect('reciprocal', '1:mul'),
            *connect('mul', 'output'),
        ], nodes_with_edges_only=True)

        (flag, resp) = compare_graphs(graph, graph_ref, 'output', check_op_attrs=True)
        self.assertTrue(flag, resp)
        self.assertTrue(graph.node[graph.get_nodes_with_attributes(type='Multiply')[0]]['name'] == 'my_div')
