"""
Mesa Space Module
=================

Objects used to add a spatial component to a model.

Grid: base grid, a simple list-of-lists.
SingleGrid: grid which strictly enforces one object per cell.
MultiGrid: extension to Grid where each cell is a set of objects.

"""
# Instruction for PyLint to suppress variable name errors, since we have a
# good reason to use one-character variable names for x and y.
# pylint: disable=invalid-name

import itertools

import numpy as np

from typing import (
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Set,
    Sequence,
    Tuple,
    Union,
    cast,
    overload,
)
from .agent import Agent

Coordinate = Tuple[int, int]
GridContent = Union[Optional[Agent], Set[Agent]]
# used in ContinuousSpace
FloatCoordinate = Union[Tuple[float, float], np.ndarray]


def accept_tuple_argument(wrapped_function):
    """Decorator to allow grid methods that take a list of (x, y) coord tuples
    to also handle a single position, by automatically wrapping tuple in
    single-item list rather than forcing user to do it.

    """

    def wrapper(*args: Any):
        if isinstance(args[1], tuple) and len(args[1]) == 2:
            return wrapped_function(args[0], [args[1]])
        else:
            return wrapped_function(*args)

    return wrapper


class Grid:
    """Base class for a square grid.

    Grid cells are indexed by [x][y], where [0][0] is assumed to be the
    bottom-left and [width-1][height-1] is the top-right. If a grid is
    toroidal, the top and bottom, and left and right, edges wrap to each other

    Properties:
        width, height: The grid's width and height.
        torus: Boolean which determines whether to treat the grid as a torus.
        grid: Internal list-of-lists which holds the grid cells themselves.

    Methods:
        get_neighbors: Returns the objects surrounding a given cell.
        get_neighborhood: Returns the cells surrounding a given cell.
        get_cell_list_contents: Returns the contents of a list of cells
            ((x,y) tuples)
        neighbor_iter: Iterates over position neighbours.
        coord_iter: Returns coordinates as well as cell contents.
        place_agent: Positions an agent on the grid, and set its pos variable.
        move_agent: Moves an agent from its current position to a new position.
        iter_neighborhood: Returns an iterator over cell coordinates that are
        in the neighborhood of a certain point.
        torus_adj: Converts coordinate, handles torus looping.
        out_of_bounds: Determines whether position is off the grid, returns
        the out of bounds coordinate.
        iter_cell_list_contents: Returns an iterator of the contents of the
        cells identified in cell_list.
        get_cell_list_contents: Returns a list of the contents of the cells
        identified in cell_list.
        remove_agent: Removes an agent from the grid.
        is_cell_empty: Returns a bool of the contents of a cell.

    """

    def __init__(self, width: int, height: int, torus: bool) -> None:
        """Create a new grid.

        Args:
            width, height: The width and height of the grid
            torus: Boolean whether the grid wraps or not.

        """
        self.height = height
        self.width = width
        self.torus = torus

        self.grid: List[List[GridContent]] = []

        for x in range(self.width):
            col: List[GridContent] = []
            for y in range(self.height):
                col.append(self.default_val())
            self.grid.append(col)

        # Add all cells to the empties list.
        self.empties = set(itertools.product(*(range(self.width), range(self.height))))

        # Neighborhood Cache
        self._neighborhood_cache: Dict[Any, List[Coordinate]] = dict()

    @staticmethod
    def default_val() -> None:
        """ Default value for new cell elements. """
        return None

    @overload
    def __getitem__(self, index: int) -> List[GridContent]:
        ...

    @overload
    def __getitem__(
        self, index: Tuple[Union[int, slice], Union[int, slice]]
    ) -> Union[GridContent, List[GridContent]]:
        ...

    @overload
    def __getitem__(self, index: Sequence[Coordinate]) -> List[GridContent]:
        ...

    def __getitem__(
        self,
        index: Union[
            int,
            Sequence[Coordinate],
            Tuple[Union[int, slice], Union[int, slice]],
        ],
    ) -> Union[GridContent, List[GridContent]]:
        """Access contents from the grid."""

        if isinstance(index, int):
            # grid[x]
            return self.grid[index]

        if isinstance(index[0], tuple):
            # grid[(x1, y1), (x2, y2)]
            index = cast(Sequence[Coordinate], index)

            cells = []
            for pos in index:
                x1, y1 = self.torus_adj(pos)
                cells.append(self.grid[x1][y1])
            return cells

        x, y = index

        if isinstance(x, int) and isinstance(y, int):
            # grid[x, y]
            index = cast(Coordinate, index)
            x, y = self.torus_adj(index)
            return self.grid[x][y]

        if isinstance(x, int):
            # grid[x, :]
            x, _ = self.torus_adj((x, 0))
            x = slice(x, x + 1)

        if isinstance(y, int):
            # grid[:, y]
            _, y = self.torus_adj((0, y))
            y = slice(y, y + 1)

        # grid[:, :]
        x, y = (cast(slice, x), cast(slice, y))
        cells = []
        for rows in self.grid[x]:
            for cell in rows[y]:
                cells.append(cell)
        return cells

        raise IndexError

    def __iter__(self) -> Iterator[GridContent]:
        """
        create an iterator that chains the
        rows of grid together as if one list:
        """
        return itertools.chain(*self.grid)

    def coord_iter(self) -> Iterator[Tuple[GridContent, int, int]]:
        """ An iterator that returns coordinates as well as cell contents. """
        for row in range(self.width):
            for col in range(self.height):
                yield self.grid[row][col], row, col  # agent, x, y

    def neighbor_iter(
        self, pos: Coordinate, moore: bool = True
    ) -> Iterator[GridContent]:
        """Iterate over position neighbors.

        Args:
            pos: (x,y) coords tuple for the position to get the neighbors of.
            moore: Boolean for whether to use Moore neighborhood (including
                   diagonals) or Von Neumann (only up/down/left/right).

        """
        neighborhood = self.get_neighborhood(pos, moore=moore)
        return self.iter_cell_list_contents(neighborhood)

    def iter_neighborhood(
        self,
        pos: Coordinate,
        moore: bool,
        include_center: bool = False,
        radius: int = 1,
    ) -> Iterator[Coordinate]:
        """Return an iterator over cell coordinates that are in the
        neighborhood of a certain point.

        Args:
            pos: Coordinate tuple for the neighborhood to get.
            moore: If True, return Moore neighborhood
                        (including diagonals)
                   If False, return Von Neumann neighborhood
                        (exclude diagonals)
            include_center: If True, return the (x, y) cell as well.
                            Otherwise, return surrounding cells only.
            radius: radius, in cells, of neighborhood to get.

        Returns:
            A list of coordinate tuples representing the neighborhood. For
            example with radius 1, it will return list with number of elements
            equals at most 9 (8) if Moore, 5 (4) if Von Neumann (if not
            including the center).

        """
        yield from self.get_neighborhood(pos, moore, include_center, radius)

    def get_neighborhood(
        self,
        pos: Coordinate,
        moore: bool,
        include_center: bool = False,
        radius: int = 1,
    ) -> List[Coordinate]:
        """Return a list of cells that are in the neighborhood of a
        certain point.

        Args:
            pos: Coordinate tuple for the neighborhood to get.
            moore: If True, return Moore neighborhood
                   (including diagonals)
                   If False, return Von Neumann neighborhood
                   (exclude diagonals)
            include_center: If True, return the (x, y) cell as well.
                            Otherwise, return surrounding cells only.
            radius: radius, in cells, of neighborhood to get.

        Returns:
            A list of coordinate tuples representing the neighborhood;
            With radius 1, at most 9 if Moore, 5 if Von Neumann (8 and 4
            if not including the center).

        """
        cache_key = (pos, moore, include_center, radius)
        neighborhood = self._neighborhood_cache.get(cache_key, None)

        if neighborhood is None:
            coordinates: Set[Coordinate] = set()

            x, y = pos
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx == 0 and dy == 0 and not include_center:
                        continue
                    # Skip coordinates that are outside manhattan distance
                    if not moore and abs(dx) + abs(dy) > radius:
                        continue

                    coord = (x + dx, y + dy)

                    if self.out_of_bounds(coord):
                        # Skip if not a torus and new coords out of bounds.
                        if not self.torus:
                            continue
                        coord = self.torus_adj(coord)

                    coordinates.add(coord)

            neighborhood = coordinates
            self._neighborhood_cache[cache_key] = neighborhood

        return neighborhood

    def iter_neighbors(
        self,
        pos: Coordinate,
        moore: bool,
        include_center: bool = False,
        radius: int = 1,
    ) -> Iterator[GridContent]:
        """Return an iterator over neighbors to a certain point.

        Args:
            pos: Coordinates for the neighborhood to get.
            moore: If True, return Moore neighborhood
                    (including diagonals)
                   If False, return Von Neumann neighborhood
                     (exclude diagonals)
            include_center: If True, return the (x, y) cell as well.
                            Otherwise,
                            return surrounding cells only.
            radius: radius, in cells, of neighborhood to get.

        Returns:
            An iterator of non-None objects in the given neighborhood;
            at most 9 if Moore, 5 if Von-Neumann
            (8 and 4 if not including the center).
        """
        neighborhood = self.get_neighborhood(pos, moore, include_center, radius)
        return self.iter_cell_list_contents(neighborhood)

    def get_neighbors(
        self,
        pos: Coordinate,
        moore: bool,
        include_center: bool = False,
        radius: int = 1,
    ) -> List[GridContent]:
        """Return a list of neighbors to a certain point.

        Args:
            pos: Coordinate tuple for the neighborhood to get.
            moore: If True, return Moore neighborhood
                    (including diagonals)
                   If False, return Von Neumann neighborhood
                     (exclude diagonals)
            include_center: If True, return the (x, y) cell as well.
                            Otherwise,
                            return surrounding cells only.
            radius: radius, in cells, of neighborhood to get.

        Returns:
            A list of non-None objects in the given neighborhood;
            at most 9 if Moore, 5 if Von-Neumann
            (8 and 4 if not including the center).

        """
        return list(self.iter_neighbors(pos, moore, include_center, radius))

    def torus_adj(self, pos: Coordinate) -> Coordinate:
        """ Convert coordinate, handling torus looping. """
        if not self.out_of_bounds(pos):
            return pos
        elif not self.torus:
            raise Exception("Point out of bounds, and space non-toroidal.")
        else:
            return pos[0] % self.width, pos[1] % self.height

    def out_of_bounds(self, pos: Coordinate) -> bool:
        """
        Determines whether position is off the grid, returns the out of
        bounds coordinate.
        """
        x, y = pos
        return x < 0 or x >= self.width or y < 0 or y >= self.height

    @accept_tuple_argument
    def iter_cell_list_contents(
        self, cell_list: Iterable[Coordinate]
    ) -> Iterator[GridContent]:
        """
        Args:
            cell_list: Array-like of (x, y) tuples, or single tuple.

        Returns:
            An iterator of the contents of the cells identified in cell_list

        """
        return filter(None, (self.grid[x][y] for x, y in cell_list))

    @accept_tuple_argument
    def get_cell_list_contents(
        self, cell_list: Iterable[Coordinate]
    ) -> List[GridContent]:
        """
        Args:
            cell_list: Array-like of (x, y) tuples, or single tuple.

        Returns:
            A list of the contents of the cells identified in cell_list

        """
        return list(self.iter_cell_list_contents(cell_list))

    def move_agent(self, agent: Agent, pos: Coordinate) -> None:
        """
        Move an agent from its current position to a new position.

        Args:
            agent: Agent object to move. Assumed to have its current location
                   stored in a 'pos' tuple.
            pos: Tuple of new position to move the agent to.

        """
        pos = self.torus_adj(pos)
        self._remove_agent(agent.pos, agent)
        self._place_agent(pos, agent)
        agent.pos = pos

    def place_agent(self, agent: Agent, pos: Coordinate) -> None:
        """ Position an agent on the grid, and set its pos variable. """
        self._place_agent(pos, agent)
        agent.pos = pos

    def _place_agent(self, pos: Coordinate, agent: Agent) -> None:
        """ Place the agent at the correct location. """
        x, y = pos
        self.grid[x][y] = agent
        self.empties.discard(pos)

    def remove_agent(self, agent: Agent) -> None:
        """ Remove the agent from the grid and set its pos variable to None. """
        pos = agent.pos
        self._remove_agent(pos, agent)
        agent.pos = None

    def _remove_agent(self, pos: Coordinate, agent: Agent) -> None:
        """ Remove the agent from the given location. """
        x, y = pos
        self.grid[x][y] = None
        self.empties.add(pos)

    def is_cell_empty(self, pos: Coordinate) -> bool:
        """ Returns a bool of the contents of a cell. """
        x, y = pos
        return self.grid[x][y] == self.default_val()

    def move_to_empty(self, agent: Agent) -> None:
        """ Moves agent to a random empty cell, vacating agent's old cell. """
        pos = agent.pos
        if not self.empties:
            raise Exception("ERROR: No empty cells")
        new_pos = agent.random.choice(self.empties)
        self._place_agent(new_pos, agent)
        agent.pos = new_pos
        self._remove_agent(pos, agent)

    def exists_empty_cells(self) -> bool:
        """ Return True if any cells empty else False. """
        return self.empties


class SingleGrid(Grid):
    """ Grid where each cell contains exactly at most one object. """

    empties: Set[Coordinate] = set()

    def __init__(self, width: int, height: int, torus: bool) -> None:
        """Create a new single-item grid.

        Args:
            width, height: The width and width of the grid
            torus: Boolean whether the grid wraps or not.

        """
        super().__init__(width, height, torus)

    def position_agent(
        self, agent: Agent, x: Union[int, str] = "random", y: Union[int, str] = "random"
    ) -> None:
        """Position an agent on the grid.
        This is used when first placing agents! Use 'move_to_empty()'
        when you want agents to jump to an empty cell.
        Use 'swap_pos()' to swap agents positions.
        If x or y are positive, they are used, but if "random",
        we get a random position.
        Ensure this random position is not occupied (in Grid).

        """
        if x == "random" or y == "random":
            if not self.empties:
                raise Exception("ERROR: Grid full")
            coords = agent.random.choice(self.empties)
        else:
            coords = (x, y)

        agent.pos = coords
        self._place_agent(coords, agent)

    def _place_agent(self, pos: Coordinate, agent: Agent) -> None:
        if self.is_cell_empty(pos):
            super()._place_agent(pos, agent)
        else:
            raise Exception("Cell not empty")
