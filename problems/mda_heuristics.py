import numpy as np
import networkx as nx
from typing import *

from framework import *
from .mda_problem import *
from .cached_air_distance_calculator import CachedAirDistanceCalculator


__all__ = ['MDAMaxAirDistHeuristic', 'MDASumAirDistHeuristic',
           'MDAMSTAirDistHeuristic', 'MDATestsTravelDistToNearestLabHeuristic']


class MDAMaxAirDistHeuristic(HeuristicFunction):
    heuristic_name = 'MDA-Max-AirDist'

    def __init__(self, problem: GraphProblem):
        super(MDAMaxAirDistHeuristic, self).__init__(problem)
        assert isinstance(self.problem, MDAProblem)
        assert self.problem.optimization_objective == MDAOptimizationObjective.Distance
        self.cached_air_distance_calculator = CachedAirDistanceCalculator()

    def estimate(self, state: GraphProblemState) -> float:
        """
        This method calculated a lower bound of the distance of the remaining path of the ambulance,
         by calculating the maximum distance within the group of air distances between each two
         junctions in the remaining ambulance path. We don't consider laboratories here because we
         do not know what laboratories would be visited in an optimal solution.

        TODO [Ex.16]:
            Calculate the `total_distance_lower_bound` by taking the maximum over the group
                {airDistanceBetween(j1,j2) | j1,j2 in CertainJunctionsInRemainingAmbulancePath s.t. j1 != j2}
            Notice: The problem is accessible via the `self.problem` field.
            Use `self.cached_air_distance_calculator.get_air_distance_between_junctions()` for air
                distance calculations.
            Use python's built-in `max()` function. Note that `max()` can receive an *ITERATOR*
                and return the item with the maximum value within this iterator.
            That is, you can simply write something like this:
        >>> max(<some expression using item1 & item2>
        >>>     for item1 in some_items_collection
        >>>     for item2 in some_items_collection
        >>>     if <some condition over item1 & item2>)
        """
        assert isinstance(self.problem, MDAProblem)
        assert isinstance(state, MDAState)
        all_certain_junctions_in_remaining_ambulance_path = \
            self.problem.get_all_certain_junctions_in_remaining_ambulance_path(state)
        if len(all_certain_junctions_in_remaining_ambulance_path) < 2:
            return 0

        return max(self.cached_air_distance_calculator.get_air_distance_between_junctions(j1, j2)
                   for j1 in all_certain_junctions_in_remaining_ambulance_path
                   for j2 in all_certain_junctions_in_remaining_ambulance_path
                   if j1.index != j2.index)         # consider: " if j1.index < j2.index "



class MDASumAirDistHeuristic(HeuristicFunction):
    heuristic_name = 'MDA-Sum-AirDist'

    def __init__(self, problem: GraphProblem):
        super(MDASumAirDistHeuristic, self).__init__(problem)
        assert isinstance(self.problem, MDAProblem)
        assert self.problem.optimization_objective == MDAOptimizationObjective.Distance
        self.cached_air_distance_calculator = CachedAirDistanceCalculator()

    def estimate(self, state: GraphProblemState) -> float:
        """
        This heuristic evaluates the distance of the remaining ambulance route in the following way:
        It builds a path that starts in the current ambulance's location, and each next junction in
         the path is the (air-distance) nearest junction (to the previous one in the path) among
         all certain junctions (in `all_certain_junctions_in_remaining_ambulance_path`) that haven't
         been visited yet.
        The remaining distance estimation is the cost of this built path.
        Note that we ignore here the problem constraints (like enforcing the #matoshim and free
         space in the ambulance's fridge). We only make sure to visit all certain junctions in
         `all_certain_junctions_in_remaining_ambulance_path`.
        TODO [Ex.19]:
            Complete the implementation of this method.
            Use `self.cached_air_distance_calculator.get_air_distance_between_junctions()` for air
             distance calculations.
        """
        assert isinstance(self.problem, MDAProblem)
        assert isinstance(state, MDAState)

        all_certain_junctions_in_remaining_ambulance_path = \
            self.problem.get_all_certain_junctions_in_remaining_ambulance_path(state)
        all_certain_junctions_in_remaining_ambulance_path = set(all_certain_junctions_in_remaining_ambulance_path)

        if len(all_certain_junctions_in_remaining_ambulance_path) < 2:
            return 0

        remaining_juncs = len(all_certain_junctions_in_remaining_ambulance_path)
        sum = 0
        min_junc = None
        min_val = float('inf')

        if isinstance(state.current_site, Junction):
            curr_junc = state.current_site
        else:
            curr_junc = state.current_site.location

        for i in range(remaining_juncs):

            for junction in all_certain_junctions_in_remaining_ambulance_path:
                curr_dist = self.cached_air_distance_calculator.get_air_distance_between_junctions(curr_junc, junction)
                if curr_dist < min_val:
                    min_val = curr_dist
                    min_junc = junction
            all_certain_junctions_in_remaining_ambulance_path.remove(min_junc)
            sum += min_val
            curr_junc = min_junc
            min_junc = None
            min_val = float('inf')
        return sum


class MDAMSTAirDistHeuristic(HeuristicFunction):
    heuristic_name = 'MDA-MST-AirDist'

    def __init__(self, problem: GraphProblem):
        super(MDAMSTAirDistHeuristic, self).__init__(problem)
        assert isinstance(self.problem, MDAProblem)
        assert self.problem.optimization_objective == MDAOptimizationObjective.Distance
        self.cached_air_distance_calculator = CachedAirDistanceCalculator()

    def estimate(self, state: GraphProblemState) -> float:
        """
        This heuristic returns a lower bound for the distance of the remaining route of the ambulance.
        Here this remaining distance is bounded (from below) by the weight of the minimum-spanning-tree
         of the graph, in-which the vertices are the junctions in the remaining ambulance route, and the
         edges weights (edge between each junctions pair) are the air-distances between the junctions.
        """
        assert isinstance(self.problem, MDAProblem)
        assert isinstance(state, MDAState)

        return self._calculate_junctions_mst_weight_using_air_distance(
            self.problem.get_all_certain_junctions_in_remaining_ambulance_path(state))

    def _calculate_junctions_mst_weight_using_air_distance(self, junctions: List[Junction]) -> float:
        """
        TODO [Ex.22]: Implement this method.
              Use `networkx` (nx) package (already imported in this file) to calculate the weight
               of the minimum-spanning-tree of the graph in which the vertices are the given junctions
               and there is an edge between each pair of distinct junctions (no self-loops) for which
               the weight is the air distance between these junctions.
              Use the method `self.cached_air_distance_calculator.get_air_distance_between_junctions()`
               to calculate the air distance between the two junctions.
              Google for how to use `networkx` package for this purpose.
              Use `nx.minimum_spanning_tree()` to get an MST. Calculate the MST size using the method
              `.size(weight='weight')`. Do not manually sum the edges' weights.
        """
        new_graph = nx.Graph()
        new_graph.add_nodes_from(junctions)

        for j1 in junctions:
            for j2 in junctions:
                if j1.index != j2.index:
                    curr_weight = self.cached_air_distance_calculator.get_air_distance_between_junctions(j1, j2)
                    new_graph.add_edge(j1, j2, weight=curr_weight)

        return nx.minimum_spanning_tree(new_graph).size(weight='weight')


class MDATestsTravelDistToNearestLabHeuristic(HeuristicFunction):
    heuristic_name = 'MDA-TimeObjectiveSumOfMinAirDistFromLab'

    def __init__(self, problem: GraphProblem):
        super(MDATestsTravelDistToNearestLabHeuristic, self).__init__(problem)
        assert isinstance(self.problem, MDAProblem)
        assert self.problem.optimization_objective == MDAOptimizationObjective.TestsTravelDistance
        self.cached_air_distance_calculator = CachedAirDistanceCalculator()

    def estimate(self, state: GraphProblemState) -> float:
        """
        This heuristic returns a lower bound to the remained tests-travel-distance of the remained ambulance path.
        The main observation is that driving from a laboratory to a reported-apartment does not increase the
         tests-travel-distance cost. So the best case (lowest cost) is when we go to the closest laboratory right
         after visiting any reported-apartment.
        If the ambulance currently stores tests, this total remained cost includes the #tests_on_ambulance times
         the distance from the current ambulance location to the closest lab.
        The rest part of the total remained cost includes the distance between each non-visited reported-apartment
         and the closest lab (to this apartment) times the roommates in this apartment (as we take tests for all
         roommates).
        TODO [Ex.29]:
            Complete the implementation of this method.
            Use `self.problem.get_reported_apartments_waiting_to_visit(state)`.
        """
        assert isinstance(self.problem, MDAProblem)
        assert isinstance(state, MDAState)

        labs_list = self.problem.problem_input.laboratories

        def air_dist_to_closest_lab(junction: Junction) -> float:
            """
            Returns the distance between `junction` and the laboratory that is closest to `junction`.
            """
            return min(self.cached_air_distance_calculator.get_air_distance_between_junctions(junction, lab.location)
                       for lab in labs_list
                       if lab != junction)

        summ = 0
        apartments = self.problem.get_reported_apartments_waiting_to_visit(state)
        for apartment in apartments:
            min_dist_from_lab = air_dist_to_closest_lab(apartment.location)
            summ += apartment.nr_roommates * min_dist_from_lab
        summ += state.get_total_nr_tests_taken_and_stored_on_ambulance() * air_dist_to_closest_lab(state.current_location)
        return summ
